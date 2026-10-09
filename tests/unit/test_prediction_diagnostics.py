"""D3 diagnostics: causal shadows, non-invasive capture and aligned physical scoring."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest
from task007d.diagnostics import accuracy, common_coverage, forecasts, residual, score, target_state
from test_committed_prefix_runtime import physical_channels, run_case

from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncRunner
from apex.state import STATE_NAMES


def captured_run(monkeypatch, parameters, track, **kwargs):
    records = []
    init = AsyncRunner.__init__

    def capture(self, *args, **options):
        return init(self, *args, **options, release_observer=records.append)

    with monkeypatch.context() as patch:
        patch.setattr(AsyncRunner, "__init__", capture)
        result, planner, tracker = run_case(parameters, track, **kwargs)
    return records, result, planner, tracker


@pytest.mark.parametrize("enabled", [False, True])
def test_capture_does_not_change_physics_solver_inputs_or_rk4(
    monkeypatch, dynamic_vehicle, straight_geometry, enabled
):
    steps = []
    step = DynamicBicycle.step

    def spy(self, x, u, h):
        steps.append((np.asarray(x).tolist(), np.asarray(u).tolist(), h))
        return step(self, x, u, h)

    monkeypatch.setattr(DynamicBicycle, "step", spy)
    original, original_planner, _ = run_case(dynamic_vehicle, straight_geometry, enabled=enabled)
    original_steps = steps.copy()
    steps.clear()
    records, observed, planner, _ = captured_run(
        monkeypatch, dynamic_vehicle, straight_geometry, enabled=enabled
    )
    assert physical_channels(original, original_planner) == physical_channels(observed, planner)
    assert steps == original_steps  # Every actual input and RK4 interval, not just end state.
    assert len(records) == len(observed["releases"])
    assert all(r.plan_id > 0 for r in records)  # Startup remains gated and uncaptured.


def test_same_release_inputs_and_no_live_mutation(monkeypatch, dynamic_vehicle, straight_geometry):
    records, result, planner, tracker = captured_run(
        monkeypatch, dynamic_vehicle, straight_geometry
    )
    r = records[0]
    before = deepcopy(physical_channels(result, planner))
    previous = tracker.previous.copy()
    packet = planner.calls[1]["active"]
    packet_before = packet.as_dict()
    calls = []
    predict = planner.predictor.predict

    def spy(state, time, duration, buffer, local, **kwargs):
        calls.append(
            (tuple(state), time, duration, buffer.active.as_dict(), local.previous.copy(), kwargs)
        )
        return predict(state, time, duration, buffer, local, **kwargs)

    monkeypatch.setattr(planner.predictor, "predict", spy)
    monkeypatch.setattr(
        planner.controller,
        "compute_control",
        lambda *args, **kwargs: pytest.fail("Shadow must never solve or alter warm starts"),
    )
    outcomes = forecasts(r, planner.predictor)
    assert calls[0][:4] == calls[1][:4]
    np.testing.assert_array_equal(calls[0][4], calls[1][4])
    assert calls[0][5] == {} and calls[1][5] == {"committed_prefix": r.prefix}
    assert outcomes["A"]["state"] == result["plans"][1]["predicted_state"]
    assert outcomes["A"]["state"] != outcomes["B"]["state"]
    assert forecasts(r, planner.predictor) == outcomes
    assert before == physical_channels(result, planner)
    np.testing.assert_array_equal(tracker.previous, previous)
    assert packet.as_dict() == packet_before
    assert not np.shares_memory(r.packet.states, packet.states)
    with pytest.raises(FrozenInstanceError):
        r.estimated_delay = 100
    with pytest.raises(ValueError):
        r.packet.states[0, 0] = 10
    planner.calls[1]["state"][:] = 99
    tracker.previous[:] = 99
    assert forecasts(r, planner.predictor) == outcomes


def test_future_readiness_and_truth_are_scoring_only(
    monkeypatch, dynamic_vehicle, straight_geometry
):
    a, ar, ap, _ = captured_run(monkeypatch, dynamic_vehicle, straight_geometry, delay=0.025)
    b, br, bp, _ = captured_run(monkeypatch, dynamic_vehicle, straight_geometry, delay=0.15)
    assert a[0].state == b[0].state and a[0].prefix == b[0].prefix
    assert a[0].estimated_delay == b[0].estimated_delay
    assert forecasts(a[0], ap.predictor) == forecasts(b[0], bp.predictor)
    br["states"][-1]["vx"] = 999  # No physical history is an input to the forecast API.
    assert forecasts(a[0], ap.predictor) == forecasts(b[0], bp.predictor)
    assert ar["plans"][1]["completion_time"] != br["plans"][1]["completion_time"]


@pytest.mark.parametrize("pending", [False, True])
def test_pending_and_no_pending(monkeypatch, dynamic_vehicle, straight_geometry, pending):
    releases, _, planner, _ = captured_run(monkeypatch, dynamic_vehicle, straight_geometry)
    r = releases[0]
    if not pending:
        r = replace(
            r, prefix=replace(r.prefix, pending_control=None, pending_application_time=None)
        )
    values = forecasts(r, planner.predictor)
    assert all(v["failure"] is None for v in values.values())
    assert forecasts(r, planner.predictor) == values


@pytest.mark.parametrize("missing", [True, False])
def test_unavailable_or_exhausted_forecast_has_no_residual(
    monkeypatch, dynamic_vehicle, straight_geometry, missing
):
    releases, result, planner, _ = captured_run(monkeypatch, dynamic_vehicle, straight_geometry)
    r = replace(releases[0], packet=None) if missing else replace(releases[0], estimated_delay=2)
    values = forecasts(r, planner.predictor)
    assert all(v["state"] is None and v["failure"] for v in values.values())
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    row = score(r, values, result, plant)
    assert row["errors"] == {"A": None, "B": None}
    report = accuracy([row])
    assert report["comparable"] == 0 and report["excluded"] == 1
    assert report["forecast_failures"] == {"A": 1, "B": 1}


def test_heading_residual_wrap():
    x, y = np.zeros(6), np.zeros(6)
    x[3], y[3] = -np.pi + 0.01, np.pi - 0.01
    assert residual(x, y)[3] == pytest.approx(0.02, abs=1e-15)
    x[4] = 40
    assert residual(x, y)[4] == 40  # Never wrap absolute progress.


def row(time, state, u=(0, 0)):
    return dict(time=time, **dict(zip(STATE_NAMES, state)), delta=u[0], a_cmd=u[1])


def test_reconstruction_real_plant_held_physics_and_event(
    monkeypatch, dynamic_vehicle, straight_geometry
):
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    x = np.asarray([2.0, 0, 0, 0, 1, 0])
    u = [0, 1]
    end = plant.step(x, u, 0.005)
    states = [row(0, x, u), row(0.005, end, [0, -1])]
    actual = target_state(states, 0.002, plant)
    assert actual["kind"] == "reconstructed_rk4"
    np.testing.assert_allclose(actual["state"], [2.002, 0, 0, 0, 1.004002, 0], atol=1e-12, rtol=0)
    np.testing.assert_allclose(actual["interval_closure_error"], 0, atol=1e-12, rtol=0)
    # Exact samples perform no reconstruction, including a changed endpoint command.
    monkeypatch.setattr(plant, "step", lambda *args: pytest.fail("Exact event must not integrate"))
    assert target_state(states, 0.005, plant)["state"] == end.tolist()
    assert target_state(states, 0.0051, plant)["kind"] == "missing_coverage"
    assert target_state([], 0.001, plant)["state"] is None


def test_reconstruction_rejects_unrecorded_jump(dynamic_vehicle, straight_geometry):
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    states = [row(0, [2, 0, 0, 0, 1, 0]), row(0.005, [2, 0, 0, 0, 1.01, 0.2])]
    assert target_state(states, 0.002, plant)["kind"] == "reconstruction_discontinuity"


def test_readiness_is_not_accepted_handoff(monkeypatch, dynamic_vehicle, straight_geometry):
    releases, result, planner, _ = captured_run(
        monkeypatch, dynamic_vehicle, straight_geometry, delay=0
    )
    r = releases[0]
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    alternatives = forecasts(r, planner.predictor)
    scored = score(r, alternatives, result, plant)
    assert scored["readiness_minus_target"] == pytest.approx(-0.017, abs=1e-12)
    assert scored["accepted_handoff_minus_target"] == pytest.approx(0, abs=1e-12)
    result["handoffs"] = []
    assert score(r, alternatives, result, plant)["accepted_handoff_minus_target"] is None
    result["plans"][1]["completed"] = False
    assert score(r, alternatives, result, plant)["readiness_minus_target"] is None


def test_censored_targets_and_unequal_coverage(monkeypatch, dynamic_vehicle, straight_geometry):
    releases, result, planner, _ = captured_run(
        monkeypatch, dynamic_vehicle, straight_geometry, duration=0.21
    )
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    scores = [score(r, forecasts(r, planner.predictor), result, plant) for r in releases]
    report = accuracy(scores)
    assert report["comparable"] == 1 and report["missing_targets"] == 1
    assert report["excluded"] == 1
    assert report["per_state"]["A"]["vx"]["p95_abs"] is None
    shorter = dict(result, states=result["states"][:-4])
    coverage = common_coverage(result, shorter)
    assert coverage["unequal"] is True and coverage["end"] == shorter["states"][-1]["time"]
    assert common_coverage(result, dict(states=[]))["end"] is None


def test_chronology_and_stop_gate_detect_failures(monkeypatch, dynamic_vehicle, straight_geometry):
    from task007d.metrics import chronology, physical_metrics, stop_reasons

    _, result, _, _ = captured_run(monkeypatch, dynamic_vehicle, straight_geometry)
    metrics = physical_metrics(result, straight_geometry)
    assert chronology(result) == [] and stop_reasons(result, metrics, []) == []
    result["controls"][0]["plan_id"] = 999
    assert chronology(result)[0]["kind"] == "controls_authority"
    assert "chronology_or_authority_violation" in stop_reasons(result, metrics, chronology(result))
    metrics["plans_slack_above_1e6"] = 1
    metrics["physical_boundary_crossings"] = 1
    metrics["solver_failures"] = 1
    reasons = stop_reasons(result, metrics, [])
    assert set(reasons) == {
        "predicted_slack_above_1e-6_m",
        "physical_boundary_crossing",
        "solver_or_preparation_failure",
    }


def test_comparison_limits_coverage_and_pairs_launch_times(
    monkeypatch, dynamic_vehicle, straight_geometry
):
    from task007d.metrics import compare

    _, result, _, _ = captured_run(monkeypatch, dynamic_vehicle, straight_geometry)
    short = deepcopy(result)
    short["states"] = short["states"][:-3]
    short["plans"] = short["plans"][1:]  # Different launch indices cannot establish pairing.
    short["plans"][0]["predicted_state"][0] += 0.001
    comparison = compare(result, short, straight_geometry)
    assert comparison["coverage"]["unequal"] is True
    assert comparison["planner_launches_and_estimates_identical"] is False
    assert comparison["first_forecast_divergence"]["release_time"] == 0.1
    assert comparison["metrics"]["A"]["observed_end"] == comparison["metrics"]["B"]["observed_end"]
    assert comparison["first_divergence"] is None
