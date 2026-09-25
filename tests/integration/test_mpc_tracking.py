"""Independent nonlinear plant validation, including injected computational latency."""

import numpy as np
import pytest

from apex.control.baseline import cornering_reference
from apex.control.mpc.controller import make_mpc
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.latency_metrics import summarize_run
from apex.simulation.runner import RunConfig, SimulationRunner
from apex.simulation.timing import LatencyConfig


def run(p, track, *, ey=0, epsi=0, latency=0, duration=8, laps=None):
    c = make_mpc(p, track)
    ref = cornering_reference(p, 2, track.sample(0).curvature)
    initial = np.array([2.0, ref.vy, ref.yaw_rate, epsi, 0, ey])
    result = SimulationRunner(
        DynamicBicycle(p, track),
        c,
        track,
        RunConfig(
            duration=duration,
            target_laps=laps,
            dt_control=0.05,
            latency=LatencyConfig("injected", latency),
        ),
        controller_diagnostics=c.diagnostics,
        reset_controller=c.reset,
        finalize_control=c.finalize_control,
    ).run(initial)
    return result, summarize_run(result, track.length, lambda s: 2)


@pytest.mark.parametrize("track_name", ["circle", "oval"])
def test_nmpc_two_laps(dynamic_vehicle, request, track_name):
    track = request.getfixturevalue(track_name)
    result, metrics = run(dynamic_vehicle, track, duration=40, laps=2)
    print(track_name, metrics)
    assert result.stop_reason == "target_laps" and len(metrics["lap_times"]) == 2
    assert metrics["solver_failures"] == 0 and metrics["fallbacks"] == 0
    assert metrics["boundary_violations"] == 0
    assert metrics["settled"]["rms_e_y"] < 0.05
    assert metrics["max_slack"] < 1e-6
    assert any(e["warm_start"] for e in result.events)
    assert np.all(np.diff([s["s_abs"] for s in result.states]) > 0)


@pytest.mark.parametrize("ey,epsi", [(0.1, 0), (-0.1, 0), (0, 0.05), (0, -0.05), (0.08, -0.04)])
def test_nmpc_recovery(dynamic_vehicle, circle, ey, epsi):
    result, metrics = run(dynamic_vehicle, circle, ey=ey, epsi=epsi, duration=6)
    assert result.failure is None
    assert metrics["solver_failures"] == 0
    assert metrics["settled"]["rms_e_y"] < 0.02
    assert metrics["boundary_violations"] == 0


def test_real_plant_moves_during_computation(dynamic_vehicle, circle):
    result, _ = run(dynamic_vehicle, circle, latency=0.025, duration=0.15)
    first = result.events[0]
    assert first["delta_s_abs"] > 0.04
    assert first["staleness_index"] > 0
    assert first["application_time"] == pytest.approx(0.025)
    for name in ("vx", "vy", "r", "e_psi", "s_abs", "e_y"):
        assert first[f"delta_{name}"] == pytest.approx(
            first[f"x_apply_{name}"] - first[f"x_sample_{name}"]
        )
    assert all(row["delta"] == 0 for row in result.states if row["time"] < 0.025)
    repeat, _ = run(dynamic_vehicle, circle, latency=0.025, duration=0.15)
    assert result.states == repeat.states
    assert result.timing == repeat.timing
    for a, b in zip(result.events, repeat.events):
        assert a["release_time"] == b["release_time"]
        assert a["application_time"] == b["application_time"]
        assert a["staleness_index"] == b["staleness_index"]


def test_active_steering_constraint(dynamic_vehicle, circle):
    result, _ = run(dynamic_vehicle, circle, ey=0.59, duration=0.15)
    assert result.failure is None
    assert result.events[0]["success"]
    assert abs(result.controls[0]["delta"]) == pytest.approx(0.05, abs=1e-6)
