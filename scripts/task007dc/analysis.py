"""Offline C evidence: recorded events only, common coverage and explicit time tolerances."""

import numpy as np

from apex.coordinates.angles import wrap_angle
from apex.state import STATE_NAMES

TOL = 1e-10


def envelope(values):
    x = np.asarray(values, dtype=float)
    return (
        dict(rms=float(np.sqrt(np.mean(x * x))), max_abs=float(np.max(abs(x)))) if x.size else None
    )


def tv(values, angle=False):
    d = np.diff(values)
    return float(np.sum(abs(np.array([wrap_angle(v) for v in d]) if angle else d)))


def delta(a, b, angle_columns=()):
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    for j in angle_columns:
        d[..., j] = np.vectorize(wrap_angle)(d[..., j])
    return d


def paired_rows(a, b, keys, *, time_key="time", angle_columns=(), grid=False):
    # Rounding identifies timestamps within the simulator tolerance; never changes execution.
    aa = {round(r[time_key], 10): r for r in a}
    bb = {round(r[time_key], 10): r for r in b}
    times = sorted(aa.keys() & bb.keys())
    if grid:
        times = [t for t in times if abs(t - round(t / 0.01) * 0.01) <= TOL]
    if not times:
        return dict(count=0, start=None, end=None, metrics=None, first_difference=None)
    av = [[aa[t][k] for k in keys] for t in times]
    bv = [[bb[t][k] for k in keys] for t in times]
    d = delta(av, bv, angle_columns)
    first = next(
        (
            dict(time=t, a_minus_b=row.tolist())
            for t, row in zip(times, d)
            if np.any(abs(row) > 1e-12)
        ),
        None,
    )
    return dict(
        count=len(times),
        start=times[0],
        end=times[-1],
        bitwise_values_equal=av == bv,
        metrics={k: envelope(d[:, j]) for j, k in enumerate(keys)},
        first_difference=first,
    )


def compare(a, b):
    states = paired_rows(a["states"], b["states"], STATE_NAMES, angle_columns=(3,))
    controls = ["requested_delta", "requested_a_cmd", "delta", "a_cmd", "application_time"]
    refs = ["reference_" + k for k in STATE_NAMES]
    plan_keys = ["predicted_state", "predicted_previous_control"]
    plan_metrics = {}
    for key in plan_keys:
        rows = []
        bp = {round(p["release_time"], 10): p for p in b["plans"]}
        first = None
        for p in a["plans"]:
            q = bp.get(round(p["release_time"], 10))
            if q is None:
                continue
            d = delta(p[key], q[key], (3,) if key == "predicted_state" else ())
            rows.append(d)
            if first is None and np.any(abs(d) > 1e-12):
                first = dict(release=p["release_time"], a_minus_b=d.tolist())
        keys = STATE_NAMES if key == "predicted_state" else ["delta", "a_cmd"]
        plan_metrics[key] = dict(
            count=len(rows),
            first_difference=first,
            metrics={k: envelope(np.asarray(rows)[:, j]) for j, k in enumerate(keys)},
        )
    packet_metrics = {}
    bp = {p["plan_id"]: p for p in b["packets"]}
    for key in ["states", "controls", "gains", "curvatures", "timestamps"]:
        diffs, first = [], None
        for p in a["packets"]:
            if p["plan_id"] not in bp:
                continue
            av, bv = np.asarray(p[key]), np.asarray(bp[p["plan_id"]][key])
            if av.shape != bv.shape:
                raise ValueError("Unmatched packet shape")
            d = delta(av, bv, (3,) if key == "states" else ())
            diffs.extend(d.ravel())
            if first is None and np.any(abs(d) > 1e-12):
                first = p["plan_id"]
        packet_metrics[key] = dict(envelope=envelope(diffs), first_plan_above_1e_minus12=first)
    # Only recorded overlap: linear progress interpolation is a derived display/comparison,
    # never used for truth scoring or physical stop gates.
    common = sorted(
        {round(r["time"], 10) for r in a["states"]} & {round(r["time"], 10) for r in b["states"]}
    )
    common = {t for t in common if abs(t - round(t / 0.01) * 0.01) <= TOL}
    sa = np.array(
        [[r[k] for k in STATE_NAMES] for r in a["states"] if round(r["time"], 10) in common]
    )
    sb = np.array(
        [[r[k] for k in STATE_NAMES] for r in b["states"] if round(r["time"], 10) in common]
    )
    lo, hi = max(sa[0, 4], sb[0, 4]), min(sa[-1, 4], sb[-1, 4])
    if np.any(np.diff(sa[:, 4]) <= 0) or np.any(np.diff(sb[:, 4]) <= 0):
        raise ValueError("Progress interpolation requires strictly increasing progress")
    points = np.linspace(lo, hi, 201)
    d = np.column_stack(
        [
            np.interp(points, sa[:, 4], np.unwrap(sa[:, j]) if j == 3 else sa[:, j])
            - np.interp(points, sb[:, 4], np.unwrap(sb[:, j]) if j == 3 else sb[:, j])
            for j in range(6)
        ]
    )
    d[:, 3] = np.array([wrap_angle(v) for v in d[:, 3]])
    ah = [(h["plan_id"], round(h["time"], 10)) for h in a["handoffs"] if h["accepted"]]
    bh = [(h["plan_id"], round(h["time"], 10)) for h in b["handoffs"] if h["accepted"]]
    return dict(
        states=states,
        grid_states=paired_rows(
            a["states"], b["states"], STATE_NAMES, angle_columns=(3,), grid=True
        ),
        controls=paired_rows(a["controls"], b["controls"], controls),
        references=paired_rows(a["controls"], b["controls"], refs, angle_columns=(3,)),
        reserve=paired_rows(a["reserves"], b["reserves"], ["reserve"]),
        plans=plan_metrics,
        packets=packet_metrics,
        release_times_bitwise_equal=[r["time"] for r in a["releases"]]
        == [r["time"] for r in b["releases"]],
        authority_ids=paired_rows(a["states"], b["states"], ["plan_id"]),
        release_times_equal=[round(r["time"], 10) for r in a["releases"]]
        == [round(r["time"], 10) for r in b["releases"]],
        accepted_ids_and_times_equal=ah == bh,
        common_progress=dict(
            start=lo,
            end=hi,
            count=len(points),
            kind="derived linear interpolation from common 10 ms samples",
            metrics={k: envelope(d[:, j]) for j, k in enumerate(STATE_NAMES)},
        ),
    )


def cycles(raw):
    if "fixed_handoffs" in raw:
        return raw["fixed_handoffs"]
    rows = []
    for p in raw["plans"][1:]:
        h = next((h for h in raw["handoffs"] if h["plan_id"] == p["plan_id"]), None)
        accepted = h is not None and h["accepted"]
        ready = p["completion_time"] if p.get("completed") else None
        accept = h["time"] if accepted else None
        packet = next((x for x in raw["packets"] if x["plan_id"] == p["plan_id"]), None)
        first = next((c["time"] for c in raw["controls"] if c["plan_id"] == p["plan_id"]), None)
        rows.append(
            dict(
                plan_id=p["plan_id"],
                t_release=p["release_time"],
                t_ready=ready,
                valid_from=None,
                forecast_target=p["predicted_completion_time"],
                t_accept=accept,
                first_TVLQR_use=first,
                expiry=packet["horizon_end_time"] if packet else None,
                preparation_duration=p["physical_delay"],
                wait_duration=accept - ready if accepted else None,
                deadline_margin=None,
                status="accepted" if accepted else ("rejected" if h else "pending"),
                packet_age=accept - p["release_time"] if accepted else None,
                reserve_at_acceptance=h.get("reserve") if accepted else None,
                consecutive_misses=None,
                miss_time=None,
                late_discard_time=None,
            )
        )
    return rows


def extra(raw, segments, track, parameters):
    states, commands = raw["states"], raw["controls"]
    geometry = [track.sample(r["s_abs"] % track.length) for r in states]
    left = [g.left_width - r["e_y"] for r, g in zip(states, geometry)]
    right = [g.right_width + r["e_y"] for r, g in zip(states, geometry)]
    side = "left" if min(left) < min(right) else "right"
    clear = np.minimum(left, right)
    nominal = [
        r["reference_e_psi"] + track.sample(r["reference_s_abs"] % track.length).heading
        for r in commands
    ]
    # Include prepositioned startup control at t=0 for actual application rate accounting.
    times = np.array([0.0] + [r["application_time"] for r in commands])
    steer = np.array([states[0]["delta"]] + [r["delta"] for r in commands])
    dt = np.diff(times)
    rates = np.diff(steer)[dt > TOL] / dt[dt > TOL]
    significant = np.sign(rates[abs(rates) > 1e-10])
    ready = [p["completion_time"] for p in raw["plans"][1:] if p.get("completed")]
    accepted = [h["time"] for h in raw["handoffs"] if h["accepted"]]
    apps = [r["application_time"] for r in commands]
    ends = [s["end"] for s in segments]

    def hits(events):
        return sum(any(abs(t - e) <= TOL for e in ends) for t in events)

    cy = cycles(raw)
    return dict(
        limiting_boundary=side,
        clearance_time=states[int(np.argmin(clear))]["time"],
        minimum_left_clearance=min(left),
        minimum_right_clearance=min(right),
        max_front_utilization=max(r["front_utilization"] for r in states),
        max_rear_utilization=max(r["rear_utilization"] for r in states),
        max_abs_beta=float(max(abs(np.arctan2(r["vy"], r["vx"])) for r in states)),
        steering_utilization=max(abs(r["delta"]) for r in states)
        / parameters.maximum_steering_angle,
        steering_rate_utilization=float(max(abs(rates))),  # existing limit = 1 rad/s
        steering_rate_max_abs_rad_s=float(max(abs(rates))),
        steering_rate_rms_rad_s=float(np.sqrt(np.mean(rates * rates))),
        rate_reversals=int(np.sum(significant[1:] != significant[:-1])),
        rate_limit_occupancy=float(np.mean(abs(rates) >= 1 - 1e-9)),
        minimum_frenet_denominator=min(
            1 - g.curvature * r["e_y"] for r, g in zip(states, geometry)
        ),
        nominal_heading_tv=tv(nominal, True),
        nominal_steering_tv=tv([r["nominal_delta"] for r in commands]),
        nominal_acceleration_tv=tv([r["nominal_a_cmd"] for r in commands]),
        applied_acceleration_tv=tv([r["a_cmd"] for r in states]),
        rk4=dict(
            count=len(segments),
            minimum_dt=min(s["dt"] for s in segments),
            maximum_dt=max(s["dt"] for s in segments),
            non_grid_readiness=sum(abs(t - round(t / 0.01) * 0.01) > TOL for t in ready),
            readiness_boundaries=hits(ready),
            handoff_boundaries=hits(accepted),
            application_boundaries=hits(apps),
            readiness_only_boundaries=sum(
                any(abs(t - e) <= TOL for e in ends)
                and all(abs(t - e) > TOL for e in accepted + apps)
                and abs(t - round(t / 0.005) * 0.005) > TOL
                for t in ready
            ),
        ),
        fixed_deadline_misses=sum(r["status"] == "missed" for r in cy),
        accepted_latency_seconds=[r["packet_age"] for r in cy if r["t_accept"] is not None],
        first_use_latency_seconds=[
            r["first_TVLQR_use"] - r["t_release"] for r in cy if r["first_TVLQR_use"] is not None
        ],
        wait_seconds=[r["wait_duration"] for r in cy if r["wait_duration"] is not None],
        censored_cycles=sum(r["status"] == "pending" for r in cy),
        clearances=[
            dict(time=r["time"], left=lc, right=rc) for r, lc, rc in zip(states, left, right)
        ],
    )
