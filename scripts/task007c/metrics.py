"""Offline oscillation diagnostics; no feedback policy or combined difficulty score."""

import numpy as np
from task007b.metrics import distribution

RATE_DEADBAND = 1e-4  # rad/s, excludes numerical chatter; report sensitivity separately.


def sideslip(states):
    states = np.asarray(states, dtype=float)
    if states.ndim != 2 or states.shape[1] != 6 or not np.isfinite(states).all():
        raise ValueError("Expected finite rows of six canonical states")
    return np.arctan2(states[:, 1], states[:, 0])


def variation(values, *, angle=False):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or len(values) == 0:
        raise ValueError("Expected nonempty finite series")
    if angle:
        values = np.unwrap(values)
    return dict(
        total_variation=float(np.abs(np.diff(values)).sum()), peak_to_peak=float(np.ptp(values))
    )


def steering_activity(steering, times, *, deadband=RATE_DEADBAND):
    steering, times = np.asarray(steering, float), np.asarray(times, float)
    if (
        steering.ndim != 1
        or times.shape != steering.shape
        or len(times) < 2
        or not np.isfinite(times).all()
        or not np.isfinite(steering).all()
        or np.any(np.diff(times) <= 0)
        or not np.isfinite(deadband)
        or deadband < 0
    ):
        raise ValueError("Expected finite steering at strictly increasing times")
    dt = np.diff(times)
    rates = np.diff(steering) / dt
    signs = np.sign(rates[np.abs(rates) > deadband])
    return dict(
        **variation(steering),
        rate_sign_reversals=int(np.count_nonzero(np.diff(signs))),
        time_at_rate_limit=float(dt[np.abs(rates) >= 1 - 1e-6].sum()),
        interval_duration=float(dt.sum()),
        max_abs_rate=float(np.abs(rates).max()),
        rate_deadband_rad_s=deadband,
    )


def prediction_metrics(states, controls, dt):
    """Within one prediction; excludes unavailable previous-command to u0 increment."""
    x, u = np.asarray(states, float), np.asarray(controls, float)
    if (
        x.ndim != 2
        or x.shape[1] != 6
        or u.shape != (len(x) - 1, 2)
        or len(u) < 2
        or not np.isfinite(x).all()
        or not np.isfinite(u).all()
        or not np.isfinite(dt)
        or dt <= 0
    ):
        raise ValueError("Invalid prediction shape or interval")
    result = {}
    for key, index in [("heading", 3), ("ey", 5), ("vy", 1), ("yaw_rate", 2)]:
        result.update(
            {key + "_" + k: v for k, v in variation(x[:, index], angle=key == "heading").items()}
        )
    result.update(
        {"steering_" + k: v for k, v in steering_activity(u[:, 0], np.arange(len(u)) * dt).items()}
    )
    result.update({"beta_" + k: v for k, v in distribution(sideslip(x)).items()})
    result["predicted_progress_m"] = float(x[-1, 4] - x[0, 4])
    result["horizon_s"] = dt * (len(x) - 1)
    return result


def traversal_metrics(frame):
    """One contiguous sector traversal; nominal controls are zero-order held."""
    result = {}
    for label, field in [("heading", "e_psi"), ("ey", "e_y"), ("vy", "vy"), ("yaw_rate", "r")]:
        for prefix, name in [("reference_", "planned"), ("actual_", "actual")]:
            result.update(
                {
                    name + "_" + label + "_" + k: v
                    for k, v in variation(frame[prefix + field], angle=field == "e_psi").items()
                }
            )
    # TV/reversal counts are descriptive for the stitched held nominal input. Do
    # not call its jumps continuous actuator-rate violations.
    for prefix, column in [("planned", "nominal_delta"), ("actual", "delta")]:
        result.update({prefix + "_steering_" + k: v for k, v in variation(frame[column]).items()})
        for deadband in [1e-5, RATE_DEADBAND, 1e-3]:
            value = steering_activity(frame[column], frame.time, deadband=deadband)
            result[f"{prefix}_steering_reversals_db_{deadband:g}"] = value["rate_sign_reversals"]
    duration = float(frame.interval.sum())
    distance = float(frame.s_abs.iloc[-1] - frame.s_abs.iloc[0])
    result.update(duration_s=duration, distance_m=distance)
    for name, value in list(result.items()):
        if name.endswith("_total_variation"):
            result[name + "_per_s"] = value / duration
            result[name + "_per_m"] = value / distance if distance > 0 else None
    result["actual_rate_limit_s"] = float(
        frame.interval[abs(frame.steering_rate) >= 1 - 1e-6].sum()
    )
    result["actual_rate_limit_fraction"] = result["actual_rate_limit_s"] / duration
    for name, column in [("planned", "planned_beta"), ("actual", "actual_beta")]:
        result.update(
            {name + "_beta_" + k: v for k, v in distribution(frame[column], frame.interval).items()}
        )
    return result


def prediction_diagnostics(states, controls, dt):
    """Retain full horizon and a common first 0.4 s window for N4/N6/N8 comparisons."""
    result = prediction_metrics(states, controls, dt)
    horizon, progress = result["horizon_s"], result["predicted_progress_m"]
    for key, value in list(result.items()):
        if key.endswith("_total_variation"):
            span = result["steering_interval_duration"] if key.startswith("steering_") else horizon
            result[key + "_per_s"] = value / span
            result[key + "_per_m"] = value / progress if progress > 0 else None
    count = round(0.4 / dt)
    if np.isclose(count * dt, 0.4) and len(controls) >= count:
        common = prediction_metrics(
            np.asarray(states)[: count + 1], np.asarray(controls)[:count], dt
        )
        result.update({"common_0p4_" + k: v for k, v in common.items()})
    return result
