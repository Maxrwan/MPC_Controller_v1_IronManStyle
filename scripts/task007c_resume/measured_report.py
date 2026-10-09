"""Descriptive measured-run distributions; preserve every outcome and its coverage."""

import csv
import json
from pathlib import Path

from threading_study.config import configure_accelerate

ROOT = Path("results/task007c_resume")


def main():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not analyze during measured repetitions")
    configure_accelerate(1)
    import numpy as np
    from task007c_resume.common_coverage import compare
    from task007c_resume.grid_report import table

    with (ROOT / "comparison.csv").open() as handle:
        indexed = {r["case"]: r for r in csv.DictReader(handle)}
    rows, groups = [], {}
    for folder in sorted(ROOT.glob("g*_measured_l1_rep*")):
        if not (folder / "summary.json").exists():
            continue
        if folder.name not in indexed:
            raise RuntimeError(f"Analyze completed measured record first: {folder.name}")
        s = json.loads((folder / "summary.json").read_text())
        a = json.loads((folder / "analysis.json").read_text())
        c = json.loads((folder / "cell.json").read_text())
        with (folder / "lap_oscillation.csv").open() as handle:
            laps = list(csv.DictReader(handle))
        row = dict(indexed[folder.name])
        for key, value in list(row.items()):
            try:
                row[key] = float(value)
            except ValueError:
                pass
        row.update(
            gamma=c["gamma"],
            horizon=c["horizon"],
            repeat=c["repeat"],
            actual_steering_tv=sum(float(lap["actual_steering_total_variation"]) for lap in laps),
            actual_reversals_db_1e4=sum(
                int(lap["actual_steering_reversals_db_0.0001"]) for lap in laps
            ),
            actual_reversals_db_1e3=sum(
                int(lap["actual_steering_reversals_db_0.001"]) for lap in laps
            ),
            tracking_ey_p95=a["tracking"]["error_e_y"]["p95_abs"],
            tracking_ey_max=a["tracking"]["error_e_y"]["max_abs"],
            reserve_min=s["reserve"]["min"],
            reserve_below_warning_s=s["reserve"]["time_below_warning"],
            codriver_core_demand=s["codriver_core_demand"],
            total_core_demand=s["total_core_demand"],
        )
        for stat in ["mean", "p95", "p99", "max"]:
            row["codriver_" + stat] = s["codriver_timing"]["total_time"][stat]
        rows.append(row)
        groups.setdefault((c["gamma"], c["horizon"]), []).append(row)
    if not rows:
        raise RuntimeError("No completed measured records")
    with (ROOT / "measured_per_run.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    def distribution(values):
        values = np.asarray(values, dtype=float)
        return dict(
            count=len(values),
            mean=float(np.mean(values)),
            median=float(np.median(values)),
            min=float(np.min(values)),
            max=float(np.max(values)),
            sample_std=float(np.std(values, ddof=1)) if len(values) > 1 else None,
        )

    fields = [
        "lap_s",
        "end_progress",
        "heading_tv",
        "steering_tv",
        "actual_steering_tv",
        "planned_reversals",
        "actual_reversals_db_1e4",
        "actual_reversals_db_1e3",
        "rate_limit_s",
        "tracking_ey_rms",
        "tracking_ey_p95",
        "tracking_ey_max",
        "adaptation_ey_rms",
        "beta_p95",
        "beta_max",
        "front_util_max",
        "rear_util_max",
        "clearance",
        "slack",
        "denominator_min",
        "iterations_per_call_mean",
        "iterations_per_call_p95",
        "iterations_per_call_max",
        "preparation_mean",
        "preparation_p95",
        "preparation_p99",
        "preparation_max",
        "codriver_mean",
        "codriver_p95",
        "codriver_p99",
        "codriver_max",
        "planner_cpu_core_seconds_per_sim_s",
        "codriver_core_demand",
        "total_core_demand",
        "planner_misses",
        "codriver_misses",
        "reserve_min",
        "reserve_below_warning_s",
        "handoff_rejections",
        "progress_rate",
    ]
    reports = []
    common_by_gamma = []
    for gamma in sorted({g for g, _ in groups}):
        selected = [r for r in rows if r["gamma"] == gamma]
        tag = f"g{gamma:g}".replace(".", "p")
        common = compare(
            [ROOT / r["case"] for r in selected],
            ROOT / f"measured_all_formulations_common_progress_{tag}.json",
        )
        prefix_rows = []
        for case in common["cases"]:
            laps = case["lap_prefixes"]
            prefix_rows.append(
                dict(
                    case=case["case"],
                    native_end_m=case["sampled_end_m"],
                    heading_tv=sum(lap["planned_heading_total_variation"] for lap in laps),
                    steering_tv=sum(lap["planned_steering_total_variation"] for lap in laps),
                    actual_steering_tv=sum(lap["actual_steering_total_variation"] for lap in laps),
                    rate_limit_s=sum(lap["actual_rate_limit_s"] for lap in laps),
                    tracking_ey_rms=case["tracking_ey_rms"],
                    clearance=case["clearance_min"],
                )
            )
        common_by_gamma.append(
            dict(
                gamma=gamma,
                shared_progress=[
                    common["cases"][0]["shared_start_m"],
                    common["cases"][0]["shared_end_m"],
                ],
                rows=prefix_rows,
            )
        )
    for (gamma, horizon), members in sorted(groups.items()):
        tag = f"g{gamma:g}_n{horizon}".replace(".", "p")
        common = compare(
            [ROOT / r["case"] for r in members], ROOT / f"measured_common_progress_{tag}.json"
        )
        metrics = {}
        for key in fields:
            values = [r[key] for r in members if isinstance(r.get(key), (float, int))]
            if values:
                metrics[key] = distribution(values)
        reports.append(
            dict(
                gamma=gamma,
                horizon=horizon,
                count=len(members),
                cases=[r["case"] for r in members],
                completed=sum(r["completed_laps"] >= 1 for r in members),
                boundary_runs=sum(r["boundary_count"] > 0 for r in members),
                solver_model_failure_runs=sum(
                    any(
                        r[k] > 0
                        for k in [
                            "solver_failures",
                            "planner_failures",
                            "forecast_or_gain_failures",
                        ]
                    )
                    for r in members
                ),
                fallback_runs=sum(r["fallback_events"] > 0 for r in members),
                common_progress=[
                    common["cases"][0]["shared_start_m"],
                    common["cases"][0]["shared_end_m"],
                ],
                metrics=metrics,
            )
        )
    report = dict(
        method="All completed measured outcomes retained. Distributions describe between-run "
        "variation of each named statistic, not pooled within-run timing quantiles. Five runs "
        "are descriptive; no confidence, probability or timing CI guarantee is inferred. "
        "First crossing starts at s_abs=1m, not a full geometric lap. Censored runs retain "
        "coverage and failure status. Unobserved lap times are excluded only from lap-time "
        "statistics; their count remains explicit. Normal OS background load is uncontrolled. "
        "Whole-record TV and rate-limit totals must not be ranked across unequal coverage. "
        "Use the common-progress tables for comparison and the whole records for failures.",
        groups=reports,
        common_by_gamma=common_by_gamma,
    )
    (ROOT / "measured_distributions.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Task007C fresh measured repetitions", "", report["method"], ""]
    outcomes = [
        {
            k: g[k]
            for k in [
                "gamma",
                "horizon",
                "count",
                "completed",
                "boundary_runs",
                "solver_model_failure_runs",
                "fallback_runs",
            ]
        }
        for g in reports
    ]
    lines += [table(outcomes, [(k, k) for k in outcomes[0]]), ""]
    for common in common_by_gamma:
        lines += [
            f"## Comparable observed progress, gamma {common['gamma']:g}",
            "",
            f"Shared interval {common['shared_progress'][0]:.6f}–"
            f"{common['shared_progress'][1]:.6f}m. A failure may shorten this interval; "
            "full-run failure counts remain above. No tail is invented.",
            "",
            table(common["rows"], [(k, k) for k in common["rows"][0]]),
            "",
        ]
    for g in reports:
        lines += [
            f"## gamma {g['gamma']:g}, N={g['horizon']}",
            "",
            f"{g['count']} runs; shared progress {g['common_progress'][0]:.6f}–"
            f"{g['common_progress'][1]:.6f}m. All per-run values: `measured_per_run.csv`.",
            "",
        ]
        stats = [dict(metric=k, **v) for k, v in g["metrics"].items()]
        lines += [
            table(
                stats,
                [(k, k) for k in ["metric", "count", "min", "median", "max", "mean", "sample_std"]],
            ),
            "",
        ]
    lines += [
        "## Individual outcomes",
        "",
        table(
            rows,
            [
                ("case", "Case"),
                ("completed_laps", "Crossings"),
                ("boundary_count", "Boundary samples"),
                ("solver_failures", "Solver failures"),
                ("lap_s", "Rolling time s"),
                ("heading_tv", "epsi TV rad"),
                ("steering_tv", "Nominal steering TV rad"),
                ("clearance", "Clearance m"),
                ("planner_misses", "Planner misses"),
                ("codriver_misses", "Codriver misses"),
            ],
        ),
        "",
    ]
    Path("docs/TASK007C_MEASURED_RESULTS.md").write_text("\n".join(lines))
    print("Measured distributions:", len(rows), "runs in", len(reports), "groups", flush=True)


if __name__ == "__main__":
    main()
