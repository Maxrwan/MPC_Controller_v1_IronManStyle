"""Nonlinear Task 004 plant, real periodic spline tracks, fixed baseline parameters."""

import numpy as np
import pytest

from apex.control.baseline import BaselineController, ConstantSpeed, cornering_reference
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.metrics import tracking_metrics
from apex.simulation.runner import RunConfig, SimulationRunner


def simulate(p, track, speed=2.0, ey=0.0, epsi=0.0, duration=12.0, laps=None):
    reference = ConstantSpeed(speed)
    controller = BaselineController(p, track, reference)
    ref = cornering_reference(p, speed, track.sample(0).curvature)
    runner = SimulationRunner(
        DynamicBicycle(p, track),
        controller,
        track,
        RunConfig(duration=duration, target_laps=laps),
        controller_diagnostics=controller.diagnostics,
        reset_controller=controller.reset,
    )
    result = runner.run(np.array([speed, ref.vy, ref.yaw_rate, epsi, 0.0, ey]))
    return result, tracking_metrics(result, track.length, reference)


@pytest.mark.parametrize("track_name", ["circle", "oval"])
@pytest.mark.parametrize("speed", [1.0, 2.0, 3.0])
def test_two_laps_all_schedule_nodes(dynamic_vehicle, request, track_name, speed):
    track = request.getfixturevalue(track_name)
    result, metrics = simulate(dynamic_vehicle, track, speed, duration=80.0, laps=2)
    print(track_name, speed, metrics)
    assert result.stop_reason == "target_laps"
    assert metrics["distance_laps"] >= 2
    assert len(metrics["lap_times"]) == 2
    assert not metrics["validity_failures"] and not metrics["boundary_violations"]
    assert np.all(np.diff([row["s_abs"] for row in result.states]) > 0)
    if speed == 2:
        assert metrics["nominal_criteria_pass"]


@pytest.mark.parametrize(
    "ey,epsi", [(0, 0), (0.1, 0), (-0.1, 0), (0, 0.05), (0, -0.05), (0.08, -0.04)]
)
def test_disturbance_recovery(dynamic_vehicle, circle, ey, epsi):
    _, metrics = simulate(dynamic_vehicle, circle, ey=ey, epsi=epsi)
    print(ey, epsi, metrics)
    assert metrics["nominal_criteria_pass"]
    assert metrics["recovery_time"] is not None and metrics["recovery_time"] < 5


def test_determinism(dynamic_vehicle, circle):
    a, _ = simulate(dynamic_vehicle, circle, ey=0.08, epsi=-0.04, duration=0.2)
    b, _ = simulate(dynamic_vehicle, circle, ey=0.08, epsi=-0.04, duration=0.2)
    assert a.states == b.states
    assert a.controls == b.controls


def test_progress_profile_changes_gains(dynamic_vehicle, oval):
    def profile(s):
        return 2 + 0.5 * np.sin(2 * np.pi * s / oval.length)

    c = BaselineController(dynamic_vehicle, oval, profile)
    ref = cornering_reference(dynamic_vehicle, 2, oval.sample(0).curvature)
    result = SimulationRunner(
        DynamicBicycle(dynamic_vehicle, oval),
        c,
        oval,
        RunConfig(duration=10),
        controller_diagnostics=c.diagnostics,
        reset_controller=c.reset,
    ).run(np.array([2.0, ref.vy, ref.yaw_rate, 0, 0, 0]))
    assert result.failure is None
    assert not any(row["boundary_violation"] for row in result.states)
    assert np.ptp([row["reference_speed"] for row in result.controls]) > 0.5
    assert np.ptp([row["gain_e_y"] for row in result.controls]) > 0.01
