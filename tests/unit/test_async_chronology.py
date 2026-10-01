"""Event ordering on the approved NumPy plant with an injected deterministic planner."""

import numpy as np
import pytest

from apex.control.trajectory.packet import TrajectoryPacket
from apex.control.trajectory.tracker import TrackerConfig, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner


class StraightPlanner:
    """Exact straight nominal motion isolates scheduling from optimizer behavior."""

    def prepare(self, plan_id, state, time, estimate, buffer, tracker, startup=False):
        times = time + estimate + np.arange(5) * 0.1
        states = np.zeros((5, 6))
        states[:, 0] = 2
        states[:, 4] = state[4] + 2 * (times - time)
        packet = TrajectoryPacket(
            plan_id,
            time,
            time,
            time + estimate,
            time,
            times,
            states,
            np.zeros((4, 2)),
            state,
            states[0],
            "test_success",
            0.01,
            0.017,
            times[:-1],
            np.tile([1.0, 2.0, 0.1, 0.1], (4, 1)),
        )
        return packet, dict(
            plan_id=plan_id,
            release_time=time,
            estimated_delay=estimate,
            predicted_state=states[0].tolist(),
            success=True,
            status="test_success",
            planner_total_time=0.017,
            planner_cpu_time=0.017,
        )


def run(p, track, **kwargs):
    config = AsyncConfig(duration=0.8, laps=2, latency_mode="injected", **kwargs)
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    tracker = TrajectoryTracker(p, [-0.4, -2], [0.4, 2], TrackerConfig())
    return AsyncRunner(plant, StraightPlanner(), tracker, track, config).run([2.0, 0, 0, 0, 0, 0])


def test_busy_planner_does_not_pause_codriver_or_plant(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0.15)
    assert r["failure"] is None
    assert len(r["misses"]) > 0 and not r["codriver_misses"]
    np.testing.assert_allclose(np.diff([c["time"] for c in r["controls"]]), 0.01, atol=1e-12)
    assert r["states"][-1]["s_abs"] > 1.5
    plans = [p for p in r["plans"] if not p["startup"]]
    assert all(a["completion_time"] <= b["release_time"] + 1e-10 for a, b in zip(plans, plans[1:]))
    for p in plans:
        if p["completed"]:
            assert p["actual_state"][4] == pytest.approx(2 * p["completion_time"], abs=1e-8)


def test_failure_keeps_old_plan_and_recovers(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0.025, failed_plan_ids=(2,))
    assert not r["fallbacks"]
    rejected = next(p for p in r["plans"] if p["plan_id"] == 2)
    assert not rejected["success"]
    assert any(h["accepted"] and h["plan_id"] == 3 for h in r["handoffs"])
    assert all(c["plan_id"] != 2 for c in r["controls"])


def test_exhaustion_fallback_and_no_extrapolation(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0.45)
    assert len(r["fallbacks"]) == 1
    assert r["fallbacks"][0]["time"] == pytest.approx(0.4)
    assert all(c["mode"] == "baseline_fallback" for c in r["controls"] if c["time"] >= 0.4)
    assert r["failure"] is None


def test_isolated_spike_old_plan_continues(dynamic_vehicle, straight_geometry):
    r = run(
        dynamic_vehicle, straight_geometry, injected_delay=0.025, spike_plan_id=3, spike_delay=0.15
    )
    assert not r["fallbacks"] and r["failure"] is None
    active = [c for c in r["controls"] if 0.30 - 1e-9 <= c["time"] < 0.45 - 1e-9]
    assert len(active) >= 14 and len({c["plan_id"] for c in active}) == 1
    assert any(h["accepted"] and h["plan_id"] == 4 for h in r["handoffs"])


def test_codriver_latency_has_own_deadlines(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0.025, codriver_delay=0.025)
    assert len(r["codriver_misses"]) > 0
    assert all(c["application_time"] - c["time"] == pytest.approx(0.025) for c in r["controls"])


def test_disturbance_requests_one_pending_urgent_replan(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0.15, disturbance_time=0.15)
    assert any(t["kind"] == "urgent_replan" and t["busy"] for t in r["triggers"])
    assert any(p.get("urgent") for p in r["plans"])


def test_injected_run_is_physically_deterministic(dynamic_vehicle, straight_geometry):
    a = run(dynamic_vehicle, straight_geometry, injected_delay=0.06)
    b = run(dynamic_vehicle, straight_geometry, injected_delay=0.06)
    assert a["states"] == b["states"]
    assert a["handoffs"] == b["handoffs"]


def test_early_completion_waits_for_intended_handoff(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0)
    first = next(h for h in r["handoffs"] if h["plan_id"] == 1)
    assert first["time"] == pytest.approx(0.117)
    assert all(c["plan_id"] == 0 for c in r["controls"] if c["time"] < 0.117 - 1e-9)


def test_large_handoff_mismatch_is_rejected(dynamic_vehicle, straight_geometry):
    r = run(
        dynamic_vehicle,
        straight_geometry,
        injected_delay=0.025,
        disturbance_time=0.15,
        disturbance_ey=0.25,
    )
    assert any(h["reason"] == "handoff_mismatch" and not h["accepted"] for h in r["handoffs"])


def test_launch_is_gated_and_first_plan_is_active(dynamic_vehicle, straight_geometry):
    r = run(dynamic_vehicle, straight_geometry, injected_delay=0.15)
    first = r["states"][0]
    assert first["time"] == 0 and first["s_abs"] == 0 and first["vx"] == 2
    assert first["plan_id"] == 0
    assert r["plans"][0]["startup"] and r["plans"][0]["completion_time"] == 0


def test_failed_startup_never_releases_vehicle(dynamic_vehicle, straight_geometry):
    class FailedStartup(StraightPlanner):
        def prepare(self, *args, **kwargs):
            return None, {"success": False, "status": "Injected_initial_failure"}

    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    tracker = TrajectoryTracker(dynamic_vehicle, [-0.4, -2], [0.4, 2])
    result = AsyncRunner(plant, FailedStartup(), tracker, straight_geometry).run(
        [2.0, 0, 0, 0, 0, 0]
    )
    assert result["stop_reason"] == "startup_failed"
    assert result["states"] == [] and result["controls"] == []
