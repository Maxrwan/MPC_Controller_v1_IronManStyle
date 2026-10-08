"""Measured copy cost only; do not infer an uninstrumented timing counterfactual."""

import json
from pathlib import Path

import numpy as np


def summarize(root=Path("results/task007cr")):
    report = {}
    for label in ["e", "f"]:
        values, totals, planner = [], [], []
        for path in sorted(root.glob(f"r4_{label}_*/summary.json")):
            summary = json.loads(path.read_text())
            snapshots = json.loads((path.parent / "nlp_snapshots.json").read_text())
            plans = json.loads((path.parent / "events.json").read_text())["plans"]
            values.extend(r["capture_seconds"] for r in snapshots)
            totals.append(summary["capture_total_seconds"])
            planner.extend(p["planner_total_time"] for p in plans)
        report[label] = dict(
            calls=len(values),
            copy_seconds=dict(
                zip(
                    ["min", "p25", "median", "p75", "p95", "max"],
                    np.quantile(values, [0, 0.25, 0.5, 0.75, 0.95, 1]).tolist(),
                )
            ),
            copy_seconds_total_per_run=totals,
            copy_to_total_planner_time_ratio=sum(values) / sum(planner),
            limits=(
                "Times cover array/statistics copies only. Context wrapper, bookkeeping, "
                "memory/cache effects are not isolated; no uninstrumented counterfactual. "
                "Serialization happens after physical simulation. Exact offline solve times "
                "may overlap offline analysis/regression and are not latency benchmarks."
            ),
        )
    (root / "instrumentation_cost.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    summarize()
