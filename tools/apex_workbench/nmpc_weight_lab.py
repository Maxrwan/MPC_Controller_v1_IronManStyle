"""Bounded M0 configuration, immutable runtime, evidence and two-attempt authorization."""

import base64
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tomllib
import uuid
from pathlib import Path

from tools.apex_workbench import storage
from tools.apex_workbench.configuration import ROOT

SOURCE = "48adbdf64d492592d15e23c917aca71fa58aa8a5"
BASE = "5831f22f8d64a69efd119edd181802adcd82dde2"
PROFILE = "configs/performance/apex_performance_synthetic_v1.json"
PROFILE_SHA = "5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf"
OUTPUT = ROOT / "results/apex_workbench_nmpc_weights"
RUNS = OUTPUT / "runs"
RUNTIME = OUTPUT / "runtime/source"
ADAPTER = "nmpc_weight_lab"
PRESETS = {"nominal": 2.0, "exploratory": 1.0}
BANNER = (
    "EXPERIMENTAL / UNQUALIFIED — synthetic NMPC/TVLQR; no physical or performance qualification"
)
PREFIXES = ("src", "scripts", "configs", "pyproject.toml", "uv.lock")
PRODUCERS = tuple(
    "tools/apex_workbench/" + name
    for name in (
        "nmpc_weight_lab.py",
        "nmpc_weight_worker.py",
        "nmpc_weight_panels.py",
        "configuration.py",
        "worker.py",
        "jobs.py",
        "workspace.py",
        "run_catalog.py",
    )
)


def validate(values):
    if (
        not isinstance(values, dict)
        or set(values) != {"preset"}
        or not isinstance(values["preset"], str)
        or values["preset"] not in PRESETS
    ):
        raise ValueError("M0 accepts only preset=nominal or exploratory; one fixed scenario")
    return {"preset": values["preset"]}


def safe(path, root=OUTPUT):
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root) or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Unsafe M0 output/runtime path")
    return path


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def frozen_blobs():
    """Git archive is read from the exact object, never from current scientific sources."""
    if git("rev-parse", SOURCE + "^{commit}").decode().strip() != SOURCE:
        raise ValueError("Missing/ambiguous frozen revision")
    archive = git("archive", SOURCE, *PREFIXES)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        result = {}
        for item in stream:
            if item.isdir():
                continue
            if not item.isfile() or Path(item.name).is_absolute() or ".." in Path(item.name).parts:
                raise ValueError("Unsupported frozen Git entry")
            result[item.name] = stream.extractfile(item).read()
    if hashlib.sha256(result[PROFILE]).hexdigest() != PROFILE_SHA:
        raise ValueError("Frozen Performance profile identity mismatch")
    return result


def source_hashes():
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in frozen_blobs().items()}


def prepare_runtime():
    blobs = frozen_blobs()
    safe(RUNTIME)
    if not RUNTIME.exists():
        staging = OUTPUT / (".source-" + uuid.uuid4().hex)
        staging.mkdir(parents=True)
        for name, raw in blobs.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(raw)
        RUNTIME.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(RUNTIME)
    verify_runtime(RUNTIME, {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()})
    return RUNTIME


def verify_runtime(runtime, expected=None):
    runtime = safe(runtime)
    if runtime != RUNTIME:
        raise ValueError("Unsupported M0 runtime root")
    expected = source_hashes() if expected is None else expected
    actual = {}
    for path in runtime.rglob("*"):
        if path.is_symlink():
            raise ValueError("Linked frozen runtime member")
        if path.is_file():
            actual[str(path.relative_to(runtime))] = storage.sha256(path)
    if actual != expected:
        raise ValueError("Frozen runtime content changed or incomplete")
    return expected


def adapter_hashes():
    return {name: storage.sha256(ROOT / name) for name in PRODUCERS}


def environment_identity():
    """Pin installed versions and distribution RECORD identities, without importing numerics."""
    blobs = frozen_blobs()
    profile = json.loads(blobs[PROFILE])
    expected = profile["environment"]["tested"]
    if sys.version != expected["python"] or platform.platform() != expected["platform"]:
        raise ValueError("M0 interpreter differs from approved numerical environment")
    versions = dict(expected["packages"])
    locked = {
        p["name"].lower(): p.get("version")
        for p in tomllib.loads(blobs["uv.lock"].decode())["package"]
    }
    for requirement in tomllib.loads(blobs["pyproject.toml"].decode())["project"]["dependencies"]:
        name = re.split(r"[<>=!~;\[]", requirement)[0].strip().lower()
        if name not in locked or not locked[name]:
            raise ValueError("Unresolved frozen dependency: " + name)
        if name in versions and versions[name] != locked[name]:
            raise ValueError("Profile/lock dependency disagreement: " + name)
        versions[name] = locked[name]
    packages = {}
    for name, version in versions.items():
        distribution = importlib.metadata.distribution(name)
        if distribution.version != version:
            raise ValueError("M0 dependency version mismatch: " + name)
        records = [p for p in distribution.files or () if str(p).endswith(".dist-info/RECORD")]
        if len(records) != 1:
            raise ValueError("Ambiguous dependency RECORD: " + name)
        record = Path(distribution.locate_file(records[0]))
        installed = {}
        for entry in distribution.files or ():
            if entry.hash is None:
                continue
            path = Path(distribution.locate_file(entry))
            if entry.hash.mode != "sha256" or not path.is_file():
                raise ValueError("Unsupported/missing dependency member: " + str(path))
            digest = storage.sha256(path)
            if (
                base64.urlsafe_b64encode(bytes.fromhex(digest)).decode().rstrip("=")
                != entry.hash.value
            ):
                raise ValueError("Installed dependency RECORD mismatch: " + str(path))
            installed[str(path)] = digest
        packages[name] = {
            "version": version,
            "record": str(record),
            "record_sha256": storage.sha256(record),
            "installed_files": len(installed),
            "installed_tree_sha256": hashlib.sha256(
                json.dumps(installed, sort_keys=True).encode()
            ).hexdigest(),
        }
    return {"python": sys.version, "executable": sys.executable, "packages": packages}


def probe(preset, *, checks=False):
    validate({"preset": preset})
    runtime = prepare_runtime()
    command = [
        sys.executable,
        "-I",
        "-B",
        str(ROOT / "tools/apex_workbench/nmpc_weight_worker.py"),
        "--check" if checks else "--probe",
        preset,
        str(runtime),
    ]
    env = os.environ.copy()
    env["VECLIB_MAXIMUM_THREADS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, capture_output=True, text=True, cwd=ROOT, timeout=60, env=env)
    logs = OUTPUT / "software_probes"
    logs.mkdir(parents=True, exist_ok=True)
    storage.write_json(
        logs / (preset + "_" + uuid.uuid4().hex + ".json"),
        {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
        exclusive=True,
    )
    if result.returncode:
        raise RuntimeError("Frozen runtime preflight failed: " + result.stderr[-4000:])
    return json.loads(result.stdout)


def verify_gate(*, check_environment=True):
    if (OUTPUT / "BLOCKED.json").exists():
        raise ValueError("M0 is blocked; retain outcomes and request Primary decision")
    gate = storage.read_json(safe(OUTPUT / "software_gate.json"))
    if (
        gate.get("status") != "SOFTWARE_GATES_PASSED"
        or gate.get("source") != SOURCE
        or gate.get("adapter_sha256") != adapter_hashes()
        or (check_environment and gate.get("environment") != environment_identity())
    ):
        raise ValueError("Software/source/environment gate absent or stale")
    for name, digest in gate["evidence_sha256"].items():
        if storage.sha256(safe(OUTPUT / name)) != digest:
            raise ValueError("Software gate evidence changed")
    return gate


def capture(values):
    values = validate(values)
    gate = verify_gate()
    report = probe(values["preset"])
    if report["resolved"] != gate["resolved_snapshots"][values["preset"]]:
        raise ValueError("Resolved configuration differs from passed software gate")
    if report["environment"] != gate["environment"]:
        raise ValueError("Actual isolated environment differs from passed software gate")
    return {
        "source": SOURCE,
        "profile_sha256": PROFILE_SHA,
        "runtime": str(RUNTIME),
        "source_sha256": source_hashes(),
        "adapter_sha256": adapter_hashes(),
        "environment": report["environment"],
        "resolved": report["resolved"],
        "software_gate_sha256": storage.sha256(OUTPUT / "software_gate.json"),
    }


def claim(preset, run_id, *, captured=False):
    """Called under the inherited shared execution lease, before numerical worker launch."""
    validate({"preset": preset})
    if captured:
        verify_gate(check_environment=False)
    else:
        verify_gate()
    path = safe(OUTPUT / "claims" / (preset + ".json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    storage.write_json(path, {"preset": preset, "run_id": run_id, "source": SOURCE}, exclusive=True)


def available(preset):
    return not (OUTPUT / "claims" / (preset + ".json")).exists()


def read_run(directory):
    directory = safe(directory, RUNS)
    request = storage.read_json(directory / "request.json")
    if request.get("adapter") != ADAPTER:
        raise ValueError("Not an M0 run")
    validate(request["effective"])
    if directory.name != request.get("run_id"):
        raise ValueError("M0 alias does not identify its original owned run")
    captured = request["nmpc_capture"]
    verify_runtime(captured["runtime"], captured["source_sha256"])
    gate_path = safe(OUTPUT / "software_gate.json")
    if storage.sha256(gate_path) != captured["software_gate_sha256"]:
        raise ValueError("M0 external software/configuration authority changed")
    gate = storage.read_json(gate_path)
    if captured["resolved"] != gate["resolved_snapshots"][request["effective"]["preset"]]:
        raise ValueError("M0 evidence has inconsistent effective parameter snapshot")
    claim_path = safe(OUTPUT / "claims" / (request["effective"]["preset"] + ".json"))
    claim_record = storage.read_json(claim_path)
    if claim_record.get("run_id") != request["run_id"] or claim_record.get("source") != SOURCE:
        raise ValueError("M0 original attempt identity/authorization disagrees")
    if (
        captured["source"] != SOURCE
        or captured["profile_sha256"] != PROFILE_SHA
        or captured["source_sha256"] != source_hashes()
    ):
        raise ValueError("Unsupported experimental scientific identity")
    status = storage.read_status(directory)
    if status.get("evidence_state") == "valid":
        # Original manifest/byte verifier; M0 does not invent legacy XY/geometry artifacts.
        manifest = storage.artifact_manifest(directory)
        required = {"request.json", "execution.json", "worker.json", "supervisor.json"}
        if status.get("scientific_outcome") == "completed":
            required.update(
                {
                    "experiment/raw.json",
                    "experiment/summary.json",
                    "experiment/pre_execution_identity.json",
                    "experiment/post_execution_identity.json",
                    "experiment/optimizations.jsonl",
                    "experiment/preparations.jsonl",
                    "experiment/plant_segments.jsonl",
                    "experiment/command_requests.jsonl",
                    "worker_result.json",
                }
            )
        if not required <= manifest.keys():
            raise ValueError("M0 required evidence is missing")
        for name in manifest:
            path = safe(directory / name, directory)
            entry = manifest[name]
            if path.stat().st_size != entry["bytes"] or storage.sha256(path) != entry["sha256"]:
                raise ValueError("M0 artifact bytes changed: " + name)
            storage.artifact_bytes(directory, name)
        if status.get("scientific_outcome") == "completed" or "experiment/raw.json" in manifest:
            identity = storage.artifact_json(directory, "experiment/pre_execution_identity.json")
            post = storage.artifact_json(directory, "experiment/post_execution_identity.json")
            if (
                identity["source"] != SOURCE
                or identity["resolved"] != captured["resolved"]
                or identity["environment"] != captured["environment"]
                or post["adapter_unchanged"] is not True
                or post["environment_unchanged"] is not True
                or post["raw_result_available"] is not True
            ):
                raise ValueError("M0 actual execution identity/availability mismatch")
    else:
        raise ValueError("Run evidence not committed; partial files remain available below")
    anchor = {
        name: storage.sha256(directory / name)
        for name in ("request.json", "status.json", "artifacts.json")
    }
    anchor["software_gate"] = storage.sha256(gate_path)
    anchor["attempt_claim"] = storage.sha256(claim_path)
    raw = storage.artifact_json(directory, "experiment/raw.json", optional=True)
    return {
        "directory": directory,
        "request": request,
        "status": status,
        "raw": raw,
        "anchor": anchor,
    }


def current(view):
    latest = read_run(view["directory"])
    if latest["anchor"] != view["anchor"]:
        raise ValueError("M0 evidence changed during presentation")


def descriptive_metrics(raw):
    """Native sampled states only; no interpolated endpoint or weighted objective score."""
    states = raw.get("states", []) if raw else []
    if not states:
        return {"state_samples": 0, "coverage": "unavailable"}
    return {
        "state_samples": len(states),
        "first_time_s": states[0]["time"],
        "last_time_s": states[-1]["time"],
        "rms_e_y_m": (sum(r["e_y"] ** 2 for r in states) / len(states)) ** 0.5,
        "rms_e_psi_rad": (sum(r["e_psi"] ** 2 for r in states) / len(states)) ** 0.5,
        "definition": (
            "Equal-weight RMS over native retained state rows; no interpolation; "
            "e_y/e_psi are native Frenet states, not a new racing-reference residual."
        ),
    }


def coverage(raw):
    return {
        "requested_duration_s": 2.0,
        "native_end_time_s": raw.get("end_time"),
        "native_stop_reason": raw.get("stop_reason"),
        "requested_duration_completed": raw.get("stop_reason") == "duration"
        and raw.get("failure") is None,
        "rule": "Native duration termination without a failure; no inferred endpoint state",
    }
