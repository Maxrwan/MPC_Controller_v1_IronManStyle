"""Versioned selection and source-bound admission; no numerical imports."""

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tools.apex_workbench import nmpc_scratch as v1
from tools.apex_workbench import storage
from tools.apex_workbench.configuration import ROOT

HERE = Path(__file__).parent
PROFILE = storage.read_json(HERE / "profile.json")
OUTPUT = ROOT / "results/apex_workbench_v2_lap"
RUNS = OUTPUT / "runs"
LEGACY_REVISION = "fdd494eb7ddf9b456b88cba243fbc704a4fd83c0"


@lru_cache(maxsize=1)
def legacy_profile():
    raw = v1.frozen.git("show", LEGACY_REVISION + ":tools/apex_workbench/lap/profile.json")
    return hashlib.sha256(raw).hexdigest(), json.loads(raw)


def validate_retained(value):
    """Read the exact historical profile; never authorize a new execution with its digest."""
    if value.get("profile_sha256") == storage.sha256(HERE / "profile.json"):
        return validate(value)
    digest, old = legacy_profile()
    allowed = copy.deepcopy(old)
    allowed["limits"]["full_lap"].update(wall_s=900, cpu_s=720)
    if value.get("profile_sha256") != digest or PROFILE != allowed:
        raise ValueError("Unsupported retained V2 profile identity or profile transition")
    result = validate({**value, "profile_sha256": storage.sha256(HERE / "profile.json")})
    return {**result, "profile_sha256": digest}


def baseline_pilot(value):
    checked = validate_retained(value)
    return {**checked, "profile_sha256": defaults()["profile_sha256"]} == defaults()


def safe(path):
    return v1.frozen.safe(path, OUTPUT)


def defaults(mode="extended", duration=10):
    return {
        "schema": "apex-lap-configuration/1",
        "profile": PROFILE["id"],
        "profile_sha256": storage.sha256(HERE / "profile.json"),
        "scientific_source": v1.frozen.SOURCE,
        "mode": mode,
        "maximum_simulation_s": duration if mode == "extended" else 80,
        "scratch": v1.defaults(),
    }


def validate(value):
    if type(value) is not dict or set(value) != set(defaults()):
        raise ValueError("Use exactly the versioned V2 fields")
    expected = defaults(value["mode"], value["maximum_simulation_s"])
    for key in ("schema", "profile", "profile_sha256", "scientific_source"):
        if value[key] != expected[key]:
            raise ValueError("V2 profile/source identity differs")
    if value["mode"] not in ("extended", "full_lap"):
        raise ValueError("Transient uses the unchanged accepted V1 path")
    duration = value["maximum_simulation_s"]
    if type(duration) is not int or duration not in (
        PROFILE["extended_seconds"] if value["mode"] == "extended" else [80]
    ):
        raise ValueError("Unsupported finite simulation ceiling")
    return {**value, "scratch": v1.validate(value["scratch"])}


def limits(value):
    return dict(PROFILE["limits"][validate(value)["mode"]])


def producers():
    paths = [*v1.PRODUCERS, "tools/apex_workbench/scratch_replay.py"]
    paths += ["Launch_APEX_Workbench_V2.command"]
    paths += [str(p.relative_to(ROOT)) for p in HERE.iterdir() if p.suffix in {".py", ".json"}]
    paths += [
        str(p.relative_to(ROOT))
        for p in (HERE.parent / "scratch_replay_web").rglob("*")
        if p.is_file()
    ]
    paths += [str(p.relative_to(ROOT)) for p in (HERE / "ui_web").rglob("*") if p.is_file()]
    return {name: storage.sha256(ROOT / name) for name in sorted(set(paths))}


def policy_identity(policy):
    """Bind every policy field except the once-only mutable full-lap run ID."""
    value = {**policy, "used": {k: v for k, v in policy["used"].items() if k != "full_lap"}}
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def access(value, *, consume=None, run_id=None):
    value = validate(value)
    policy = storage.read_json(safe(OUTPUT / "access.json"))
    review_path = safe(Path(policy["review_record"]))
    review = storage.read_json(review_path)
    if (
        policy.get("schema") != "apex-lap-access/1"
        or policy.get("producer_sha256") != producers()
        or storage.sha256(review_path) != policy.get("review_sha256")
        or review.get("outcome") != "PASS"
        or review.get("candidate") != policy.get("reviewed_revision")
    ):
        raise ValueError("V2 independent review/source identity absent or stale")
    for name, digest in policy["producer_sha256"].items():
        if (
            hashlib.sha256(
                v1.frozen.git("show", policy["reviewed_revision"] + ":" + name)
            ).hexdigest()
            != digest
        ):
            raise ValueError("V2 reviewed Git source differs")
    authority = safe(Path(policy["authority_record"]))
    if storage.sha256(authority) != policy.get("authority_sha256"):
        raise ValueError("Explicit Primary authority changed")
    if policy.get("stage") == "accepted-interactive":
        accepted = storage.read_json(authority)
        if (
            accepted.get("schema") != "apex-lap-primary-acceptance/1"
            or accepted.get("accepted_revision") != policy["reviewed_revision"]
            or accepted.get("decision") != "ACCEPTED"
        ):
            raise ValueError(
                "Repeatable V2 needs explicit final Primary acceptance of this revision"
            )
        return policy
    if policy.get("stage") != "reviewed-work":
        raise ValueError("V2 execution awaits review/acceptance")
    authorization = storage.read_json(authority)
    if (
        authorization.get("schema") != "apex-lap-final-work-authorization/1"
        or authorization.get("reviewed_revision") != policy["reviewed_revision"]
        or authorization.get("profile_sha256") != value["profile_sha256"]
        or authorization.get("scientific_source") != v1.frozen.SOURCE
        or policy.get("automatic_retry") is not False
        or authorization.get("primary_brief_sha256")
        != hashlib.sha256(
            v1.frozen.git(
                "show", policy["reviewed_revision"] + ":docs/workbench_v2_final/PRIMARY_WORK.md"
            )
        ).hexdigest()
    ):
        raise ValueError("Source-bound Primary WORK authorization differs")
    prior = authorization["prior_policy"]
    prior_path = safe(Path(prior["path"]))
    if storage.sha256(prior_path) != prior["sha256"]:
        raise ValueError("Historical execution policy changed")
    historical = storage.read_json(prior_path)
    if any(policy.get("used", {}).get(k) != v for k, v in historical["used"].items()) or policy.get(
        "maximum_genuine_attempts"
    ) != historical.get("maximum_genuine_attempts"):
        raise ValueError("Historical consumed attempts must remain intact")
    slot = "pilot" if value == defaults() else "full_lap" if value == defaults("full_lap") else None
    if (
        slot is None
        or type(policy.get("used")) is not dict
        or set(policy["used"]) - {"pilot", "full_lap"}
    ):
        raise ValueError(
            "Only the once-only baseline10s pilot and conditional full lap are authorized"
        )
    if slot not in authorization.get("allowed_new_slots", []):
        raise ValueError("This slot is not authorized by the current Primary assignment")
    if slot in policy["used"] and policy["used"][slot] != run_id:
        raise ValueError("This V2 WORK attempt is already consumed; no automatic retry")
    if run_id is not None and policy["used"].get(slot) != run_id:
        raise ValueError("V2 worker is not the consumed authorized run")
    if slot == "full_lap":
        from .analysis import resource_budget
        from .evidence import read_run

        pilot = read_run(RUNS / policy["used"].get("pilot", "missing"))
        budget = resource_budget(pilot)
        declared = storage.read_json(safe(OUTPUT / "full_lap_preflight.json"))
        if (
            declared["pilot_manifest_sha256"] != pilot["status"]["manifest_sha256"]
            or declared["budget"] != budget
            or declared.get("reviewed_revision") != policy["reviewed_revision"]
            or declared.get("policy_identity") != policy_identity(policy)
            or declared.get("host", {}).get("status") != "PASS"
        ):
            raise ValueError("Full-lap finite pilot-supported preflight differs")
    if consume is not None:
        policy["used"][slot] = consume
        storage.write_json(safe(OUTPUT / "access.json"), policy)
    return policy


def canonical(value):
    return json.dumps(validate(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
