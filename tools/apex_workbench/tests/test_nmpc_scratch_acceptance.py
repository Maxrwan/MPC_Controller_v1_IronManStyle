"""Accepted-policy checks; no optimizer, worker or scientific execution."""

import copy
import hashlib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs, storage
from tools.apex_workbench import nmpc_scratch as scratch
from tools.apex_workbench.tests.test_nmpc_scratch import policy_fixture, widget


def accepted_fixture(tmp_path, monkeypatch):
    policy = policy_fixture(tmp_path, monkeypatch)
    policy["used"] = {k: "historical_" + k for k in scratch.work_cases()}
    primary = scratch.OUTPUT / "primary.json"
    storage.write_json(primary, {"decision": "Synthetic experimentation accepted fixture"})
    policy.update(
        stage="accepted-interactive",
        primary_acceptance_record=str(primary),
        primary_acceptance_sha256=storage.sha256(primary),
    )
    storage.write_json(scratch.OUTPUT / "access.json", policy)
    return policy


def test_accepted_repeatable_admission_preserves_consumed_history(tmp_path, monkeypatch):
    policy = accepted_fixture(tmp_path, monkeypatch)
    before = (scratch.OUTPUT / "access.json").read_bytes()
    values = scratch.defaults()
    values["costs"]["lateral"] = 1.25
    for name in ["first_explicit_run", "second_explicit_run"]:
        assert scratch.access(values)["stage"] == "accepted-interactive"
        scratch.consume(values, name)
    assert (scratch.OUTPUT / "access.json").read_bytes() == before
    assert scratch.access(values)["used"] == policy["used"]


@pytest.mark.parametrize(
    "fault",
    [
        "missing_primary",
        "changed_primary",
        "changed_review",
        "failed_review",
        "producer",
        "git_reseal",
    ],
)
def test_accepted_admission_fails_closed(tmp_path, monkeypatch, fault):
    policy = accepted_fixture(tmp_path, monkeypatch)
    primary, review = (Path(policy[k]) for k in ("primary_acceptance_record", "review_record"))
    if fault == "missing_primary":
        primary.unlink()
    elif fault == "changed_primary":
        primary.write_text("changed acceptance")
    elif fault == "changed_review":
        review.write_text("{}")
    elif fault == "failed_review":
        storage.write_json(review, {"outcome": "BLOCKED", "candidate": policy["reviewed_revision"]})
        policy["review_sha256"] = storage.sha256(review)
    else:
        hashes = dict(policy["producer_sha256"])
        hashes["tools/apex_workbench/nmpc_scratch_panels.py"] = "e" * 64
        monkeypatch.setattr(scratch, "producer_hashes", lambda: hashes)
        if fault == "git_reseal":
            policy["producer_sha256"] = hashes
    storage.write_json(scratch.OUTPUT / "access.json", policy)
    with pytest.raises((OSError, ValueError)):
        scratch.access(scratch.defaults())


@pytest.mark.parametrize("field", ["mass", "solver", "horizon", "duration"])
def test_acceptance_does_not_expand_configuration(tmp_path, monkeypatch, field):
    accepted_fixture(tmp_path, monkeypatch)
    values = scratch.defaults()
    values[field] = 1
    with pytest.raises(ValueError):
        scratch.access(values)


def test_actual_primary_binding_and_source_lineage_are_read_only():
    policy = scratch.access(scratch.defaults())
    primary = storage.read_json(Path(policy["primary_acceptance_record"]))
    previous = storage.read_json(Path(policy["previous_policy_record"]))
    assert (
        storage.sha256(Path(policy["previous_policy_record"])) == policy["previous_policy_sha256"]
    )
    assert primary["decision"] == "ACCEPTED_FOR_SYNTHETIC_EXPERIMENTATION"
    assert primary["accepted_implementation"] == policy["reviewed_revision"]
    assert primary["historical_used"] == previous["used"] == policy["used"]
    assert primary["historical_cases"] == previous["cases"] == policy["cases"]
    assert primary["limits"] == jobs.LIMITS
    assert set(primary["approved_producer_delta"]) == {
        "tools/apex_workbench/nmpc_scratch_panels.py"
    }
    assert len(primary["independent_reviews"]) == 2
    for review in primary["independent_reviews"]:
        path = scratch.safe(scratch.OUTPUT / review["record_copy"])
        assert storage.sha256(path) == review["sha256"]
        data = storage.read_json(path)
        assert data["candidate"] == review["candidate"] and data["outcome"] == "PASS"
        raw = scratch.frozen.git(
            "show", review["record_git_delivery"] + ":" + review["record_git_path"]
        )
        assert hashlib.sha256(raw).hexdigest() == review["sha256"]


def test_standard_accepted_navigation_without_execution(monkeypatch):
    def forbidden(*a, **kw):
        raise AssertionError("No genuine run/probe during software checks")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    monkeypatch.setattr(scratch, "probe", forbidden)
    app = AppTest.from_file(
        str(Path(__file__).parents[1] / "workspace.py"), default_timeout=45
    ).run()
    widget(app.button, "Open NMPC Scratch / Control Analysis").click().run()
    assert not app.exception and not app.warning
    assert not widget(app.button, "Run Scratch experiment").disabled
    assert len([w for w in app.number_input if w.label in scratch.FIELDS]) == 8
    widget(app.number_input, "lateral").set_value(1.25).run()
    widget(app.button, "Reset costs to accepted baseline").click().run()
    assert widget(app.number_input, "lateral").value == 2.0
    for page in ("Analyze", "Inspect", "Compare"):
        widget(app.radio, "Workspace").set_value(page).run()
        assert not app.exception and not app.error
    widget(app.radio, "Comparison source").set_value("NMPC Scratch (unqualified)").run()
    views = {
        scratch.read_run(p)["request"]["effective"]["configuration_id"]: p
        for p in scratch.RUNS.iterdir()
    }
    widget(app.multiselect, "Scratch experiments").set_value(
        [views["baseline"], views["lateral_1"]]
    ).run()
    assert any(x.value.startswith("Controlled cost-configuration") for x in app.info)


def test_saved_experimental_draft_is_versioned_and_exclusive(tmp_path, monkeypatch):
    monkeypatch.setattr(scratch, "OUTPUT", tmp_path)
    value = copy.deepcopy(scratch.defaults())
    value["configuration_id"] = "experimental_draft"
    path = scratch.saved_configuration(value)
    assert scratch.loads(path.read_text()) == value
    with pytest.raises(FileExistsError):
        scratch.saved_configuration(value)
    value["version"] = 2
    assert scratch.saved_configuration(value) != path
