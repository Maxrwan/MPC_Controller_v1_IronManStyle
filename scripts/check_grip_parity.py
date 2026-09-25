"""Independent grip NumPy/CasADi derivative, force, utilization and RK4 parity."""

import json
from dataclasses import replace
from pathlib import Path

import casadi as ca
import numpy as np
from check_mpc_parity import ConstantCurvatureChart

from apex.config import load_vehicle_parameters
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.state import STATE_NAMES

ROOT = Path(__file__).resolve().parents[1]


def check_parity(samples=1000):
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    rng = np.random.default_rng(60061)
    derivative, step, forces, utilization = np.zeros(6), np.zeros(6), np.zeros(4), np.zeros(2)
    for params in (
        p,
        replace(
            p,
            lf=0.12,
            lr=0.18,
            front_cornering_stiffness=30,
            rear_cornering_stiffness=52,
            tire_road_friction_coefficient=0.7,
        ),
    ):
        chart = ConstantCurvatureChart(0)
        plant = DynamicBicycle(params, chart, tire_physics=RACING_TIRE_PHYSICS)
        symbolic = SymbolicBicycle(params, RACING_TIRE_PHYSICS)
        transition = symbolic.rk4()
        for _ in range(samples // 2):
            x = np.array(
                [
                    rng.uniform(1.5, 3),
                    rng.uniform(-0.3, 0.3),
                    rng.uniform(-0.8, 0.8),
                    rng.uniform(-0.1, 0.1),
                    rng.uniform(1, 100),
                    rng.uniform(-0.1, 0.1),
                ]
            )
            u = np.array([rng.uniform(-0.4, 0.4), rng.uniform(-3, 2)])
            chart.curvature = k = rng.uniform(-0.6, 0.6)
            derivative = np.maximum(
                derivative,
                abs(plant.derivative(x, u) - np.asarray(symbolic.derivative(x, u, k)).ravel()),
            )
            d = plant.diagnostics(x, u)
            sf, su = symbolic.tire_diagnostics(x, u)
            forces = np.maximum(
                forces,
                abs(np.array([d.fx_front, d.fx_rear, d.fyf, d.fyr]) - np.asarray(sf).ravel()),
            )
            utilization = np.maximum(
                utilization,
                abs(
                    np.array([d.front_combined_utilization, d.rear_combined_utilization])
                    - np.asarray(su).ravel()
                ),
            )
            z = x.copy()
            for _ in range(5):
                z = plant.step(z, u, 0.01)
            step = np.maximum(step, abs(z - np.asarray(transition(x, u, k)[0]).ravel()))
    sx, su = ca.SX.sym("x", 6), ca.SX.sym("u", 2)
    model = SymbolicBicycle(p, RACING_TIRE_PHYSICS)
    function = ca.Function(
        "grip_derivative_jacobian",
        [sx, su],
        [ca.jacobian(model.derivative(sx, su, 0.2), ca.vertcat(sx, su))],
    )
    jacobian_error = 0.0
    state = np.array([2, 0.02, 0.4, 0, 0, 0])
    for delta in np.linspace(-0.3, 0.3, 25):
        command = np.array([delta, 1.0])
        h = 1e-6
        numeric = (
            np.asarray(model.derivative(state, command + [h, 0], 0.2))
            - np.asarray(model.derivative(state, command - [h, 0], 0.2))
        ) / (2 * h)
        analytic = np.asarray(function(state, command))[:, 6]
        jacobian_error = max(jacobian_error, float(np.max(abs(numeric.ravel() - analytic))))
    finite_points = 0
    for a in (-9.81 * (1 - 2e-6), 0, 9.81 * (1 - 2e-6)):
        for delta in (0, 0.05, 0.15, 0.3):
            assert np.isfinite(np.asarray(function(state, [delta, a]))).all()
            finite_points += 1
    report = {
        "jacobian_finite_points_including_near_boundary": finite_points,
        "steering_jacobian_max_abs_difference_vs_central_difference": jacobian_error,
        "samples": samples,
        "seed": 60061,
        "parameter_sets": 2,
        "derivative_max_abs": dict(zip(STATE_NAMES, derivative.tolist())),
        "rk4_50ms_max_abs": dict(zip(STATE_NAMES, step.tolist())),
        "force_max_abs": dict(zip(["fx_front", "fx_rear", "fy_front", "fy_rear"], forces.tolist())),
        "utilization_max_abs": utilization.tolist(),
    }
    assert (
        max(derivative) < 1e-11
        and max(step) < 1e-11
        and max(forces) < 1e-12
        and max(utilization) < 1e-12
    )
    return report


if __name__ == "__main__":
    out = ROOT / "results/tire_model"
    out.mkdir(parents=True, exist_ok=True)
    report = check_parity()
    (out / "parity.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
