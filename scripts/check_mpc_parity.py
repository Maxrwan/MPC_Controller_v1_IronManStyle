"""Reproducible equation/integrator parity on fixed-curvature local test charts."""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from apex.config import load_vehicle_parameters
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.state import STATE_NAMES
from apex.track.base import TrackSample

ROOT = Path(__file__).resolve().parents[1]


class ConstantCurvatureChart:
    """Local equation test double, not a claim of a globally closed physical track."""

    length = 1e6

    def __init__(self, curvature):
        self.curvature = curvature

    def sample(self, s):
        return TrackSample(s, s, 0, 0, self.curvature, 1, 1)


def check_parity(samples=1000):
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    rng = np.random.default_rng(6006)
    derivative_error, step_error, interval_error = np.zeros(6), np.zeros(6), np.zeros(6)
    for params in (
        p,
        replace(p, lf=0.12, lr=0.18, front_cornering_stiffness=30.0, rear_cornering_stiffness=52.0),
    ):
        symbolic = SymbolicBicycle(params)
        step = symbolic.rk4(0.01, 1)
        interval = symbolic.rk4(0.05, 5)
        chart = ConstantCurvatureChart(0)
        plant = DynamicBicycle(params, chart)
        for _ in range(samples // 2):
            x = np.array(
                [
                    rng.uniform(1, 3),
                    rng.uniform(-0.15, 0.15),
                    rng.uniform(-0.6, 0.6),
                    rng.uniform(-0.1, 0.1),
                    rng.uniform(1, 100),
                    rng.uniform(-0.1, 0.1),
                ]
            )
            u = np.array([rng.uniform(-0.25, 0.25), rng.uniform(-1, 1)])
            chart.curvature = k = rng.uniform(-0.8, 0.8)
            derivative_error = np.maximum(
                derivative_error,
                abs(plant.derivative(x, u) - np.asarray(symbolic.derivative(x, u, k)).ravel()),
            )
            step_error = np.maximum(
                step_error, abs(plant.step(x, u, 0.01) - np.asarray(step(x, u, k)[0]).ravel())
            )
            numerical = x.copy()
            for _ in range(5):
                numerical = plant.step(numerical, u, 0.01)
            interval_error = np.maximum(
                interval_error, abs(numerical - np.asarray(interval(x, u, k)[0]).ravel())
            )
    assert max(derivative_error) < 1e-11
    assert max(step_error) < 1e-11
    assert max(interval_error) < 1e-11
    symbolic = SymbolicBicycle(p)
    seed = np.array([2.0, 0.07, 0.25, 0.03, 1.0, 0.04])
    command = np.array([0.06, 0.1])
    exact = solve_ivp(
        lambda t, z: np.asarray(symbolic.derivative(z, command, 0.2)).ravel(),
        [0, 0.05],
        seed,
        method="DOP853",
        rtol=1e-12,
        atol=1e-13,
    ).y[:, -1]
    convergence = {}
    for count in (5, 10, 20):
        predicted = np.asarray(symbolic.rk4(0.05, count)(seed, command, 0.2)[0]).ravel()
        convergence[str(count)] = dict(zip(STATE_NAMES, abs(predicted - exact).tolist()))
    return {
        "convergence_vs_DOP853_by_substep_count": convergence,
        "samples": samples,
        "seed": 6006,
        "parameter_sets": 2,
        "chart": "frozen curvature per interval",
        "derivative_max_abs": dict(zip(STATE_NAMES, derivative_error.tolist())),
        "rk4_10ms_max_abs": dict(zip(STATE_NAMES, step_error.tolist())),
        "rk4_50ms_max_abs": dict(zip(STATE_NAMES, interval_error.tolist())),
    }


if __name__ == "__main__":
    report = check_parity()
    directory = ROOT / "results/mpc_baseline"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "parity.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
