"""Generate reviewable tables and portability data from retained observations."""

import json
import re

import pandas as pd
from threading_study.config import OUT, ROOT


def table(frame):
    headers = list(frame.columns)
    rows = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for values in frame.itertuples(index=False, name=None):
        rows.append(
            "| "
            + " | ".join(
                (f"{v:.3e}" if 0 < abs(v) < 1e-4 else f"{v:.4f}")
                if isinstance(v, float)
                else str(v)
                for v in values
            )
            + " |"
        )
    return "\n".join(rows)


def generate():
    pooled = pd.read_csv(OUT / "pooled.csv")
    experiments = pd.read_csv(OUT / "experiments.csv")
    sections = [
        "# Task 006.2.2 — generated measurements",
        "Generated from retained CSV/JSON/logs. All n values are requested ceilings; "
        "actual sampled NMPC thread count was one. Solver/controller timing columns are "
        "milliseconds; lap times are seconds.",
    ]
    for workload, group in pooled.groupby("workload"):
        sections.append(f"## Candidate {workload}")
        keys = [
            "threads",
            "samples",
            "solve_time_mean",
            "solve_time_p50",
            "solve_time_p95",
            "solve_time_p99",
            "solve_time_max",
            "solve_time_std",
            "solve_time_cv",
            "total_compute_time_mean",
            "total_compute_time_p95",
        ]
        frame = group[keys].copy()
        for k in keys:
            if "time_" in k and not k.endswith("cv"):
                frame[k] *= 1000
        sections.append(table(frame))
        keys = [
            "threads",
            "speedup_mean",
            "speedup_p95",
            "efficiency_mean",
            "efficiency_p95",
            "backend_cpu_time_mean",
            "controller_cpu_time_mean",
            "controller_cpu_time_p95",
            "effective_cores",
            "planner_core_demand",
            "rss_mean_mib",
            "rss_max_mib",
        ]
        frame = group[keys].copy()
        for k in keys:
            if "_time_" in k:
                frame[k] *= 1000
            elif "efficiency" in k:
                frame[k] *= 100
        sections.append(
            "Efficiencies are percentages of requested count, not CPU utilization.\n\n"
            + table(frame)
        )
        keys = ["threads", "iterations_mean"] + [
            k for k in pooled if k.startswith(("n_call_", "t_wall_"))
        ]
        frame = group[keys].copy()
        for k in keys:
            if k.startswith("t_wall"):
                frame[k] *= 1000
        sections.append(
            "Callback times are accumulated per solve, not per callback.\n\n" + table(frame)
        )
    phases = []
    for (workload, n), group in experiments[experiments.kind == "benchmark"].groupby(
        ["workload", "threads"]
    ):
        row = {"workload": workload, "threads": n}
        observations = pd.concat(
            [
                pd.read_csv(OUT / "runs" / f"{workload}_t{n}_r{int(r.replicate)}/observations.csv")
                for r in group.itertuples()
            ],
            ignore_index=True,
        )
        for phase in [
            "preview_time",
            "warm_start_preparation_time",
            "parameter_update_time",
            "solve_time",
            "solver_adapter_time",
            "postprocessing_time",
            "total_compute_time",
        ]:
            row[phase + "_mean_ms"] = observations[phase].mean() * 1000
        row["lifetime_peak_rss_mib"] = group.rss_peak_process_bytes.max() / 2**20
        phases.append(row)
    phase_frame = pd.DataFrame(phases)
    phase_frame.to_csv(OUT / "phases.csv", index=False)
    sections.extend(
        [
            "## Controller phases and lifetime memory",
            "Nested adapter/backend timers must not be added twice.",
            table(phase_frame),
        ]
    )
    component_rows = []
    names = [
        "PDSystemSolverTotal",
        "LinearSystemSymbolicFactorization",
        "LinearSystemFactorization",
        "LinearSystemBackSolve",
        "UpdateBarrierParameter",
    ]
    for path in sorted((OUT / "components").glob("*/worker.log")):
        workload, ceiling, _ = path.parent.name.split("_")
        for name in names:
            pattern = re.escape(name) + r"\.+:\s+([\d.]+) \(sys:\s+([\d.]+) wall:\s+([\d.]+)\)"
            for i, match in enumerate(re.finditer(pattern, path.read_text())):
                user, system, wall = map(float, match.groups())
                component_rows.append(
                    dict(
                        workload=workload,
                        threads=int(ceiling[1:]),
                        call=i,
                        component=name,
                        cpu_ms=1000 * (user + system),
                        wall_ms=1000 * wall,
                    )
                )
    components = pd.DataFrame(component_rows)
    components.to_csv(OUT / "solver_components.csv", index=False)
    sections.extend(
        [
            "## Supplementary IPOPT timing-print probes",
            "Two calls per condition, no warmup; 1 ms printed precision. Zero means "
            "rounded below precision, not free computation. Not a scaling benchmark; "
            "these nested timers overlap. Primary callback timings above "
            "are stronger evidence.",
            table(
                components.groupby(["workload", "threads", "component"], as_index=False)[
                    ["cpu_ms", "wall_ms"]
                ].mean()
            ),
        ]
    )
    loops = pd.read_csv(OUT / "closed_loop.csv")
    sections.append("## Fresh two-lap measured-latency confirmations")
    sections.append(
        table(
            loops[
                [
                    "threads",
                    "success",
                    "rms_e_y",
                    "rms_e_psi",
                    "rms_speed_error",
                    "lap_times",
                    "solver_failures",
                    "fallbacks",
                    "boundary_violations",
                    "max_slack",
                    "front_utilization",
                    "rear_utilization",
                ]
            ]
        )
    )
    timing_keys = [k for k in loops if k.startswith(("solve_time", "total_compute_time"))]
    timings = loops[["threads", "missed_deadlines", "effective_update_hz"] + timing_keys].copy()
    for k in timing_keys:
        if not k.endswith("cv"):
            timings[k] *= 1000
    sections.append(table(timings))
    portability = {}
    for workload in ["C", "D"]:
        row = pooled[(pooled.workload == workload) & (pooled.threads == 1)].iloc[0]
        raw = json.loads((OUT / "runs" / f"{workload}_t1_r0/summary.json").read_text())
        portability[workload] = dict(
            dimensions=raw["dimensions"],
            required_hz=1 / row.period,
            deadline_seconds=row.period,
            observed_useful_threads=1,
            mac_controller_cpu_seconds_mean=row.controller_cpu_time_mean,
            mac_controller_cpu_seconds_p95=row.controller_cpu_time_p95,
            mac_total_wall_seconds_p95=row.total_compute_time_p95,
            mac_backend_cpu_seconds_mean=row.backend_cpu_time_mean,
            mac_mean_iterations=row.iterations_mean,
            mac_peak_rss_mib=max(
                v["lifetime_peak_rss_mib"] for v in phases if v["workload"] == workload
            ),
            evaluation_counts={k: float(row[k]) for k in pooled if k.startswith("n_call")},
            target_measurement_required=True,
        )
    c = portability["C"]
    headroom = dict(
        candidate="C",
        hz=10,
        active_effective_cores=float(pooled.iloc[0].effective_cores),
        planner_average_core_seconds_per_second=10 * c["mac_controller_cpu_seconds_mean"],
        planner_p95_cpu_seconds_per_call=c["mac_controller_cpu_seconds_p95"],
        mean_wall_duty=float(pooled.iloc[0].controller_wall_duty),
        p95_wall_fraction_of_period=float(pooled.iloc[0].compute_ratio_p95),
        nominal_8_core_capacity_minus_planner=8 - 10 * c["mac_controller_cpu_seconds_mean"],
        caveat="Accounting only: heterogeneous cores, OS, observers and future workloads "
        "are not measured as available capacity; no scheduling or target guarantee.",
        codriver_budget_relation=(
            "additional_core_demand = codriver_hz * measured_cpu_seconds_per_call"
        ),
        illustrative_codriver_cpu_ms=1,
        illustrative_100_hz_core_demand=0.1,
        illustrative_200_hz_core_demand=0.2,
        illustrative_values_are_measured=False,
    )
    (OUT / "portability.json").write_text(json.dumps(portability, indent=2) + "\n")
    (OUT / "headroom.json").write_text(json.dumps(headroom, indent=2) + "\n")
    (ROOT / "docs/NMPC_MULTITHREADING_RESULTS.md").write_text("\n\n".join(sections) + "\n")


if __name__ == "__main__":
    generate()
