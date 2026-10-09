"""Offline matched forecasts and target scoring. Physical history is scoring-only."""

import numpy as np

from apex.coordinates.angles import wrap_angle
from apex.state import STATE_NAMES, state_vector

TIME_TOL = 1e-10  # Existing physical-event tolerance, never an inserted event.


def residual(prediction, truth):
    error = np.asarray(prediction) - np.asarray(truth)
    error[3] = wrap_angle(error[3])
    return error


def forecasts(release, predictor):
    """No plant, result log, timing trace, solver or future packet argument exists here."""
    outcomes = {}
    for architecture in ("A", "B"):
        buffer, tracker = release.forecast_inputs()
        try:
            kwargs = {} if architecture == "A" else {"committed_prefix": release.prefix}
            state, control = predictor.predict(
                release.state,
                release.prefix.release_time,
                release.estimated_delay,
                buffer,
                tracker,
                **kwargs,
            )
            outcomes[architecture] = dict(
                state=state.tolist(), control=control.tolist(), failure=None
            )
        except (ValueError, np.linalg.LinAlgError) as error:
            outcomes[architecture] = dict(state=None, control=None, failure=str(error))
    return outcomes


def target_state(states, target, plant):
    """Use a recorded event, or one partial RK4 step under the recorded held input.

    Caller supplies an independent plant with the same model/configuration. Never
    interpolate state components or split the *actual* integration. Coverage ends at
    the last recorded event, not the runner's possibly later end_time.
    """
    times = np.asarray([row["time"] for row in states])
    missing = dict(state=None, kind="missing_coverage")
    if not len(times) or target < times[0] - TIME_TOL or target > times[-1] + TIME_TOL:
        return missing
    if np.any(np.diff(times) <= 0) or not np.isfinite(target):
        raise ValueError("Finite target and strictly increasing recorded events required")
    exact = np.flatnonzero(abs(times - target) <= TIME_TOL)
    if len(exact):
        row = states[exact[0]]
        return dict(
            state=[row[k] for k in STATE_NAMES],
            kind="recorded_event",
            sampled_time=row["time"],
            target_offset=row["time"] - target,
        )
    i = int(np.searchsorted(times, target)) - 1
    left, right = states[i : i + 2]
    x = state_vector([left[k] for k in STATE_NAMES])
    u = np.asarray([left["delta"], left["a_cmd"]])
    h = float(target - times[i])
    try:
        full = plant.step(x, u, float(times[i + 1] - times[i]))
        closure = residual(full, [right[k] for k in STATE_NAMES])
        # Round-trip replay should differ only by float arithmetic, not physical jumps.
        if np.max(abs(closure)) > 1e-10:
            return dict(
                state=None,
                kind="reconstruction_discontinuity",
                interval_closure_error=closure.tolist(),
            )
        partial = plant.step(x, u, h)
        two_half = plant.step(plant.step(x, u, h / 2), u, h / 2)
        return dict(
            state=partial.tolist(),
            kind="reconstructed_rk4",
            bracket=[float(times[i]), float(times[i + 1])],
            interval_closure_error=closure.tolist(),
            step_doubling_difference=residual(partial, two_half).tolist(),
        )
    except ValueError as error:
        return dict(state=None, kind="reconstruction_failed", failure=str(error))


def score(release, alternatives, result, plant):
    target = release.prefix.release_time + release.estimated_delay
    truth = target_state(result["states"], target, plant)
    plan = next(p for p in result["plans"] if p["plan_id"] == release.plan_id)
    handoffs = [h for h in result["handoffs"] if h["plan_id"] == release.plan_id]
    accepted = next((h for h in handoffs if h["accepted"]), None)
    return dict(
        plan_id=release.plan_id,
        release_time=release.prefix.release_time,
        target_time=target,
        active_plan_id=None if release.packet is None else release.packet.plan_id,
        pending=release.prefix.pending_control is not None,
        pending_application_time=release.prefix.pending_application_time,
        truth=truth,
        forecasts=alternatives,
        errors={
            a: (
                None
                if f["state"] is None or truth["state"] is None
                else residual(f["state"], truth["state"]).tolist()
            )
            for a, f in alternatives.items()
        },
        # Readiness must actually have been processed, not merely scheduled at launch.
        readiness_minus_target=(
            plan["completion_time"] - target if plan.get("completed") else None
        ),
        scheduled_readiness_minus_target=plan["completion_time"] - target,
        accepted_handoff_minus_target=None if accepted is None else accepted["time"] - target,
        handoffs=handoffs,
    )


def accuracy(rows):
    paired = [r for r in rows if all(r["errors"][a] is not None for a in ("A", "B"))]
    metrics = {}
    for a in ("A", "B"):
        errors = np.asarray([r["errors"][a] for r in paired]).reshape(-1, 6)
        metrics[a] = (
            {
                k: dict(
                    mean_signed=float(np.mean(errors[:, i])),
                    rms=float(np.sqrt(np.mean(errors[:, i] ** 2))),
                    max_abs=float(np.max(abs(errors[:, i]))),
                    # A percentile from fewer than 20 releases is essentially an extreme.
                    p95_abs=float(np.percentile(abs(errors[:, i]), 95))
                    if len(paired) >= 20
                    else None,
                )
                for i, k in enumerate(STATE_NAMES)
            }
            if len(paired)
            else {}
        )
    improvement = {
        k: (
            100 * (1 - metrics["B"][k]["rms"] / metrics["A"][k]["rms"])
            if metrics["A"][k]["rms"] > 0
            else None
        )
        for k in metrics["A"]
    }
    return dict(
        releases=len(rows),
        comparable=len(paired),
        pending=sum(r["pending"] for r in paired),
        excluded=len(rows) - len(paired),
        forecast_failures={
            a: sum(r["forecasts"][a]["failure"] is not None for r in rows) for a in ("A", "B")
        },
        missing_targets=sum(r["truth"]["state"] is None for r in rows),
        per_state=metrics,
        rms_improvement_percent=improvement,
    )


def common_coverage(a, b):
    if not a["states"] or not b["states"]:
        return dict(start=None, end=None, unequal=True)
    start = max(a["states"][0]["time"], b["states"][0]["time"])
    end = min(a["states"][-1]["time"], b["states"][-1]["time"])
    return dict(
        start=start,
        end=end if end >= start else None,
        unequal=abs(a["states"][-1]["time"] - b["states"][-1]["time"]) > TIME_TOL,
    )
