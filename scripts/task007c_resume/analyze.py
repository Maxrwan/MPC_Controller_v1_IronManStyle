"""Offline metrics only: never execute alongside measured campaigns."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("results/task007c_resume")


def main(args):
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not compete with active measured repetitions")

    from threading_study.config import configure_accelerate

    configure_accelerate(1)
    from task007b.analysis import analyze_case
    from task007c.metrics_export import export_case
    from task007c_resume.physics import export

    for p in sorted(ROOT.glob("g*/summary.json")):
        folder = p.parent
        if args.cases and folder.name not in args.cases:
            continue
        if shutil.disk_usage(ROOT).free < 1024**3:
            raise RuntimeError("Less than 1 GiB free: recover space before derived exports")
        if not (folder / "analysis.json").exists():
            analyze_case(folder)
        if not (folder / "oscillation.json").exists():
            export_case(folder)
        if args.physics:
            validation = folder / "physics_validation.json"
            if (
                not validation.exists()
                or json.loads(validation.read_text()).get("schema_version") != 2
            ):
                export(folder)
        print("Analyzed", folder.name, flush=True)
    summarize()


def summarize():
    import numpy as np
    import pandas as pd

    rows = []
    for p in sorted(ROOT.glob("g*/analysis.json")):
        a = json.loads(p.read_text())
        s = json.loads((p.parent / "summary.json").read_text())
        cell = json.loads((p.parent / "cell.json").read_text())
        t = pd.read_csv(p.parent / "telemetry.csv")
        events = json.loads((p.parent / "events.json").read_text())
        plans = [event for event in events["plans"] if not event["startup"]]
        o = (
            json.loads((p.parent / "oscillation.json").read_text())
            if (p.parent / "oscillation.json").exists()
            else None
        )
        row = dict(
            case=p.parent.name,
            **cell,
            completed_laps=len(s["lap_times"]),
            lap_s=s["lap_times"][-1] if s["lap_times"] else None,
            end_progress=float(t.s_abs.iloc[-1]),
            boundary_count=s["boundary_violations"],
            solver_failures=s["solver_failures"],
            failure=s["failure"],
            stop_reason=s["stop_reason"],
            beta_p95=float(np.quantile(abs(t.actual_beta), 0.95)),
            beta_max=float(abs(t.actual_beta).max()),
            front_util_max=float(t.front_utilization.max()),
            rear_util_max=float(t.rear_utilization.max()),
            rate_limit_s=a["tracking"]["steering_rate_limit_seconds"],
            heading_tv=a["tracking"]["apex_heading_total_variation"],
            steering_tv=float(
                sum(abs(np.diff(g.nominal_delta)).sum() for _, g in t.groupby("lap"))
            ),
            adaptation_ey_rms=float(np.sqrt(np.mean(t.node_adaptation_e_y**2))),
            tracking_ey_rms=a["tracking"]["error_e_y"]["rms"],
            slack=a["predicted_slack_max"],
            clearance=a["physical_constraints"]["physical_clearance_min"],
            iterations_mean=float(t.planner_iterations.mean()),
            denominator_min=float(t.denominator.min()),
            progress_rate=a["progress_rate"],
            planner_misses=s["planner_misses"],
            codriver_misses=s["codriver_misses"],
            planner_failures=s["planner_failures"],
            forecast_or_gain_failures=s["forecast_or_gain_failures"],
            fallback_events=s["fallback_events"],
            handoff_rejections=sum(not h["accepted"] for h in events["handoffs"]),
            observed_time_s=s["end_time"],
            full_requested_coverage=len(s["lap_times"]) >= cell["laps"],
            planner_cpu_core_seconds_per_sim_s=sum(
                event.get("planner_cpu_time", 0) for event in plans
            )
            / s["end_time"],
        )
        iterations = [event["iterations"] for event in plans if "iterations" in event]
        for field, value in [
            ("mean", np.mean(iterations)),
            ("p95", np.quantile(iterations, 0.95)),
            ("max", max(iterations)),
        ]:
            row["iterations_per_call_" + field] = float(value)
        for field in ["mean", "p95", "p99", "max"]:
            row["preparation_" + field] = s["planner_timing"]["planner_total_time"].get(field)
        for sector in a["sectors"]:
            row[sector["sector"] + "_heading_tv"] = sector["tracking"][
                "apex_heading_total_variation"
            ]
        if o:
            row["planned_reversals"] = sum(
                lap["planned_steering_reversals_db_0.0001"] for lap in o["laps"]
            )
            pred = pd.read_csv(p.parent / "prediction_oscillation.csv")
            pred = pred[pred.handoff_accepted]
            for field in [
                "heading_total_variation_per_s",
                "steering_total_variation_per_s",
                "common_0p4_heading_total_variation",
                "common_0p4_steering_total_variation",
                "common_0p4_steering_rate_sign_reversals",
            ]:
                row["accepted_prediction_mean_" + field] = float(pred[field].mean())
        rows.append(row)
    pd.DataFrame(rows).to_csv(ROOT / "comparison.csv", index=False)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="*")
    parser.add_argument("--physics", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        main(args)
    else:
        from threading_study.config import environment

        subprocess.run(
            [sys.executable, __file__, *sys.argv[1:], "--worker"], env=environment(1), check=True
        )
