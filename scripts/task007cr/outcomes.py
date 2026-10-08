"""Run-wise outcome distributions and separate observable event labels."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def summarize(output=Path("results/task007cr")):
    rows = []
    for path in sorted(output.glob("r*/analysis.json")):
        a = json.loads(path.read_text())
        s = json.loads((path.parent / "summary.json").read_text())
        t = pd.read_csv(path.parent / "telemetry.csv")
        sectors = {x["sector"]: x["tracking"] for x in a["sectors"]}
        events = json.loads((path.parent / "events.json").read_text())["plans"]
        iterations = [p["iterations"] for p in events if p.get("solver_attempted")]
        row = dict(
            case=path.parent.name,
            family=path.parent.name.split("_")[0],
            configuration=path.parent.name.split("_")[1],
            complete_lap=bool(a["lap_times"]),
            boundary_violations=a["physical_constraints"]["boundary_violations"],
            lap_s=a["lap_times"][0] if a["lap_times"] else None,
            end_time=s["end_time"],
            end_progress=float(t.s_abs.iloc[-1]),
            predicted_slack_m=a["predicted_slack_max"],
            physical_clearance_m=a["physical_constraints"]["physical_clearance_min"],
            tire_max=max(
                a["physical_constraints"]["front_max"], a["physical_constraints"]["rear_max"]
            ),
            beta_max_rad=a["tracking"]["actual_beta"]["max_abs"],
            planned_steering_TV_rad=float(np.abs(np.diff(t.nominal_delta)).sum()),
            rate_limit_s=a["tracking"]["steering_rate_limit_seconds"],
            local_ey_rms_m=a["tracking"]["error_e_y"]["rms"],
            planner_mean_s=s["planner_timing"]["planner_total_time"]["mean"],
            planner_p95_s=s["planner_timing"]["planner_total_time"]["p95"],
            solve_mean_s=s["planner_timing"]["solve_time"]["mean"],
            iterations_mean=float(np.mean(iterations)),
            iterations_p95=float(np.quantile(iterations, 0.95)),
            rate_limit_fraction=a["tracking"]["steering_rate_limit_seconds"]
            / a["tracking"]["duration_s"],
            capture_total_s=s.get("capture_total_seconds", 0),
        )
        for name in ["fast_sweeper", "technical_section"]:
            row[name + "_heading_TV_rad"] = sectors.get(name, {}).get(
                "apex_heading_total_variation"
            )
            row[name + "_rate_limit_s"] = sectors.get(name, {}).get("steering_rate_limit_seconds")
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(output / "outcomes.csv", index=False)
    # Disclosed descriptive indicators, not a safety certificate or combined score.
    definitions = {
        "high_sweeper_heading_TV": ("fast_sweeper_heading_TV_rad", ">", 3.0),
        "high_technical_heading_TV": ("technical_section_heading_TV_rad", ">", 6.0),
        "repeated_rate_saturation": ("rate_limit_fraction", ">", 0.2),
        "high_planned_steering_TV": ("planned_steering_TV_rad", ">", 20.0),
        "persistent_sweeper_rate_saturation": ("fast_sweeper_rate_limit_s", ">", 1.0),
        "material_predicted_slack": ("predicted_slack_m", ">", 1e-6),
        "physical_margin_shortfall": ("physical_clearance_m", "<", 0.08),
        "physical_boundary_crossing": ("physical_clearance_m", "<", 0.0),
        "high_tire_utilization": ("tire_max", ">=", 0.97),
        "large_sideslip": ("beta_max_rad", ">=", 0.35),
    }
    distributions = {}
    events = {}
    measured = frame[frame.family == "r4"]
    for label, group in measured.groupby("configuration"):
        distributions[label] = {}
        for column in group.select_dtypes("number").columns:
            values = group[column].dropna().to_numpy()
            if len(values):
                distributions[label][column] = dict(
                    zip(
                        ["min", "p25", "median", "p75", "p95", "max"],
                        np.quantile(values, [0, 0.25, 0.5, 0.75, 0.95, 1]).tolist(),
                    )
                )
        pooled = {
            "iterations": [],
            "solver_seconds": [],
            "planner_ready_seconds": [],
            "codriver_seconds": [],
        }
        for case in group.case:
            event_plans = json.loads((output / case / "events.json").read_text())["plans"]
            for p in event_plans:
                if p["startup"]:
                    continue
                if p.get("solver_attempted"):
                    pooled["iterations"].append(p["iterations"])
                    pooled["solver_seconds"].append(p["solve_time"])
                pooled["planner_ready_seconds"].append(p["physical_delay"])
            controls = pd.read_csv(output / case / "controls.csv")
            pooled["codriver_seconds"].extend(controls.physical_latency.tolist())
        distributions[label]["pooled_nonstartup_calls"] = {
            key: dict(
                zip(
                    ["min", "p25", "median", "p75", "p95", "max"],
                    np.quantile(values, [0, 0.25, 0.5, 0.75, 0.95, 1]).tolist(),
                )
            )
            for key, values in pooled.items()
            if values
        }
        events[label] = {}
        for name, (column, operation, threshold) in definitions.items():
            data = group[column].dropna()
            counts = {}
            for factor in [0.8, 1.0, 1.2]:
                limit = threshold * factor
                comparison = (
                    data < limit
                    if operation == "<"
                    else data > limit
                    if operation == ">"
                    else data >= limit
                )
                counts[str(factor)] = {"count": int(comparison.sum()), "denominator": len(data)}
            events[label][name] = counts
    report = dict(
        distributions=distributions,
        event_definitions=definitions,
        event_counts=events,
        event_interpretation=(
            "Separate descriptive indicators; threshold sensitivity +/-20%; "
            "not one bad-run score. Whole-lap steering TV depends on coverage. "
            "Incomplete replay laps are censored, not zero-time results."
        ),
    )
    (output / "outcome_distributions.json").write_text(json.dumps(report, indent=2) + "\n")
    return frame, report


if __name__ == "__main__":
    summarize()
