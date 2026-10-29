"""Verified inspection/comparison data for presentation. No dynamics or new metrics."""

import io
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from tools.apex_workbench import comparison, plots, storage

ACTIVE = {"queued", "running", "finalizing"}
SOURCES = ("states.csv", "controls.csv", "diagnostics.csv", "trajectory_xy.csv", "geometry.csv")
RAW_NAMES = (
    "request.json",
    "status.json",
    "execution.json",
    "worker_result.json",
    "numerical_environment.json",
    "artifacts.json",
    "stdout.log",
    "stderr.log",
    "supervisor.log",
)
REFERENCES = {"vx": "reference_speed", "vy": "vy_ref", "r": "r_ref"}


@dataclass
class Inspection:
    request: dict = field(default_factory=dict)
    status: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    contract: dict = field(default_factory=dict)
    frames: dict = field(default_factory=dict)
    manifest: dict = field(default_factory=dict)
    error: str = ""
    valid: bool = False


def inspect(run):
    """Pure reads, including for corrupt/active archives. Never reconcile execution owners."""
    result = Inspection()
    try:
        result.status = storage.read_status(run.directory)
        if run.conflict and "qualification archive" not in run.origins:
            raise storage.IntegrityError("Conflicting execution aliases")
        if result.status["state"] in ACTIVE:
            result.request = storage.read_request(run.directory)
            result.error = (
                "Evidence pending"
                if run.owned
                else "Nonterminal archive: read-only, not a live owner"
            )
            return result
        result.request = storage.read_request(run.directory, verified=True)
        if not run.owned and result.request["adapter"] != "dynamic_lab":
            raise storage.IntegrityError(
                "Only declared dynamic-lab qualification archives are supported"
            )
        storage.check_required_artifacts(run.directory, result.request, result.status)
        result.manifest = storage.artifact_manifest(run.directory)
        for name in result.manifest:
            storage.artifact_bytes(run.directory, name)
        if result.request["adapter"] == "dynamic_lab":
            from tools.apex_workbench.lab_evidence import read_record

            record = read_record(run.directory)
            result.summary = record["summary"]
        else:
            result.summary = (
                storage.artifact_json(run.directory, "worker_result.json", optional=True) or {}
            )
        result.environment = (
            storage.artifact_json(run.directory, "numerical_environment.json", optional=True) or {}
        )
        result.contract = (
            storage.artifact_json(
                run.directory, "experiment/telemetry_contract.json", optional=True
            )
            or {}
        )
        result.frames = {
            name: plots.read_frame(run.directory, name)
            for name in SOURCES
            if "experiment/" + name in result.manifest
        }
        result.valid = True
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        result.error = str(error)
        result.frames = {}  # Raw forensic records remain separate from scientific plots.
    return result


def qualification(run, directory):
    from tools.apex_workbench.qualification import applicability

    data = inspect(run)
    if not data.valid or data.status.get("state") in ACTIVE:
        raise storage.IntegrityError(data.error or "Unverified record")
    return applicability(directory, run.directory)


def invalid_comparison(reason):
    return {"classification": "invalid", "reason": reason, "differences": {}, "varied_inputs": {}}


def comparison_epoch(runs, qualification_record=None):
    paths = [run.directory / name for run in runs for name in ("status.json", "artifacts.json")]
    if qualification_record is not None:
        paths.extend(
            Path(qualification_record) / name for name in ("commit.json", "qualification.json")
        )
    return tuple((str(path), storage.sha256(path)) for path in paths)


def comparison_current(decision):
    """Bind display to the exact evidence/qualification anchors consumed, not validity alone."""
    try:
        anchors = decision.get("presentation_epoch", ())
        return bool(anchors) and all(
            storage.sha256(Path(path)) == digest for path, digest in anchors
        )
    except (OSError, ValueError, RuntimeError):
        return False


def compare(first, second, *, qualification_record=None):
    try:
        before = comparison_epoch((first, second), qualification_record)
        decision = _compare(first, second, qualification_record=qualification_record)
        if before != comparison_epoch((first, second), qualification_record):
            raise storage.IntegrityError("Evidence changed during comparison")
        return {**decision, "presentation_epoch": before}
    except (OSError, ValueError, RuntimeError):
        return invalid_comparison("Evidence unavailable/changed during comparison")


def _compare(first, second, *, qualification_record=None):
    try:
        data = [inspect(run) for run in (first, second)]
        for item in data:
            if (
                not item.valid
                or item.status.get("scientific_outcome", item.status.get("state")) != "completed"
            ):
                raise storage.IntegrityError(
                    item.error or "Only completed verified runs can be compared"
                )
        if all(item.request["adapter"] == "dynamic_lab" for item in data):
            # The accepted lab reader is pure. Do not invoke lifecycle reconciliation on archives.
            from tools.apex_workbench.lab_comparison import eligibility

            return eligibility(
                first.directory, second.directory, qualification_record=qualification_record
            )
        if not first.owned or not second.owned:
            # Same cross-adapter branch as the accepted wrapper, without its lifecycle calls.
            for run, item in zip((first, second), data):
                if item.request["adapter"] != "dynamic_lab":
                    comparison.fingerprint(run.directory)
            return {
                "classification": "illustrative",
                "reason": "Cross-adapter overlay; no causal ranking",
                "differences": {"adapter": [item.request["adapter"] for item in data]},
                "varied_inputs": {},
            }
        return comparison.eligibility(first.directory, second.directory)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        return {
            "classification": "invalid",
            "reason": str(error),
            "differences": {},
            "varied_inputs": {},
        }


def raw_records(run):
    """Bounded, explicitly unverified diagnostic text; no outside symlink targets."""
    records = {}
    for name in RAW_NAMES:
        path = run.directory / name
        try:
            if path.is_file() and path.resolve().is_relative_to(run.directory.resolve()):
                with path.open("rb") as stream:
                    stream.seek(max(0, path.stat().st_size - 100_000))
                    records[name] = stream.read(100_000).decode(errors="replace")
        except OSError as error:
            records[name] = "Unavailable: " + str(error)
    return records


def notes(run):
    try:
        for path in run.directory.glob("notes-*.json"):
            if not path.resolve().is_relative_to(run.directory.resolve()):
                return {}, ["Unsafe note path withheld"]
    except (OSError, RuntimeError) as error:
        return {}, ["Unreadable note path: " + str(error)]
    return storage.latest_note(run.directory)


def bundle(run):
    status = (run.directory / "status.json").read_bytes()
    manifest = (run.directory / "artifacts.json").read_bytes()
    data = inspect(run)
    if not data.valid:
        raise storage.IntegrityError(data.error)
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zipped:
        for name in data.manifest:
            zipped.writestr(name, storage.artifact_bytes(run.directory, name))
        if (run.directory / "status.json").read_bytes() != status or (
            run.directory / "artifacts.json"
        ).read_bytes() != manifest:
            raise storage.IntegrityError("Run changed during export; bundle withheld")
        zipped.writestr("artifacts.json", manifest)
        zipped.writestr("status.json", status)
    return target.getvalue()


def unit(data, channel):
    contract = data.contract
    units = dict(zip(contract.get("state_names", []), contract.get("state_units", [])))
    units.update(zip(contract.get("control_names", []), contract.get("control_units", [])))
    units.update(contract.get("diagnostic_units", {}))
    units.update(reference_speed="m/s", vy_ref="m/s", r_ref="rad/s", time="s")
    return units.get(channel, "unit not declared by this exporter")
