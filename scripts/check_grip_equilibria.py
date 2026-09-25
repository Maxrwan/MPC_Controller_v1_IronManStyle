"""Constant-radius equilibrium-compatible demand sweep, without feedback control."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
from check_mpc_parity import ConstantCurvatureChart
from scipy.optimize import root

from apex.config import load_vehicle_parameters
from apex.control.baseline.references import cornering_reference
from apex.models.errors import ModelValidationError
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "results/tire_model"
    out.mkdir(parents=True, exist_ok=True)
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    # Root search may try beyond actuator limits; only validated original-parameter
    # solutions are accepted. Tire, load and speed validity remain enforced throughout.
    search = DynamicBicycle(
        replace(
            p,
            maximum_steering_angle=None,
            maximum_acceleration=None,
            maximum_braking_deceleration=None,
        ),
        ConstantCurvatureChart(0.5),
        tire_physics=RACING_TIRE_PHYSICS,
    )
    plant = DynamicBicycle(p, ConstantCurvatureChart(0.5), tire_physics=RACING_TIRE_PHYSICS)
    rows = []
    for speed in np.linspace(1, 4.4, 35):
        ref = cornering_reference(p, speed, 0.5)

        def state_control(z):
            vy, delta = z
            r = np.hypot(speed, vy) / 2
            return np.array([speed, vy, r, -np.arctan2(vy, speed), 1.0, 0.0]), np.array(
                [delta, -r * vy]
            )

        def residual(z):
            x, u = state_control(z)
            return search.derivative(x, u)[[1, 2]]

        try:
            solution = root(residual, [ref.vy, ref.delta_dynamic])
            x, u = state_control(solution.x)
            d = plant.diagnostics(x, u)
            dx = plant.derivative(x, u)
            residual_max = float(np.max(abs(dx[[0, 1, 2, 3, 5]])))
            if not solution.success or residual_max > 1e-7:
                rows.append(dict(speed=speed, accepted=False, reason="No converged equilibrium"))
                continue
            z = x.copy()
            for _ in range(100):
                z = plant.step(z, u, 0.005)
            drift = float(np.max(abs((z - x)[[0, 1, 2, 3, 5]])))
            rows.append(
                dict(
                    speed=speed,
                    accepted=True,
                    delta=u[0],
                    residual=residual_max,
                    half_second_state_drift=drift,
                    **asdict(d),
                )
            )
        except (ModelValidationError, ValueError) as error:
            rows.append(dict(speed=speed, accepted=False, reason=str(error)))
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "constant_radius_equilibria.csv", index=False)
    accepted = frame[frame.accepted]
    report = {
        "radius_m": 2,
        "attempted_speeds": len(frame),
        "accepted_equilibria": len(accepted),
        "maximum_accepted_speed": float(accepted.speed.max()),
        "maximum_utilization": float(
            accepted[["front_combined_utilization", "rear_combined_utilization"]].max().max()
        ),
        "maximum_equilibrium_residual": float(accepted.residual.max()),
        "maximum_half_second_nonprogress_state_drift": float(
            accepted.half_second_state_drift.max()
        ),
        "failed_searches": frame[~frame.accepted][["speed", "reason"]].to_dict("records"),
        "interpretation": (
            "Accepted roots validated with original actuator limits and propagated "
            "for0.5s. Failed root searches do not prove infeasibility."
        ),
    }
    (out / "constant_radius_equilibria.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
