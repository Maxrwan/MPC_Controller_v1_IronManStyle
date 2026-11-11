"""Compact native JSONL chunks and epoch-bound verified reads."""

import json
import os
from pathlib import Path

from tools.apex_workbench import storage

from . import config

# Primary's bounded recovery admits only this original failed capture, never a resealed copy.
FAILED_NATIVE_RECOVERY = (
    "2026-11-11T095747.505385_0000_6a18eaab96bd4949835d7c481116806e",
    "dee9fa25607186027f726e7df76e0827d43b6bbc8cca36f1e2ba713b6f600a2e",
    "b6b8b56c9d70906860f471203f1cdef947b8fd2d573b9f05b66ad3e0278c8ba5",
)


def _recovery_members(directory, manifest):
    members = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}
    if members != set(manifest) | {"status.json", "artifacts.json"}:
        raise ValueError("Failed-native recovery has unverified or missing files")


class Chunks:
    """One open file per stream, compact JSON, finite chunks; flush each retained observation."""

    def __init__(self, directory, maximum=None):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=False)
        self.maximum = maximum or config.PROFILE["recording"]["chunk_bytes"]
        self.streams = {}

    def append(self, kind, row):
        if not kind.isidentifier():
            raise ValueError("Invalid native stream name")
        data = (
            json.dumps(
                row, separators=(",", ":"), allow_nan=False, default=lambda value: value.tolist()
            ).encode()
            + b"\n"
        )
        if len(data) > self.maximum:
            raise ValueError("One observation exceeds the finite chunk ceiling")
        stream, number, size = self.streams.get(kind, (None, -1, 0))
        if stream is None or size + len(data) > self.maximum:
            if stream:
                stream.close()
            number += 1
            fd = os.open(
                self.directory / f"{kind}-{number:05d}.jsonl",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
            )
            stream, size = os.fdopen(fd, "wb"), 0
        stream.write(data)
        stream.flush()
        self.streams[kind] = stream, number, size + len(data)

    def close(self):
        for stream, _, _ in self.streams.values():
            stream.close()


def store_raw(directory, raw):
    chunks = Chunks(Path(directory) / "native")
    scalar = {}
    try:
        for name, value in raw.items():
            if isinstance(value, list):
                for row in value:
                    chunks.append(name, row)
                scalar[name] = {"rows": len(value)}
            else:
                scalar[name] = value
    finally:
        chunks.close()
    storage.write_json(Path(directory) / "native.json", scalar, exclusive=True)


def rows(view, kind, prefix="native"):
    result = []
    for name in sorted(view["anchor"]):
        if name.startswith(prefix + "/" + kind + "-") and name.endswith(".jsonl"):
            data = storage.artifact_bytes(view["directory"], name)
            result.extend(json.loads(line) for line in data.splitlines())
    return result


def current(view):
    for name, digest in view["anchor"].items():
        if storage.sha256(config.safe(view["directory"] / name)) != digest:
            raise ValueError("V2 evidence changed during presentation")
    if view.get("recovery"):
        _recovery_members(
            view["directory"], set(view["anchor"]) - {"status.json", "artifacts.json"}
        )


def read_run(directory, *, recover_failed=False):
    """Strict normal ingestion; explicit recovery never supplies a replacement summary."""
    directory = config.safe(directory)
    if directory.parent != config.RUNS.absolute():
        raise ValueError("Read only original V2 run directories")
    for p in directory.rglob("*"):
        config.safe(p)
    status_bytes = (directory / "status.json").read_bytes()
    manifest_bytes = (directory / "artifacts.json").read_bytes()
    status = storage.read_status(directory)
    manifest = storage.artifact_manifest(directory)
    if status != json.loads(status_bytes) or manifest != json.loads(manifest_bytes):
        raise ValueError("V2 evidence epoch changed during ingestion")
    import hashlib

    anchor = {
        "status.json": hashlib.sha256(status_bytes).hexdigest(),
        "artifacts.json": hashlib.sha256(manifest_bytes).hexdigest(),
        **{name: entry["sha256"] for name, entry in manifest.items()},
    }
    if anchor["artifacts.json"] != status.get("manifest_sha256"):
        raise ValueError("V2 manifest/status epoch differs")
    required = {"request.json", "execution.json", "stdout.log", "stderr.log"}
    recovering = recover_failed and "native.json" in manifest and "summary.json" not in manifest
    if recovering:
        if (
            (directory.name, anchor["status.json"], anchor["artifacts.json"])
            != FAILED_NATIVE_RECOVERY
            or status.get("state") != "failed"
            or status.get("scientific_outcome") != "failed"
            or status.get("evidence_state") != "valid"
            or status.get("returncode") != 2
            or "worker_result.json" in manifest
        ):
            raise ValueError("No approved failed-native recovery identity")
        _recovery_members(directory, manifest)
        required |= {
            "native.json",
            "presentation.json",
            "pre_identity.json",
            "post_identity.json",
            "worker.json",
            "supervisor.json",
        }
    if status["scientific_outcome"] == "completed":
        required |= {
            "native.json",
            "summary.json",
            "pre_identity.json",
            "post_identity.json",
            "presentation.json",
            "worker_result.json",
            "worker.json",
            "supervisor.json",
        }
    if not required <= manifest.keys():
        raise ValueError("V2 required evidence missing")
    # Validate all members, including journals. A missing listed member quarantines all data.
    for name, entry in manifest.items():
        if set(entry) != {"bytes", "sha256"} or name in {"status.json", "artifacts.json"}:
            raise ValueError("Malformed V2 artifact member")
        storage.artifact_bytes(directory, name)
    request = storage.artifact_json(directory, "request.json")
    config.validate_retained(request["effective"])
    if request["run_id"] != directory.name or request.get("adapter") != "nmpc_lap_v2":
        raise ValueError("V2 run identity differs")
    view = {"directory": directory, "status": status, "request": request, "anchor": anchor}
    if "native.json" in manifest:
        scalar = storage.artifact_json(directory, "native.json")
        view["raw"] = {
            name: rows(view, name) if type(value) is dict and set(value) == {"rows"} else value
            for name, value in scalar.items()
        }
        for name, value in scalar.items():
            if (
                type(value) is dict
                and set(value) == {"rows"}
                and len(view["raw"][name]) != value["rows"]
            ):
                raise ValueError("V2 native stream coverage differs")
        view["presentation"] = storage.artifact_json(directory, "presentation.json")
        derived = rows(view, "states", "derived")
        if (
            len(derived) != view["presentation"]["state_rows"]
            or len(derived) != len(view["raw"]["states"])
            or any(
                a["time"] != b["time"] for a, b in zip(derived, view["raw"]["states"], strict=True)
            )
        ):
            raise ValueError("V2 derived/native coverage differs")
        view["presentation"]["states"] = derived
        pre = storage.artifact_json(directory, "pre_identity.json")
        post = storage.artifact_json(directory, "post_identity.json")
        if (
            pre["resolved"] != request["capture"]["resolved"]
            or pre["environment"] != request["capture"]["environment"]
            or not post["source_unchanged"]
            or not post["environment_unchanged"]
        ):
            raise ValueError("V2 effective source/environment identity differs")
        if pre["resolved"]["effective"] != request["effective"]:
            raise ValueError("V2 effective parameter snapshot differs")
        if (
            pre["resolved"]["configuration"]["costs"] != request["effective"]["scratch"]["costs"]
            or pre["resolved"]["simulation"]["duration"]
            != request["effective"]["maximum_simulation_s"]
            or pre["resolved"]["simulation"]["laps"] != config.PROFILE["native_lap_crossings"]
            or request["capture"]["source_sha256"] != config.v1.frozen.source_hashes()
        ):
            raise ValueError("V2 parameter/scientific source provenance differs")
        if recovering:
            if post.get("raw_available") is not True:
                raise ValueError("Failed-native recovery has no complete native snapshot")
            view["recovery"] = {
                "mode": "failed-native-read-only",
                "classification": (
                    "Read-only recovery · descriptive observations from a failed Workbench run. "
                    "Execution remains failed / valid evidence / exit 2; "
                    "no completed or qualified experiment."
                ),
                "missing_artifacts": ["summary.json", "worker_result.json"],
            }
        else:
            view["summary"] = storage.artifact_json(directory, "summary.json")
    current(view)
    return view
