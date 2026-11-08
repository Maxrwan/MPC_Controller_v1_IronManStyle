"""Thin versioned CostScales documents and disposable Scratch job/evidence bindings."""

import copy
import hashlib
import json
import math
import re
import subprocess
import sys
import uuid
from pathlib import Path

from tools.apex_workbench import nmpc_weight_lab as frozen
from tools.apex_workbench import storage
from tools.apex_workbench.configuration import ROOT

ADAPTER = "nmpc_scratch"
OUTPUT = ROOT / "results/apex_workbench_nmpc_lab_v1"
RUNS = OUTPUT / "runs"
RUNTIME = frozen.RUNTIME  # Shared exact-source cache, mounted read-only; no historical writes.
PROFILE_PATH = ROOT / "tools/apex_workbench/nmpc_scratch_profile.json"
PROFILE = storage.read_json(PROFILE_PATH)
FIELDS = tuple(PROFILE["baseline_costs"])
SCHEMA = "apex-nmpc-scratch-config/1"
BANNER = "SYNTHETIC / EXPERIMENTAL / UNQUALIFIED · NMPC Scratch"
PRODUCERS = tuple(
    dict.fromkeys(
        (
            *frozen.PRODUCERS,
            *(
                "tools/apex_workbench/" + name
                for name in (
                    "nmpc_scratch.py",
                    "nmpc_scratch_worker.py",
                    "nmpc_analysis.py",
                    "nmpc_scratch_panels.py",
                    "nmpc_scratch_profile.json",
                    "storage.py",
                    "lifecycle.py",
                )
            ),
        )
    )
)


def safe(path):
    return frozen.safe(path, OUTPUT)


def defaults():
    return {
        "schema": SCHEMA,
        "configuration_id": "baseline",
        "version": 1,
        "profile": PROFILE["id"],
        "scientific_source": frozen.SOURCE,
        "profile_sha256": storage.sha256(PROFILE_PATH),
        "costs": dict(PROFILE["baseline_costs"]),
        "disturbance": "none",
    }


def validate(value):
    """Structural boundary only; frozen CostScales/MPCConfig validate again in isolation."""
    if type(value) is not dict or set(value) != set(defaults()):
        raise ValueError("Use exactly the versioned Scratch configuration fields")
    if (
        value["schema"] != SCHEMA
        or value["profile"] != PROFILE["id"]
        or value["scientific_source"] != frozen.SOURCE
        or value["profile_sha256"] != storage.sha256(PROFILE_PATH)
        or type(value["version"]) is not int
        or value["version"] < 1
        or type(value["configuration_id"]) is not str
        or re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value["configuration_id"]) is None
    ):
        raise ValueError("Unsupported Scratch configuration/source/version identity")
    costs = value["costs"]
    if type(costs) is not dict or set(costs) != set(FIELDS):
        raise ValueError("Only the eight native CostScales fields are editable")
    result = copy.deepcopy(value)
    for name, item in costs.items():
        if type(item) not in (int, float) or not math.isfinite(item):
            raise ValueError(name + " must be a finite real number")
        if item < 0 or (name not in {"terminal", "alpha_vy", "alpha_r"} and item == 0):
            raise ValueError(name + " violates native CostScales positivity")
        result["costs"][name] = float(item)
    if value["disturbance"] not in ("none", PROFILE["disturbance"]["id"]):
        raise ValueError("Only the declared native V1 disturbance is supported")
    return result


def dumps(value):
    return json.dumps(validate(value), sort_keys=True, indent=2, allow_nan=False) + "\n"


def loads(text):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate configuration key: " + key)
            value[key] = item
        return value

    return validate(json.loads(text, object_pairs_hook=unique))


def identity(value):
    value = validate(value)
    # Name/version describe a saved draft; they do not change its physical experiment.
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in value.items() if k not in {"configuration_id", "version"}},
            sort_keys=True,
        ).encode()
    ).hexdigest()


def work_cases():
    baseline = defaults()
    treatment, disturbance = copy.deepcopy(baseline), copy.deepcopy(baseline)
    treatment["configuration_id"] = "lateral_1"
    treatment["costs"]["lateral"] = 1.0
    disturbance["configuration_id"] = "disturbance"
    disturbance["disturbance"] = PROFILE["disturbance"]["id"]
    return {"baseline": baseline, "lateral_1": treatment, "disturbance": disturbance}


def producer_hashes():
    return {p: storage.sha256(ROOT / p) for p in PRODUCERS}


def prepare_runtime():
    frozen.verify_runtime(RUNTIME)
    return RUNTIME


def probe(value, *, check=False):
    value = validate(value)
    command = [
        sys.executable,
        "-I",
        "-B",
        str(ROOT / "tools/apex_workbench/nmpc_scratch_worker.py"),
        "--check" if check else "--probe",
        str(prepare_runtime()),
    ]
    result = subprocess.run(
        command,
        input=dumps(value),
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
        env={
            **__import__("os").environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        },
    )
    directory = safe(OUTPUT / "software_probes")
    directory.mkdir(parents=True, exist_ok=True)
    storage.write_json(
        directory / (uuid.uuid4().hex + ".json"),
        {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
        exclusive=True,
    )
    if result.returncode:
        raise RuntimeError("Frozen Scratch configuration failed: " + result.stderr[-4000:])
    return json.loads(result.stdout)


def access(value, *, run_id=None):
    value = validate(value)
    try:
        policy = storage.read_json(safe(OUTPUT / "access.json"))
    except FileNotFoundError:
        raise ValueError(
            ("Initial Scratch experiments await independent review and prepared access")
        ) from None
    review = safe(Path(policy["review_record"]))
    report = storage.read_json(review)
    if (
        policy.get("schema") != "apex-nmpc-scratch-access/1"
        or storage.sha256(review) != policy.get("review_sha256")
        or report.get("outcome") != "PASS"
        or report.get("candidate") != policy.get("reviewed_revision")
        or policy.get("producer_sha256") != producer_hashes()
    ):
        raise ValueError("Scratch source/review gate absent or stale")
    for name, digest in policy["producer_sha256"].items():
        if (
            hashlib.sha256(frozen.git("show", policy["reviewed_revision"] + ":" + name)).hexdigest()
            != digest
        ):
            raise ValueError("Scratch reviewed Git source differs")
    if policy.get("stage") == "reviewed-work":
        expected = {name: identity(v) for name, v in work_cases().items()}
        if policy.get("cases") != expected or not isinstance(policy.get("used"), dict):
            raise ValueError("Malformed three-attempt WORK budget")
        matches = [name for name, digest in expected.items() if identity(value) == digest]
        if not set(policy["used"]) <= set(expected) or len(set(policy["used"].values())) != len(
            policy["used"]
        ):
            raise ValueError("Malformed consumed WORK attempts")
        if len(matches) != 1 or (
            (run_id is None and matches[0] in policy["used"])
            or (run_id is not None and policy["used"].get(matches[0]) != run_id)
        ):
            raise ValueError("This WORK configuration is unavailable or its attempt is consumed")
    elif policy.get("stage") == "accepted-interactive":
        acceptance = safe(Path(policy["primary_acceptance_record"]))
        if storage.sha256(acceptance) != policy.get("primary_acceptance_sha256"):
            raise ValueError("Explicit Primary acceptance record absent or changed")
    else:
        raise ValueError("Primary acceptance is required for repeatable interactive Scratch")
    return policy


def capture(value):
    value = validate(value)
    access(value)
    report = probe(value)
    return {
        "source": frozen.SOURCE,
        "runtime": str(RUNTIME),
        "source_sha256": frozen.source_hashes(),
        "producer_sha256": producer_hashes(),
        "environment": report["environment"],
        "resolved": report["resolved"],
    }


def consume(value, run_id):
    """One flat initial WORK budget, serialized by the existing Workbench execution lease."""
    policy = access(value)
    if policy["stage"] == "reviewed-work":
        name = next(k for k, d in policy["cases"].items() if d == identity(value))
        policy["used"][name] = run_id
        storage.write_json(safe(OUTPUT / "access.json"), policy)


def owned(selected):
    directory = safe(selected.directory)
    if (
        directory.parent != RUNS.absolute()
        or selected.adapter != ADAPTER
        or not selected.owned
        or selected.aliases != (directory,)
        or selected.run_id != directory.name
        or selected.key
        != "run-" + hashlib.sha256(("id:" + directory.name).encode()).hexdigest()[:20]
    ):
        raise ValueError("Scratch lifecycle requires the original owned record")
    for path in directory.rglob("*"):
        safe(path)
    request = storage.read_json(directory / "request.json")
    if request.get("adapter") != ADAPTER or request.get("run_id") != directory.name:
        raise ValueError("Scratch request identity differs")
    validate(request["effective"])
    return directory


def read_run(directory):
    directory = safe(directory)
    if directory.parent != RUNS.absolute():
        raise ValueError("Read the original Scratch directory; aliases are not new executions")
    for path in directory.rglob("*"):
        safe(path)
    status = storage.read_status(directory)
    if status.get("evidence_state") != "valid":
        raise ValueError("Partial/uncommitted Scratch evidence; native journals remain retained")
    manifest = storage.artifact_manifest(directory)
    request = storage.artifact_json(directory, "request.json")
    if request["adapter"] != ADAPTER or request["run_id"] != directory.name:
        raise ValueError("Scratch identity changed")
    validate(request["effective"])
    storage.check_required_artifacts(directory, request, status)
    for name in manifest:
        storage.artifact_bytes(directory, name)
    raw = storage.artifact_json(directory, "experiment/raw.json", optional=True)
    presentation = storage.artifact_json(directory, "experiment/presentation.json", optional=True)
    if raw is not None:
        pre = storage.artifact_json(directory, "experiment/pre_execution_identity.json")
        post = storage.artifact_json(directory, "experiment/post_execution_identity.json")
        captured = request["scratch_capture"]
        if (
            pre["resolved"] != captured["resolved"]
            or pre["environment"] != captured["environment"]
            or pre["source"] != frozen.SOURCE
            or not post["adapter_unchanged"]
            or not post["environment_unchanged"]
        ):
            raise ValueError("Scratch execution identities differ")
        if captured["resolved"]["configuration"]["costs"] != request["effective"]["costs"]:
            raise ValueError("Scratch effective costs disagree")
        if (
            captured["resolved"]["effective"] != request["effective"]
            or captured["source"] != frozen.SOURCE
        ):
            raise ValueError("Scratch configuration/scientific source disagrees")
    packet_bytes = storage.artifact_bytes(directory, "experiment/packets.jsonl", optional=True)
    packets = (
        [json.loads(row) for row in packet_bytes.decode().splitlines()] if packet_bytes else []
    )
    return {
        "directory": directory,
        "request": request,
        "status": status,
        "raw": raw,
        "presentation": presentation,
        "packets": packets,
        "anchor": {
            name: storage.sha256(directory / name)
            for name in (*manifest, "status.json", "artifacts.json")
        },
    }


def current(view):
    for name, digest in view["anchor"].items():
        if storage.sha256(safe(view["directory"] / name)) != digest:
            raise ValueError("Scratch evidence changed during presentation")


def saved_configuration(value):
    value = validate(value)
    directory = safe(OUTPUT / "configurations")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (value["configuration_id"] + "_v" + str(value["version"]) + ".json")
    storage.write_json(path, value, exclusive=True)
    return path
