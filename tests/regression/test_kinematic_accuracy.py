"""Analytical errors and RK4 refinement; run with pytest -s for measured numbers."""

import json
from math import atan, cos, sin, tan

import numpy as np

from apex.models.vehicle.kinematic import KinematicBicycle
from apex.state import StateIndex as I
from apex.state import state_vector


def test_kinematic_accuracy_report(synthetic_vehicle, straight_geometry):
    model = KinematicBicycle(synthetic_vehicle, straight_geometry)
    metrics = {}
    for name, acceleration in [("straight", 0), ("acceleration", 0.4)]:
        x = state_vector([2, 0, 0, 0, 10, 0])
        for _ in range(100):
            x = model.step(x, [0, acceleration])
        metrics[f"{name}_position_error_m"] = abs(x[I.S_ABS] - (12 + 0.5 * acceleration))
        metrics[f"{name}_speed_error_m_per_s"] = abs(x[I.VX] - (2 + acceleration))
    delta, acceleration, duration = 0.2, 0.4, 1.0
    beta = atan(0.5 * tan(delta))
    factor = tan(beta) / 0.15
    yaw0 = 0.1
    turn = factor * (2 * duration + 0.5 * acceleration * duration**2)
    reference = np.array(
        [
            10 + (sin(yaw0 + beta + turn) - sin(yaw0 + beta)) / (factor * cos(beta)),
            (-cos(yaw0 + beta + turn) + cos(yaw0 + beta)) / (factor * cos(beta)),
        ]
    )
    errors, results = [], []
    for dt in [0.1, 0.05, 0.025]:
        x = state_vector([2, 0, 0, yaw0, 10, 0])
        for _ in range(round(duration / dt)):
            x = model.step(x, [delta, acceleration], dt)
        result = x[[I.S_ABS, I.E_Y]]
        results.append(result)
        errors.append(float(np.linalg.norm(result - reference)))
    metrics["rk4_position_errors_dt_0_1_0_05_0_025_m"] = errors
    metrics["rk4_error_ratios"] = [errors[0] / errors[1], errors[1] / errors[2]]
    metrics["rk4_refinement_differences_m"] = [
        float(np.linalg.norm(results[0] - results[1])),
        float(np.linalg.norm(results[1] - results[2])),
    ]
    metrics["vy_consistency_error_m_per_s"] = abs(x[I.VY] - x[I.VX] * tan(beta))
    metrics["r_consistency_error_rad_per_s"] = abs(x[I.YAW_RATE] - x[I.VX] / 0.15 * tan(beta))
    assert metrics["straight_position_error_m"] < 1e-11
    assert metrics["acceleration_position_error_m"] < 1e-11
    assert metrics["acceleration_speed_error_m_per_s"] < 1e-12
    assert all(14 < ratio < 18 for ratio in metrics["rk4_error_ratios"])
    assert errors[-1] < 1e-7
    print("\nKinematic accuracy metrics:\n" + json.dumps(metrics, indent=2))
