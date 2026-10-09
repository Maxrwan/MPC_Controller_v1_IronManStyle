"""D4 delay interface and analysis; retain original D3 mathematical scoring."""

from copy import deepcopy

import pytest
from run_task007d_pilot import parse_args
from task007d.diagnostics import accuracy
from task007d.sensitivity import REGIMES, pending_category, release_table, stratify
from test_prediction_diagnostics import captured_run

BASE_ARGS = ["--architecture", "A", "--gamma", "2", "--output", "results/task007d/d4/test"]


def test_d3_delay_defaults_preserved():
    args = parse_args(BASE_ARGS)
    assert (args.planner_delay, args.codriver_delay, args.duration) == (0.035, 0.015, 2.0)


@pytest.mark.parametrize(
    "option,value",
    [
        ("--planner-delay", "-.001"),
        ("--codriver-delay", "nan"),
        ("--planner-delay", "inf"),
        ("--codriver-delay", "-1"),
    ],
)
def test_invalid_delay_rejected(option, value):
    with pytest.raises(SystemExit):
        parse_args([*BASE_ARGS, option, value])


@pytest.mark.parametrize("regime", list(REGIMES))
def test_explicit_delays_retain_release_phase_semantics(
    monkeypatch, dynamic_vehicle, straight_geometry, regime
):
    planner_delay, driver_delay = REGIMES[regime]
    args = parse_args(
        [*BASE_ARGS, "--planner-delay", str(planner_delay), "--codriver-delay", str(driver_delay)]
    )
    records, result, _, _ = captured_run(
        monkeypatch,
        dynamic_vehicle,
        straight_geometry,
        delay=args.planner_delay,
        driver_delay=args.codriver_delay,
        duration=0.19,
    )
    prefix = records[0].prefix
    event = result["plans"][1]
    row = dict(
        release_time=prefix.release_time,
        pending=prefix.pending_control is not None,
        pending_application_time=prefix.pending_application_time,
    )
    assert pending_category(row) == ("due_now" if driver_delay == 0 else "future")
    assert event["physical_delay"] == planner_delay
    assert event["completion_time"] == pytest.approx(0.1 + planner_delay, rel=0, abs=1e-10)
    assert records[0].estimated_delay == 0.017
    assert event["predicted_completion_time"] == pytest.approx(0.117, rel=0, abs=1e-10)
    assert all(c["physical_latency"] == driver_delay for c in result["controls"])
    assert bool(result["codriver_misses"]) == (driver_delay > 0.01)


@pytest.mark.parametrize(
    "pending,due,category", [(False, None, "none"), (True, 0.1, "due_now"), (True, 0.105, "future")]
)
def test_pending_categories(pending, due, category):
    assert (
        pending_category(dict(pending=pending, pending_application_time=due, release_time=0.1))
        == category
    )


def test_inconsistent_pending_metadata_fails():
    with pytest.raises(ValueError):
        pending_category(dict(pending=False, pending_application_time=0.1, release_time=0.1))
    with pytest.raises(ValueError):
        pending_category(dict(pending=True, pending_application_time=0.09, release_time=0.1))


def scored(time, a, b):
    return dict(
        plan_id=int(round(time * 10)),
        release_time=time,
        pending=True,
        pending_application_time=time,
        errors={"A": [a] * 6, "B": [b] * 6},
        forecasts={"A": {"failure": None}, "B": {"failure": None}},
        truth={"state": [0.0] * 6},
    )


def test_first_release_is_separate_and_counts_are_per_state():
    rows = [scored(0.1, 10.0, 1.0), scored(0.2, 1.0, 2.0), scored(0.3, 1.0, 1.0)]
    before = deepcopy(rows)
    summary = stratify(rows)
    assert rows == before
    assert summary["all"]["per_state"] == accuracy(rows)["per_state"]
    assert summary["first"]["comparable"] == 1
    assert summary["subsequent"]["comparable"] == 2
    assert summary["all"]["individual_absolute_error_counts"]["vx"] == dict(
        better=1, worse=1, tie=1
    )
    assert summary["first"]["rms_change_b_minus_a"]["vx"] == -9
    assert summary["subsequent"]["rms_change_b_minus_a"]["vx"] > 0
    assert summary["all"]["per_state"]["A"]["vx"]["p95_abs"] is None


def test_exclusions_are_not_wins_or_fictitious_zero_errors():
    r = scored(0.1, 1.0, 0.5)
    r["errors"]["B"] = None
    r["forecasts"]["B"]["failure"] = "expired"
    summary = stratify([r])["all"]
    assert summary["excluded"] == 1 and summary["comparable"] == 0
    assert summary["forecast_failures"]["B"] == 1
    assert summary["individual_absolute_error_counts"]["vx"] == dict(better=0, worse=0, tie=0)
    assert summary["per_state"]["B"] == {}


def test_timing_table_separates_readiness_and_handoff():
    r = scored(0.1, 1.0, 0.5)
    r.update(
        target_time=0.117,
        scheduled_readiness_minus_target=-0.017,
        readiness_minus_target=-0.017,
        accepted_handoff_minus_target=0,
        handoffs=[dict(time=0.117, accepted=True)],
        truth=dict(kind="recorded_event"),
    )
    raw = dict(plans=[dict(plan_id=1, estimated_delay=0.017, completion_time=0.1, completed=True)])
    row = release_table([r], raw, "D4-R1", "A")[0]
    assert row["imposed_readiness_time"] == 0.1
    assert row["target_time"] == row["accepted_handoff_time"] == 0.117
    assert row["pending_category"] == "due_now" and row["phase"] == "first"


def test_exploratory_transient_dominance_is_not_confused_with_persistent_improvement():
    from task007d.sensitivity import transient_audit

    rows = [scored(0.1, 10.0, 1.0), scored(0.2, 20.0, 1.0), scored(0.3, 1.0, 2.0)]
    audit = transient_audit(rows)["vx"]
    assert audit["first_A_squared_error_share_percent"] == pytest.approx(10000 / 501)
    assert audit["second_A_squared_error_share_percent"] == pytest.approx(40000 / 501)
    assert audit["after_second_rms_reduction_percent"] == -100
    assert audit["after_second_count"] == 1
    assert audit["maximum_B_absolute_error_increase"]["plan_id"] == 3
    assert transient_audit([])["vx"]["after_second_A_rms"] is None
