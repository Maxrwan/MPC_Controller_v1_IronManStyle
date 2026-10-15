"""Native endpoint coverage, derived crossing brackets and preserved command provenance."""

import numpy as np

from apex.state import STATE_NAMES

TOL = 1e-10  # Existing simulator event-comparison tolerance, not a physical tolerance.


def native_states(raw, segments, plant):
    """Append the actual final RK4 endpoint, never an interpolated seam state."""
    rows = [dict(r, sample_kind="runtime_event") for r in raw["states"]]
    if not segments:
        return rows
    for i, seg in enumerate(segments):
        if seg["dt"] <= 0 or abs(seg["end"] - seg["start"] - seg["dt"]) > TOL:
            raise ValueError("Invalid RK4 segment timing")
        if i and (
            abs(seg["start"] - segments[i - 1]["end"]) > TOL
            or seg["state_before"] != segments[i - 1]["state_after"]
        ):
            raise ValueError("Discontinuous physical segments")
    final = segments[-1]
    if not rows:
        raise ValueError("Missing initial physical state")
    if abs(final["end"] - raw["end_time"]) > TOL:
        raise ValueError("Terminal physical coverage mismatch")
    if rows[-1]["time"] < final["end"] - TOL:
        x, u = final["state_after"], final["control"]
        d = plant.diagnostics(x, u)
        g = plant.track.sample(x[4])
        rows.append(
            dict(
                time=final["end"],
                **dict(zip(STATE_NAMES, x)),
                delta=u[0],
                a_cmd=u[1],
                plan_id=rows[-1]["plan_id"],
                mode=rows[-1]["mode"],
                front_utilization=d.front_combined_utilization,
                rear_utilization=d.rear_combined_utilization,
                boundary_violation=x[5] > g.left_width or x[5] < -g.right_width,
                sample_kind="recorded_RK4_endpoint_before_next_events",
            )
        )
    elif not np.array_equal([rows[-1][k] for k in STATE_NAMES], final["state_after"]):
        raise ValueError("Terminal state disagrees with recorded RK4")
    return rows


def crossings(segments, progress_points):
    """Linear-in-progress crossing time with native brackets, not ground-truth seam samples."""
    if not segments:
        return []
    before = np.array([s["state_before"][4] for s in segments])
    after = np.array([s["state_after"][4] for s in segments])
    if np.any(after <= before):
        raise ValueError("Crossing reconstruction requires forward progress")
    out = []
    for value in sorted(set(progress_points)):
        i = int(np.searchsorted(after, value))
        if i >= len(segments) or not before[i] < value <= after[i]:
            continue
        seg = segments[i]
        out.append(
            dict(
                s_abs=value,
                time=seg["start"] + seg["dt"] * (value - before[i]) / (after[i] - before[i]),
                bracket_start=seg["start"],
                bracket_end=seg["end"],
                segment_id=i,
                method="linear_progress_in_recorded_RK4_bracket",
            )
        )
    return out


def lap_coverage(raw, segments, length):
    if not segments:
        return dict(crossings=[], complete_laps=0, windows=[], crossing_count=0)
    start = segments[0]["state_before"][4]
    end = segments[-1]["state_after"][4]
    points = [k * length for k in range(int(start // length) + 1, int(end // length) + 1)]
    found = crossings(segments, points)
    prior_time, prior_s = 0.0, start
    windows = []
    for i, row in enumerate(found):
        complete = abs(prior_s / length - round(prior_s / length)) <= TOL
        windows.append(
            dict(
                kind="lap",
                index=i,
                start=prior_time,
                end=row["time"],
                start_s=prior_s,
                end_s=row["s_abs"],
                complete=complete,
                status="complete" if complete else "initial_partial",
            )
        )
        prior_time, prior_s = row["time"], row["s_abs"]
    if raw["stop_reason"] != "target_laps" and end > prior_s + TOL:
        windows.append(
            dict(
                kind="lap",
                index=len(windows),
                start=prior_time,
                end=raw["end_time"],
                start_s=prior_s,
                end_s=end,
                complete=False,
                status="censored_partial",
            )
        )
    return dict(
        crossings=found,
        crossing_count=len(found),
        complete_laps=sum(w["complete"] for w in windows),
        windows=windows,
    )


def sector_windows(raw, segments, length, sectors):
    if not segments:
        return []
    lo, hi = segments[0]["state_before"][4], segments[-1]["state_after"][4]
    points = [
        lap * length + sector["start_s_m"]
        for lap in range(int(lo // length), int(hi // length) + 2)
        for sector in sectors
    ]
    borders = [dict(s_abs=lo, time=0.0, partial=True)]
    borders += [dict(r, partial=False) for r in crossings(segments, points)]
    # The integration endpoint can be slightly past the final seam; keep that tail explicit.
    if hi > borders[-1]["s_abs"] + TOL:
        borders.append(dict(s_abs=hi, time=raw["end_time"], partial=True))
    out = []
    for a, b in zip(borders, borders[1:]):
        mid = (a["s_abs"] + b["s_abs"]) / 2
        sector = next(s for s in reversed(sectors) if s["start_s_m"] <= mid % length)
        out.append(
            dict(
                kind="sector",
                index=len(out),
                lap_index=int(mid // length),
                sector=sector["name"],
                start=a["time"],
                end=b["time"],
                start_s=a["s_abs"],
                end_s=b["s_abs"],
                complete=not a["partial"] and not b["partial"],
                status="complete" if not a["partial"] and not b["partial"] else "partial",
            )
        )
    return out


def command_sources(states, controls):
    """Source packet of the held command, independent of current high-level authority."""
    apps = np.array([c["application_time"] for c in controls])
    if len(apps) and np.any(np.diff(apps) < -TOL):
        raise ValueError("Inverted command application history")
    return [
        controls[i]["plan_id"]
        if (i := np.searchsorted(apps, r["time"] + TOL, side="right") - 1) >= 0
        else 0
        for r in states
    ]
