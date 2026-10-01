"""Explicit pooled timing, paired replicate comparisons and numerical parity."""

import json

import numpy as np
import pandas as pd
from threading_study.config import OUT
from threading_study.worker import stats


def parity(reference, candidate):
    maxima = dict(objective=0.0, first_control=0.0, states=0.0, controls=0.0, slacks=0.0)
    passed = len(reference) == len(candidate)
    tolerances = dict(objective=1e-6, first_control=1e-6, states=1e-5, controls=1e-6, slacks=1e-7)
    for a, b in zip(reference, candidate):
        passed &= a["success"] and b["success"] and a["status"] == b["status"]
        passed &= a["primal_infeasibility"] <= 1e-6 and b["primal_infeasibility"] <= 1e-6
        for field, tolerance in tolerances.items():
            if a[field] is None or b[field] is None:
                passed = False
                continue
            x, y = np.asarray(a[field]), np.asarray(b[field])
            if x.shape != y.shape or not np.isfinite(x).all() or not np.isfinite(y).all():
                passed = False
                continue
            maxima[field] = max(maxima[field], float(np.max(abs(x - y))))
            passed &= np.allclose(x, y, atol=tolerance, rtol=1e-6 if field == "objective" else 0)
    return {
        "pass": bool(passed),
        "maximum_absolute_differences": maxima,
        "absolute_tolerances": tolerances,
        "objective_relative_tolerance": 1e-6,
    }


def records():
    return [
        (p.parent, json.loads(p.read_text())) for p in sorted((OUT / "runs").glob("*/summary.json"))
    ]


def analyze():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    conditions, rows, parity_results = {}, [], {}
    for folder, r in records():
        frame = pd.read_csv(folder / "observations.csv")
        monitor = json.loads((folder / "monitor.json").read_text())
        samples = [
            v
            for v in monitor["samples"]
            if r["measurement_start"] <= v["time"] <= r["measurement_end"]
        ]
        row = {
            "workload": r["workload"],
            "threads": r["threads"],
            "replicate": r["replicate"],
            "samples": len(frame),
            "success": r["all_success"],
            "backend": "Accelerate via IPOPT/MUMPS; requested ceiling",
            "backend_effective_cores": r["effective_backend_cores"],
            "controller_effective_cores": r["effective_controller_cores"],
            "sampled_peak_threads": max((v["threads"] for v in samples), default=None),
            "sampled_mean_threads": np.mean([v["threads"] for v in samples]) if samples else None,
            "sampled_peak_rss_bytes": max((v["rss_bytes"] for v in samples), default=None),
            "rss_peak_process_bytes": r["rss_peak_process_bytes"],
            **{
                f"{key}_{stat}": value
                for key, values in r["statistics"].items()
                for stat, value in values.items()
            },
            **{
                f"mean_{key}": float(frame[key].mean())
                for key in frame
                if key.startswith(("n_call_nlp_", "t_wall_nlp_", "t_proc_nlp_"))
            },
        }
        rows.append(row)
        conditions.setdefault((r["workload"], r["threads"]), []).append(frame)
        baseline = OUT / "runs" / f"{r['workload']}_t1_r{r['replicate']}" / "solutions.json"
        if baseline.exists():
            parity_results[folder.name] = parity(
                json.loads(baseline.read_text()),
                json.loads((folder / "solutions.json").read_text()),
            )
    loop_rows = []
    for path in sorted((OUT / "closed_loop").glob("*/summary.json")):
        report = json.loads(path.read_text())
        frame = pd.read_csv(path.parent / "solver_events.csv")
        loop_rows.append(
            {
                "workload": "C",
                "kind": "closed_loop",
                "threads": report["threading_control"]["requested_ceiling"],
                "replicate": report["threading_replicate"],
                "success": json.loads((path.parent / "quality.json").read_text())["quality_pass"],
                **report["full_run"],
                **report["timing"],
                "lap_times": json.dumps(report["lap_times"]),
                "solver_failures": report["solver_failures"],
                "fallbacks": report["fallbacks"],
                "max_slack": report["max_slack"],
                "boundary_violations": report["boundary_violations"],
                "front_utilization": report["max_front_combined_utilization"],
                "rear_utilization": report["max_rear_combined_utilization"],
                **{f"solve_time_{k}": v for k, v in stats(frame.solve_time).items()},
                **{
                    f"total_compute_time_{k}": v for k, v in stats(frame.total_compute_time).items()
                },
            }
        )
    pd.DataFrame([{**r, "kind": "benchmark"} for r in rows] + loop_rows).to_csv(
        OUT / "experiments.csv", index=False
    )
    if loop_rows:
        pd.DataFrame(loop_rows).to_csv(OUT / "closed_loop.csv", index=False)
    pooled = []
    for (workload, threads), frames in conditions.items():
        frame = pd.concat(frames, ignore_index=True)
        period = 0.1 if workload == "C" else 0.05
        row = {
            "workload": workload,
            "threads": threads,
            "replicates": len(frames),
            "samples": len(frame),
            "success": bool(frame.success.all()),
            "period": period,
            "effective_cores": frame.backend_cpu_time.sum() / frame.backend_measured_wall.sum(),
            "planner_core_demand": frame.controller_cpu_time.mean() / period,
            "planner_backend_core_demand": frame.backend_cpu_time.mean() / period,
            "controller_wall_duty": frame.total_compute_time.mean() / period,
            "rss_mean_mib": frame.rss_bytes.mean() / 2**20,
            "rss_max_mib": frame.rss_bytes.max() / 2**20,
            "threads_between_max": int(frame.threads_between_solves.max()),
            "max_primal_residual": frame.primal_infeasibility.max(),
        }
        for key in [
            "solve_time",
            "backend_cpu_time",
            "total_compute_time",
            "controller_cpu_time",
            "iterations",
        ]:
            row.update({key + "_" + k: v for k, v in stats(frame[key]).items()})
        row["compute_ratio_mean"] = row["total_compute_time_mean"] / period
        row["compute_ratio_p95"] = row["total_compute_time_p95"] / period
        for key in frame:
            if key.startswith(("n_call_nlp_", "t_wall_nlp_", "t_proc_nlp_")):
                row[key + "_mean"] = float(frame[key].mean())
        pooled.append(row)
    table = pd.DataFrame(pooled).sort_values(["workload", "threads"])
    for workload in table.workload.unique():
        baseline = table[(table.workload == workload) & (table.threads == 1)]
        if baseline.empty:
            continue
        baseline = baseline.iloc[0]
        mask = table.workload == workload
        for stat in ["mean", "p95"]:
            table.loc[mask, "speedup_" + stat] = (
                baseline["solve_time_" + stat] / table.loc[mask, "solve_time_" + stat]
            )
            table.loc[mask, "efficiency_" + stat] = (
                table.loc[mask, "speedup_" + stat] / table.loc[mask, "threads"]
            )
    table.to_csv(OUT / "pooled.csv", index=False)
    (OUT / "parity.json").write_text(json.dumps(parity_results, indent=2) + "\n")
    plots = [
        ("thread_vs_mean", "solve_time_mean", "Mean solve [s]"),
        ("thread_vs_p95", "solve_time_p95", "p95 solve [s]"),
        ("thread_vs_speedup", "speedup_p95", "p95 wall-time speedup"),
        ("thread_vs_efficiency", "efficiency_p95", "Efficiency per requested ceiling (fraction)"),
        ("thread_vs_effective_cores", "effective_cores", "Measured average active CPU cores"),
    ]
    for name, key, label in plots:
        fig, ax = plt.subplots(figsize=(8, 5))
        for workload, group in table.groupby("workload"):
            ax.plot(group.threads, group[key], "o-", label=workload)
        ax.set(xlabel="Requested Accelerate ceiling (not verified active count)", ylabel=label)
        ax.set_xticks([1, 2, 4, 8])
        if key == "effective_cores":
            ax.set_ylim(0, 1.1)
        ax.legend()
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT / (name + ".png"), dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for workload, group in table.groupby("workload"):
        ax.scatter(group.backend_cpu_time_mean * 1000, group.speedup_p95, label=workload)
        for row in group.itertuples():
            ax.annotate(
                f"{workload}, n={row.threads}",
                (row.backend_cpu_time_mean * 1000, row.speedup_p95),
                xytext=(
                    -8 if workload == "D" else 8,
                    -12 if (workload, row.threads) in [("C", 4), ("D", 2)] else 6,
                ),
                textcoords="offset points",
                ha="right" if workload == "D" else "left",
            )
    ax.margins(x=0.1, y=0.12)
    ax.set(xlabel="Mean backend CPU core-time [ms]", ylabel="p95 wall-time speedup")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "speedup_vs_core_time.png", dpi=150)
    plt.close(fig)
    for workload in ["C", "D"]:
        group = table[table.workload == workload]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(group.threads, group.compute_ratio_mean, "o-", label="mean total / period")
        ax.plot(group.threads, group.compute_ratio_p95, "s-", label="p95 total / period")
        ax.axhline(1, color="red", linestyle="--", label="nominal deadline")
        ax.set(
            xlabel="Requested Accelerate ceiling",
            ylabel="Total compute / controller period",
            title=f"Candidate {workload}",
        )
        ax.set_xticks([1, 2, 4, 8])
        ax.legend()
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT / f"{workload}_compute_ratio.png", dpi=150)
        plt.close(fig)
    selections = {}
    if not table[(table.workload == "C") & (table.threads == 1)].empty:
        c = table[table.workload == "C"]
        best = c.loc[c.solve_time_p95.idxmin()]
        per_rep = pd.DataFrame(rows)
        improvements = {}
        for n in c.threads:
            b = per_rep[(per_rep.workload == "C") & (per_rep.threads == 1)].set_index("replicate")
            t = per_rep[(per_rep.workload == "C") & (per_rep.threads == n)].set_index("replicate")
            ids = b.index.intersection(t.index)
            improvements[str(n)] = [
                float(b.loc[i, "solve_time_p95"] / t.loc[i, "solve_time_p95"]) for i in ids
            ]
        reliable = best.speedup_p95 >= 1 / 0.9 and 3 * sum(
            v > 1 for v in improvements[str(int(best.threads))]
        ) >= 2 * len(improvements[str(int(best.threads))])
        valid = all(v["pass"] for v in parity_results.values())
        selections = {
            "T1": 1,
            "lowest_observed_p95": int(best.threads),
            "Tbest_latency": int(best.threads) if reliable and valid else 1,
            "Tbest_efficiency": int(best.threads)
            if reliable and valid and best.effective_cores <= 1.1
            else 1,
            "Trecommended": int(best.threads)
            if reliable and valid and best.effective_cores <= 1.1
            else 1,
            "material_reliable_p95_improvement": bool(reliable and valid),
            "paired_p95_speedups": improvements,
            "policy": (
                "10% pooled p95 reduction, direction improves in >=2/3 replicates, "
                "numerical parity; prefer one core absent material benefit"
            ),
        }
        (OUT / "selected_threading.json").write_text(json.dumps(selections, indent=2) + "\n")
    print(
        table[
            [
                "workload",
                "threads",
                "solve_time_mean",
                "solve_time_p95",
                "speedup_p95",
                "effective_cores",
                "compute_ratio_p95",
            ]
        ].to_string(index=False)
    )
    print("SELECTION", json.dumps(selections))
    from threading_study.report import generate

    generate()


def audit():
    checks = []
    for folder, r in records():
        frame = pd.read_csv(folder / "observations.csv")
        assert len(frame) == r["samples"] and frame.success.all()
        assert (
            np.isfinite(frame[["solve_time", "backend_cpu_time", "total_compute_time"]]).all().all()
        )
        assert r["environment"]["VECLIB_MAXIMUM_THREADS"] == str(r["threads"])
        assert all(
            r["environment"][k] is None
            for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]
        )
        assert r["native_control"]["blas_threading_mode"] == (1 if r["threads"] == 1 else 0)
        assert r["max_primal_residual"] <= 1e-6
        baseline = OUT / "runs" / f"{r['workload']}_t1_r{r['replicate']}"
        b = json.loads((baseline / "summary.json").read_text())
        assert r["configuration"] == b["configuration"] and r["indices"] == b["indices"]
        assert r["input_file_sha256"] == b["input_file_sha256"]
        result = parity(
            json.loads((baseline / "solutions.json").read_text()),
            json.loads((folder / "solutions.json").read_text()),
        )
        assert result["pass"], result
        checks.append({"condition": folder.name, "samples": len(frame), "parity": result})
    assert checks, "No benchmark conditions found"
    closed_loop_checks = []
    for path in sorted((OUT / "closed_loop").glob("*/summary.json")):
        summary = json.loads(path.read_text())
        quality = json.loads((path.parent / "quality.json").read_text())
        assert quality["quality_pass"]
        assert json.loads((path.parent / "monitor.json").read_text())["exit_code"] == 0
        closed_loop_checks.append(
            {
                "condition": path.parent.name,
                "quality_pass": True,
                "missed_deadlines": summary["timing"]["missed_deadlines"],
            }
        )
    report = {
        "closed_loop_checks": closed_loop_checks,
        "conditions": len(checks),
        "samples": sum(v["samples"] for v in checks),
        "checks": checks,
    }
    (OUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}))
