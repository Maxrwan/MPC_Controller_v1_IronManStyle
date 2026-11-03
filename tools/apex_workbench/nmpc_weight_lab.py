"""Bounded M0 configuration, immutable runtime, evidence and two-attempt authorization."""

import base64
import hashlib
import importlib.metadata
import io
import json
import math
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
SUCCESSOR = "primary-r1-r2-20261102"
PRIMARY_DECISION_SHA = "8c5147b33c8da3270558ee43a140a10dd69397bdd9258fb091db24bfb03eb1f8"
ORIGINAL_ANCHORS = {
    "BLOCKED.json": "66089de1966846b8a50c0238200fb92130ccd46be6a7f0935eb6b78ca02f457d",
    "claims/nominal.json": "eee9e7d515b319b91c54264db8f14350bbdfab6770914028f41a68cc9df63abf",
    "software_gate.json": "1be5c19db51b82dcc4815f0a716ac306b145865d4bb7bb96b1f907ffb557357f",
}
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


def safe(path, root=None):
    path, root = Path(path).absolute(), Path(OUTPUT if root is None else root).absolute()
    if (
        ".." in path.parts
        or not path.is_relative_to(root)
        or any(p.is_symlink() for p in (path, *path.parents))
    ):
        raise ValueError("Unsafe M0 output/runtime path")
    return path


def canonical_snapshot(value):
    """One finite JSON representation; only sequence tuple/list representation is normalized."""

    def convert(item):
        if item is None or type(item) in (str, bool, int):
            return item
        if isinstance(item, float) and math.isfinite(item):
            return float(item)
        if type(item) in (list, tuple):
            return [convert(v) for v in item]
        if type(item) is dict and all(type(k) is str for k in item):
            return {k: convert(v) for k, v in item.items()}
        raise ValueError("Unsupported/nonfinite configuration representation")

    if type(value) is not dict:
        raise ValueError("Configuration snapshot must be an object")
    return convert(value)


def same_configuration(actual, captured):
    actual, captured = canonical_snapshot(actual), canonical_snapshot(captured)
    # Serialized comparison also distinguishes bool/int/float and signed zero.
    if json.dumps(actual, sort_keys=True, allow_nan=False) != json.dumps(
        captured, sort_keys=True, allow_nan=False
    ):
        raise ValueError("Actual frozen resolved configuration differs from captured request")
    return actual


def authority_root(identifier=SUCCESSOR):
    if identifier == "original":
        return OUTPUT
    if identifier != SUCCESSOR:
        raise ValueError("Unsupported M0 authorization identity")
    return safe(OUTPUT / "authorizations" / identifier)


def gate_path(identifier=SUCCESSOR):
    return safe(authority_root(identifier) / "software_gate.json")


def claim_path(preset, identifier=SUCCESSOR):
    validate({"preset": preset})
    return safe(authority_root(identifier) / "claims" / (preset + ".json"))


def verify_successor(*, check_current=True, allow_blocked=False):
    """Explicit Primary successor, exact corrective PASS and unchanged original failure anchors."""
    root = authority_root()
    for name, digest in ORIGINAL_ANCHORS.items():
        if storage.sha256(safe(OUTPUT / name)) != digest:
            raise ValueError("Original failed authority/evidence changed")
    if storage.sha256(safe(root / "PRIMARY_DECISION.md")) != PRIMARY_DECISION_SHA:
        raise ValueError("Primary replacement decision absent or changed")
    authority = storage.read_json(safe(root / "authorization.json"))
    review_path = safe(root / "corrective_review.json")
    review = storage.read_json(review_path)
    if (
        authority.get("schema") != "apex-m0-successor-authorization/1"
        or authority.get("id") != SUCCESSOR
        or authority.get("primary_decision_sha256") != PRIMARY_DECISION_SHA
        or authority.get("original_anchors") != ORIGINAL_ANCHORS
        or authority.get("maximum_attempts") != {"nominal": 1, "exploratory": 1}
        or authority.get("corrective_review_sha256") != storage.sha256(review_path)
        or review.get("outcome") != "PASS"
        or (check_current and review.get("adapter_sha256") != adapter_hashes())
        or set(review.get("adapter_sha256", {})) != set(PRODUCERS)
        or review.get("scientific_source") != SOURCE
        or not re.fullmatch(r"[0-9a-f]{40}", review.get("candidate", ""))
        or git("rev-parse", review["candidate"] + "^{commit}").decode().strip()
        != review["candidate"]
        or any(
            hashlib.sha256(git("show", review["candidate"] + ":" + name)).hexdigest() != digest
            for name, digest in review["adapter_sha256"].items()
        )
    ):
        raise ValueError("Primary successor or exact corrective-review PASS absent/stale")
    for name, digest in review["evidence_sha256"].items():
        if storage.sha256(safe(root / name)) != digest:
            raise ValueError("Corrective review evidence changed")
    if storage.sha256(gate_path()) != review.get("software_gate_sha256"):
        raise ValueError("Software gate is not the independently reviewed identity")
    if not allow_blocked and (root / "BLOCKED.json").exists():
        raise ValueError("Successor attempt blocked; no further execution")
    return authority


def record_block(directory, error, captured):
    root = authority_root(captured.get("authorization_id", "original"))
    path = root / "BLOCKED.json"
    if not path.exists():
        storage.write_json(path, {"reason": repr(error), "run": str(directory)}, exclusive=True)


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
    runtime = safe(runtime, RUNTIME)
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


def probe(preset, *, checks=False, captured=None):
    validate({"preset": preset})
    runtime = prepare_runtime()
    command = [
        sys.executable,
        "-I",
        "-B",
        str(ROOT / "tools/apex_workbench/nmpc_weight_worker.py"),
        "--boundary" if captured is not None else "--check" if checks else "--probe",
        preset,
        str(runtime),
    ]
    env = os.environ.copy()
    env["VECLIB_MAXIMUM_THREADS"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
        env=env,
        input=json.dumps(captured, allow_nan=False) if captured is not None else None,
    )
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
    authority = verify_successor()
    gate = storage.read_json(gate_path())
    if (
        gate.get("status") != "SOFTWARE_GATES_PASSED"
        or gate.get("implementation_revision")
        != storage.read_json(authority_root() / "corrective_review.json")["candidate"]
        or authority.get("id") != SUCCESSOR
        or gate.get("source") != SOURCE
        or gate.get("adapter_sha256") != adapter_hashes()
        or (check_environment and gate.get("environment") != environment_identity())
    ):
        raise ValueError("Software/source/environment gate absent or stale")
    validate_run_ids(gate)
    for name, digest in gate["evidence_sha256"].items():
        if storage.sha256(safe(OUTPUT / name)) != digest:
            raise ValueError("Software gate evidence changed")
    return gate


def validate_run_ids(gate):
    values = gate.get("run_ids")
    if (
        type(values) is not dict
        or set(values) != set(PRESETS)
        or any(
            type(v) is not str or not re.fullmatch(r"[0-9]{8}T[0-9]{12}Z_[0-9a-f]{32}", v)
            for v in values.values()
        )
        or len(set(values.values())) != 2
    ):
        raise ValueError("Gate must reserve exactly two distinct canonical M0 run identities")
    return values


def authorized_run_id(preset):
    validate({"preset": preset})
    return validate_run_ids(verify_gate(check_environment=False))[preset]


def capture(values):
    values = validate(values)
    gate = verify_gate()
    report = probe(values["preset"])
    same_configuration(report["resolved"], gate["resolved_snapshots"][values["preset"]])
    if report["environment"] != gate["environment"]:
        raise ValueError("Actual isolated environment differs from passed software gate")
    return {
        "source": SOURCE,
        "profile_sha256": PROFILE_SHA,
        "runtime": str(RUNTIME),
        "source_sha256": source_hashes(),
        "adapter_sha256": adapter_hashes(),
        "environment": report["environment"],
        "resolved": canonical_snapshot(report["resolved"]),
        "authorization_id": SUCCESSOR,
        "authorization_sha256": storage.sha256(authority_root() / "authorization.json"),
        "software_gate_sha256": storage.sha256(gate_path()),
    }


def claim(preset, run_id, *, captured=False):
    """Called under the inherited shared execution lease, before numerical worker launch."""
    validate({"preset": preset})
    if captured:
        gate = verify_gate(check_environment=False)
    else:
        gate = verify_gate()
    if run_id != validate_run_ids(gate)[preset]:
        raise ValueError("Run identity is not the independently authorized reservation")
    # The exploratory claim requires a completed, intact and comparable successor nominal.
    if preset == "exploratory":
        nominal = storage.read_json(claim_path("nominal"))
        view = read_run(RUNS / nominal["run_id"])
        if (
            view["status"]["scientific_outcome"] != "completed"
            or view["raw"] is None
            or not coverage(view["raw"])["requested_duration_completed"]
        ):
            raise ValueError("Replacement nominal has no valid comparable result")
        same_configuration(
            view["request"]["nmpc_capture"]["resolved"],
            verify_gate(check_environment=False)["resolved_snapshots"]["nominal"],
        )
    path = claim_path(preset)
    path.parent.mkdir(parents=True, exist_ok=True)
    storage.write_json(
        path,
        {
            "preset": preset,
            "run_id": run_id,
            "source": SOURCE,
            "authorization_id": SUCCESSOR,
            "authorization_sha256": storage.sha256(authority_root() / "authorization.json"),
        },
        exclusive=True,
    )


def available(preset):
    return not claim_path(preset).exists()


def retained_authority(request):
    """Pure external authority binding, shared by ownership and evidence readers."""
    captured = request["nmpc_capture"]
    identifier = captured.get("authorization_id", "original")
    preset = validate(request["effective"])["preset"]
    selected_gate, selected_claim = gate_path(identifier), claim_path(preset, identifier)
    if identifier == "original":
        for name, digest in ORIGINAL_ANCHORS.items():
            if storage.sha256(safe(OUTPUT / name)) != digest:
                raise ValueError("Original historical authority/claim is not the approved identity")
    else:
        verify_successor(check_current=False, allow_blocked=True)
    gate, claim_record = storage.read_json(selected_gate), storage.read_json(selected_claim)
    if storage.sha256(selected_gate) != captured["software_gate_sha256"]:
        raise ValueError("M0 external software/configuration authority changed")
    if identifier != "original":
        review = storage.read_json(safe(authority_root(identifier) / "corrective_review.json"))
        digest = storage.sha256(safe(authority_root(identifier) / "authorization.json"))
        expected_claim = {
            "preset": preset,
            "run_id": validate_run_ids(gate)[preset],
            "source": SOURCE,
            "authorization_id": identifier,
            "authorization_sha256": digest,
        }
        if (
            gate.get("implementation_revision") != review["candidate"]
            or gate.get("adapter_sha256") != review["adapter_sha256"]
            or captured.get("authorization_sha256") != digest
            or claim_record != expected_claim
            or request.get("run_id") != expected_claim["run_id"]
        ):
            raise ValueError("M0 successor gate/claim/reserved identity disagrees")
    return selected_gate, selected_claim, gate, claim_record


def owned_run(selected):
    """Pure authentication before any UI lifecycle call; discovery alone conveys no ownership."""
    from tools.apex_workbench.run_catalog import Run

    if not isinstance(selected, Run):
        raise ValueError("M0 inspection requires the selected catalog identity")
    directory = safe(selected.directory, RUNS)
    if (
        directory.parent != RUNS
        or directory != directory.resolve(strict=True)
        or not selected.owned
        or selected.aliases != (directory,)
        or selected.adapter != ADAPTER
        or selected.run_id != directory.name
        or selected.key
        != "run-" + hashlib.sha256(("id:" + directory.name).encode()).hexdigest()[:20]
    ):
        raise ValueError("M0 selected record is foreign, aliased or conflicting")
    # Reconciliation/finalization can touch any member. Reject links before reading status,
    # including links whose target stays inside the record (atomic replace still mutates it).
    for member in directory.rglob("*"):
        safe(member, directory)
    request = storage.read_json(safe(directory / "request.json", directory))
    effective = validate(request["effective"])
    if (
        request.get("adapter") != ADAPTER
        or request.get("run_id") != selected.run_id
        or selected.case != effective["preset"]
    ):
        raise ValueError("M0 selected request identity/adapter changed")
    captured = request["nmpc_capture"]
    selected_gate, _, gate, claim = retained_authority(request)
    if (
        claim.get("run_id") != selected.run_id
        or claim.get("source") != SOURCE
        or claim.get("preset") != effective["preset"]
        or captured.get("source") != SOURCE
        or captured.get("profile_sha256") != PROFILE_SHA
        or storage.sha256(selected_gate) != captured["software_gate_sha256"]
        or gate.get("status") != "SOFTWARE_GATES_PASSED"
        or gate.get("source") != SOURCE
        or gate.get("profile_sha256") != PROFILE_SHA
        or captured.get("adapter_sha256") != gate.get("adapter_sha256")
        or set(captured.get("adapter_sha256", {})) != set(PRODUCERS)
        or captured.get("source_sha256") != source_hashes()
    ):
        raise ValueError("M0 original ownership/authority disagrees")
    same_configuration(captured["resolved"], gate["resolved_snapshots"][effective["preset"]])
    same_configuration(captured["environment"], gate["environment"])
    verify_runtime(captured["runtime"], captured["source_sha256"])
    return directory, storage.sha256(directory / "request.json")


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
    selected_gate, selected_claim, gate, claim_record = retained_authority(request)
    same_configuration(
        captured["resolved"], gate["resolved_snapshots"][request["effective"]["preset"]]
    )
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
    anchor["software_gate"] = storage.sha256(selected_gate)
    anchor["attempt_claim"] = storage.sha256(selected_claim)
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
