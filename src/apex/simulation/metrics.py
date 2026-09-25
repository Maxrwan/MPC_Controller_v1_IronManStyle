"""Explicit full-run and fixed-settling-window baseline metrics."""

from collections.abc import Callable

import numpy as np

from apex.simulation.runner import RunResult


def tracking_metrics(
    result: RunResult,
    track_length: float,
    reference: Callable[[float], float],
    settling_time: float = 5.0,
) -> dict:
    if not np.isfinite(settling_time) or settling_time < 0:
        raise ValueError("settling_time must be nonnegative finite")
    rows = result.states
    t = np.array([row["time"] for row in rows])
    s = np.array([row["s_abs"] for row in rows])
    ey = np.array([row["e_y"] for row in rows])
    epsi = np.array([row["e_psi"] for row in rows])
    ev = np.array([reference(row["track_s"]) - row["vx"] for row in rows])
    settled = t >= settling_time

    def errors(mask):
        if not np.any(mask):
            return None
        return {
            "rms_e_y": float(np.sqrt(np.mean(ey[mask] ** 2))),
            "peak_abs_e_y": float(np.max(np.abs(ey[mask]))),
            "rms_e_psi": float(np.sqrt(np.mean(epsi[mask] ** 2))),
            "rms_speed_error": float(np.sqrt(np.mean(ev[mask] ** 2))),
        }

    # Only complete seam-to-seam intervals; omit an initial partial lap.
    crossings = []
    if s[0] == round(s[0] / track_length) * track_length:
        crossings.append(float(t[0]))
    for i in range(1, len(s)):
        if s[i] > s[i - 1]:
            for lap in range(
                int(np.floor(s[i - 1] / track_length)) + 1, int(np.floor(s[i] / track_length)) + 1
            ):
                fraction = (lap * track_length - s[i - 1]) / (s[i] - s[i - 1])
                crossings.append(float(t[i - 1] + fraction * (t[i] - t[i - 1])))
    commands = result.controls
    speeds = np.array([row["vx"] for row in rows])
    delta = np.array([row["delta"] for row in commands])
    in_band = (np.abs(ey) < 0.02) & (np.abs(epsi) < 0.02) & (np.abs(ev) < 0.1)
    suffix_in_band = np.logical_and.accumulate(in_band[::-1])[::-1]
    indices = np.flatnonzero(suffix_in_band)
    # Require at least one second remaining, not a single lucky last sample.
    recovery = float(t[indices[0]]) if len(indices) and t[-1] - t[indices[0]] >= 1 else None
    metrics = {
        "speed_range": [float(speeds.min()), float(speeds.max())],
        "maximum_schedule_excursion": float(max(0, 1 - speeds.min(), speeds.max() - 3)),
        "duration": float(t[-1]),
        "distance_laps": float((s[-1] - s[0]) / track_length),
        "settling_time": settling_time,
        "full_run": errors(np.ones(len(t), dtype=bool)),
        "settled": errors(settled),
        "steering_range": [float(delta.min()), float(delta.max())] if len(delta) else None,
        "steering_saturation_percent": 100
        * float(np.mean([row.get("steering_saturated", False) for row in commands]))
        if commands
        else None,
        "schedule_clamp_percent": 100
        * float(np.mean([row.get("scheduling_clamped", False) for row in commands]))
        if commands
        else None,
        "boundary_violations": sum(bool(row["boundary_violation"]) for row in rows),
        "validity_failures": int(result.failure is not None),
        "failure": result.failure,
        "stop_reason": result.stop_reason,
        "lap_times": np.diff(crossings).tolist(),
        "recovery_time": recovery,
    }
    e = metrics["settled"]
    metrics["nominal_criteria_pass"] = bool(
        e is not None
        and e["rms_e_y"] < 0.05
        and e["peak_abs_e_y"] < 0.15
        and e["rms_speed_error"] < 0.1
        and not metrics["boundary_violations"]
        and not metrics["validity_failures"]
    )
    return metrics
