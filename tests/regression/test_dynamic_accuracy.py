"""Analytical force balance and smooth dynamic RK4 convergence metrics."""

import json
from math import tan

import numpy as np
from scipy.integrate import solve_ivp

from apex.models.constants import STANDARD_GRAVITY
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer
from apex.state import StateIndex as I
from apex.state import state_vector


def test_dynamic_accuracy_report(dynamic_vehicle, straight_geometry):
    model = DynamicBicycle(dynamic_vehicle, straight_geometry)
    hand = state_vector([2, 2 * tan(0.1), 0, 0, 1, 0])
    d = model.diagnostics(hand, [0.15, 0])
    dx = model.derivative(hand, [0.15, 0])
    loads = QuasiStaticLongitudinalLoadTransfer()
    metrics = {
        "front_force_error_N": abs(d.fyf - 2.25),
        "rear_force_error_N": abs(d.fyr + 4.5),
        "lateral_acceleration_error_m_per_s2": abs(dx[I.VY] + 1.125),
        "yaw_acceleration_error_rad_per_s2": abs(dx[I.YAW_RATE] - 40.5),
        "max_load_conservation_error_N": max(
            abs(
                loads.evaluate(dynamic_vehicle, a).front
                + loads.evaluate(dynamic_vehicle, a).rear
                - 2 * STANDARD_GRAVITY
            )
            for a in np.linspace(-10, 10, 101)
        ),
    }
    # Smooth held-input transient, no validity boundary or switching event.
    initial = state_vector([2, 0.03, 0.1, 0.02, 10, 0.05])
    control = np.array([0.025, 0.1])
    duration = 0.2
    reference = solve_ivp(
        lambda t, x: model.derivative(x, control),
        (0, duration),
        initial,
        method="DOP853",
        rtol=2e-13,
        atol=2e-14,
    )
    assert reference.success
    reference = reference.y[:, -1]
    results = []
    errors = []
    for dt in [0.01, 0.005, 0.0025]:
        x = initial.copy()
        for _ in range(round(duration / dt)):
            x = model.step(x, control, dt)
        results.append(x)
        errors.append(float(np.max(np.abs(x - reference))))
    ratios = [errors[0] / errors[1], errors[1] / errors[2]]
    metrics["rk4_max_state_errors_dt_0_01_0_005_0_0025"] = errors
    metrics["rk4_error_ratios"] = ratios
    metrics["rk4_cartesian_position_errors_m"] = [
        float(np.linalg.norm((result - reference)[[I.S_ABS, I.E_Y]])) for result in results
    ]
    metrics["rk4_successive_max_state_differences"] = [
        float(np.max(np.abs(results[0] - results[1]))),
        float(np.max(np.abs(results[1] - results[2]))),
    ]
    assert max(metrics[key] for key in list(metrics)[:5]) < 1e-12
    assert all(12 < ratio < 22 for ratio in ratios)
    assert errors[-1] < 1e-7
    print("\nDynamic accuracy metrics:\n" + json.dumps(metrics, indent=2))
