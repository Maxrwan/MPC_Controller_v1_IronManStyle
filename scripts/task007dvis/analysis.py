"""Lap-aware scientific gates and native, explicitly bounded visual-validation metrics."""

import numpy as np
from task007b.metrics import distribution, local_tracking_error, planning_deviation
from task007c.metrics import steering_activity, variation
from task007d.forensics import accepted_packets, active_at
from task007d.metrics import chronology, physical_metrics, stop_reasons
from task007dcx.analysis import cycle_rows, timing_summary

from apex.coordinates.angles import wrap_angle
from apex.state import STATE_NAMES
from task007dvis.coverage import TOL, command_sources, lap_coverage, native_states, sector_windows


def gates(raw, states, segments, track, case, matches, threads):
    covered = dict(raw, states=states)
    physical = physical_metrics(covered, track)
    issues = chronology(raw)
    runtime = raw["plans"][1:]
    for a, b in zip(runtime, runtime[1:]):
        if a["completion_time"] > b["release_time"] + TOL:
            issues.append(dict(kind="overlapping_preparations", plan_id=b["plan_id"]))
    for c in raw.get("fixed_handoffs", []):
        if c["t_accept"] is not None and abs(c["t_accept"] - c["valid_from"]) > TOL:
            issues.append(dict(kind="fixed_acceptance_timestamp", plan_id=c["plan_id"]))
        if c["status"] == "missed" and any(
            h["accepted"] and h["plan_id"] == c["plan_id"] for h in raw["handoffs"]
        ):
            issues.append(dict(kind="late_packet_authority", plan_id=c["plan_id"]))
    coverage = lap_coverage(raw, segments, track.length)
    expected = (
        raw["stop_reason"] == "duration"
        if case.phase == "parity"
        else (
            raw["stop_reason"] == "target_laps"
            and coverage["crossing_count"] == 2
            and coverage["complete_laps"] >= 1
        )
    )
    # Adapt only the expected termination label; preserve every old physical/solver check.
    gate_input = dict(covered, stop_reason="duration" if expected else raw["stop_reason"])
    reasons = stop_reasons(gate_input, physical, issues)
    if not expected:
        reasons.append("incomplete_requested_coverage")
    if coverage["crossing_count"] != len(raw["lap_times"]):
        reasons.append("lap_count_mismatch")
    elif coverage["crossings"] and not np.allclose(
        np.cumsum(raw["lap_times"]), [r["time"] for r in coverage["crossings"]], atol=TOL, rtol=0
    ):
        reasons.append("lap_crossing_timestamp_mismatch")
    if physical.get("minimum_reserve", 0) <= 0:
        reasons.append("reserve_exhaustion")
    if not matches or not all(matches):
        reasons.append("release_context_A_forecast_mismatch")
    if sorted(set(threads)) != [1]:
        reasons.append("native_thread_policy")
    return dict(physical=physical, coverage=coverage, chronology_issues=issues, stop_gate=reasons)


def enrich(raw, states, track, reference):
    """Sample only already accepted packet authority at native physical timestamps."""
    timeline = accepted_packets(raw)
    sources = command_sources(states, raw["controls"])
    rows = []
    for row, source in zip(states, sources):
        x = np.array([row[k] for k in STATE_NAMES])
        packet = active_at(timeline, row["time"])
        g = track.sample(x[4])
        result = dict(
            row,
            applied_source_plan_id=source,
            x_world=g.x - x[5] * np.sin(g.heading),
            y_world=g.y + x[5] * np.cos(g.heading),
            heading_world=g.heading + x[3],
            beta=float(np.arctan2(x[1], x[0])),
            left_clearance=g.left_width - x[5],
            right_clearance=g.right_width + x[5],
            clearance=min(g.left_width - x[5], g.right_width + x[5]),
            frenet_denominator=1 - g.curvature * x[5],
            packet_age=row["time"] - packet.planner_sample_time,
            reserve=packet.horizon_end_time - row["time"],
        )
        planning, deviation = planning_deviation(x.reshape(1, 6), reference)
        result.update({"planning_" + k: float(v) for k, v in zip(STATE_NAMES, planning[0])})
        result.update({"planning_error_" + k: float(v) for k, v in zip(STATE_NAMES, deviation[0])})
        pg = track.sample(planning[0, 4])
        result.update(
            planning_x=pg.x - planning[0, 5] * np.sin(pg.heading),
            planning_y=pg.y + planning[0, 5] * np.cos(pg.heading),
        )
        try:
            nom, u, _ = packet.sample(row["time"])
            err = local_tracking_error(x.reshape(1, 6), nom.reshape(1, 6))[0]
            _, adapt = planning_deviation(nom.reshape(1, 6), reference)
            ng = track.sample(nom[4])
            result.update(
                reference_status="available",
                nominal_delta=float(u[0]),
                nominal_a_cmd=float(u[1]),
                reference_heading_world=ng.heading + nom[3],
                reference_x=ng.x - nom[5] * np.sin(ng.heading),
                reference_y=ng.y + nom[5] * np.cos(ng.heading),
            )
            for prefix, values in [("reference_", nom), ("error_", err), ("adaptation_", adapt[0])]:
                result.update({prefix + k: float(v) for k, v in zip(STATE_NAMES, values)})
        except ValueError:
            result.update(reference_status="unavailable_or_exhausted")
            for prefix in ["reference_", "error_", "adaptation_"]:
                result.update({prefix + k: None for k in STATE_NAMES})
        rows.append(result)
    return rows


def window_metrics(rows, raw, window):
    sample = [r for r in rows if window["start"] - TOL <= r["time"] <= window["end"] + TOL]
    result = dict(
        window,
        samples=len(sample),
        timing_method="derived_crossing_times",
        metric_sampling="native_samples; left-held error weighting; no extrapolation",
    )
    if len(sample) < 2:
        return dict(result, metric_status="insufficient_samples")
    times = np.array([r["time"] for r in sample])
    weights = np.r_[np.diff(times), 0.0]
    result.update(
        metric_status="available",
        sampled_start=times[0],
        sampled_end=times[-1],
        duration=window["end"] - window["start"],
        progress_rate=(window["end_s"] - window["start_s"]) / (window["end"] - window["start"]),
        minimum_clearance=min(r["clearance"] for r in sample),
        minimum_reserve=min(r["reserve"] for r in sample),
        maximum_packet_age=max(r["packet_age"] for r in sample),
        max_front_utilization=max(r["front_utilization"] for r in sample),
        max_rear_utilization=max(r["rear_utilization"] for r in sample),
        max_abs_beta=max(abs(r["beta"]) for r in sample),
        min_frenet_denominator=min(r["frenet_denominator"] for r in sample),
        boundary_samples=sum(r["boundary_violation"] for r in sample),
    )
    for label, field in [
        ("tracking", "error_"),
        ("planning_vehicle", "planning_error_"),
        ("planning_apex", "adaptation_"),
    ]:
        result[label] = {
            k: distribution(
                [r[field + k] if r[field + k] is not None else np.nan for r in sample], weights
            )
            for k in STATE_NAMES
        }
    for field in [
        "delta",
        "a_cmd",
        "e_psi",
        "heading_world",
        "nominal_delta",
        "nominal_a_cmd",
        "reference_e_psi",
        "reference_heading_world",
    ]:
        values = [r.get(field) for r in sample]
        result[field + "_variation"] = (
            None
            if any(v is None for v in values)
            else variation(values, angle="psi" in field or "heading" in field)
        )
    # Actual actuator rates use actual application intervals, not resampled state differences.
    apps = [dict(time=0.0, delta=rows[0]["delta"], a_cmd=rows[0]["a_cmd"])] + [
        dict(c, time=c["application_time"]) for c in raw["controls"]
    ]
    # Keep a single value per coincident application timestamp, retaining last applied value.
    apps = list({r["time"]: r for r in apps}.values())
    selected = [c for c in apps if window["start"] - TOL <= c["time"] <= window["end"] + TOL]
    result["actuator_activity"] = (
        steering_activity([c["delta"] for c in selected], [c["time"] for c in selected])
        if len(selected) >= 2
        else None
    )
    plans = [p for p in raw["plans"] if window["start"] <= p["release_time"] <= window["end"]]
    result["max_predicted_slack"] = max((p.get("max_slack") or 0 for p in plans), default=None)
    return result


def analyze(raw, segments, plant, reference, case, matches, threads):
    states = native_states(raw, segments, plant)
    report = gates(raw, states, segments, plant.track, case, matches, threads)
    rows = enrich(raw, states, plant.track, reference)
    sectors = sector_windows(raw, segments, plant.track.length, reference.manifest["sectors"])
    windows = [
        dict(
            kind="run",
            index=0,
            start=rows[0]["time"],
            end=rows[-1]["time"],
            start_s=rows[0]["s_abs"],
            end_s=rows[-1]["s_abs"],
            complete=not report["stop_gate"],
            status="observed",
        )
    ]
    windows += report["coverage"]["windows"] + sectors
    cycles = cycle_rows(raw)
    report.update(
        windows=[window_metrics(rows, raw, w) for w in windows],
        timing=timing_summary(cycles, case.offset is not None),
        endpoint_samples=sum(r["sample_kind"] != "runtime_event" for r in rows),
        request_tail_complete=False,
    )
    if any(r["reference_status"] != "available" for r in rows):
        report["stop_gate"].append("active_reference_coverage_unavailable")
    return report, rows, cycles


def physical_difference(a, b):
    """Recorded common times only; no synthetic state at a different run's event."""
    ma, mb = ({round(r["time"], 10): r for r in rows} for rows in [a, b])
    times = sorted(ma.keys() & mb.keys())
    keys = (*STATE_NAMES, "delta", "a_cmd")
    errors = []
    for t in times:
        row = [ma[t][k] - mb[t][k] for k in keys]
        row[3] = wrap_angle(row[3])
        errors.append(row)
    return dict(
        count=len(times),
        start=times[0] if times else None,
        end=times[-1] if times else None,
        first_difference=next(
            (t for t, row in zip(times, errors) if max(abs(v) for v in row) > 1e-12), None
        ),
        errors={k: distribution(np.asarray(errors)[:, i]) for i, k in enumerate(keys)}
        if times
        else {},
    )
