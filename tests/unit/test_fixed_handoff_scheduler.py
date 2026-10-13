"""Approved C0 amendment: deterministic fixed commitments on the existing plant."""

from dataclasses import replace

import numpy as np
import pytest
from test_async_chronology import StraightPlanner

from apex.control.trajectory.packet import TrajectoryBuffer
from apex.control.trajectory.tracker import TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.asynchronous import AsyncConfig, AsyncRunner
from apex.simulation.diagnostic_timing import DiagnosticTiming
from apex.simulation.fixed_handoff import on_grid


def simulate(p, track, *, delay=0.035, offset=0.07, timing=None, planner=None, **kwargs):
    kwargs.setdefault("duration", 0.6)
    config = AsyncConfig(
        latency_mode="injected", injected_delay=delay, fixed_handoff_offset=offset, **kwargs
    )
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    tracker = TrajectoryTracker(p, [-0.4, -2], [0.4, 2])
    return AsyncRunner(
        plant, planner or StraightPlanner(), tracker, track, config, timing=timing
    ).run([2, 0, 0, 0, 0, 0])


def cycle(result, plan_id):
    return next(r for r in result["fixed_handoffs"] if r["plan_id"] == plan_id)


def check_grid_and_no_overlap(result):
    assert all(on_grid(r["time"]) for r in result["releases"])
    assert all(on_grid(h["time"]) for h in result["handoffs"] if h["accepted"])
    plans = result["plans"][1:]
    assert all(a["completion_time"] <= b["release_time"] + 1e-10 for a, b in zip(plans, plans[1:]))
    assert all(r["valid_from"] == r["t_release"] + 0.07 for r in result["fixed_handoffs"])


@pytest.mark.parametrize(
    "bad", [True, False, "0.07", 0, 1e-11, -0.01, 0.055, 0.101, np.nan, np.inf]
)
def test_offset_requires_finite_positive_global_grid_value(bad):
    with pytest.raises(ValueError):
        AsyncConfig(fixed_handoff_offset=bad)


def test_fixed_configuration_requires_legacy_a_and_grid():
    assert AsyncConfig().fixed_handoff_offset is None
    with pytest.raises(ValueError):
        AsyncConfig(fixed_handoff_offset=0.07, committed_prefix_prediction=True)
    with pytest.raises(ValueError):
        AsyncConfig(fixed_handoff_offset=0.07, tracker_dt=0.02)
    with pytest.raises(ValueError):
        AsyncConfig(fixed_handoff_offset=0.07, planner_dt=0.105)


def test_original_155ms_case_defers_and_misses_without_cancellation(
    dynamic_vehicle, straight_geometry
):
    r = simulate(dynamic_vehicle, straight_geometry, delay=0.155, disturbance_time=0.15)
    assert r["failure"] is None
    demand = r["urgent_demands"][0]
    assert demand["trigger_time"] == pytest.approx(0.16, abs=1e-12, rel=0)
    assert demand["eligible_time"] == pytest.approx(0.255, abs=1e-12, rel=0)
    assert demand["release_time"] == pytest.approx(0.260, abs=1e-12, rel=0)
    assert demand["planner_busy_wait"] == pytest.approx(0.095, abs=1e-12, rel=0)
    assert demand["grid_alignment_wait"] == pytest.approx(0.005, abs=1e-12, rel=0)
    assert not any(abs(e["time"] - 0.255) < 1e-10 for e in r["releases"])
    second = cycle(r, 2)
    assert second["valid_from"] == pytest.approx(0.330, abs=1e-12, rel=0)
    assert second["miss_time"] == pytest.approx(0.330, abs=1e-12, rel=0)
    assert second["t_ready"] == pytest.approx(0.415, abs=1e-12, rel=0)
    assert second["late_discard_time"] == second["t_ready"]
    assert second["status"] == "missed" and second["t_accept"] is None
    assert cycle(r, 1)["consecutive_misses"] == 1
    assert second["consecutive_misses"] == 2
    assert all(s["plan_id"] == 0 for s in r["states"])
    assert r["fallbacks"][0]["time"] == pytest.approx(0.4, abs=1e-12, rel=0)
    assert demand["trigger_to_authority"] is None and demand["status"] == "fallback"
    assert any(abs(m["time"] - 0.4) < 1e-10 for m in r["misses"])
    assert r["states"][-1]["s_abs"] > 1
    check_grid_and_no_overlap(r)


def test_deferred_urgent_ready_in_time_accepts_at_330ms(dynamic_vehicle, straight_geometry):
    timing = DiagnosticTiming("replay", (0.155, *([0.035] * 10)), tuple([0.0] * 100))
    r = simulate(dynamic_vehicle, straight_geometry, timing=timing, disturbance_time=0.15)
    assert r["failure"] is None and not r["fallbacks"]
    c = cycle(r, 2)
    assert c["t_release"] == pytest.approx(0.26, abs=1e-12, rel=0)
    assert c["t_ready"] == pytest.approx(0.295, abs=1e-12, rel=0)
    assert c["t_accept"] == pytest.approx(0.33, abs=1e-12, rel=0)
    assert c["wait_duration"] == pytest.approx(0.035, abs=1e-12, rel=0)
    assert c["first_TVLQR_use"] == pytest.approx(0.33, abs=1e-12, rel=0)
    assert c["packet_age"] == pytest.approx(0.07, abs=1e-12, rel=0)
    assert c["reserve_at_acceptance"] == pytest.approx(0.4, abs=1e-12, rel=0)
    demand = r["urgent_demands"][0]
    assert demand["trigger_to_authority"] == pytest.approx(0.17, abs=1e-12, rel=0)
    assert all(c["plan_id"] == 0 for c in r["controls"] if c["time"] < 0.33 - 1e-10)
    check_grid_and_no_overlap(r)


@pytest.mark.parametrize("delay", [0.0, 0.035, 0.07, 0.075])
def test_early_exact_late_and_startup(dynamic_vehicle, straight_geometry, delay):
    r = simulate(dynamic_vehicle, straight_geometry, delay=delay, duration=0.29, urgent=False)
    assert r["failure"] is None
    c = cycle(r, 1)
    assert c["valid_from"] == 0.1 + 0.07
    assert r["plans"][0]["completion_time"] == 0
    assert "valid_from" not in r["packets"][0]
    assert r["packets"][1]["timestamps"][0] == r["packets"][1]["valid_from"]
    if delay <= 0.07:
        assert c["status"] == "accepted" and c["t_accept"] == pytest.approx(0.17, abs=1e-12, rel=0)
        assert c["wait_duration"] == pytest.approx(0.07 - delay, abs=1e-12, rel=0)
        assert next(c for c in r["controls"] if abs(c["time"] - 0.17) < 1e-10)["plan_id"] == 1
    else:
        assert c["status"] == "missed" and c["t_accept"] is None
        assert c["miss_time"] == pytest.approx(0.17, abs=1e-12, rel=0)
        assert c["late_discard_time"] == pytest.approx(0.175, abs=1e-12, rel=0)
        assert all(c["plan_id"] == 0 for c in r["controls"])
    check_grid_and_no_overlap(r)


def test_pending_old_command_survives_handoff(dynamic_vehicle, straight_geometry):
    r = simulate(dynamic_vehicle, straight_geometry, codriver_delay=0.015, duration=0.21)
    old = next(c for c in r["controls"] if c["time"] == pytest.approx(0.16, abs=1e-12, rel=0))
    assert old["plan_id"] == 0 and old["application_time"] == pytest.approx(0.175, abs=1e-12, rel=0)
    assert cycle(r, 1)["t_accept"] == pytest.approx(0.17, abs=1e-12, rel=0)
    assert cycle(r, 1)["first_TVLQR_use"] == pytest.approx(0.18, abs=1e-12, rel=0)


@pytest.mark.parametrize(
    "disturbance,expected_release,coalesced", [(0.035, 0.05, False), (0.085, 0.1, True)]
)
def test_on_grid_urgent_and_nominal_priority(
    dynamic_vehicle, straight_geometry, disturbance, expected_release, coalesced
):
    r = simulate(dynamic_vehicle, straight_geometry, disturbance_time=disturbance, duration=0.3)
    d = r["urgent_demands"][0]
    assert d["release_time"] == pytest.approx(expected_release, abs=1e-12, rel=0)
    assert d["planner_busy_wait"] == 0 and d["grid_alignment_wait"] == 0
    assert d["coalesced_nominal"] is coalesced
    assert len([e for e in r["releases"] if abs(e["time"] - expected_release) < 1e-10]) == 1
    check_grid_and_no_overlap(r)


def test_waiting_commitment_survives_new_urgent_completion(dynamic_vehicle, straight_geometry):
    r = simulate(
        dynamic_vehicle, straight_geometry, delay=0.01, disturbance_time=0.125, duration=0.25
    )
    # First packet waits .110->.170; an urgent .140 launch is ready .150, before that handoff.
    assert cycle(r, 1)["t_accept"] == pytest.approx(0.17, abs=1e-12, rel=0)
    assert cycle(r, 2)["t_release"] == pytest.approx(0.14, abs=1e-12, rel=0)
    assert cycle(r, 2)["t_accept"] == pytest.approx(0.21, abs=1e-12, rel=0)
    assert r["urgent_demands"][0]["accepted_plan_id"] == 2
    assert r["urgent_demands"][0]["accepted_time"] == pytest.approx(0.21, abs=1e-12, rel=0)
    check_grid_and_no_overlap(r)


def test_packet_eligibility_staleness_and_reserve(dynamic_vehicle, straight_geometry):
    r = simulate(dynamic_vehicle, straight_geometry, duration=0.21)
    from apex.control.trajectory.packet import TrajectoryPacket

    data = {
        k: v
        for k, v in r["packets"][1].items()
        if k not in ("horizon_end_time", "remaining_reserve_at_completion")
    }
    p = TrajectoryPacket(**data)
    b = TrajectoryBuffer()
    assert b.insert(p, 0.16) == (False, "outside_fixed_handoff")
    assert b.insert(p, 0.18) == (False, "outside_fixed_handoff")
    assert b.insert(replace(p, actual_completion_time=0.175), 0.17) == (
        False,
        "fixed_deadline_missed",
    )
    assert b.insert(p, p.valid_from) == (True, "accepted")
    assert b.insert(p, p.valid_from) == (False, "stale_plan")
    assert TrajectoryBuffer(minimum_handoff_reserve=0.5).insert(p, p.valid_from) == (
        False,
        "insufficient_reserve",
    )
    assert b.reserve(p.valid_from) == pytest.approx(0.4, abs=1e-12, rel=0)
    with pytest.raises(ValueError):
        b.sample(p.horizon_end_time)
    with pytest.raises(ValueError):
        TrajectoryBuffer().sample(0)


def test_replay_is_exact_and_defaults_have_no_new_telemetry(dynamic_vehicle, straight_geometry):
    a = simulate(dynamic_vehicle, straight_geometry)
    b = simulate(dynamic_vehicle, straight_geometry)
    for k in ("states", "handoffs", "fixed_handoffs", "urgent_demands", "releases", "misses"):
        assert a[k] == b[k]
    legacy = simulate(dynamic_vehicle, straight_geometry, offset=None)
    assert "fixed_handoffs" not in legacy
    assert all("valid_from" not in p for p in legacy["packets"])


def test_real_planner_uses_exact_fixed_duration_and_legacy_predictor(
    dynamic_vehicle, straight_geometry
):
    from test_committed_prefix_runtime import run_case

    result, planner, _ = run_case(dynamic_vehicle, straight_geometry, fixed_handoff_offset=0.07)
    for call, event in zip(planner.calls[1:], result["plans"][1:], strict=True):
        assert call["estimate"] == 0.07
        assert "committed_prefix" not in call["kwargs"]
        assert event["prediction_mode"] == "legacy"
        assert event["predicted_completion_time"] == event["valid_from"]
        assert event["valid_from"] == call["time"] + 0.07
    assert planner.calls[0]["estimate"] == 0


def test_repeated_urgent_trigger_coalesces_without_losing_initial_wait():
    from apex.simulation.fixed_handoff import FixedHandoffs

    fixed = FixedHandoffs(0.07)
    fixed.trigger(0.16, True)
    fixed.trigger(0.20, True)
    fixed.idle(0.255)
    fixed.release(2, 0.26, False, None)
    assert len(fixed.demands) == 1
    demand = fixed.demands[0]
    assert demand["coalesced_trigger_times"] == [0.20]
    assert demand["planner_busy_wait"] == pytest.approx(0.095, abs=1e-12, rel=0)
    assert demand["grid_alignment_wait"] == pytest.approx(0.005, abs=1e-12, rel=0)
    assert demand["coalesced_nominal"]


def test_due_old_application_precedes_fixed_handoff_and_new_sampling(
    dynamic_vehicle, straight_geometry
):
    r = simulate(dynamic_vehicle, straight_geometry, codriver_delay=0.01, duration=0.2)
    old = next(c for c in r["controls"] if abs(c["time"] - 0.16) < 1e-10)
    new = next(c for c in r["controls"] if abs(c["time"] - 0.17) < 1e-10)
    state = next(s for s in r["states"] if abs(s["time"] - 0.17) < 1e-10)
    assert old["plan_id"] == 0 and old["application_time"] == pytest.approx(0.17, abs=1e-12, rel=0)
    assert new["plan_id"] == state["plan_id"] == 1
    assert state["delta"] == old["delta"]
    assert state["a_cmd"] == old["a_cmd"]
