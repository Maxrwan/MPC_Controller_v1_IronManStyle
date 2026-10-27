"""Atomic record publication and selected-artifact integrity checks."""

import hashlib
import io
import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path


class IntegrityError(ValueError):
    """Retained data is incomplete, unverified or changed."""


def read_json(path):
    return json.loads(Path(path).read_text())


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


def artifact_bytes(directory, relative):
    """Read only the selected file. Cache is keyed by content hash and full file identity."""
    directory = Path(directory)
    try:
        status = read_json(directory / "status.json")
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


def artifact_json(directory, relative):
    try:
        return json.loads(artifact_bytes(directory, relative))
    except json.JSONDecodeError as error:
        raise IntegrityError(f"Invalid JSON artifact: {relative}") from error


def artifact_stream(directory, relative):
    return io.BytesIO(artifact_bytes(directory, relative))


def list_runs(runs):
    retained, problems = [], []
    for path in Path(runs).iterdir():
        if not path.is_dir() or path.name.startswith("."):
            continue
        try:
            request = read_json(path / "request.json")
            status = read_json(path / "status.json")
            if not isinstance(request.get("effective"), dict) or not isinstance(
                status.get("state"), str
            ):
                raise ValueError("Incomplete request/status contract")
            if request.get("adapter") not in {"dynamic_demo", "lqr_baseline"}:
                raise ValueError("Unknown adapter")
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
