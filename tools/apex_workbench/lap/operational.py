"""Explicit Primary operational acceptance; historical research budgets are immutable."""

import hashlib
import json
from pathlib import Path

from tools.apex_workbench import jobs, storage

from . import admission, config, evidence

BRIEF = "docs/workbench_v2_operational/PRIMARY_WORK.md"
HISTORY_SHA = "f9a0304ff136a1d7fe0b56ef0f3a2efff2f7fe37d74acbba1c369c5fa2772346"
HISTORY = {
    "pilot": "2026-11-10T145233.755880_0000_f46cc76634dd4322b1720f37eb96442b",
    "full_lap": evidence.FAILED_NATIVE_RECOVERY[0],
}


def _historical(reference):
    path = config.safe(Path(reference["path"]))
    if reference["sha256"] != HISTORY_SHA or storage.sha256(path) != HISTORY_SHA:
        raise ValueError("Original consumed research policy changed")
    policy = storage.read_json(path)
    if policy["used"] != HISTORY or policy["maximum_genuine_attempts"] != {
        "pilot": 1,
        "full_lap": 1,
    }:
        raise ValueError("Historical attempts must remain consumed and unchanged")
    for field in ("review", "authority"):
        if (
            storage.sha256(config.safe(Path(policy[field + "_record"])))
            != policy[field + "_sha256"]
        ):
            raise ValueError("Historical review/Primary record changed")
    return policy


def _reference(directory):
    return {
        "run_id": directory.name,
        "status_sha256": storage.sha256(directory / "status.json"),
        "manifest_sha256": storage.sha256(directory / "artifacts.json"),
    }


def _verify_reference(ref):
    directory = config.safe(config.RUNS / ref["run_id"])
    if _reference(directory) != ref:
        raise ValueError("Operational acceptance evidence identity changed")
    for name in storage.artifact_manifest(directory):
        storage.artifact_bytes(directory, name)
    return storage.read_status(directory)


def authority(policy):
    """Validate immutable acceptance, evidence and Git bindings; also usable for retained reads."""
    path = config.safe(Path(policy["authority_record"]))
    if storage.sha256(path) != policy["authority_sha256"]:
        raise ValueError("Operational Primary authority changed")
    value = storage.read_json(path)
    stage = policy["stage"]
    if (
        stage not in {"reviewed-smoke", "accepted-interactive"}
        or value.get("schema") != "apex-v2-operational-acceptance/1"
        or value.get("decision")
        != ("CONDITIONAL_SMOKE" if stage == "reviewed-smoke" else "ACCEPTED")
        or value.get("accepted_revision") != policy["reviewed_revision"]
        or value.get("scientific_source") != config.v1.frozen.SOURCE
        or value.get("profile_sha256") != config.defaults()["profile_sha256"]
        or value.get("review_sha256") != policy["review_sha256"]
        or value.get("producer_sha256") != policy["producer_sha256"]
        or policy.get("automatic_retry") is not False
    ):
        raise ValueError("Operational acceptance source, scope or decision differs")
    brief = config.v1.frozen.git("show", policy["reviewed_revision"] + ":" + BRIEF)
    if hashlib.sha256(brief).hexdigest() != value["primary_brief_sha256"]:
        raise ValueError("Primary conditional operational assignment differs from reviewed source")
    historical = _historical(value["historical_policy"])
    if (
        policy["used"] != historical["used"]
        or policy["maximum_genuine_attempts"] != historical["maximum_genuine_attempts"]
    ):
        raise ValueError("Interactive execution must not mutate research slots")
    if {k: v["run_id"] for k, v in value["historical_evidence"].items()} != HISTORY:
        raise ValueError("Original pilot/full-lap identity differs")
    full = value["historical_evidence"]["full_lap"]
    if (
        full["run_id"],
        full["status_sha256"],
        full["manifest_sha256"],
    ) != evidence.FAILED_NATIVE_RECOVERY:
        raise ValueError("Original failed full lap cannot be reclassified")
    if (
        value["historical_evidence"]["pilot"]["manifest_sha256"]
        != "f18a0639f5f4c6786fb0cfc53fd52a09d3656f0eef24c569a14d7960cbfec911"
    ):
        raise ValueError("Original successful pilot manifest differs")
    for ref in value["historical_evidence"].values():
        _verify_reference(ref)
    if stage == "accepted-interactive":
        smoke_status = _verify_reference(value["smoke"])
        if not all(
            smoke_status.get(k) == v
            for k, v in {
                "state": "completed",
                "scientific_outcome": "completed",
                "evidence_state": "valid",
                "returncode": 0,
            }.items()
        ):
            raise ValueError("Operational acceptance requires the genuine successful5s smoke")
        claim = storage.read_json(config.safe(Path(policy["smoke_claim"])))
        smoke_directory = config.safe(config.RUNS / value["smoke"]["run_id"])
        request = storage.artifact_json(smoke_directory, "request.json")
        if (
            claim
            != {
                "run_id": smoke_directory.name,
                "effective": config.defaults("extended", 5),
                "reviewed_revision": policy["reviewed_revision"],
            }
            or request["provenance"].get("access_stage") != "reviewed-smoke"
            or request["capture"]["producer_sha256"] != policy["producer_sha256"]
            or request["effective"] != config.defaults("extended", 5)
        ):
            raise ValueError("Acceptance smoke must be the exact unique reviewed baseline5s run")
        smoke = evidence.read_run(
            smoke_directory
        )  # Its captured policy is conditional, not recursive.
        if (
            smoke["raw"].get("failure")
            or smoke["raw"].get("stop_reason") != "duration"
            or smoke["summary"].get("coverage_completed") is not True
            or smoke["summary"].get("native_end_time_s") != 5
            or storage.artifact_json(smoke_directory, "worker_result.json") != smoke["summary"]
        ):
            raise ValueError("Successful smoke summary/worker result or native coverage differs")
    return value


def validate(policy, value, *, consume=None, run_id=None):
    authority(policy)
    if policy["stage"] == "accepted-interactive":
        return policy  # Run identity is unique; historical used/counters are never written here.
    if value != config.defaults("extended", 5):
        raise ValueError("Only the explicitly authorized baseline5s operational smoke is available")
    claim = config.safe(Path(policy["smoke_claim"]))
    if consume is not None:
        storage.write_json(
            claim,
            {
                "run_id": consume,
                "effective": value,
                "reviewed_revision": policy["reviewed_revision"],
            },
            exclusive=True,
        )
    elif run_id is None and claim.exists():
        raise ValueError("The single operational smoke is consumed; no automatic retry")
    if run_id is not None:
        record = storage.read_json(claim)
        if record != {
            "run_id": run_id,
            "effective": value,
            "reviewed_revision": policy["reviewed_revision"],
        }:
            raise ValueError("Smoke worker is not the unique authorized run")
    return policy


def retained(policy, request):
    """Verify a captured operational policy independently of the currently installed policy."""
    authority(policy)
    review_path = config.safe(Path(policy["review_record"]))
    review = storage.read_json(review_path)
    if (
        storage.sha256(review_path) != policy["review_sha256"]
        or review.get("outcome") != "PASS"
        or review.get("candidate") != policy["reviewed_revision"]
    ):
        raise ValueError("Retained operational review differs")
    if (
        request["capture"]["producer_sha256"] != policy["producer_sha256"]
        or request["provenance"]["git_revision"] != policy["reviewed_revision"]
        or request["provenance"]["review_sha256"] != policy["review_sha256"]
        or request["provenance"]["authority_sha256"] != policy["authority_sha256"]
        or request["provenance"]["limits"] != config.limits(request["effective"])
    ):
        raise ValueError("Retained operational producer identity differs")
    for name, digest in policy["producer_sha256"].items():
        if (
            hashlib.sha256(
                config.v1.frozen.git("show", policy["reviewed_revision"] + ":" + name)
            ).hexdigest()
            != digest
        ):
            raise ValueError("Retained reviewed Git producer differs")
    if policy["stage"] == "reviewed-smoke":
        validate(policy, request["effective"], run_id=request["run_id"])


def prepare(review_path, folder):
    """Install the separately authorized one-smoke stage, preserving exact historical policy."""
    lease = jobs.execution_lock()
    try:
        review_bytes = Path(review_path).read_bytes()
        review = json.loads(review_bytes)
        source = admission.reviewed_source(review)
        access = config.safe(config.OUTPUT / "access.json")
        old_bytes = access.read_bytes()
        if hashlib.sha256(old_bytes).hexdigest() != HISTORY_SHA:
            raise ValueError("Expected exact original spent research policy; do not reset/retry")
        folder = config.safe(folder)
        folder.mkdir(parents=True, exist_ok=False)
        historical_path = folder / "access_historical.json"
        with historical_path.open("xb") as f:
            f.write(old_bytes)
        historical = {"path": str(historical_path), "sha256": HISTORY_SHA}
        old = _historical(historical)
        pilot = evidence.read_run(config.RUNS / HISTORY["pilot"])
        from .analysis import resource_budget

        resource_budget(pilot)
        failed = evidence.read_run(config.RUNS / HISTORY["full_lap"], recover_failed=True)
        if failed["status"]["state"] != "failed" or not failed.get("recovery"):
            raise ValueError("Original failed full lap must remain failed and descriptive")
        brief = config.v1.frozen.git("show", source + ":" + BRIEF)
        if brief != (config.ROOT / BRIEF).read_bytes():
            raise ValueError("Primary operational assignment changed")
        for name, data in [("PRIMARY_WORK.md", brief), ("review_record.json", review_bytes)]:
            with (folder / name).open("xb") as f:
                f.write(data)
        auth = {
            "schema": "apex-v2-operational-acceptance/1",
            "decision": "CONDITIONAL_SMOKE",
            "accepted_revision": source,
            "scientific_source": config.v1.frozen.SOURCE,
            "profile_sha256": config.defaults()["profile_sha256"],
            "producer_sha256": config.producers(),
            "review_sha256": storage.sha256(folder / "review_record.json"),
            "primary_brief_sha256": hashlib.sha256(brief).hexdigest(),
            "historical_policy": historical,
            "historical_evidence": {k: _reference(config.RUNS / v) for k, v in HISTORY.items()},
            "scope": (
                "Existing finite V2 profiles/eight CostScales/fixed disturbance; "
                "explicit user triggers only; no sweeps or automatic retries"
            ),
        }
        storage.write_json(folder / "conditional_authority.json", auth, exclusive=True)
        policy = {
            **old,
            "stage": "reviewed-smoke",
            "reviewed_revision": source,
            "producer_sha256": config.producers(),
            "review_record": str(folder / "review_record.json"),
            "review_sha256": auth["review_sha256"],
            "authority_record": str(folder / "conditional_authority.json"),
            "authority_sha256": storage.sha256(folder / "conditional_authority.json"),
            "smoke_claim": str(folder / "smoke_claim.json"),
        }
        validate(policy, config.defaults("extended", 5))
        if access.read_bytes() != old_bytes:
            raise ValueError("Historical policy changed during preparation")
        storage.write_json(folder / "policy_smoke.json", policy, exclusive=True)
        storage.write_json(access, policy)
        return policy
    finally:
        lease.close()


def activate():
    """Primary's conditional acceptance becomes effective only after the sole smoke succeeds."""
    lease = jobs.execution_lock()
    try:
        path = config.safe(config.OUTPUT / "access.json")
        before = path.read_bytes()
        policy = json.loads(before)
        if policy["stage"] != "reviewed-smoke":
            raise ValueError("Operational activation is not a reset or repeatable installer")
        source = admission.reviewed_source(storage.read_json(Path(policy["review_record"])))
        auth = authority(policy)
        claim = storage.read_json(config.safe(Path(policy["smoke_claim"])))
        validate(policy, config.defaults("extended", 5), run_id=claim["run_id"])
        view = evidence.read_run(config.RUNS / claim["run_id"])
        if (
            view["status"].get("state") != "completed"
            or view["status"].get("scientific_outcome") != "completed"
            or view["status"].get("returncode") != 0
            or view["status"].get("evidence_state") != "valid"
            or view["request"]["effective"] != config.defaults("extended", 5)
            or view["request"]["capture"]["producer_sha256"] != config.producers()
            or not view["summary"]["coverage_completed"]
            or view["raw"].get("failure")
            or view["raw"].get("stop_reason") != "duration"
        ):
            raise ValueError(
                "The single genuine5s smoke did not complete; preserve outcome and stop"
            )
        folder = Path(policy["authority_record"]).parent
        acceptance = {**auth, "decision": "ACCEPTED", "smoke": _reference(view["directory"])}
        storage.write_json(folder / "accepted_authority.json", acceptance, exclusive=True)
        accepted = {
            **policy,
            "stage": "accepted-interactive",
            "reviewed_revision": source,
            "authority_record": str(folder / "accepted_authority.json"),
            "authority_sha256": storage.sha256(folder / "accepted_authority.json"),
        }
        validate(accepted, config.defaults("full_lap"))
        evidence.current(view)
        if path.read_bytes() != before:
            raise ValueError("Policy changed during final activation")
        storage.write_json(folder / "policy_accepted.json", accepted, exclusive=True)
        storage.write_json(path, accepted)
        return accepted
    finally:
        lease.close()
