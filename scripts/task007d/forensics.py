"""D5 offline record analysis: no forecasting, optimization or plant propagation."""

from dataclasses import fields

import numpy as np
from task007d.diagnostics import TIME_TOL, residual
from task007d.sensitivity import ERROR_TIE, pending_category

from apex.control.trajectory.packet import TrajectoryPacket
from apex.state import STATE_NAMES


def packet_from_record(record):
    values = {f.name: record[f.name] for f in fields(TrajectoryPacket)}
    # JSON loses the second dimension of an empty (0, 4) gain schedule.
    if not len(values["gains"]):
        values["gains"] = np.empty((0, 4))
    return TrajectoryPacket(**values)


def accepted_packets(raw):
    """Reproduce acceptance trimming, not controller execution or new authority."""
    packets = {p["plan_id"]: packet_from_record(p) for p in raw["packets"]}
    first = raw["states"][0]
    timeline = [(first["time"], packets[first["plan_id"]].trim(first["time"]))]
    for handoff in raw["handoffs"]:
        if handoff["accepted"]:
            t, pid = handoff["time"], handoff["plan_id"]
            packet = packets[pid]
            if t < timeline[-1][0] or pid <= timeline[-1][1].plan_id:
                raise ValueError("Nonmonotonic accepted authority")
            if t < max(packet.actual_completion_time, packet.timestamps[0]) - TIME_TOL:
                raise ValueError("Packet accepted before availability")
            timeline.append((t, packet.trim(t)))
    return timeline


def active_at(timeline, time):
    if time < timeline[0][0] - TIME_TOL:
        raise ValueError("No accepted packet at requested time")
    return next(p for t, p in reversed(timeline) if t <= time + TIME_TOL)


def clearance(left_width, right_width, ey):
    left, right = left_width - ey, right_width + ey
    return dict(
        left_clearance=left,
        right_clearance=right,
        clearance=min(left, right),
        boundary="left" if left <= right else "right",
    )


def describe(row, timeline, track, sectors):
    packet = active_at(timeline, row["time"])
    if "plan_id" in row and packet.plan_id != row["plan_id"]:
        raise ValueError("Recorded state disagrees with accepted authority")
    nominal, control, _ = packet.sample(row["time"])
    g = track.sample(row["s_abs"] % track.length)
    return dict(
        **{**row, "plan_id": packet.plan_id},
        sector=next(s["name"] for s in reversed(sectors) if s["start_s_m"] <= g.track_s),
        curvature=g.curvature,
        left_width=g.left_width,
        right_width=g.right_width,
        **clearance(g.left_width, g.right_width, row["e_y"]),
        nominal_ey=float(nominal[5]),
        nominal_epsi=float(nominal[3]),
        nominal_progress=float(nominal[4]),
        nominal_delta=float(control[0]),
        nominal_acceleration=float(control[1]),
        tracking_ey=row["e_y"] - float(nominal[5]),
    )


def interpolate_progress(rows, progress):
    """Linear spatial estimate of continuous position/time, never command or packet ID.

    Exact knots are returned exactly; reject nonmonotonic progress and all extrapolation.
    This is descriptive interpolation, not reconstructed RK4 ground truth.
    """
    s = np.asarray([r["s_abs"] for r in rows])
    t = np.asarray([r["time"] for r in rows])
    if (
        not len(s)
        or not np.isfinite(s).all()
        or not np.isfinite(t).all()
        or not np.isfinite([r["e_y"] for r in rows]).all()
        or np.any(np.diff(s) <= 0)
        or np.any(np.diff(t) <= 0)
    ):
        raise ValueError("Strictly increasing finite progress/time required")
    if not np.isfinite(progress) or not s[0] <= progress <= s[-1]:
        raise ValueError("Progress outside observed coverage")
    j = int(np.searchsorted(s, progress))
    exact = j < len(s) and s[j] == progress
    i = j if exact else j - 1
    fraction = 0.0 if exact else (progress - s[i]) / (s[j] - s[i])
    return dict(
        s_abs=float(progress),
        time=float(t[i] + fraction * (t[j] - t[i])),
        e_y=float(rows[i]["e_y"] + fraction * (rows[j]["e_y"] - rows[i]["e_y"])),
        kind="recorded_knot" if exact else "linear_progress_interpolation",
        bracket_start_time=float(t[i]),
        bracket_end_time=float(t[j]),
    )


def paired_row(a, b):
    """Side-specific identities remain valid even when limiting boundary changes."""
    keys = (
        "time",
        "s_abs",
        "e_y",
        "plan_id",
        "left_width",
        "right_width",
        "boundary",
        "clearance",
        "nominal_ey",
        "tracking_ey",
    )
    row = {host + "_" + k: r[k] for host, r in [("A", a), ("B", b)] for k in keys}
    for side, sign in [("left", -1), ("right", 1)]:
        width = b[side + "_width"] - a[side + "_width"]
        nominal = sign * (b["nominal_ey"] - a["nominal_ey"])
        tracking = sign * (b["tracking_ey"] - a["tracking_ey"])
        delta = b[side + "_clearance"] - a[side + "_clearance"]
        if abs(delta - width - nominal - tracking) > ERROR_TIE:
            raise ValueError("Clearance decomposition failed")
        row.update(
            {
                side + "_width_contribution": width,
                side + "_nominal_contribution": nominal,
                side + "_tracking_contribution": tracking,
                side + "_clearance_B_minus_A": delta,
            }
        )
    row["clearance_B_minus_A"] = b["clearance"] - a["clearance"]
    return row


def comparisons(a, b, timelines, track, sectors):
    start, end = max(a[0]["time"], b[0]["time"]), min(a[-1]["time"], b[-1]["time"])
    bt = {round(r["time"], 10): r for r in b}
    same_time = []
    for ar in a:
        if start <= ar["time"] <= end and (br := bt.get(round(ar["time"], 10))) is not None:
            if abs(ar["time"] - br["time"]) > TIME_TOL:
                raise ValueError("Time match exceeds event tolerance")
            same_time.append(paired_row(ar, br))
    lo, hi = max(a[0]["s_abs"], b[0]["s_abs"]), min(a[-1]["s_abs"], b[-1]["s_abs"])
    if end < start or hi < lo:
        raise ValueError("No common observed coverage")
    knots = sorted({r["s_abs"] for r in a + b if lo <= r["s_abs"] <= hi} | {lo, hi})
    spatial = []
    for s in knots:
        ar, br = [
            describe(interpolate_progress(rows, s), timeline, track, sectors)
            for rows, timeline in [(a, timelines["A"]), (b, timelines["B"])]
        ]
        pair = paired_row(ar, br)
        for host, row in [("A", ar), ("B", br)]:
            for key in ("kind", "bracket_start_time", "bracket_end_time"):
                pair[host + "_" + key] = row[key]
        spatial.append(pair)
    return (
        dict(
            time_start=start,
            time_end=end,
            progress_start=lo,
            progress_end=hi,
            same_time_samples=len(same_time),
            same_progress_knots=len(spatial),
        ),
        same_time,
        spatial,
    )


def audit_nominals(raw, timeline):
    """Match reconstructed active samples to recorded driver references and handoff errors."""
    states = {round(r["time"], 10): r for r in raw["states"]}
    differences = []
    for c in raw["controls"]:
        p = active_at(timeline, c["time"])  # sample time, not delayed application
        if p.plan_id != c["plan_id"]:
            raise ValueError("Command sampled wrong packet")
        x, u, _ = p.sample(c["time"])
        differences.extend(x - [c["reference_" + k] for k in STATE_NAMES])
        differences.extend(u - [c["nominal_delta"], c["nominal_a_cmd"]])
        actual = [states[round(c["time"], 10)][k] for k in STATE_NAMES]
        differences.extend(residual(actual, x) - [c["error_" + k] for k in STATE_NAMES])
    for h in raw["handoffs"]:
        if h["accepted"]:
            p = active_at(timeline, h["time"])
            if p.plan_id != h["plan_id"]:
                raise ValueError("Handoff reconstruction selected wrong packet")
            actual = [states[round(h["time"], 10)][k] for k in STATE_NAMES]
            differences.extend(
                residual(actual, p.sample(h["time"])[0]) - [h["error_" + k] for k in STATE_NAMES]
            )
    maximum = float(max(abs(np.asarray(differences)), default=0))
    if maximum > ERROR_TIE:
        raise ValueError("Nominal reconstruction disagrees with retained references")
    return dict(
        commands=len(raw["controls"]),
        accepted_handoffs=len(timeline) - 1,
        maximum_absolute_reference_or_error_difference=maximum,
    )


def low_latency_tables(scores, regime, host):
    ordered = sorted(scores, key=lambda r: r["release_time"])
    details, phases = [], []
    for number, row in enumerate(ordered, 1):
        for index in (2, 3, 5):
            a, b = [
                None if row["errors"][h] is None else row["errors"][h][index] for h in ("A", "B")
            ]
            delta = None if a is None or b is None else abs(b) - abs(a)
            details.append(
                dict(
                    regime=regime,
                    host=host,
                    release_number=number,
                    plan_id=row["plan_id"],
                    release_time=row["release_time"],
                    target_time=row["target_time"],
                    readiness_minus_target=row["readiness_minus_target"],
                    accepted_handoff_minus_target=row["accepted_handoff_minus_target"],
                    pending_category=pending_category(row),
                    state=STATE_NAMES[index],
                    A_signed=a,
                    B_signed=b,
                    A_absolute=None if a is None else abs(a),
                    B_absolute=None if b is None else abs(b),
                    absolute_increase=delta,
                    outcome="excluded"
                    if delta is None
                    else "worse"
                    if delta > ERROR_TIE
                    else "better"
                    if delta < -ERROR_TIE
                    else "tie",
                )
            )
    for state in ("r", "e_psi", "e_y"):
        all_rows = [r for r in details if r["state"] == state]
        for label, group in [
            ("release_1", all_rows[:1]),
            ("release_2", all_rows[1:2]),
            ("releases_3_19", all_rows[2:]),
        ]:
            paired = [r for r in group if r["outcome"] != "excluded"]
            record = dict(
                regime=regime,
                host=host,
                state=state,
                phase=label,
                releases=len(group),
                comparable=len(paired),
                excluded=len(group) - len(paired),
            )
            for h in ("A", "B"):
                errors = [r[h + "_signed"] for r in paired]
                total = sum(r[h + "_signed"] ** 2 for r in all_rows if r["outcome"] != "excluded")
                record[h + "_rms"] = float(np.sqrt(np.mean(np.square(errors)))) if errors else None
                record[h + "_squared_error_share_percent"] = (
                    100 * sum(e * e for e in errors) / total if total else None
                )
            record.update(
                {k: sum(r["outcome"] == k for r in group) for k in ("better", "worse", "tie")}
            )
            record["maximum_absolute_increase"] = max(
                (r["absolute_increase"] for r in paired), default=None
            )
            phases.append(record)
    return details, phases
