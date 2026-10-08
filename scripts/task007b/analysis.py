"""Offline node-level adaptation, physical-time tracking and constraint evidence."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from async_study.analysis import audit
from task007b.diagnostics import tracking_cost_channels, variation
from task007b.metrics import distribution, local_tracking_error, planning_deviation
from task007b.references import PACKAGES, package_name

from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track
from apex.state import STATE_NAMES


def sectors(progress, ref):
    starts = [v["start_s_m"] for v in ref.manifest["sectors"]]
    names = np.array([v["name"] for v in ref.manifest["sectors"]])
    return names[
        np.maximum(0, np.searchsorted(starts, np.asarray(progress) % ref.length, side="right") - 1)
    ]


def analyze_case(folder):
    summary = json.loads((folder / "summary.json").read_text())
    fixture = folder / "fixture"
    if not fixture.exists():
        fixture = PACKAGES / package_name(summary["gamma"])
    track, _, identity = load_track(fixture / "track_source.json")
    ref = PlanningReference(fixture, track, identity, feasibility_policy="advisory")
    states = pd.read_csv(folder / "states.csv")
    controls = pd.read_csv(folder / "controls.csv")
    plans = pd.read_csv(folder / "plans.csv")
    reserves = pd.read_csv(folder / "reserves.csv")
    predictions = json.loads((folder / "predictions.json").read_text())
    packets = {
        p["plan_id"]: p for p in json.loads((folder / "trajectory_packets.json").read_text())
    }
    nodes = []
    costs = []
    for record in predictions:
        pred = record["prediction"]
        d = record["diagnostics"]
        if pred is None or "states" not in pred:
            continue
        x = np.asarray(pred["states"]).T
        nominal, error = planning_deviation(x, ref)
        slack = np.asarray(pred["slacks"]).T
        for j, (state, goal, err) in enumerate(zip(x, nominal, error)):
            g = track.sample(state[4])
            row = dict(
                plan_id=record["plan_id"],
                release_time=record["release_time"],
                node=j,
                s_abs=state[4],
                progress=state[4] % track.length,
                beta=np.arctan2(state[1], state[0]),
                slack_left=slack[j, 0],
                slack_right=slack[j, 1],
                denominator=1 - g.curvature * state[5],
                clearance=min(g.left_width - state[5], g.right_width + state[5]),
                speed_lower_margin=state[0] - 0.5,
                speed_upper_margin=6 - state[0],
                heading=state[3],
                curvature=g.curvature,
                preview_progress=pred["preview_progress"][j],
                preview_curvature=pred["preview"][0][j],
                curvature_preview_error=g.curvature - pred["preview"][0][j],
                curvature_ahead=track.sample(x[-1, 4]).curvature,
            )
            row.update({f"planned_{k}": v for k, v in zip(STATE_NAMES, state)})
            row.update({f"planning_{k}": v for k, v in zip(STATE_NAMES, goal)})
            row.update({f"adaptation_{k}": v for k, v in zip(STATE_NAMES, err)})
            nodes.append(row)
        costs.append(
            dict(
                plan_id=record["plan_id"],
                time=record["release_time"],
                s_abs=x[0, 4],
                **d["objective_components"],
            )
        )
    nodes = pd.DataFrame(nodes)
    costs = pd.DataFrame(costs)
    nodes["sector"] = sectors(nodes.s_abs, ref)
    nodes.to_csv(folder / "planning_apex_nodes.csv", index=False)
    costs.to_csv(folder / "objective_components.csv", index=False)
    telemetry = controls.copy()
    physical_samples = np.column_stack(
        [np.interp(controls.time, states.time, states[key]) for key in STATE_NAMES]
    )
    packet_samples = controls[["reference_" + key for key in STATE_NAMES]].to_numpy()
    audited_errors = local_tracking_error(physical_samples, packet_samples)
    np.testing.assert_allclose(
        audited_errors, controls[["error_" + key for key in STATE_NAMES]], atol=1e-8, rtol=0
    )
    telemetry["s_abs"] = physical_samples[:, 4]
    telemetry["progress"] = telemetry.s_abs % track.length
    telemetry["lap"] = (telemetry.s_abs / track.length).astype(int) + 1
    telemetry["sector"] = sectors(telemetry.s_abs, ref)
    telemetry["interval"] = np.maximum(0, np.diff(np.r_[telemetry.time, summary["end_time"]]))
    for index, key in enumerate(STATE_NAMES):
        telemetry["actual_" + key] = physical_samples[:, index]
    goals = pd.DataFrame([ref.sample(s) for s in telemetry.s_abs])
    telemetry["planning_vx"] = goals.v_ref_mps
    telemetry["planning_e_y"] = goals.e_y_ref_m
    telemetry["planning_e_psi"] = goals.e_psi_ref_rad
    telemetry["planning_r"] = goals.v_ref_mps * goals.kappa_ref_1pm
    telemetry["planning_vy"] = 0
    telemetry["racing_curvature"] = goals.kappa_ref_1pm
    telemetry["centerline_curvature"] = [track.sample(s).curvature for s in telemetry.s_abs]
    telemetry["curvature_ahead"] = [
        track.sample(s + 0.4 * v).curvature for s, v in zip(telemetry.s_abs, telemetry.actual_vx)
    ]
    telemetry["actual_beta"] = np.arctan2(telemetry.actual_vy, telemetry.actual_vx)
    telemetry["planned_beta"] = np.arctan2(controls.reference_vy, controls.reference_vx)
    telemetry["applied_delta"] = controls.delta
    telemetry["applied_a_cmd"] = controls.a_cmd
    telemetry["application_s_abs"] = np.interp(controls.application_time, states.time, states.s_abs)
    # State/actuator panels refer to the SAME release instant. Pending commands
    # are retained separately at their logged application time.
    telemetry["delta"] = np.interp(controls.time, states.time, states.delta)
    telemetry["a_cmd"] = np.interp(controls.time, states.time, states.a_cmd)
    telemetry["steering_utilization"] = abs(telemetry.delta) / 0.4
    intervals = np.diff(np.r_[0, controls.application_time])
    initial = summary["startup"]["prepositioned_control"][0]
    applied_rates = np.divide(
        np.diff(np.r_[initial, controls.delta]),
        intervals,
        out=np.zeros(len(controls)),
        where=intervals > 1e-12,
    )
    applied_index = np.searchsorted(controls.application_time, controls.time, side="right") - 1
    telemetry["steering_rate"] = np.where(
        applied_index >= 0, applied_rates[np.maximum(0, applied_index)], 0.0
    )
    telemetry["steering_rate_utilization"] = abs(telemetry.steering_rate)
    telemetry["acceleration_utilization"] = np.where(
        telemetry.a_cmd >= 0, telemetry.a_cmd / 2, -telemetry.a_cmd / 3
    )
    for key in ["front_utilization", "rear_utilization"]:
        telemetry[key] = np.interp(controls.time, states.time, states[key])
    telemetry["lateral_acceleration"] = (
        np.gradient(telemetry.actual_vy, telemetry.time) + telemetry.actual_vx * telemetry.actual_r
    )
    telemetry["clearance"] = 0.55 - abs(telemetry.actual_e_y)
    telemetry["denominator"] = 1 - telemetry.centerline_curvature * telemetry.actual_e_y
    telemetry["speed_lower_margin"] = telemetry.actual_vx - 0.5
    telemetry["speed_upper_margin"] = 6 - telemetry.actual_vx
    telemetry["reserve"] = np.interp(controls.time, reserves.time, reserves.reserve)
    telemetry["age"] = [
        max(0, t - packets[int(pid)]["planner_release_time"]) if int(pid) in packets else np.nan
        for t, pid in zip(controls.time, controls.plan_id)
    ]
    # Attach costs/node deviations by active plan ID, not nearest reference point.
    maps = costs.set_index("plan_id")
    for key in costs.columns.difference(["plan_id", "time", "s_abs"]):
        telemetry["cost_" + key] = telemetry.plan_id.map(maps[key])
    telemetry["predicted_slack"] = telemetry.plan_id.map(
        nodes.groupby("plan_id")[["slack_left", "slack_right"]].max().max(axis=1)
    )
    for key in ["e_y", "e_psi", "vx", "vy", "r"]:
        telemetry["node_adaptation_" + key] = telemetry.plan_id.map(
            nodes.groupby("plan_id")["adaptation_" + key].mean()
        )
    for key in ["solve_time", "planner_total_time", "iterations", "primal_infeasibility"]:
        telemetry["planner_" + key] = telemetry.plan_id.map(
            plans.drop_duplicates("plan_id").set_index("plan_id")[key]
        )
    completed = [
        p
        for p in json.loads((folder / "events.json").read_text())["plans"]
        if p.get("completed") and "prediction_error" in p
    ]
    if completed:
        completed.sort(key=lambda p: p["completion_time"])
        times = np.array([p["completion_time"] for p in completed])
        indices = np.searchsorted(times, telemetry.time, side="right") - 1
        for j, key in enumerate(STATE_NAMES):
            values = np.array([p["prediction_error"][j] for p in completed])
            telemetry["forecast_residual_" + key] = np.where(
                indices >= 0, values[np.maximum(indices, 0)], np.nan
            )
    telemetry.to_csv(folder / "telemetry.csv", index=False)
    comparable = telemetry[telemetry.lap.isin([2, 3])]
    if comparable.empty:
        comparable = telemetry

    def metrics(group):
        w = group.interval
        result = {
            k: distribution(group[k], w)
            for k in [
                "error_vx",
                "error_s_abs",
                "delta",
                "a_cmd",
                "actual_vy",
                "actual_r",
                "reference_vy",
                "reference_r",
                "error_e_y",
                "error_e_psi",
                "error_vy",
                "error_r",
                "actual_vx",
                "actual_beta",
                "planned_beta",
                "steering_utilization",
                "steering_rate",
                "acceleration_utilization",
                "front_utilization",
                "rear_utilization",
                "lateral_acceleration",
                "clearance",
                "denominator",
                "reserve",
                "age",
                "planner_solve_time",
                "planner_planner_total_time",
                "total_time",
                "cost_progress_reward",
            ]
        }
        dv = group.actual_vx - group.planning_vx
        result.update(
            duration_s=float(w.sum()),
            actual_ey_total_variation=variation(group, "actual_e_y"),
            apex_ey_total_variation=variation(group, "reference_e_y"),
            actual_heading_total_variation=variation(group, "actual_e_psi"),
            apex_heading_total_variation=variation(group, "reference_e_psi"),
            steering_total_variation=variation(group, "delta"),
            time_above_reference=float(w[dv > 1e-6].sum()),
            time_below_reference=float(w[dv < -1e-6].sum()),
            integrated_excess_m=float(w @ np.maximum(dv, 0)),
            integrated_shortfall_m=float(w @ np.maximum(-dv, 0)),
            steering_rate_limit_seconds=float(w[abs(group.steering_rate) >= 1 - 1e-6].sum()),
        )
        return result

    node_evaluation = nodes
    if len(summary["lap_times"]) >= 3:
        node_evaluation = nodes[
            (nodes.release_time >= summary["lap_times"][0])
            & (nodes.release_time < sum(summary["lap_times"][:3]))
        ]
    adaptation = {
        k: distribution(node_evaluation["adaptation_" + k])
        for k in ["e_y", "e_psi", "vx", "vy", "r"]
    }
    sector_rows = []
    for sector, g in comparable.groupby("sector", sort=False):
        ns = node_evaluation[node_evaluation.sector == sector]
        sector_rows.append(
            dict(
                sector=sector,
                tracking=metrics(g),
                adaptation={
                    k: distribution(ns["adaptation_" + k])
                    for k in ["e_y", "e_psi", "vx", "vy", "r"]
                },
            )
        )
    timing = {
        k: distribution(plans[k])
        for k in [
            "preview_time",
            "solve_time",
            "planner_total_time",
            "prediction_time",
            "gain_time",
            "iterations",
        ]
        if k in plans
    }
    costs_summary = {
        k: distribution(costs[k]) for k in costs.columns.difference(["plan_id", "time", "s_abs"])
    }
    # Independent coordinate audit: physical path length and centerline advancement are distinct.
    path_distance = float(np.trapezoid(np.hypot(states.vx, states.vy), states.time))
    report = dict(
        case=folder.name,
        gamma=summary["gamma"],
        progress_weight=summary["progress_weight"],
        lap_times=summary["lap_times"],
        stop_reason=summary["stop_reason"],
        failure=summary["failure"],
        adaptation=adaptation,
        adaptation_basis="all predicted nodes of solves released during comparable laps 2/3"
        if len(summary["lap_times"]) >= 3
        else "all predicted nodes of startup screen",
        tracking=metrics(comparable),
        sectors=sector_rows,
        timing=timing,
        costs=costs_summary,
        progress_rate=float(
            (states.s_abs.iloc[-1] - states.s_abs.iloc[0])
            / (states.time.iloc[-1] - states.time.iloc[0])
        ),
        terminal_progress_rate=float(
            (
                states.vx.iloc[-1] * np.cos(states.e_psi.iloc[-1])
                - states.vy.iloc[-1] * np.sin(states.e_psi.iloc[-1])
            )
            / (1 - track.sample(states.s_abs.iloc[-1]).curvature * states.e_y.iloc[-1])
        ),
        progress_per_physical_distance=float(
            (states.s_abs.iloc[-1] - states.s_abs.iloc[0]) / path_distance
        ),
        node_denominator_min=float(nodes.denominator.min()),
        node_heading_max=float(abs(nodes.heading).max()),
        node_clearance_min=float(nodes.clearance.min()),
        predicted_slack_max=float(nodes[["slack_left", "slack_right"]].max().max()),
        objective_accounting_max_error=float(
            abs(
                costs.drop(columns=["plan_id", "time", "s_abs", "total"]).sum(axis=1) - costs.total
            ).max()
        ),
    )
    from task007b.residuals import residuals

    report["nominal_defect_max_abs"] = residuals(folder, ref, track)
    report["state_cost_channel_means"] = tracking_cost_channels(
        predictions, summary["planner_config"], folder
    )
    report["physical_constraints"] = dict(
        boundary_violations=summary["boundary_violations"],
        physical_clearance_min=float((0.55 - abs(states.e_y)).min()),
        speed_min=float(states.vx.min()),
        speed_max=float(states.vx.max()),
        front_max=float(states.front_utilization.max()),
        rear_max=float(states.rear_utilization.max()),
        solver_failures=summary["solver_failures"],
        planner_failures=summary["planner_failures"],
        global_fallbacks=summary["fallback_events"],
        local_modes=controls["mode"].value_counts().to_dict(),
        planner_misses=summary["planner_misses"],
        codriver_misses=summary["codriver_misses"],
    )
    (folder / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    return report, telemetry, nodes, ref, track


def analyze(output, cases=None):
    output = Path(output)
    reports = []
    for path in sorted(output.glob("*/summary.json")):
        if cases and path.parent.name not in cases:
            continue
        report, *_ = analyze_case(path.parent)
        reports.append(report)
        print(path.parent.name, report["lap_times"], flush=True)
    reports = [json.loads(p.read_text()) for p in sorted(output.glob("*/analysis.json"))]
    (output / "comparison.json").write_text(json.dumps(reports, indent=2) + "\n")
    audit(output)
