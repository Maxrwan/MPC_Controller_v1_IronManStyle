"""Physical-time-weighted tracking, actuator effort and separate latency metrics."""

import numpy as np

from apex.simulation.metrics import tracking_metrics


def summarize_run(result, track_length, reference, settling_time=5.0):
    metrics = tracking_metrics(result, track_length, reference, settling_time)
    metrics["plant_validity_failures"] = int(result.stop_reason == "model_validity_failure")
    metrics["controller_application_failures"] = int(
        result.stop_reason == "controller_application_failure"
    )
    rows = result.states
    t = np.array([r["time"] for r in rows])
    errors = np.array([[r["e_y"], r["e_psi"], reference(r["track_s"]) - r["vx"]] for r in rows])
    # Event splitting makes samples nonuniform. Weight by physical elapsed time for
    # every controller, including both LQR comparisons; do not overweight solve events.
    for label, start in (("full_run", 0.0), ("settled", settling_time)):
        mask = t >= start
        if mask.sum() < 2:
            metrics[label] = None
            continue
        ts = t[mask]
        rms = np.sqrt(np.trapezoid(errors[mask] ** 2, ts, axis=0) / (ts[-1] - ts[0]))
        metrics[label] = {
            "rms_e_y": float(rms[0]),
            "rms_e_psi": float(rms[1]),
            "rms_speed_error": float(rms[2]),
            "peak_abs_e_y": float(abs(errors[mask, 0]).max()),
        }
    settled = metrics["settled"]
    metrics["nominal_criteria_pass"] = bool(
        settled is not None
        and settled["rms_e_y"] < 0.05
        and settled["peak_abs_e_y"] < 0.15
        and settled["rms_speed_error"] < 0.1
        and not metrics["boundary_violations"]
        and result.failure is None
    )
    dt = np.diff(t)
    u = np.array([[r["delta"], r["a_cmd"]] for r in rows])
    effort = np.sum(u[:-1] ** 2 * dt[:, None], axis=0) if len(dt) else np.zeros(2)
    metrics.update(
        steering_squared_integral=float(effort[0]),
        acceleration_squared_integral=float(effort[1]),
        steering_total_variation=float(np.abs(np.diff(u[:, 0])).sum()),
        acceleration_range=[float(u[:, 1].min()), float(u[:, 1].max())],
        steering_range=[float(u[:, 0].min()), float(u[:, 0].max())],
        timing=result.timing,
    )
    events = result.events
    applied = [e for e in events if e["applied"]]

    def distribution(values):
        values = np.asarray(values, dtype=float)
        if not len(values):
            return {"mean": None, "p50": None, "p95": None, "max": None}
        return {
            "mean": float(values.mean()),
            "p50": float(np.median(values)),
            "p95": float(np.quantile(values, 0.95)),
            "max": float(values.max()),
        }

    metrics["solve_time"] = distribution([e["solve_time"] for e in events])
    metrics["latency"] = distribution([e["latency"] for e in events])
    metrics["iterations"] = distribution([e.get("iterations", 0) for e in events])
    metrics["staleness_index"] = distribution([e["staleness_index"] for e in applied])
    for name in ("e_y", "e_psi", "s_abs"):
        metrics[f"absolute_delta_{name}"] = distribution([abs(e[f"delta_{name}"]) for e in applied])
    metrics["solver_failures"] = sum(not e.get("success", True) for e in events)
    metrics["fallbacks"] = sum(e["fallback"] for e in applied)
    metrics["solve_below_50ms_fraction"] = (
        float(np.mean([e["solve_time"] < 0.05 for e in events])) if events else None
    )
    metrics["solve_at_or_above_50ms_fraction"] = (
        float(np.mean([e["solve_time"] >= 0.05 for e in events])) if events else None
    )
    for kind in ("cold", "warm"):
        selected = [e for e in events if bool(e.get("warm_start", False)) == (kind == "warm")]
        metrics[f"{kind}_start"] = {
            "count": len(selected),
            "solve_time": distribution([e["solve_time"] for e in selected]),
            "iterations": distribution([e.get("iterations", 0) for e in selected]),
        }
    slacks = [e["max_slack"] for e in events if e.get("max_slack") is not None]
    metrics["max_slack"] = max(slacks, default=0.0)
    metrics["nonzero_slack_solves"] = sum(e.get("nonzero_slack", False) for e in events)
    metrics["slack_above_1um_solves"] = sum(s > 1e-6 for s in slacks)
    metrics["slack_sum_over_predictions"] = sum(e.get("slack_sum") or 0 for e in events)
    return metrics
