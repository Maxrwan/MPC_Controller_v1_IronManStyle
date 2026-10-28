"""Atomic record publication and selected-artifact integrity checks."""

import hashlib
import io
import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path

from tools.apex_workbench.configuration import validate, validate_note


class IntegrityError(ValueError):
    """Retained data is incomplete, unverified or changed."""


def read_json(path):
    return json.loads(Path(path).read_text())


def read_status(directory, *, lifecycle_only=False):
    status = read_json(Path(directory) / "status.json")
    if not isinstance(status, dict) or status.get("state") not in {
        "queued",
        "running",
        "finalizing",
        "completed",
        "failed",
        "cancelled",
        "timed_out",
        "interrupted",
        "evidence_failed",
        "quarantined",
    }:
        raise IntegrityError("Incomplete or unknown status contract")
    for key in ("pid", "supervisor_pid"):
        if key in status and (
            isinstance(status[key], bool) or not isinstance(status[key], int) or status[key] <= 0
        ):
            raise IntegrityError(f"Invalid lifecycle field: {key}")
    if not lifecycle_only:
        for key in ("scientific_outcome", "evidence_state"):
            if key in status and not isinstance(status[key], str):
                raise IntegrityError(f"Invalid status field: {key}")
    return status


def read_request(directory, *, verified=False):
    """Validate every field the UI consumes; never repair retained metadata."""
    request = (
        artifact_json(directory, "request.json")
        if verified
        else read_json(Path(directory) / "request.json")
    )
    if not isinstance(request, dict):
        raise IntegrityError("Request must be a JSON object")
    try:
        validate(request["adapter"], request["effective"])
        validate_note(request["prediction"])
        if request["adapter"] == "dynamic_lab":
            from tools.apex_workbench.lab_configuration import validate_context, validate_resolved
            from tools.apex_workbench.lab_sources import validate as validate_inventory

            validate_context(request["effective"], request["execution_context"])
            validate_inventory(request)
            validate_resolved(
                request["effective"],
                request["lab_resolved"],
                vehicle_yaml=request["provenance"]["vehicle_yaml"],
            )
    except (KeyError, TypeError, ValueError) as error:
        raise IntegrityError(f"Incomplete or invalid request: {error}") from error
    return request


def required_artifacts(request, status):
    """Successful version-2 exports are required; failed/legacy exports may be absent."""
    if (
        request.get("record_version") != 2
        or status.get("scientific_outcome", status["state"]) != "completed"
    ):
        return set()
    expected = {
        "experiment/states.csv",
        "experiment/summary.json",
        "experiment/geometry.csv",
        "experiment/trajectory_xy.csv",
        "experiment/telemetry_contract.json",
        "worker_result.json",
        "numerical_environment.json",
    }
    if request["adapter"] == "lqr_baseline":
        expected.add("experiment/controls.csv")
    if request["adapter"] == "dynamic_lab":
        expected.update(
            {
                "experiment/controls.csv",
                "experiment/diagnostics.csv",
                "experiment/resolved_lab.json",
                "experiment/track_samples.csv",
                "request.json",
                "execution.json",
                "worker.json",
                "supervisor.json",
                "stdout.log",
                "stderr.log",
            }
        )
    return expected


def write_json(path, value, *, exclusive=False):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, prefix=".pending-", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            os.link(
                temporary, path
            )  # Complete bytes become visible; never replace an older version.
        else:
            temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def signature(path):
    info = path.stat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@lru_cache(maxsize=8)
def _checked_bytes(path, observed, expected):
    data = Path(path).read_bytes()
    if signature(Path(path)) != observed or hashlib.sha256(data).hexdigest() != expected:
        raise IntegrityError(f"Artifact checksum mismatch: {Path(path).name}")
    return data


def artifact_manifest(directory):
    """Verify the committed manifest before interpreting membership or consuming files."""
    directory = Path(directory)
    try:
        status = read_status(directory)
        if status.get("state") not in {
            "completed",
            "failed",
            "cancelled",
            "timed_out",
            "interrupted",
        }:
            raise IntegrityError("Execution/evidence finalization is not complete")
        if status.get("evidence_state", "valid") != "valid":
            raise IntegrityError("Evidence is failed or incomplete; telemetry is quarantined")
        manifest_data = (directory / "artifacts.json").read_bytes()
        if status.get("manifest_sha256"):
            if hashlib.sha256(manifest_data).hexdigest() != status["manifest_sha256"]:
                raise IntegrityError("Artifact manifest checksum mismatch")
        elif status.get("record_version") == 2:
            raise IntegrityError("Corrected run has no committed artifact manifest")
        manifest = json.loads(manifest_data)
        if not isinstance(manifest, dict):
            raise IntegrityError("Artifact manifest must be a JSON object")
        return manifest
    except (OSError, TypeError, AttributeError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Unverified artifact manifest: {error}") from error


def check_required_artifacts(directory, request, status):
    """Every listed file must remain present; selected contents are hashed on ingestion."""
    manifest = artifact_manifest(directory)
    root = Path(directory).resolve()
    for relative in sorted(set(manifest) | required_artifacts(request, status)):
        path = Path(directory) / relative
        if not path.resolve().is_relative_to(root):
            raise IntegrityError(f"Retained artifact lies outside its run directory: {relative}")
        if relative not in manifest or not path.is_file():
            raise IntegrityError(f"Required retained artifact missing: {relative}")


def artifact_bytes(directory, relative, *, optional=False):
    """Optional means never recorded/produced; a missing manifest-listed file always fails."""
    directory = Path(directory)
    try:
        manifest = artifact_manifest(directory)
        if optional and relative not in manifest and not (directory / relative).exists():
            return None
        entry = manifest[relative]
        path = directory / relative
        if not path.resolve().is_relative_to(directory.resolve()):
            raise IntegrityError("Artifact lies outside its run directory")
        observed = signature(path)
        if "bytes" in entry and entry["bytes"] != observed[2]:
            raise IntegrityError(f"Artifact size mismatch: {relative}")
        data = _checked_bytes(str(path), observed, entry["sha256"])
        # A cached read must still match the file identity at consumption time.
        if signature(path) != observed:
            raise IntegrityError(f"Artifact changed while reading: {relative}")
        return data
    except (OSError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as error:
        raise IntegrityError(f"Unverified artifact {relative}: {error}") from error


def artifact_json(directory, relative, *, optional=False):
    try:
        data = artifact_bytes(directory, relative, optional=optional)
        return None if data is None else json.loads(data)
    except json.JSONDecodeError as error:
        raise IntegrityError(f"Invalid JSON artifact: {relative}") from error


def artifact_stream(directory, relative):
    return io.BytesIO(artifact_bytes(directory, relative))


def run_directories(runs):
    return sorted(
        (path for path in Path(runs).iterdir() if path.is_dir() and not path.name.startswith(".")),
        reverse=True,
    )


def list_runs(runs):
    retained, problems = [], []
    for path in run_directories(runs):
        try:
            read_request(path)
            read_status(path)
            retained.append(path)
        except (OSError, ValueError, AttributeError, TypeError) as error:
            problems.append(f"{path.name}: {error}")
    return sorted(retained, reverse=True), problems


def latest_note(directory):
    problems = []
    for path in sorted(Path(directory).glob("notes-*.json"), reverse=True):
        try:
            record = read_json(path)
            if not all(isinstance(record[key], str) for key in ("observation", "explanation")):
                raise ValueError("Incomplete note")
            return record, problems
        except (OSError, ValueError, KeyError, TypeError) as error:
            problems.append(f"Unreadable note retained: {path.name}: {error}")
    return {}, problems
