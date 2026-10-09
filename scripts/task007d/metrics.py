"""Compact pilot validity/chronology metrics and common-time comparisons."""

import numpy as np
from task007d.diagnostics import TIME_TOL, common_coverage, residual

from apex.coordinates.angles import wrap_angle
from apex.state import STATE_NAMES


def envelope(values):
    x = np.asarray(values, dtype=float)
    return (
        None
        if not x.size
        else dict(rms=float(np.sqrt(np.mean(x * x))), max_abs=float(np.max(abs(x))))
    )


def chronology(result):
    issues = []
    plans = {p["plan_id"]: p for p in result["plans"]}
    accepted = [h for h in result["handoffs"] if h["accepted"]]
    previous_id = 0
    for h in accepted:
        p = plans[h["plan_id"]]
        if (
            not p.get("completed")
            or h["time"] < p["completion_time"] - TIME_TOL
            or h["time"] < p["predicted_completion_time"] - TIME_TOL
            or h["plan_id"] <= previous_id
        ):
            issues.append(dict(kind="handoff_authority", plan_id=h["plan_id"]))
        previous_id = h["plan_id"]
    for channel in ("states", "controls"):
        for row in result[channel]:
            expected = 0
            for h in accepted:
                if h["time"] <= row["time"] + TIME_TOL:
                    expected = h["plan_id"]
            if row["plan_id"] != expected:
                issues.append(dict(kind=channel + "_authority", time=row["time"]))
            if (
                channel == "controls"
                and abs(row["application_time"] - row["time"] - row["physical_latency"]) > TIME_TOL
            ):
                issues.append(dict(kind="application_chronology", time=row["time"]))
    return issues


def physical_metrics(result, track, end=None):
    if not result["states"]:
        return dict(observed_end=None, failure=result["failure"], stop_reason=result["stop_reason"])
    end = result["states"][-1]["time"] if end is None else end
    states = [r for r in result["states"] if r["time"] <= end + TIME_TOL]
    commands = [r for r in result["controls"] if r["application_time"] <= end + TIME_TOL]
    plans = [p for p in result["plans"] if p["release_time"] <= end + TIME_TOL]
    reserves = [r["reserve"] for r in result["reserves"] if r["time"] <= end + TIME_TOL]
    geometry = [track.sample(r["s_abs"] % track.length) for r in states]
    clearance = [
        min(g.left_width - r["e_y"], g.right_width + r["e_y"]) for r, g in zip(states, geometry)
    ]
    heading = [r["e_psi"] + g.heading for r, g in zip(states, geometry)]

    def tv(values, angle=False):
        change = np.diff(values)
        return float(np.sum(np.abs([wrap_angle(v) for v in change] if angle else change)))

    return dict(
        observed_end=states[-1]["time"],
        simulated_end=result.get("end_time"),
        stop_reason=result["stop_reason"],
        failure=result["failure"],
        progress_reached=states[-1]["s_abs"],
        progress_gain=states[-1]["s_abs"] - states[0]["s_abs"],
        physical_boundary_crossings=sum(r["boundary_violation"] for r in states),
        minimum_center_clearance=float(min(clearance)),
        minimum_tracking_margin_clearance=float(min(clearance) - 0.08),
        solver_failures=sum(not p["success"] for p in plans),
        max_predicted_slack=max((p.get("max_slack") or 0 for p in plans), default=None),
        plans_slack_above_1e6=sum((p.get("max_slack") or 0) > 1e-6 for p in plans),
        handoff_rejections=sum(not h["accepted"] for h in result["handoffs"] if h["time"] <= end),
        accepted_handoffs=sum(h["accepted"] for h in result["handoffs"] if h["time"] <= end),
        planner_busy_misses=sum(r["time"] <= end for r in result["misses"]),
        codriver_busy_misses=sum(r["time"] <= end for r in result.get("codriver_misses", [])),
        planner_delays_over_period=sum(p.get("physical_delay", 0) > 0.1 for p in plans),
        applied_codriver_delays_over_period=sum(c["physical_latency"] > 0.01 for c in commands),
        minimum_reserve=min(reserves),
        actual_steering_tv=tv([r["delta"] for r in states]),
        actual_heading_tv=tv(heading, True),
        actual_frenet_heading_tv=tv([r["e_psi"] for r in states], True),
        apex_vehicle_tracking={
            k: envelope([c["error_" + k] for c in commands]) for k in STATE_NAMES
        },
        handoff_continuity={
            k: envelope(
                [
                    h["error_" + k]
                    for h in result["handoffs"]
                    if h["time"] <= end and "error_" + k in h
                ]
            )
            for k in STATE_NAMES
        },
    )


def stop_reasons(result, metrics, issues):
    reasons = []
    if result["failure"] or result["stop_reason"] != "duration":
        reasons.append("runtime_failure_or_early_stop")
    if metrics.get("physical_boundary_crossings"):
        reasons.append("physical_boundary_crossing")
    if metrics.get("solver_failures"):
        reasons.append("solver_or_preparation_failure")
    # Conservative gate: even one >1e-6 m slack plan pauses continuation for review.
    if metrics.get("plans_slack_above_1e6"):
        reasons.append("predicted_slack_above_1e-6_m")
    if result["fallbacks"]:
        reasons.append("trajectory_exhaustion")
    if issues:
        reasons.append("chronology_or_authority_violation")
    return reasons


def compare(a, b, track):
    coverage = common_coverage(a, b)
    end = coverage["end"]
    if end is None:
        return dict(coverage=coverage, metrics=None, first_divergence=None)
    # Pair by physical timestamp, never by launch row index. Round only to event tolerance.
    astates = {round(r["time"], 10): r for r in a["states"] if r["time"] <= end + TIME_TOL}
    bstates = {round(r["time"], 10): r for r in b["states"] if r["time"] <= end + TIME_TOL}
    common_times = sorted(astates.keys() & bstates.keys())
    if not common_times:
        return dict(coverage=coverage, metrics=None, first_divergence=None)
    end = common_times[-1]
    coverage["common_recorded_end"] = end
    first = None
    for t in common_times:
        ar, br = astates[t], bstates[t]
        dx = residual([ar[k] for k in STATE_NAMES], [br[k] for k in STATE_NAMES])
        du = np.asarray([ar[k] - br[k] for k in ("delta", "a_cmd")])
        if np.any(abs(dx) > 1e-12) or np.any(abs(du) > 1e-12):
            preceding = {}
            for label, result in [("A", a), ("B", b)]:
                preceding[label] = dict(
                    last_handoff=next(
                        (h for h in reversed(result["handoffs"]) if h["time"] <= t), None
                    ),
                    last_application=next(
                        (
                            dict(
                                time=c["time"],
                                application_time=c["application_time"],
                                plan_id=c["plan_id"],
                                delta=c["delta"],
                                a_cmd=c["a_cmd"],
                            )
                            for c in reversed(result["controls"])
                            if c["application_time"] <= t + TIME_TOL
                        ),
                        None,
                    ),
                )
            first = dict(
                time=t,
                a_minus_b_state=dx.tolist(),
                a_minus_b_control=du.tolist(),
                preceding_events=preceding,
            )
            break
    launch_a = [(p["release_time"], p["estimated_delay"]) for p in a["plans"]]
    launch_b = [(p["release_time"], p["estimated_delay"]) for p in b["plans"]]
    by_time_b = {round(p["release_time"], 10): p for p in b["plans"]}
    prediction_split = next(
        (
            dict(
                release_time=pa["release_time"],
                a_minus_b=residual(pa["predicted_state"], pb["predicted_state"]).tolist(),
            )
            for pa in a["plans"]
            if (pb := by_time_b.get(round(pa["release_time"], 10))) is not None
            and pa["predicted_state"] != pb["predicted_state"]
        ),
        None,
    )
    return dict(
        coverage=coverage,
        metrics={"A": physical_metrics(a, track, end), "B": physical_metrics(b, track, end)},
        planner_launches_and_estimates_identical=launch_a == launch_b,
        first_forecast_divergence=prediction_split,
        first_divergence=first,
        exact_common_event_count=len(astates.keys() & bstates.keys()),
    )
