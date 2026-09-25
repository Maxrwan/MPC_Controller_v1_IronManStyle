"""Fixed-curvature independent NumPy reference integration and symbolic fidelity."""

import json

import numpy as np
from check_mpc_parity import ConstantCurvatureChart
from parameter_study.common import OUT, ROOT
from scipy.integrate import solve_ivp

from apex.config import load_vehicle_parameters
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.models.errors import FrenetGeometryError, ModelValidationError
from apex.models.integration import rk4_step
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle


def measure(dt, substeps, samples=80):
    path = OUT / f"fidelity_{dt:.9f}_{substeps}.json"
    if path.exists():
        return json.loads(path.read_text())
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    chart = ConstantCurvatureChart(0)
    plant = DynamicBicycle(p, chart, tire_physics=RACING_TIRE_PHYSICS)
    symbolic = SymbolicBicycle(p, RACING_TIRE_PHYSICS)
    step = symbolic.rk4(dt, substeps)
    rng = np.random.default_rng(60062)
    errors = []
    parity = np.zeros(6)
    invalid_predictions = 0
    parity_samples = 0
    # Explicit control-relevant scales; progress gets a separate 0.1m scale here.
    scales = np.array([0.5, 0.5, 1, 0.1, 0.1, 0.1])
    for _ in range(samples):
        x = np.array(
            [
                rng.uniform(1, 3),
                rng.uniform(-0.15, 0.15),
                rng.uniform(-0.8, 0.8),
                rng.uniform(-0.1, 0.1),
                10.0,
                rng.uniform(-0.1, 0.1),
            ]
        )
        u = np.array([rng.uniform(-0.25, 0.25), rng.uniform(-1, 1)])
        chart.curvature = k = rng.uniform(-0.8, 0.8)
        reference = solve_ivp(
            lambda t, z: plant.derivative(z, u), (0, dt), x, method="DOP853", rtol=1e-11, atol=1e-12
        )
        if not reference.success or not np.isfinite(reference.y).all():
            raise RuntimeError("Independent reference integration did not converge")
        exact = reference.y[:, -1]
        predicted = np.asarray(step(x, u, k)[0]).ravel()
        numeric = x.copy()
        try:
            for _ in range(substeps):
                numeric = rk4_step(lambda z: plant.derivative(z, u), numeric, dt / substeps)
            parity = np.maximum(parity, abs(numeric - predicted))
            parity_samples += 1
        except (ModelValidationError, FrenetGeometryError):
            invalid_predictions += 1
        errors.append(predicted - exact)
    errors = np.array(errors)
    norm = np.linalg.norm(errors / scales, axis=1)
    report = {
        "dt": dt,
        "substeps": substeps,
        "samples": samples,
        "invalid_prediction_domain_samples": invalid_predictions,
        "valid_parity_samples": parity_samples,
        "seed": 60062,
        "scale_order": ["vx", "vy", "r", "e_psi", "s_abs", "e_y"],
        "scales": scales.tolist(),
        "maximum_channel_error": np.max(abs(errors), axis=0).tolist(),
        "maximum_scaled_error": float(norm.max()),
        "rms_scaled_error": float(np.sqrt(np.mean(norm**2))),
        "numpy_casadi_parity_max_by_channel": parity.tolist(),
        "accuracy_pass": bool(
            invalid_predictions == 0 and norm.max() <= 0.02 and np.sqrt(np.mean(norm**2)) <= 0.005
        ),
    }
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("FIDELITY", report, flush=True)
    return report
