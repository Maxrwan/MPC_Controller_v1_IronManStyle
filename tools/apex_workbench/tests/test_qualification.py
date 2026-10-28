"""Literal calculation fixtures are never real qualification evidence or model trajectories."""

import shutil
from copy import deepcopy
from math import pi

import pytest

from tools.apex_workbench import storage
from tools.apex_workbench.lab_configuration import CASES, GRIDS, execution_context, request_for
from tools.apex_workbench.lab_evidence import read_record
from tools.apex_workbench.qualification import (
    PARITY_FILES,
    SCHEMA,
    SLOTS,
    bind_run,
    bound_run,
    check_current_source,
    evaluate_references,
    exact_export_comparison,
    read_qualification,
    require_protocol_run,
)
from tools.apex_workbench.qualification_campaign import execute, plan
from tools.apex_workbench.qualification_math import calculate
from tools.apex_workbench.tests.test_corrections import reseal_fixture


def literal_family():
    """Nonphysical numerical arrays for arithmetic tests; explicitly not experimental output."""
    family = {}
    for case in CASES:
        family[case] = {}
        for grid, (h, steps, onset) in GRIDS.items():
            states, diagnostics = [], []
            for k in range(steps + 1):
                states.append(
                    dict(
                        time=k * h,
                        vx=2.0,
                        vy=0.0,
                        r=0.001 if case != "VDL1_BASE" and k >= onset else 0.0,
                        e_psi=0.0,
                        s_abs=0.0,
                        e_y=0.0,
                        boundary_violation=False,
                    )
                )
                diagnostics.append(
                    dict(
                        time=k * h,
                        alpha_f=0.0,
                        alpha_r=0.0,
                        front_lateral_utilization=0.0,
                        rear_lateral_utilization=0.0,
                    )
                )
            family[case][grid] = {
                "states": states,
                "diagnostics": diagnostics,
                "summary": {
                    "horizon_reached": True,
                    "runner_stop_reason": "duration",
                    "failure": None,
                },
                "test_fixture_only": True,
            }
    return family


def add_error(family, case, grid, channel, value):
    for row in family[case][grid]["states"][1:]:
        row[channel] += value


def test_literal_zero_error_and_signal_calculation_has_no_evidence_authority():
    result = calculate(literal_family())
    assert result["authority"] == "calculation_only_not_qualification_evidence"
    assert result["physical_validity"] == "not_established"
    assert result["all_criteria_satisfied"]
    for case in CASES:
        for c in result["cases"][case]["components"].values():
            assert c["d0"] == c["d1"] == c["nominal_finest"] == 0.0
            assert c["refinement_ratio"] is None
    for p in result["pairs"].values():
        assert p["peak_yaw_difference_rad_per_s"] == 0.001
        assert p["required_signal_rad_per_s"] == 0.0001


@pytest.mark.parametrize("channel", ["vx", "vy", "r", "e_psi", "s_abs", "e_y"])
def test_literal_componentwise_convergence_numbers(channel):
    family = literal_family()
    add_error(family, "VDL1_BASE", "nominal", channel, 4e-6)
    add_error(family, "VDL1_BASE", "half", channel, 1e-6)
    result = calculate(family)["cases"]["VDL1_BASE"]["components"][channel]
    assert result["d0"] == pytest.approx(3e-6, abs=1e-12)
    assert result["d1"] == pytest.approx(1e-6, abs=1e-12)
    assert result["nominal_finest"] == pytest.approx(4e-6, abs=1e-12)
    assert result["satisfied"]


def test_tolerance_and_contraction_failures_are_retained_without_tuning():
    family = literal_family()
    add_error(family, "VDL1_BASE", "nominal", "vy", 2e-5)
    result = calculate(family)
    assert not result["cases"]["VDL1_BASE"]["components"]["vy"]["satisfied"]
    family = literal_family()
    add_error(family, "VDL1_BASE", "nominal", "vy", 3e-6)
    add_error(family, "VDL1_BASE", "half", "vy", 2e-6)
    c = calculate(family)["cases"]["VDL1_BASE"]["components"]["vy"]
    assert c["nominal_finest"] < 1e-5 and not c["satisfied"]


def test_only_heading_wraps_and_shared_times_use_no_interpolation():
    family = literal_family()
    for row in family["VDL1_BASE"]["nominal"]["states"][1:]:
        row["e_psi"] = pi - 1e-7
    for grid in ("half", "quarter"):
        for row in family["VDL1_BASE"][grid]["states"][1:]:
            row["e_psi"] = -pi + 1e-7
    result = calculate(family)
    assert result["cases"]["VDL1_BASE"]["components"]["e_psi"]["nominal_finest"] == pytest.approx(
        2e-7, abs=1e-12
    )
    family = literal_family()
    family["VDL1_BASE"]["half"]["states"][1]["r"] = 1.0  # Not a shared nominal tick.
    assert calculate(family)["cases"]["VDL1_BASE"]["components"]["r"]["nominal_finest"] == 0
    for channel in ("r", "s_abs"):
        family = literal_family()
        add_error(family, "VDL1_BASE", "nominal", channel, 2 * pi)
        assert not calculate(family)["cases"]["VDL1_BASE"]["components"][channel]["satisfied"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("alpha_f", 0.051),
        ("alpha_r", -0.051),
        ("front_lateral_utilization", 1.01),
        ("rear_lateral_utilization", -0.1),
    ],
)
def test_native_intersample_filters(key, value):
    family = literal_family()
    family["VDL1_BASE"]["half"]["diagnostics"][1][key] = value
    result = calculate(family)
    assert not result["cases"]["VDL1_BASE"]["native_windows"]["half"]["satisfied"]
    assert result["cases"]["VDL1_BASE"]["numerical_satisfied"]
    assert not result["all_criteria_satisfied"]


def test_corridor_coverage_and_insufficient_excitation():
    family = literal_family()
    family["VDL1_BASE"]["quarter"]["states"][1]["boundary_violation"] = True
    assert not calculate(family)["all_criteria_satisfied"]
    family = literal_family()
    family["VDL1_BASE"]["half"]["summary"]["horizon_reached"] = False
    assert not calculate(family)["all_criteria_satisfied"]
    family = literal_family()
    for grid in GRIDS:
        for row in family["VDL1_CR_HIGH"][grid]["states"]:
            row["r"] = 0
    result = calculate(family)
    assert not result["pairs"]["VDL1_CR_HIGH"]["excitation_sufficient"]
    assert result["cases"]["VDL1_CR_HIGH"]["numerical_satisfied"]
    assert result["pairs"]["VDL1_IZ_HIGH"]["satisfied"]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "0.0"])
def test_bad_numeric_fixtures_rejected(bad):
    family = literal_family()
    family["VDL1_BASE"]["nominal"]["states"][1]["vy"] = bad
    with pytest.raises(ValueError):
        calculate(family)


def test_missing_coverage_or_bad_time_is_not_interpolated():
    for bad in ("missing", "time"):
        family = literal_family()
        if bad == "missing":
            family["VDL1_BASE"]["quarter"]["states"].pop()
        else:
            family["VDL1_BASE"]["quarter"]["states"][3]["time"] = 0.123
        with pytest.raises(ValueError):
            calculate(family)


def test_exact_plan_and_execution_ack_gate_without_workers(tmp_path):
    p = plan()
    assert len(SLOTS) == p["execution_count"] == 17
    assert p["plant_intervals"] == 3700 and p["aggregate_simulation_s"] == 8.5
    assert p["execution_authorized_by_plan"] is False
    assert [(r["steps"], r["onset_tick"]) for r in p["slots"][:3]] == [
        (100, 20),
        (200, 40),
        (400, 80),
    ]
    with pytest.raises(ValueError, match="authorization"):
        execute(tmp_path / "forbidden", "0" * 40)
    assert not (tmp_path / "forbidden").exists()


def test_interactive_or_fixture_runs_cannot_be_qualification(lab_runs):
    record = read_record(lab_runs[0])
    with pytest.raises(storage.IntegrityError, match="Test/interactive"):
        require_protocol_run(record, "VDL1_BASE/nominal")
    fake = deepcopy(record)
    fake["request"]["execution_context"] = execution_context(request_for(), qualification=True)
    fake["request"]["test_fixture_only"] = True
    with pytest.raises(storage.IntegrityError):
        require_protocol_run(fake, "VDL1_BASE/nominal")


def test_bound_manifest_and_source_changes_invalidate(lab_runs, tmp_path):
    target = tmp_path / "copied"
    shutil.copytree(lab_runs[0], target)
    reference, record = bind_run(target)
    assert bound_run(reference)["summary"]["horizon_reached"]
    inventory = record["request"]["source_inventory"]
    check_current_source(inventory)
    altered = deepcopy(inventory)
    altered["sha256"]["src/apex/state.py"] = "0" * 64
    with pytest.raises(storage.IntegrityError, match="changed source"):
        check_current_source(altered)
    request = storage.read_json(target / "request.json")
    request["provenance"]["source_sha256"]["src/apex/state.py"] = "0" * 64
    request["source_inventory"]["sha256"]["src/apex/state.py"] = "0" * 64
    storage.write_json(target / "request.json", request)
    reseal_fixture(target)
    with pytest.raises(storage.IntegrityError, match="manifest identity changed"):
        bound_run(reference)


def test_changed_nonplotted_referenced_artifact_invalidates(lab_runs, tmp_path):
    target = tmp_path / "copied"
    shutil.copytree(lab_runs[0], target)
    reference, _ = bind_run(target)
    with (target / "stdout.log").open("a") as stream:
        stream.write("changed without rebinding\n")
    with pytest.raises(storage.IntegrityError):
        bound_run(reference)


def test_fake_calculations_cannot_be_published_as_real_evidence(tmp_path):
    # This is an explicitly invalid test record, never real qualification evidence.
    fixture = calculate(literal_family())
    fixture["test_fixture_only"] = True
    storage.write_json(tmp_path / "qualification.json", fixture)
    storage.write_json(
        tmp_path / "commit.json",
        {"schema": SCHEMA, "qualification_sha256": storage.sha256(tmp_path / "qualification.json")},
    )
    with pytest.raises(storage.IntegrityError, match="Unknown/test-only"):
        read_qualification(tmp_path)
    with pytest.raises(storage.IntegrityError):
        evaluate_references({})


def test_literal_repeat_reference_bytes_and_unique_execution_requirement(lab_runs):
    values = {name: b"literal export\n" for name in PARITY_FILES}
    assert all(exact_export_comparison(values, values).values())
    changed = dict(values)
    changed[PARITY_FILES[1]] = b"different command\n"
    assert not exact_export_comparison(values, changed)[PARITY_FILES[1]]
    with pytest.raises(ValueError):
        exact_export_comparison(values, {})
    reference, _ = bind_run(lab_runs[0])
    with pytest.raises(storage.IntegrityError, match="distinct"):
        evaluate_references({slot: reference for slot in SLOTS})


def test_manifest_epoch_change_during_consumption_is_rejected(lab_runs, tmp_path, monkeypatch):
    from tools.apex_workbench import qualification as q

    target = tmp_path / "moving"
    shutil.copytree(lab_runs[0], target)
    original = q.read_record

    def moving_record(path):
        result = original(path)
        with (target / "stdout.log").open("a") as stream:
            stream.write("new disposable metadata epoch\n")
        reseal_fixture(target)
        return result

    monkeypatch.setattr(q, "read_record", moving_record)
    with pytest.raises(storage.IntegrityError, match="changed while consumed"):
        q.bind_run(target)


def test_qualification_parses_only_verified_bytes(tmp_path, monkeypatch):
    # Invalid test-only record: no real qualification is manufactured.
    storage.write_json(
        tmp_path / "qualification.json", {"schema": "test-fixture-only", "test_fixture_only": True}
    )
    storage.write_json(
        tmp_path / "commit.json",
        {"schema": SCHEMA, "qualification_sha256": storage.sha256(tmp_path / "qualification.json")},
    )

    def forbidden(path):
        raise AssertionError("Do not re-read unverified JSON after checksum validation")

    monkeypatch.setattr(storage, "read_json", forbidden)
    with pytest.raises(storage.IntegrityError, match="Unknown/test-only"):
        read_qualification(tmp_path)


def test_different_recorded_environment_is_not_identical(lab_runs, tmp_path):
    from tools.apex_workbench.qualification import scientific_identity

    target = tmp_path / "different-environment"
    shutil.copytree(lab_runs[0], target)
    env = storage.read_json(target / "numerical_environment.json")
    env["machine"] = "different-recorded-architecture"
    storage.write_json(target / "numerical_environment.json", env)
    reseal_fixture(target)
    assert scientific_identity(read_record(target)) != scientific_identity(read_record(lab_runs[0]))
