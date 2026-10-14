"""CX timing and consequence metrics from saved histories, without forecast feedback."""

import math

import numpy as np
from task007d.forensics import accepted_packets, active_at
from task007dc.analysis import cycles, delta, envelope, tv

from apex.coordinates.angles import wrap_angle
from apex.state import STATE_NAMES

TOL = 1e-10
ENGINEERING = dict(
    vx=0.001, vy=0.001, r=0.001, e_psi=0.0001, s_abs=0.001, e_y=0.001, delta=0.0001, a_cmd=0.001
)


def distribution(values):
    x = np.asarray([v for v in values if v is not None], dtype=float)
    if not len(x):
        return dict(n=0, mean=None, median=None, p95=None, p99=None, maximum=None, minimum=None)
    return dict(
        n=len(x),
        mean=float(np.mean(x)),
        median=float(np.median(x)),
        p95=float(np.quantile(x, 0.95)),
        p99=float(np.quantile(x, 0.99)) if len(x) >= 100 else None,
        maximum=float(np.max(x)),
        minimum=float(np.min(x)),
    )


def wilson(hits, total):
    if total == 0:
        return None
    z = 1.959963984540054
    p = hits / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return [max(0.0, center - half), min(1.0, center + half)]


def cycle_rows(raw):
    plans = {p["plan_id"]: p for p in raw["plans"]}
    out = []
    for c in cycles(raw):
        p = plans[c["plan_id"]]
        ready = c["t_ready"]
        row = dict(c)
        row.update(
            preparation_start=p["release_time"],
            preparation_finish=ready,
            measured_preparation_duration=p["planner_total_time"],
            measured_solver_duration=p.get("solve_time"),
            prediction_duration=p.get("prediction_time"),
            gain_duration=p.get("gain_time"),
            forecast_target=p["predicted_completion_time"],
            runtime_completed=bool(p.get("completed")),
            active_reserve_at_completion=p.get("active_reserve_at_completion"),
        )
        # Physical completion may be outside coverage even though host preparation returned.
        row["preparation_finish_censored"] = ready is None
        row["accepted_latency"] = None if c["t_accept"] is None else c["t_accept"] - c["t_release"]
        out.append(row)
    return out


def timing_summary(rows, fixed):
    resolved = [r for r in rows if r["status"] in ("accepted", "missed", "rejected")]
    misses = sum(r["status"] == "missed" for r in resolved)
    # Ready on time and accepted are separate: a ready packet may fail continuity/validity.
    hits = (
        sum(r["t_ready"] is not None and r["t_ready"] <= r["valid_from"] + TOL for r in resolved)
        if fixed
        else None
    )
    return dict(
        attempts=len(rows),
        resolved=len(resolved),
        censored=len(rows) - len(resolved),
        accepted=sum(r["status"] == "accepted" for r in rows),
        rejected=sum(r["status"] == "rejected" for r in rows),
        hits=hits,
        misses=misses if fixed else None,
        miss_fraction=misses / len(resolved) if fixed and resolved else None,
        miss_fraction_wilson95=wilson(misses, len(resolved)) if fixed else None,
        maximum_consecutive_misses=max((r.get("consecutive_misses") or 0 for r in rows), default=0),
        preparation=distribution([r["measured_preparation_duration"] for r in rows]),
        deadline_margin=distribution([r["deadline_margin"] for r in rows]),
        wait=distribution([r["wait_duration"] for r in rows]),
        accepted_latency=distribution([r["accepted_latency"] for r in rows]),
    )


def paired_samples(a, b):
    """Recorded common-grid state/control/reserve data; no interpolation of authority."""
    maps = [{round(r["time"], 10): r for r in raw["states"]} for raw in (a, b)]
    reserves = [{round(r["time"], 10): r for r in raw["reserves"]} for raw in (a, b)]
    rows = []
    keys = (*STATE_NAMES, "delta", "a_cmd")
    for t in sorted(maps[0].keys() & maps[1].keys()):
        if abs(t - round(t / 0.01) * 0.01) > TOL:
            continue
        x, y = maps[0][t], maps[1][t]
        d = delta([x[k] for k in keys], [y[k] for k in keys], (3,))
        rows.append(
            dict(
                time=t,
                progress_a=x["s_abs"],
                progress_b=y["s_abs"],
                plan_id_a=x["plan_id"],
                plan_id_b=y["plan_id"],
                reserve_a=reserves[0][t]["reserve"],
                reserve_b=reserves[1][t]["reserve"],
                **{k: float(v) for k, v in zip(keys, d)},
            )
        )
    if not rows:
        raise ValueError("No common observed grid coverage")
    summary = {
        k: dict(
            **envelope([r[k] for r in rows]),
            first_numerical=next((r["time"] for r in rows if abs(r[k]) > 1e-12), None),
            first_engineering=next((r["time"] for r in rows if abs(r[k]) > ENGINEERING[k]), None),
        )
        for k in keys
    }
    return rows, summary


def miss_consequences(raw, track, sectors):
    timeline = accepted_packets(raw)
    out = []
    for cycle in cycle_rows(raw):
        if cycle["status"] != "missed":
            continue
        t = cycle["miss_time"]
        state = next((s for s in raw["states"] if abs(s["time"] - t) <= TOL), None)
        if state is None:
            raise ValueError("Missing recorded deadline state")
        packet = active_at(timeline, t)
        nominal, _, _ = packet.sample(t)
        err = delta([state[k] for k in STATE_NAMES], nominal, (3,))
        g = track.sample(state["s_abs"] % track.length)
        recovery = next(
            (h["time"] for h in raw["handoffs"] if h["accepted"] and h["time"] > t + TOL), None
        )
        end = raw["states"][-1]["time"] if recovery is None else recovery
        authority_start = next(at for at, p in timeline if p.plan_id == packet.plan_id)
        window = [s for s in raw["states"] if t - TOL <= s["time"] <= end + TOL]
        reserve = [r["reserve"] for r in raw["reserves"] if t - TOL <= r["time"] <= end + TOL]
        plans = [p for p in raw["plans"] if t - TOL <= p["release_time"] <= end + TOL]
        clearance = min(
            min(
                (gg := track.sample(s["s_abs"] % track.length)).left_width - s["e_y"],
                gg.right_width + s["e_y"],
            )
            for s in window
        )
        invalid = any(s["boundary_violation"] for s in window)
        # Descriptive categories expose their thresholds; no fabricated no-miss counterfactual.
        category = (
            "physically_invalid"
            if invalid
            else (
                "reserve_threatening"
                if min(reserve) < 0.2
                else "recovered_without_observed_validity_or_reserve_violation"
                if recovery is not None
                else "recovery_censored"
            )
        )
        out.append(
            dict(
                plan_id=cycle["plan_id"],
                time=t,
                late_discard_time=cycle["late_discard_time"],
                recovery_time=recovery,
                recovery_censored=recovery is None,
                recovery_latency=None if recovery is None else recovery - t,
                old_authority_start=authority_start,
                authority_gap=None if recovery is None else recovery - authority_start,
                derived_old_reserve_at_recovery=(
                    None if recovery is None else packet.horizon_end_time - recovery
                ),
                sector=next(s["name"] for s in reversed(sectors) if s["start_s_m"] <= g.track_s),
                progress=state["s_abs"],
                speed=state["vx"],
                curvature=g.curvature,
                front_utilization=state["front_utilization"],
                rear_utilization=state["rear_utilization"],
                beta=math.atan2(state["vy"], state["vx"]),
                old_plan_id=packet.plan_id,
                old_packet_age=t - packet.planner_sample_time,
                reserve_at_miss=packet.horizon_end_time - t,
                minimum_reserve_to_recovery=min(reserve),
                minimum_clearance_to_recovery=clearance,
                steering_tv_to_recovery=tv([s["delta"] for s in window]),
                max_slack_of_releases_in_window=max(
                    (p.get("max_slack") or 0 for p in plans), default=None
                ),
                **{"error_" + k: float(v) for k, v in zip(STATE_NAMES, err)},
                classification=category,
            )
        )
    return out


def quality(raw, track, reference, end=1.99):
    """Equal recorded physical-grid coverage, wrapped state errors; separate extrema elsewhere."""
    states = [
        r
        for r in raw["states"]
        if r["time"] <= end + TOL and abs(r["time"] - round(r["time"] / 0.01) * 0.01) <= TOL
    ]
    if len(states) != round(end / 0.01) + 1:
        return dict(complete_common_coverage=False, end=states[-1]["time"] if states else None)
    controls = [
        c for c in raw["controls"] if c["time"] <= end + TOL and c["application_time"] <= end + TOL
    ]
    timeline = accepted_packets(raw)
    errors = []
    planned_delta = []
    planned_heading = []
    actual_heading = []
    planning_speed = []
    adaptation = []
    for s in states:
        nom, u, _ = active_at(timeline, s["time"]).sample(s["time"])
        errors.append(delta([s[k] for k in STATE_NAMES], nom, (3,)))
        planned_delta.append(u[0])
        planned_heading.append(nom[3] + track.sample(nom[4] % track.length).heading)
        actual_heading.append(s["e_psi"] + track.sample(s["s_abs"] % track.length).heading)
        planning_speed.append(s["vx"] - reference.sample(s["s_abs"])["v_ref_mps"])
        planning = reference.sample(float(nom[4]))
        adaptation.append(
            [
                nom[0] - planning["v_ref_mps"],
                wrap_angle(nom[3] - planning["e_psi_ref_rad"]),
                nom[5] - planning["e_y_ref_m"],
            ]
        )
    times = np.array([0.0] + [c["application_time"] for c in controls])
    steering = np.array([raw["states"][0]["delta"]] + [c["delta"] for c in controls])
    dt = np.diff(times)
    rates = np.diff(steering)[dt > TOL] / dt[dt > TOL]
    signs = np.sign(rates[abs(rates) > 1e-10])
    nonzero = rates[abs(rates) > 1e-10]
    reversals = np.where(signs[1:] != signs[:-1])[0]
    errors = np.asarray(errors)
    return dict(
        complete_common_coverage=True,
        start=0.0,
        end=end,
        samples=len(states),
        tracking={k: envelope(errors[:, j]) for j, k in enumerate(STATE_NAMES)},
        planned_heading_tv=tv(planned_heading, True),
        actual_heading_tv=tv(actual_heading, True),
        planned_steering_tv=tv(planned_delta),
        applied_steering_tv=tv(steering),
        acceleration_tv=tv([s["a_cmd"] for s in states]),
        rate_reversals=len(reversals),
        reversal_max_magnitude=float(
            max((abs(nonzero[j + 1] - nonzero[j]) for j in reversals), default=0)
        ),
        steering_rate_max_abs=float(max(abs(rates))),
        steering_rate_rms=float(np.sqrt(np.mean(rates**2))),
        steering_rate_limit_time=float(np.sum(dt[dt > TOL][abs(rates) >= 1 - 1e-9])),
        steering_rate_limit_fraction=float(np.sum(dt[dt > TOL][abs(rates) >= 1 - 1e-9]) / end),
        progress_gain=states[-1]["s_abs"] - states[0]["s_abs"],
        progress_rate=(states[-1]["s_abs"] - states[0]["s_abs"]) / end,
        planning_speed_error=envelope(planning_speed),
        planning_to_apex={
            k: envelope(np.asarray(adaptation)[:, j]) for j, k in enumerate(["vx", "e_psi", "e_y"])
        },
    )
