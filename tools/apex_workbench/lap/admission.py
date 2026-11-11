"""Explicit one-shot V2 policy transition; no numerical execution or automatic acceptance."""

import copy
import hashlib
import json
from pathlib import Path

from tools.apex_workbench import storage

from . import analysis, config, evidence

BRIEF = "docs/workbench_v2_final/PRIMARY_WORK.md"


def reviewed_source(review):
    if review.get("outcome") != "PASS" or len(review.get("candidate", "")) != 40:
        raise ValueError("An exact independent PASS is required")
    source = review["candidate"]
    for name, digest in config.producers().items():
        if hashlib.sha256(config.v1.frozen.git("show", source + ":" + name)).hexdigest() != digest:
            raise ValueError("Current/Git reviewed producer differs: " + name)
    return source


def install(review_path, folder):
    """Install only after independent PASS, preserving original policy and consumed pilot."""
    review_path = Path(review_path)
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    source = reviewed_source(review)
    folder = config.safe(folder)
    if folder.exists():
        raise ValueError("Policy transition destination already exists; preserve it")
    path = config.safe(config.OUTPUT / "access.json")
    previous_bytes = path.read_bytes()
    previous = json.loads(previous_bytes)
    if (
        previous.get("schema") != "apex-lap-access/1"
        or previous.get("stage") != "reviewed-work"
        or set(previous.get("used", {})) != {"pilot"}
        or previous.get("maximum_genuine_attempts") != {"pilot": 1, "full_lap": 1}
        or previous.get("automatic_retry") is not False
    ):
        raise ValueError("Expected intact consumed pilot and unused once-only full-lap slot")
    old_review_path = config.safe(Path(previous["review_record"]))
    old_review = storage.read_json(old_review_path)
    if (
        storage.sha256(old_review_path) != previous["review_sha256"]
        or old_review.get("outcome") != "PASS"
        or old_review.get("candidate") != previous["reviewed_revision"]
    ):
        raise ValueError("Original review/source binding differs")
    for name, digest in previous["producer_sha256"].items():
        if (
            hashlib.sha256(
                config.v1.frozen.git("show", previous["reviewed_revision"] + ":" + name)
            ).hexdigest()
            != digest
        ):
            raise ValueError("Original producer provenance differs")
    authority_path = config.safe(Path(previous["authority_record"]))
    if storage.sha256(authority_path) != previous["authority_sha256"]:
        raise ValueError("Original Primary authority changed")
    pilot = evidence.read_run(config.RUNS / previous["used"]["pilot"])
    budget = analysis.resource_budget(pilot)
    if pilot["request"]["capture"]["producer_sha256"] != previous["producer_sha256"]:
        raise ValueError("Historical pilot producer source differs")
    brief = config.v1.frozen.git("show", source + ":" + BRIEF)
    if brief != (config.ROOT / BRIEF).read_bytes():
        raise ValueError("Primary assignment differs from reviewed source")
    folder.mkdir(parents=True, exist_ok=False)
    for name, data in [
        ("access_before.json", previous_bytes),
        ("review_record.json", review_bytes),
        ("PRIMARY_WORK.md", brief),
    ]:
        with (folder / name).open("xb") as stream:
            stream.write(data)
    authority = {
        "schema": "apex-lap-final-work-authorization/1",
        "reviewed_revision": source,
        "scientific_source": config.v1.frozen.SOURCE,
        "profile_sha256": config.defaults()["profile_sha256"],
        "primary_brief_sha256": hashlib.sha256(brief).hexdigest(),
        "prior_policy": {
            "path": str(folder / "access_before.json"),
            "sha256": hashlib.sha256(previous_bytes).hexdigest(),
        },
        "allowed_new_slots": ["full_lap"],
        "automatic_retry": False,
        "historical_pilot": previous["used"]["pilot"],
        "historical_pilot_manifest_sha256": pilot["status"]["manifest_sha256"],
        "accepted_presentation_revision": "b1cc8b3d7b306a56adf99a63d8dc689c13856114",
    }
    storage.write_json(folder / "authority.json", authority, exclusive=True)
    replacement = {
        **previous,
        "reviewed_revision": source,
        "review_record": str(folder / "review_record.json"),
        "review_sha256": storage.sha256(folder / "review_record.json"),
        "producer_sha256": config.producers(),
        "authority_record": str(folder / "authority.json"),
        "authority_sha256": storage.sha256(folder / "authority.json"),
    }
    # No spent slot is removed, copied into a new slot, or reset.
    if replacement["used"] != previous["used"] or path.read_bytes() != previous_bytes:
        raise ValueError("Execution history changed during transition")
    storage.write_json(path, replacement)
    storage.write_json(
        folder / "transition.json",
        {
            "prior_sha256": hashlib.sha256(previous_bytes).hexdigest(),
            "current_sha256": storage.sha256(path),
            "reviewed_revision": source,
            "used_before": previous["used"],
            "used_after": replacement["used"],
            "budget": budget,
            "new_execution_started": False,
        },
        exclusive=True,
    )
    return replacement


def acceptance_proposal(full_run):
    """A pending proposal cannot authorize accepted-interactive execution."""
    policy = storage.read_json(config.safe(config.OUTPUT / "access.json"))
    source = reviewed_source(storage.read_json(config.safe(Path(policy["review_record"]))))
    view = evidence.read_run(full_run)
    if (
        view["directory"].name != policy["used"].get("full_lap")
        or view["status"]["state"] != "completed"
        or view["status"]["scientific_outcome"] != "completed"
        or view["status"]["evidence_state"] != "valid"
        or view["status"].get("returncode") != 0
        or not view["summary"]["coverage_completed"]
        or view["summary"]["lap"]["completed_laps"] != 1
        or view["raw"].get("failure")
    ):
        raise ValueError(
            "A genuine successful full-lap outcome is required for the acceptance proposal"
        )
    if view["request"]["capture"]["producer_sha256"] != policy["producer_sha256"]:
        raise ValueError("Full-lap accepted-source proposal differs from its execution")
    return {
        "schema": "apex-lap-primary-acceptance/1",
        "decision": "PENDING_PRIMARY_ACCEPTANCE",
        "accepted_revision": source,
        "scientific_source": config.v1.frozen.SOURCE,
        "profile_sha256": config.defaults()["profile_sha256"],
        "producer_sha256": config.producers(),
        "review_sha256": policy["review_sha256"],
        "authority_sha256": policy["authority_sha256"],
        "used": copy.deepcopy(policy["used"]),
        "full_run": view["directory"].name,
        "full_manifest_sha256": view["status"]["manifest_sha256"],
        "scope": (
            "Existing finite profiles, explicit user triggers, eight cost fields, "
            "fixed disturbance; no sweeps"
        ),
        "installed": False,
    }
