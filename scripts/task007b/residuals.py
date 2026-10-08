"""Offline frozen-nominal defects using the independent physical plant."""

import numpy as np
import pandas as pd

from apex.config import load_vehicle_parameters
from apex.coordinates.angles import wrap_angle
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.state import STATE_NAMES


def nominal(reference, s):
    g = reference.sample(s)
    return np.array(
        [
            g["v_ref_mps"],
            0,
            g["v_ref_mps"] * g["kappa_ref_1pm"],
            g["e_psi_ref_rad"],
            s,
            g["e_y_ref_m"],
        ]
    )


def residuals(folder, ref, track):
    p = load_vehicle_parameters("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    rows = []
    for s in np.arange(1, track.length, 0.5):
        x = nominal(ref, s)
        g = ref.sample(s)
        command = np.array([np.arctan(0.3 * g["kappa_ref_1pm"]), 0.0])
        row = dict(s_abs=s, gamma=ref.manifest.get("aggression_factor", 1), dt=0.01)
        try:
            actual = plant.step(plant.step(x, command, 0.005), command, 0.005)
            progress_rate = x[0] * np.cos(x[3]) / (1 - track.sample(s).curvature * x[5])
            desired = nominal(ref, s + 0.01 * progress_rate)
            defect = actual - desired
            defect[3] = wrap_angle(defect[3])
            row.update({k: float(v) for k, v in zip(STATE_NAMES, defect)})
            row["status"] = "evaluated"
        except ValueError as error:
            row["status"] = str(error)
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(folder / "nominal_state_defect.csv", index=False)
    return {k: float(frame[k].abs().max()) for k in STATE_NAMES if k in frame}
