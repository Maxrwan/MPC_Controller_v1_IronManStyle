"""Separate nominal-intent adaptation from local tracking; SI throughout."""

import numpy as np

from apex.coordinates.angles import wrap_angle


def planning_deviation(states, reference):
    """One row per predicted node; query at THAT node's unwrapped progress."""
    states = np.asarray(states, dtype=float)
    goals = [reference.sample(s) for s in states[:, 4]]
    nominal = np.array(
        [
            [
                g["v_ref_mps"],
                0,
                g["v_ref_mps"] * g["kappa_ref_1pm"],
                g["e_psi_ref_rad"],
                x[4],
                g["e_y_ref_m"],
            ]
            for x, g in zip(states, goals)
        ]
    )
    errors = states - nominal
    errors[:, 3] = [wrap_angle(v) for v in errors[:, 3]]
    return nominal, errors


def local_tracking_error(vehicle, active):
    """Vehicle minus timestamped active APEX state, with periodic heading error."""
    error = np.asarray(vehicle, dtype=float) - np.asarray(active, dtype=float)
    if error.ndim != 2 or error.shape[1] != 6:
        raise ValueError("Expected rows of six canonical states")
    error[:, 3] = [wrap_angle(v) for v in error[:, 3]]
    return error


def distribution(values, weights=None):
    v = np.asarray(values, dtype=float)
    valid = np.isfinite(v)
    if not valid.any():
        return dict(mean=None, rms=None, p95_abs=None, max_abs=None, min=None, max=None)
    w = np.ones(len(v)) if weights is None else np.asarray(weights, dtype=float)
    v, w = v[valid], w[valid]
    w = w / w.sum() if w.sum() > 0 else np.ones(len(v)) / len(v)
    return dict(
        mean=float(w @ v),
        rms=float(np.sqrt(w @ (v * v))),
        p95_abs=float(np.quantile(abs(v), 0.95)),
        max_abs=float(max(abs(v))),
        min=float(min(v)),
        max=float(max(v)),
    )
