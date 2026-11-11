"""Final V2 display/admission checks; no simulation or optimizer execution."""

import copy
import math
from types import SimpleNamespace

import pytest

from tools.apex_workbench import storage
from tools.apex_workbench.lap import (
    admission,
    analysis,
    config,
    evidence,
    final_attempt,
    reference_view,
    ui_data,
)
from tools.apex_workbench.tests.test_lap_v2 import policy
from tools.apex_workbench.tests.test_lap_v2 import valid_pilot as valid_pilot


def test_only_two_authorized_full_lap_resource_fields_change():
    digest, old = config.legacy_profile()
    expected = copy.deepcopy(old)
    expected["limits"]["full_lap"].update(wall_s=900, cpu_s=720)
    assert config.PROFILE == expected
    assert digest == "a271bc46655b50d3c1bc921e20a0b951c7004d28110ea7ad111c44c02e731610"
    assert config.PROFILE["limits"]["extended"] == old["limits"]["extended"]
    legacy = {**config.defaults(), "profile_sha256": digest}
    assert config.validate_retained(legacy) == legacy
    assert config.baseline_pilot(legacy)
    with pytest.raises(ValueError):
        config.validate(legacy)
    legacy["scratch"]["costs"]["lateral"] = 1
    assert not config.baseline_pilot(legacy)


def test_original_pilot_remains_source_bound_and_current_projection_fits():
    value = storage.read_json(config.OUTPUT / "access.json")
    view = evidence.read_run(config.RUNS / value["used"]["pilot"])
    before = {name: storage.sha256(view["directory"] / name) for name in view["anchor"]}
    assert view["request"]["effective"]["profile_sha256"] == config.legacy_profile()[0]
    budget = analysis.resource_budget(view)
    assert budget["conservative_extrapolation"]["cpu_s"] == 551.42816
    assert budget["limits"]["cpu_s"] == 720 and budget["limits"]["wall_s"] == 900
    assert before == {name: storage.sha256(view["directory"] / name) for name in view["anchor"]}


@pytest.mark.parametrize(
    "fault", ["revision", "profile", "brief", "prior_bytes", "history", "slot"]
)
def test_bound_authority_cannot_change_source_history_or_scope(tmp_path, monkeypatch, fault):
    value = policy(tmp_path, monkeypatch)
    authority = storage.read_json(tmp_path / "authority.json")
    if fault == "revision":
        authority["reviewed_revision"] = "other"
    elif fault == "profile":
        authority["profile_sha256"] = "other"
    elif fault == "brief":
        authority["primary_brief_sha256"] = "other"
    elif fault == "prior_bytes":
        (tmp_path / "prior.json").write_text("{}")
    elif fault == "history":
        storage.write_json(
            tmp_path / "prior.json",
            {
                "used": {"pilot": "original"},
                "maximum_genuine_attempts": {"pilot": 1, "full_lap": 1},
            },
        )
        authority["prior_policy"]["sha256"] = storage.sha256(tmp_path / "prior.json")
    else:
        authority["allowed_new_slots"] = ["full_lap"]
    storage.write_json(tmp_path / "authority.json", authority)
    value["authority_sha256"] = storage.sha256(tmp_path / "authority.json")
    storage.write_json(tmp_path / "access.json", value)
    with pytest.raises(ValueError):
        config.access(config.defaults(), consume="not-permitted")
    assert storage.read_json(tmp_path / "access.json")["used"] == {}


def test_full_lap_declaration_is_bound_and_consumed_once(tmp_path, monkeypatch, valid_pilot):
    value = policy(tmp_path, monkeypatch)
    valid_pilot["status"]["manifest_sha256"] = "pilot-manifest"
    monkeypatch.setattr(evidence, "read_run", lambda _: valid_pilot)
    budget = analysis.resource_budget(valid_pilot)
    declared = {
        "pilot_manifest_sha256": "pilot-manifest",
        "budget": budget,
        "reviewed_revision": "fixture-revision",
        "policy_identity": config.policy_identity(value),
        "host": {"status": "PASS"},
    }
    storage.write_json(tmp_path / "full_lap_preflight.json", declared)
    config.access(config.defaults("full_lap"), consume="one-full")
    assert (
        config.access(config.defaults("full_lap"), run_id="one-full")["used"]["full_lap"]
        == "one-full"
    )
    with pytest.raises(ValueError):
        config.access(config.defaults("full_lap"), consume="retry")
    declared["host"]["status"] = "BLOCKED"
    storage.write_json(tmp_path / "full_lap_preflight.json", declared)
    with pytest.raises(ValueError):
        config.access(config.defaults("full_lap"), run_id="one-full")


def test_pending_acceptance_draft_cannot_enable_interactive_execution(tmp_path, monkeypatch):
    value = policy(tmp_path, monkeypatch)
    storage.write_json(
        tmp_path / "authority.json",
        {
            "schema": "apex-lap-primary-acceptance/1",
            "accepted_revision": "fixture-revision",
            "decision": "PENDING_PRIMARY_ACCEPTANCE",
        },
    )
    value.update(
        stage="accepted-interactive", authority_sha256=storage.sha256(tmp_path / "authority.json")
    )
    storage.write_json(tmp_path / "access.json", value)
    with pytest.raises(ValueError, match="Operational acceptance"):
        config.access(config.defaults("extended", 20))


def test_transition_preserves_exact_prior_bytes_and_consumed_pilot(
    tmp_path, monkeypatch, valid_pilot
):
    old = policy(tmp_path, monkeypatch)
    old["used"] = {"pilot": "original"}
    storage.write_json(tmp_path / "access.json", old)
    prior = (tmp_path / "access.json").read_bytes()
    monkeypatch.setattr(config, "ROOT", tmp_path)
    (tmp_path / admission.BRIEF).parent.mkdir(parents=True)
    (tmp_path / admission.BRIEF).write_bytes(b"reviewed source fixture")
    valid_pilot["request"]["capture"] = {"producer_sha256": old["producer_sha256"]}
    valid_pilot["status"]["manifest_sha256"] = "original-manifest"
    monkeypatch.setattr(evidence, "read_run", lambda _: valid_pilot)
    storage.write_json(tmp_path / "current_review.json", {"outcome": "PASS", "candidate": "a" * 40})
    new = admission.install(tmp_path / "current_review.json", tmp_path / "transition")
    assert new["used"] == {"pilot": "original"} and new["automatic_retry"] is False
    assert (tmp_path / "transition/access_before.json").read_bytes() == prior
    assert storage.read_json(tmp_path / "transition/authority.json")["allowed_new_slots"] == [
        "full_lap"
    ]
    with pytest.raises(ValueError):
        admission.install(tmp_path / "current_review.json", tmp_path / "transition")


def test_existing_once_only_claim_never_restarts(tmp_path, monkeypatch):
    policy(tmp_path, monkeypatch)
    (tmp_path / "full_lap_final_claim.json").write_text("original claim")
    monkeypatch.setattr(admission, "reviewed_source", lambda _: "a" * 40)
    monkeypatch.setattr(
        final_attempt, "host", lambda _: pytest.fail("Claim retry reached host preflight")
    )
    with pytest.raises(ValueError, match="claim already exists"):
        final_attempt.start_once()


@pytest.mark.parametrize("enough", [False, True])
def test_metadata_host_capacity_keeps_original_full_lap_floor(
    tmp_path, monkeypatch, valid_pilot, enough
):
    monkeypatch.setattr(final_attempt.jobs, "preflight", lambda: None)
    monkeypatch.setattr(final_attempt.psutil, "process_iter", lambda *_: [])
    monkeypatch.setattr(final_attempt.os, "walk", lambda *a, **kw: [])
    floor = 2 * 768 * 2**20
    monkeypatch.setattr(
        final_attempt.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(available=floor + (1 if enough else 0)),
    )
    monkeypatch.setattr(
        final_attempt.shutil, "disk_usage", lambda _: SimpleNamespace(free=3 * 2**30)
    )
    monkeypatch.setattr(final_attempt.psutil, "cpu_percent", lambda **_: 0)
    result = final_attempt.host(analysis.resource_budget(valid_pilot))
    assert result["required_available_ram_bytes"] == floor
    assert result["status"] == ("PASS" if enough else "BLOCKED")


def test_genuine_nine_node_projection_is_derived_without_scientific_execution_modules():
    view = ui_data.read(ui_data.recordings("V2")[0])
    data = ui_data.payload(ui_data.window(view, ui_data.windows(view)[0]))
    first = data["packets"][0]
    assert len(first["microscope"]) == 9 and len(first["controls"]) == 8
    assert first["microscope"][0]["lateral_error_m"] == 0
    assert first["microscope"][0]["heading_error_rad"] == 0
    assert [n["predicted_xy"] for n in first["microscope"]] == first["xy"]
    projected = reference_view.project(ui_data.capture(view), [first])
    assert not any(
        n.startswith(("apex.control", "apex.models", "apex.simulation", "casadi"))
        for n in projected["imports"]
    )
    assert "not retained NMPC preview" in data["meta"]["microscope_status"]


def test_missing_reference_stays_unavailable_without_fabricated_errors(monkeypatch):
    view = ui_data.read(ui_data.recordings("V2")[0])
    view["request"]["capture"]["source_sha256"].pop(ui_data.REFERENCE)
    monkeypatch.setattr(
        reference_view, "project", lambda *_: pytest.fail("Missing source reached projection")
    )
    data = ui_data.payload(ui_data.window(view, ui_data.windows(view)[0]))
    assert data["planning_reference"] == [] and all(
        p["microscope"] is None for p in data["packets"]
    )
    assert data["meta"]["microscope_status"].startswith("Unavailable")


def test_reference_scalar_seam_and_heading_endpoint_follow_canonical_semantics():
    # Geometry-only fixture: not a trajectory, optimizer input, execution or qualification case.
    view = ui_data.read(ui_data.recordings("V2")[0])
    import csv
    import io

    csv_bytes = config.v1.frozen.git("show", config.v1.frozen.SOURCE + ":" + ui_data.REFERENCE)
    row = next(csv.DictReader(io.StringIO(csv_bytes.decode())))
    ey = float(row["e_y_ref_m"])
    heading = float(row["e_psi_ref_rad"])
    length = view["request"]["capture"]["resolved"]["track_length_m"]
    state = [1.0, 0.0, 0.0, heading + math.pi, 0.0, ey]
    other = [1.0, 0.0, 0.0, heading - math.pi, length, ey]
    values = reference_view.project(
        ui_data.capture(view),
        [{"id": 80001, "states": [state] * 9}, {"id": 80002, "states": [other] * 9}],
    )["packets"]
    for packet in values:
        node = packet["nodes"][0]
        assert node["reference_e_y_m"] == pytest.approx(ey, abs=1e-12)
        assert node["lateral_error_m"] == pytest.approx(0, abs=1e-12)
        assert node["heading_error_rad"] == pytest.approx(math.pi, abs=1e-12)
    assert values[0]["nodes"][0]["reference_xy"] == values[1]["nodes"][0]["reference_xy"]


def test_preclaim_source_failure_preserves_unused_full_attempt(tmp_path, monkeypatch, valid_pilot):
    value = policy(tmp_path, monkeypatch)
    value["used"] = {"pilot": "original"}
    storage.write_json(tmp_path / "access.json", value)
    monkeypatch.setattr(admission, "reviewed_source", lambda _: "a" * 40)
    monkeypatch.setattr(evidence, "read_run", lambda _: valid_pilot)
    monkeypatch.setattr(final_attempt, "host", lambda _: {"status": "PASS"})
    monkeypatch.setattr(config.v1.frozen, "source_hashes", lambda: {})

    def fail(*args):
        raise ValueError("source changed before claim")

    monkeypatch.setattr(config.v1.frozen, "verify_runtime", fail)
    with pytest.raises(ValueError, match="before claim"):
        final_attempt.start_once()
    assert storage.read_json(tmp_path / "access.json")["used"] == {"pilot": "original"}
    assert not (tmp_path / "full_lap_final_claim.json").exists()
    assert not (tmp_path / "full_lap_preflight.json").exists()
    result = storage.read_json(next(tmp_path.glob("final_source_preflight_*.json")))
    assert result["status"] == "BLOCKED" and result["claim_consumed"] is False
