"""Generate measured tables without hiding fallback or failed conditions."""

import json

import numpy as np
import pandas as pd
from async_study.analysis import read_csv
from async_study.export import export
from threading_study.config import ROOT
from threading_study.report import table


def generate(root):
    frame = pd.read_csv(root / "experiments.csv")
    sections = [
        "# Task006.3 — measured results",
        "Final experiments use the timestamp-boundary fix and explicit command-validation "
        "timing. Earlier exploratory runs are retained separately and excluded. "
        "Desktop measurements are not hard-real-time guarantees.",
        "## All conditions",
        table(
            frame[
                [
                    "case",
                    "completed",
                    "completed_without_fallback",
                    "rms_e_y",
                    "rms_e_psi",
                    "rms_speed_error",
                    "planner_misses",
                    "codriver_misses",
                    "fallback_events",
                    "boundary_violations",
                    "solver_failures",
                ]
            ]
        ),
        "Tracking RMS units are metres, radians and metres/second. A completed run with "
        "fallback is not uninterrupted operation of the planned architecture.",
    ]
    active = frame[frame.architecture != "sync"]
    sections += [
        "## Lap times, control activity and tires",
        table(
            frame[
                [
                    "case",
                    "lap_times",
                    "steering_total_variation",
                    "acceleration_total_variation",
                    "max_front_utilization",
                    "max_rear_utilization",
                ]
            ]
        ),
        "## Reserve and update rates",
        table(
            active[
                [
                    "case",
                    "planner_effective_hz",
                    "codriver_effective_hz",
                    "codriver_computational_exceedances",
                    "reserve_min",
                    "reserve_mean",
                    "reserve_p95",
                    "reserve_time_below_warning",
                    "reserve_time_below_critical",
                    "urgent_triggers",
                ]
            ]
        ),
        "Reserve statistics integrate its physical-time linear decay between events, including "
        "instantaneous handoff resets and zero reserve after exhaustion. Threshold durations "
        "are seconds, not event-count fractions.",
        "Computational exceedances count measured callback durations above 10 ms. Injected "
        "planner-delay cases use zero simulated codriver latency, so these can coexist with "
        "zero simulated codriver misses. Fallback-case callback costs include the Task005 "
        "controller and must not be attributed solely to TVLQR.",
    ]
    envelope = []
    for path in sorted(root.glob("*/summary.json")):
        r = json.loads(path.read_text())
        if r["architecture"] == "sync":
            continue
        for key, values in r["tracker_envelope"].items():
            envelope.append(dict(case=path.parent.name, error=key, **values))
    sections += ["## Trajectory tracking envelopes", table(pd.DataFrame(envelope))]
    timing_rows, memory_rows, handoff_rows, prediction_rows = [], [], [], []
    jumps, recovery = [], []
    for path in sorted(root.glob("*/summary.json")):
        r, name = json.loads(path.read_text()), path.parent.name
        if r["architecture"] == "sync":
            continue
        for owner, key in [
            ("planner", "solve_time"),
            ("planner", "preview_time"),
            ("planner", "prediction_time"),
            ("planner", "gain_time"),
            ("planner", "planner_total_time"),
            ("planner", "planner_cpu_time"),
            ("codriver", "interpolation_time"),
            ("codriver", "feedback_time"),
            ("codriver", "total_time"),
            ("codriver", "kernel_time"),
            ("codriver", "command_validation_time"),
            ("codriver", "cpu_time"),
        ]:
            values = r[owner + "_timing"][key]
            timing_rows.append(
                dict(
                    case=name,
                    component=owner + "_" + key,
                    **{k + "_ms": values[k] * 1000 for k in ["mean", "p50", "p95", "p99", "max"]},
                )
            )
        memory_rows.append(
            dict(
                case=name,
                final_rss_mib=r["rss_final_bytes"] / 2**20,
                peak_rss_mib=r["rss_lifetime_peak_bytes"] / 2**20,
                construction_rss_delta_mib=(
                    r["rss_after_construction_bytes"] - r["rss_before_bytes"]
                )
                / 2**20,
                planner_core_demand=r["planner_core_demand"],
                codriver_core_demand=r["codriver_core_demand"],
                total_core_demand=r["total_core_demand"],
            )
        )
        h = read_csv(path.parent / "handoffs.csv")
        if not h.empty:
            accepted_h = h[h.accepted]
            jumps.append(
                dict(
                    case=name,
                    accepted=int(h.accepted.sum()),
                    rejected=int((~h.accepted).sum()),
                    max_abs_nominal_delta_jump=float(accepted_h.nominal_delta_jump.abs().max())
                    if "nominal_delta_jump" in accepted_h
                    else None,
                    max_abs_nominal_acceleration_jump=float(
                        accepted_h.nominal_acceleration_jump.abs().max()
                    )
                    if "nominal_acceleration_jump" in accepted_h
                    else None,
                )
            )
        if r["config"]["disturbance_time"] is not None:
            commands = read_csv(path.parent / "controls.csv")
            start = r["config"]["disturbance_time"]
            post = commands[(commands.time >= start) & (commands.time <= start + 5)]
            settled_time = None
            good = (post.error_e_y.abs() <= 0.01) & (post.error_e_psi.abs() <= 0.05)
            # Explicit diagnostic: remain within both tolerances for 100 consecutive updates.
            for i in range(max(0, len(post) - 99)):
                if good.iloc[i : i + 100].all():
                    settled_time = float(post.time.iloc[i] - start)
                    break
            physical = read_csv(path.parent / "states.csv")
            physical = physical[(physical.time >= start) & (physical.time <= start + 5)]
            centerline_settling = None
            for row in physical.itertuples():
                window = physical[(physical.time >= row.time) & (physical.time <= row.time + 1)]
                if row.time + 1 > physical.time.iloc[-1]:
                    break
                if (window.e_y.abs() <= 0.02).all() and (window.e_psi.abs() <= 0.05).all():
                    centerline_settling = float(row.time - start)
                    break
            recovery.append(
                dict(
                    case=name,
                    trajectory_settling_seconds=settled_time,
                    centerline_settling_seconds=centerline_settling,
                    post5s_lateral_tracking_rms=float(np.sqrt(np.mean(post.error_e_y**2))),
                    post5s_max_abs_steering_correction=float(post.delta_correction.abs().max()),
                    urgent_triggers=r["urgent_triggers"],
                )
            )
        for accepted in [True, False]:
            subset = h[h.accepted == accepted] if not h.empty else h
            for key in ["vx", "vy", "r", "e_psi", "s_abs", "e_y"]:
                column = "error_" + key
                values = subset[column].dropna().to_numpy() if column in subset else []
                if len(values):
                    handoff_rows.append(
                        dict(
                            case=name,
                            accepted=accepted,
                            component=key,
                            rms=float(np.sqrt(np.mean(np.asarray(values) ** 2))),
                            p95_abs=float(np.percentile(abs(values), 95)),
                            max_abs=float(np.max(abs(values))),
                        )
                    )
        events = json.loads((path.parent / "events.json").read_text())
        plans = [p for p in events["plans"] if not p["startup"] and p.get("completed")]
        for index, key in enumerate(["vx", "vy", "r", "e_psi", "s_abs", "e_y"]):
            values = np.array([p["prediction_error"][index] for p in plans])
            if len(values):
                prediction_rows.append(
                    dict(
                        case=name,
                        component=key,
                        rms=float(np.sqrt(np.mean(values**2))),
                        p95_abs=float(np.percentile(abs(values), 95)),
                        max_abs=float(abs(values).max()),
                    )
                )
    for name, rows in [
        ("timing", timing_rows),
        ("cpu_memory", memory_rows),
        ("handoff_statistics", handoff_rows),
        ("prediction_statistics", prediction_rows),
        ("handoff_input_jumps", jumps),
        ("disturbance_recovery", recovery),
    ]:
        data = pd.DataFrame(rows)
        data.to_csv(root / (name + ".csv"), index=False)
        sections += ["## " + name.replace("_", " ").title(), table(data)]
    sections += [
        "CPU-core demand excludes simulation integration, logging and transport. Codriver total "
        "includes command validation; its interpolation/feedback kernel is reported separately. "
        "RSS includes imports, NLP, gains and logs; it is not isolated tracker allocation.",
        "Prediction error compares intended-handoff forecast with actual-completion state, "
        "so it includes delay-estimation error. Handoff mismatch uses aligned nominal state.",
        "Disturbance settling is a diagnostic measured from the perturbation to the first "
        "100 consecutive codriver samples within 0.01 m lateral and 0.05 rad heading "
        "trajectory error, searched in the following five seconds. Replanning changes that "
        "reference; this is not an isolated fixed-reference disturbance-rejection claim.",
        "Centerline settling separately requires physical lateral error within 0.02 m and "
        "heading error within 0.05 rad continuously for one second, within the same window.",
        "## Reproduction",
        "Use scripts/run_async_planner_tracker.py run/suite/analyze/audit. Select fresh case names "
        "or a fresh output directory; existing evidence is never silently overwritten.",
    ]
    (ROOT / "docs/ASYNC_PLANNER_CODRIVER_RESULTS.md").write_text("\n\n".join(sections) + "\n")
    export(root)
