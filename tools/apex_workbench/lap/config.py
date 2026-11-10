"""Versioned selection and source-bound admission; no numerical imports."""

import hashlib
import json
from pathlib import Path

from tools.apex_workbench import nmpc_scratch as v1
from tools.apex_workbench import storage
from tools.apex_workbench.configuration import ROOT

HERE = Path(__file__).parent
PROFILE = storage.read_json(HERE / "profile.json")
OUTPUT = ROOT / "results/apex_workbench_v2_lap"
RUNS = OUTPUT / "runs"


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
    return {name: storage.sha256(ROOT / name) for name in sorted(set(paths))}


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
        ):
            raise ValueError(
                "Repeatable V2 needs explicit final Primary acceptance of this revision"
            )
        return policy
    if policy.get("stage") != "reviewed-work":
        raise ValueError("V2 execution awaits review/acceptance")
    slot = "pilot" if value == defaults() else "full_lap" if value == defaults("full_lap") else None
    if (
        slot is None
        or type(policy.get("used")) is not dict
        or set(policy["used"]) - {"pilot", "full_lap"}
    ):
        raise ValueError(
            "Only the once-only baseline10s pilot and conditional full lap are authorized"
        )
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
        ):
            raise ValueError("Full-lap finite pilot-supported preflight differs")
    if consume is not None:
        policy["used"][slot] = consume
        storage.write_json(safe(OUTPUT / "access.json"), policy)
    return policy


def canonical(value):
    return json.dumps(validate(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
