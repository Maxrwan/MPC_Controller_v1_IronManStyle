"""Short deterministic N8 fixtures for the opt-in runtime prediction path; no racing laps."""

import hashlib
import json

import numpy as np
import pytest
from test_async_chronology import StraightPlanner

from apex.control.mpc.controller import make_mpc
from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.prediction import ActuationPredictor
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner


def _time(value):
    """Use the scheduler event tolerance, with no relative tolerance."""
    return pytest.approx(value, rel=0, abs=1e-10)


class RecordingPlanner(TrajectoryPlanner):
    def __init__(self, *args):
        super().__init__(*args)
        self.calls = []
        self.requests = []
        solve = self.controller.solver.solve

        def record(request):
            self.requests.append((request.initial.copy(), request.parameters.copy()))
            return solve(request)

        self.controller.solver.solve = record

    def prepare(self, plan_id, state, time, estimate, buffer, tracker, **kwargs):
        self.calls.append(
            dict(
                time=time,
                state=state.copy(),
                estimate=estimate,
                kwargs=kwargs.copy(),
                applied=tracker.previous.copy(),
                active=buffer.active,
            )
        )
        return super().prepare(plan_id, state, time, estimate, buffer, tracker, **kwargs)


class RecordingTracker(TrajectoryTracker):
    def __init__(self, *args):
        super().__init__(*args)
        self.calls = []

    def update(self, state, buffer, time):
        applied = self.previous.copy()
        requested, info = super().update(state, buffer, time)
        self.calls.append(dict(time=time, applied=applied, requested=requested))
        return requested, info


def run_case(
    parameters, track, *, enabled=None, driver_delay=0.025, delay=0.06, duration=0.24, **config
):
    # Frozen review weights, N8/dt0.1; the straight 2 m/s fixture is not a gamma racing case.
    controller = make_mpc(
        parameters,
        track,
        config=MPCConfig(
            horizon=8,
            dt=0.1,
            substeps=4,
            costs=CostScales(lateral=2),
            tire_physics=RACING_TIRE_PHYSICS,
            tracker_margin=0.08,
        ),
    )
    planner = RecordingPlanner(controller, track)
    problem = controller.problem
    tracker = RecordingTracker(
        parameters,
        problem.lbx[problem.nx : problem.nx + 2],
        problem.ubx[problem.nx : problem.nx + 2],
    )
    if enabled is not None:
        config["committed_prefix_prediction"] = enabled
    config.setdefault("urgent", False)
    runner = AsyncRunner(
        DynamicBicycle(parameters, track, tire_physics=RACING_TIRE_PHYSICS),
        planner,
        tracker,
        track,
        AsyncConfig(
            duration=duration,
            latency_mode="injected",
            injected_delay=delay,
            codriver_delay=driver_delay,
            **config,
        ),
    )
    result = runner.run([2, 0, 0, 0, 1, 0.015])
    assert result["failure"] is None
    return result, planner, tracker


def physical_channels(result, planner):
    """Exclude wall/CPU durations and additive telemetry, never physical chronology."""
    channels = {
        k: result[k]
        for k in (
            "states",
            "handoffs",
            "releases",
            "misses",
            "codriver_misses",
            "reserves",
            "triggers",
            "fallbacks",
            "stop_reason",
            "end_time",
            "pending_at_end",
            "lap_times",
        )
    }
    timing_fields = {
        "interpolation_time",
        "feedback_time",
        "command_validation_time",
        "kernel_time",
        "cpu_time",
        "total_time",
        "computational_deadline_exceeded",
    }
    channels["controls"] = [
        {k: v for k, v in row.items() if k not in timing_fields} for row in result["controls"]
    ]
    channels["predictions"] = [
        {
            k: row.get(k)
            for k in (
                "release_time",
                "estimated_delay",
                "predicted_completion_time",
                "source_state",
                "predicted_state",
                "completion_time",
                "completed",
            )
        }
        for row in result["plans"]
    ]
    channels["solver_inputs"] = [
        [guess.tolist(), params.tolist()] for guess, params in planner.requests
    ]
    return channels


def fingerprints(channels):
    return {
        key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
        for key, value in channels.items()
    }


# Captured before D2 source edits at 4a7026e on this backend. Exact numeric/chronology
# channels include requested/applied commands and full solver guesses/parameters.
BASELINE = {
    "states": "bce893cc18c47866be28713441536dce28f3b58d84ac848cd2441726036daa45",
    "handoffs": "c7b69ee308f99bfe3a65196da6e599f8adc8ac4f599ac1da1ed2e01ddd8780ab",
    "releases": "71557e74794f6c9eae0d591d6c33cab8b26dd65cdd043c3ab219f8f177a60071",
    "misses": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "codriver_misses": "e9f758970c299062c21233407bbb12197094526c2aa28577d42506e5bca1b693",
    "reserves": "200d9153883fd01b0579cec75081095651ca1e4bc7d7ad133828ac23136265d0",
    "triggers": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "fallbacks": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "stop_reason": "ae7dede1aff756bbfebd1da3d146eb98374042dbbb62d92f80fbb7518062278e",
    "end_time": "6382e07f9de0c85293aee2a45b88c61c28589419682ecc2f8c097f750e861a24",
    "pending_at_end": "b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b",
    "lap_times": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "controls": "ca8751b4e15636c2ef0255c949ed5208d688ee6085d66f123b2c3a995b65b8ae",
    "predictions": "972aa0d02f0577f0b739ef09cd1602f67c3fc5b2deb7df8c0b2825eb5dae1492",
    "solver_inputs": "2c38c130e31ff55cc03860d45edbf40904ba792e122293cbbca7c1c31cf30619",
}


@pytest.mark.parametrize("enabled", [None, False])
def test_architecture_a_matches_pre_d2(dynamic_vehicle, straight_geometry, enabled):
    assert AsyncConfig().committed_prefix_prediction is False
    result, planner, _ = run_case(dynamic_vehicle, straight_geometry, enabled=enabled)
    actual = fingerprints(physical_channels(result, planner))
    for key, expected in BASELINE.items():
        assert actual[key] == expected, key
    assert all("committed_prefix" not in c["kwargs"] for c in planner.calls)
    assert all(p["prediction_architecture"] == "A" for p in result["plans"])


@pytest.mark.parametrize("bad", [0, 1, None, "False", np.bool_(True)])
def test_setting_requires_actual_bool(bad):
    with pytest.raises(ValueError, match="must be a boolean"):
        AsyncConfig(committed_prefix_prediction=bad)


def test_legacy_planner_works_only_when_disabled(dynamic_vehicle, straight_geometry):
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    tracker = TrajectoryTracker(dynamic_vehicle, [-0.4, -2], [0.4, 2])
    for enabled in (False, True):
        config = AsyncConfig(
            duration=0.12, latency_mode="zero", committed_prefix_prediction=enabled
        )
        if enabled:
            with pytest.raises(TypeError, match="Architecture B requires planner.prepare"):
                AsyncRunner(plant, StraightPlanner(), tracker, straight_geometry, config)
        else:
            result = AsyncRunner(plant, StraightPlanner(), tracker, straight_geometry, config).run(
                [2, 0, 0, 0, 0, 0]
            )
            assert result["failure"] is None and len(result["plans"]) == 2


def test_capture_forwarding_and_telemetry(dynamic_vehicle, straight_geometry, monkeypatch):
    invocations = []
    predict = ActuationPredictor.predict

    def observe(self, state, time, duration, buffer, tracker, **kwargs):
        invocations.append((state.copy(), time, duration, kwargs.copy()))
        return predict(self, state, time, duration, buffer, tracker, **kwargs)

    monkeypatch.setattr(ActuationPredictor, "predict", observe)
    result, planner, tracker = run_case(dynamic_vehicle, straight_geometry, enabled=True)
    call, event = planner.calls[1], result["plans"][1]
    snapshot = call["kwargs"]["committed_prefix"]
    assert invocations[0][3]["committed_prefix"] is snapshot
    assert snapshot.release_time == call["time"] == event["release_time"] == 0.1
    assert invocations[0][2] == call["estimate"] == 0.017
    np.testing.assert_array_equal(invocations[0][0], call["state"])
    np.testing.assert_array_equal(snapshot.applied_control, call["applied"])
    launched = next(c for c in tracker.calls if c["time"] == _time(0.09))
    applied = [c for c in result["controls"] if c["application_time"] <= 0.1][-1]
    np.testing.assert_array_equal(snapshot.pending_control, launched["requested"])
    np.testing.assert_array_equal(snapshot.applied_control, [applied["delta"], applied["a_cmd"]])
    assert snapshot.last_application_time == applied["application_time"]
    assert not np.array_equal(snapshot.applied_control, snapshot.pending_control)
    assert snapshot.pending_application_time == _time(0.115)
    assert event["release_command_pending"] is True
    assert event["pending_application_time"] == snapshot.pending_application_time
    assert (
        event["prediction_architecture"] == "B" and event["prediction_mode"] == "committed_prefix"
    )
    assert event["predicted_completion_time"] == 0.1 + 0.017
    assert event["completion_time"] == 0.1 + 0.06
    np.testing.assert_array_equal(event["predicted_state"], planner.requests[1][1][:6])
    np.testing.assert_array_equal(event["predicted_previous_control"], planner.requests[1][1][6:8])
    # Requested arrays retained by the test tracker are the runtime arrays, not copies.
    committed = snapshot.pending_control
    launched["requested"][:] = 99
    call["applied"][:] = -99
    assert snapshot.pending_control == committed
    np.testing.assert_array_equal(snapshot.applied_control, [applied["delta"], applied["a_cmd"]])


def test_completed_application_precedes_new_request_and_release(dynamic_vehicle, straight_geometry):
    result, planner, tracker = run_case(
        dynamic_vehicle, straight_geometry, enabled=True, driver_delay=0.02, duration=0.13
    )
    snapshot = planner.calls[1]["kwargs"]["committed_prefix"]
    applied = next(c for c in result["controls"] if c["application_time"] == _time(0.1))
    new = next(c for c in tracker.calls if c["time"] == _time(0.1))
    assert applied["time"] == _time(0.08)
    assert snapshot.last_application_time == _time(0.1)
    np.testing.assert_array_equal(snapshot.applied_control, [applied["delta"], applied["a_cmd"]])
    np.testing.assert_array_equal(new["applied"], snapshot.applied_control)
    np.testing.assert_array_equal(snapshot.pending_control, new["requested"])
    assert snapshot.pending_application_time == _time(0.12)  # Not the completed 0.1 job.


def test_same_tick_zero_latency_stays_pending_at_release(dynamic_vehicle, straight_geometry):
    result, planner, tracker = run_case(
        dynamic_vehicle, straight_geometry, enabled=True, driver_delay=0, duration=0.12
    )
    snapshot = planner.calls[1]["kwargs"]["committed_prefix"]
    assert snapshot.last_application_time == _time(0.09)
    assert snapshot.pending_application_time == snapshot.release_time == 0.1
    new = next(c for c in tracker.calls if c["time"] == 0.1)
    np.testing.assert_array_equal(snapshot.applied_control, new["applied"])
    np.testing.assert_array_equal(snapshot.pending_control, new["requested"])
    actual = [c for c in result["controls"] if c["time"] == 0.1]
    assert len(actual) == 1 and actual[0]["application_time"] == 0.1
    assert all(c["application_time"] >= c["time"] for c in result["controls"])


def test_urgent_release_captures_same_contract(dynamic_vehicle, straight_geometry):
    result, planner, tracker = run_case(
        dynamic_vehicle,
        straight_geometry,
        enabled=True,
        urgent=True,
        driver_delay=0.015,
        duration=0.14,
        disturbance_time=0.035,
        disturbance_ey=0.06,
        disturbance_heading=0,
    )
    event = next(p for p in result["plans"] if p.get("urgent"))
    call = next(c for c in planner.calls if c["time"] == event["release_time"])
    snapshot = call["kwargs"]["committed_prefix"]
    assert snapshot.release_time == event["release_time"] == _time(0.06)
    update = next(c for c in tracker.calls if c["time"] == snapshot.release_time)
    np.testing.assert_array_equal(snapshot.pending_control, update["requested"])
    np.testing.assert_array_equal(snapshot.applied_control, update["applied"])
    assert snapshot.pending_application_time == _time(snapshot.release_time + 0.015)


def test_future_readiness_does_not_change_release_inputs(dynamic_vehicle, straight_geometry):
    early = run_case(dynamic_vehicle, straight_geometry, enabled=True, delay=0.025)
    late = run_case(dynamic_vehicle, straight_geometry, enabled=True, delay=0.15)
    er, ep, _ = early
    lr, lp, _ = late
    assert ep.calls[1]["kwargs"] == lp.calls[1]["kwargs"]
    for a, b in zip(ep.requests[1], lp.requests[1]):
        np.testing.assert_array_equal(a, b)
    assert er["plans"][1]["predicted_state"] == lr["plans"][1]["predicted_state"]
    assert er["plans"][1]["completion_time"] != lr["plans"][1]["completion_time"]


def test_pending_command_changes_only_opt_in_forecast_and_b_repeats(
    dynamic_vehicle, straight_geometry
):
    a, ap, _ = run_case(dynamic_vehicle, straight_geometry, enabled=False)
    b, bp, _ = run_case(dynamic_vehicle, straight_geometry, enabled=True)
    again, againp, _ = run_case(dynamic_vehicle, straight_geometry, enabled=True)
    assert physical_channels(b, bp) == physical_channels(again, againp)
    assert (
        b["plans"][1]["predicted_previous_control"]
        == again["plans"][1]["predicted_previous_control"]
    )
    np.testing.assert_array_equal(ap.calls[1]["state"], bp.calls[1]["state"])
    assert not np.array_equal(ap.requests[1][1][:8], bp.requests[1][1][:8])
    call = bp.calls[1]
    expected = bp.predictor.predict(
        call["state"],
        call["time"],
        call["estimate"],
        _buffer(call["active"]),
        _tracker(ap.controller.parameters),
        committed_prefix=call["kwargs"]["committed_prefix"],
    )
    np.testing.assert_array_equal(b["plans"][1]["predicted_state"], expected[0])
    np.testing.assert_array_equal(b["plans"][1]["predicted_previous_control"], expected[1])
    # Nothing new is authoritative during preparation, even though forecast inputs differ.
    assert [r for r in a["states"] if r["time"] < 0.16] == [
        r for r in b["states"] if r["time"] < 0.16
    ]


def _buffer(packet):
    from apex.control.trajectory.packet import TrajectoryBuffer

    buffer = TrajectoryBuffer()
    buffer.active = packet
    return buffer


def _tracker(parameters):
    # Same actuator box as the composed controller; predictor uses only the snapshot input.
    return TrajectoryTracker(parameters, [-0.4, -2], [0.4, 2])


@pytest.mark.parametrize("delay,first_accept", [(0, 0.117), (0.06, 0.16)])
def test_startup_and_authority_policy_unchanged(
    dynamic_vehicle, straight_geometry, delay, first_accept
):
    a, ap, _ = run_case(dynamic_vehicle, straight_geometry, enabled=False, delay=delay)
    b, bp, _ = run_case(dynamic_vehicle, straight_geometry, enabled=True, delay=delay)
    assert ap.calls[0]["kwargs"] == bp.calls[0]["kwargs"] == {"startup": True}
    assert a["plans"][0]["prediction_mode"] == b["plans"][0]["prediction_mode"] == "startup"
    for aa, bb in zip(ap.requests[0], bp.requests[0]):
        np.testing.assert_array_equal(aa, bb)
    for result in (a, b):
        accepted = [h for h in result["handoffs"] if h["accepted"]]
        assert accepted[0]["plan_id"] == 1 and accepted[0]["time"] == _time(first_accept)
        assert all(s["plan_id"] == 0 for s in result["states"] if s["time"] < first_accept - 1e-10)
        assert result["plans"][0]["completion_time"] == 0
