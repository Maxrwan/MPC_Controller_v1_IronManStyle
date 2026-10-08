"""Auditable result tables; selection remains an explicit reviewed record."""

import json
from pathlib import Path

import pandas as pd


def table(rows):
    frame = pd.DataFrame(rows)
    if frame.empty:
        return "(No rows.)\n"

    def fmt(v):
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v)

    return (
        "\n".join(
            [
                "| " + " | ".join(frame.columns) + " |",
                "| " + " | ".join(["---"] * len(frame.columns)) + " |",
            ]
            + [
                "| " + " | ".join(fmt(v) for v in row) + " |"
                for row in frame.itertuples(index=False, name=None)
            ]
        )
        + "\n"
    )


def generate(output):
    output = Path(output)
    from apex.config import load_vehicle_parameters
    from apex.control.mpc.cost import TerminalSchedule

    parameters = load_vehicle_parameters("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    terminal = TerminalSchedule(parameters)
    (output / "frozen_costs.json").write_text(
        json.dumps(
            dict(
                stage_state_error_order=["vx", "vy", "r", "e_psi", "e_y"],
                Q_diagonal=[4, 4, 1, 200, 200],
                input_order=["delta", "a_cmd"],
                R_diagonal=[25, 1],
                W_diagonal=[1, 0.1],
                terminal_error_order=["e_y", "e_psi", "vy", "r"],
                terminal_speed_weight=4,
                terminal_multiplier=1,
                terminal_speed_nodes=terminal.nodes.tolist(),
                terminal_matrices=terminal.matrices.tolist(),
                terminal_interpolation="entrywise linear; speed clipped to [1,3] m/s",
                slack_linear=1e4,
                slack_quadratic=1e5,
                stage_dt_multiplier=False,
                progress_normalization_m=2.4,
            ),
            indent=2,
        )
        + "\n"
    )
    records = []
    for path in sorted(output.glob("*/analysis.json")):
        r = json.loads(path.read_text())
        s = json.loads((path.parent / "summary.json").read_text())
        records.append((r, s))
    selection = (
        json.loads((output / "selection.json").read_text())
        if (output / "selection.json").exists()
        else {}
    )
    parts = [
        "# Task007B measured results\n",
        "Planning→APEX errors query the nominal package at every predicted node. "
        "APEX→vehicle errors use the active packet at physical release time. "
        "Node statistics weight nodes equally; local means/RMS use physical intervals. "
        "First lap is a rolling-launch transient. "
        "Timing is measured, not a hard real-time guarantee.\n",
        "## Study cases\n",
    ]
    rows = []
    for r, s in records:
        rows.append(
            dict(
                case=r["case"],
                gamma=r["gamma"],
                lambda_s=r["progress_weight"],
                laps=", ".join(f"{v:.6f}" for v in r["lap_times"]),
                stop=s["stop_reason"],
                solver_failures=s["solver_failures"],
                planner_failures=s["planner_failures"],
                global_fallback=s["fallback_events"],
                boundary_violations=s["boundary_violations"],
            )
        )
    parts.append(table(rows))
    parts += [
        "## Selection and interpretation\n",
        "\n\n".join(selection.get("interpretation", [])) + "\n",
        "Machine-readable decisions and case membership: `results/task007b/selection.json`.\n",
        "## Adaptation versus local tracking\n",
    ]
    rows = []
    for r, s in records:
        rows.append(
            dict(
                case=r["case"],
                plan_ey_rms=r["adaptation"]["e_y"]["rms"],
                plan_epsi_rms=r["adaptation"]["e_psi"]["rms"],
                plan_v_rms=r["adaptation"]["vx"]["rms"],
                plan_v_mean=r["adaptation"]["vx"]["mean"],
                local_ey_rms=r["tracking"]["error_e_y"]["rms"],
                local_ey_max=r["tracking"]["error_e_y"]["max_abs"],
                local_heading_rms=r["tracking"]["error_e_psi"]["rms"],
                beta_max=r["tracking"]["actual_beta"]["max_abs"],
            )
        )
    parts.append(table(rows))
    parts.append("## Constraint and coordinate audit\n")
    rows = []
    for r, s in records:
        rows.append(
            dict(
                case=r["case"],
                front_max=s["max_front_utilization"],
                rear_max=s["max_rear_utilization"],
                clearance_min=r["physical_constraints"]["physical_clearance_min"],
                slack_max=r["predicted_slack_max"],
                predicted_denominator_min=r["node_denominator_min"],
                predicted_heading_max=r["node_heading_max"],
                progress_per_physical_distance=r["progress_per_physical_distance"],
                steering_TV=s["steering_total_variation"],
                acceleration_TV=s["acceleration_total_variation"],
            )
        )
    parts.append(table(rows))
    parts.append("## Physical-time performance\n")
    rows = []
    for r, s in records:
        t = r["tracking"]
        rows.append(
            dict(
                case=r["case"],
                progress_mps=r["progress_rate"],
                terminal_progress_mps=r["terminal_progress_rate"],
                above_ref_s=t["time_above_reference"],
                below_ref_s=t["time_below_reference"],
                excess_m=t["integrated_excess_m"],
                shortfall_m=t["integrated_shortfall_m"],
                rate_limit_s=t["steering_rate_limit_seconds"],
                reserve_min=s["reserve"]["min"],
                planner_misses=s["planner_misses"],
                codriver_misses=s["codriver_misses"],
            )
        )
    parts.append(table(rows))
    parts.append("## Computation (milliseconds; excludes startup in official timing summaries)\n")
    rows = []
    for r, s in records:
        p = s["planner_timing"]
        c = s["codriver_timing"]["total_time"]
        rows.append(
            dict(
                case=r["case"],
                solve_mean=1000 * p["solve_time"]["mean"],
                solve_p95=1000 * p["solve_time"]["p95"],
                planner_mean=1000 * p["planner_total_time"]["mean"],
                planner_p95=1000 * p["planner_total_time"]["p95"],
                planner_max=1000 * p["planner_total_time"]["max"],
                codriver_mean=1000 * c["mean"],
                codriver_p95=1000 * c["p95"],
                codriver_max=1000 * c["max"],
                core_seconds_per_s=s["total_core_demand"],
                peak_RSS_bytes=s["rss_peak_bytes"],
            )
        )
    parts.append(table(rows))
    parts.append("## Objective component distributions (mean / p95 absolute / maximum absolute)\n")
    for r, s in records:
        parts.append("### " + r["case"] + "\n")
        parts.append(
            table(
                [
                    dict(component=k, mean=v["mean"], p95_abs=v["p95_abs"], max_abs=v["max_abs"])
                    for k, v in r["costs"].items()
                ]
            )
        )
    parts.append("## Selected-case sectors\n")
    for r, s in records:
        if r["case"] not in selection.get("dashboard_cases", []):
            continue
        parts.append("### " + r["case"] + "\n")
        rows = []
        for row in r["sectors"]:
            t = row["tracking"]
            a = row["adaptation"]
            rows.append(
                dict(
                    sector=row["sector"],
                    plan_ey_rms=a["e_y"]["rms"],
                    plan_v_rms=a["vx"]["rms"],
                    local_ey_rms=t["error_e_y"]["rms"],
                    speed_mean=t["actual_vx"]["mean"],
                    steer_max=t["steering_utilization"]["max_abs"],
                    rate_limit_s=t["steering_rate_limit_seconds"],
                    acceleration_max=t["a_cmd"]["max"],
                    braking_min=t["a_cmd"]["min"],
                    longitudinal_util_max=t["acceleration_utilization"]["max_abs"],
                    front_max=t["front_utilization"]["max_abs"],
                    rear_max=t["rear_utilization"]["max_abs"],
                    ay_max=t["lateral_acceleration"]["max_abs"],
                    planner_mean=t["planner_planner_total_time"]["mean"],
                    codriver_mean=t["total_time"]["mean"],
                    reserve_min=t["reserve"]["min"],
                    progress_cost_mean=t["cost_progress_reward"]["mean"],
                )
            )
        parts.append(table(rows))
    parts.append("## Frozen nominal-state defect,10ms, independent plant\n")
    parts.append(table([dict(case=r["case"], **r["nominal_defect_max_abs"]) for r, s in records]))
    parts.append("## Mean stage tracking cost by frozen state channel\n")
    parts.append(table([dict(case=r["case"], **r["state_cost_channel_means"]) for r, s in records]))
    parts.append(
        "No reference-state redesign or codriver switching was performed. "
        "Residuals diagnose the geometric approximation; "
        "they are not accepted-solver constraint violations.\n"
    )
    Path("docs/TASK007B_RESULTS.md").write_text("\n".join(parts))
    pd.DataFrame(
        [
            dict(
                case=r["case"],
                gamma=r["gamma"],
                progress_weight=r["progress_weight"],
                lap_time=sum(r["lap_times"][1:]) / len(r["lap_times"][1:])
                if len(r["lap_times"]) > 1
                else r["lap_times"][0],
                phase="comparable" if len(r["lap_times"]) > 1 else "startup_screen",
                plan_lateral_rms=r["adaptation"]["e_y"]["rms"],
                local_lateral_rms=r["tracking"]["error_e_y"]["rms"],
                front_utilization=s["max_front_utilization"],
                planner_p95=s["planner_timing"]["planner_total_time"]["p95"],
            )
            for r, s in records
        ]
    ).to_csv(output / "pareto_metrics.csv", index=False)

    timing_rows = []
    for r, s in records:
        for component, key in [("planner", "planner_timing"), ("codriver", "codriver_timing")]:
            for measurement, values in s[key].items():
                timing_rows.append(
                    dict(
                        case=r["case"],
                        component=component,
                        measurement=measurement,
                        **{k: 1000 * v for k, v in values.items() if k != "cv"},
                    )
                )
        iterations = pd.read_csv(output / r["case"] / "plans.csv").iterations
        timing_rows.append(
            dict(
                case=r["case"],
                component="solver",
                measurement="iterations_count",
                mean=iterations.mean(),
                p50=iterations.quantile(0.5),
                p95=iterations.quantile(0.95),
                p99=iterations.quantile(0.99),
                max=iterations.max(),
                std=iterations.std(ddof=0),
            )
        )
    pd.DataFrame(timing_rows).to_csv(output / "timing_distributions.csv", index=False)
