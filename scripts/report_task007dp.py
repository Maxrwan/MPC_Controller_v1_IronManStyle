"""Compact Task007D-P evidence and three figures; never benchmark during reporting."""

import argparse
import csv
import json
from pathlib import Path

from threading_study.config import configure_accelerate


def csv_write(path, rows):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        list(Path("results").rglob("MEASURED_ACTIVE"))
        or Path("results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Do not analyze or render during measurement")
    configure_accelerate(1)
    import numpy as np
    from task007dp.benchmark import distribution
    from task007dp.candidates import METHODS
    from task007dp.evaluation import CHANNELS, dataset, sha, statistics, write
    from task007dp.figures import render

    track, cases = dataset()
    rows = json.loads((args.input / "predictions.json").read_text())
    audit = json.loads((args.input / "audit.json").read_text())
    args.output.mkdir(parents=True, exist_ok=False)
    csv_write(args.output / "accuracy.csv", statistics(rows))
    releases = []
    for r in rows:
        for method in METHODS:
            p = r["predictions"][method]
            entry = {
                k: r[k]
                for k in (
                    "case",
                    "plan_id",
                    "release_time",
                    "target_time",
                    "estimated_delay",
                    "target_on_node",
                    "truth_kind",
                )
            }
            entry.update(
                method=method,
                failure=p["failure"],
                contaminated=bool(r["contamination"]),
                predicted_center_clearance=p["predicted_center_clearance"],
            )
            entry.update(
                {
                    "error_" + k: None if p["error"] is None else p["error"][i]
                    for i, k in enumerate(CHANNELS)
                }
            )
            entry.update(
                {
                    "predicted_" + k: None if p["predicted"] is None else p["predicted"][i]
                    for i, k in enumerate(CHANNELS)
                }
            )
            releases.append(entry)
    csv_write(args.output / "release_errors.csv", releases)
    timing = []
    benchmarks = {}
    for method in METHODS:
        b = json.loads((args.input / f"benchmark_{method}.json").read_text())
        benchmarks[method] = {k: v for k, v in b.items() if k != "samples"}
        for group in ["all", *sorted({r["case"] for r in b["samples"]})]:
            selected = [r for r in b["samples"] if group == "all" or r["case"] == group]
            entry = dict(
                method=method,
                group=group,
                calls=len(selected),
                initialization_wall_ms=b["initialization"]["wall_ms"],
                initialization_cpu_ms=b["initialization"]["cpu_ms"],
                precomputation_wall_ms=b["precomputation"]["wall_ms"],
                precomputation_cpu_ms=b["precomputation"]["cpu_ms"],
            )
            for clock in ("wall", "cpu"):
                values = distribution([r[clock + "_ms"] for r in selected])
                for key, field in [("median", "median"), ("p95", "p95"), ("maximum", "max")]:
                    entry[clock + "_" + field + "_ms"] = values[key]
            timing.append(entry)
    csv_write(args.output / "benchmark_summary.csv", timing)
    historical = []
    for name, c in cases.items():
        plans = [p for p in c["raw"]["plans"] if not p["startup"]]
        historical.append(
            dict(
                case=name,
                n=len(plans),
                preparation_median_ms=float(
                    np.median([p["planner_total_time"] * 1e3 for p in plans])
                ),
                prediction_median_ms=float(np.median([p["prediction_time"] * 1e3 for p in plans])),
                prediction_fraction_median_percent=float(
                    np.median([100 * p["prediction_time"] / p["planner_total_time"] for p in plans])
                ),
                solver_median_ms=float(np.median([p["solve_time"] * 1e3 for p in plans])),
                gain_median_ms=float(np.median([p["gain_time"] * 1e3 for p in plans])),
            )
        )
    csv_write(args.output / "historical_preparation.csv", historical)
    figure1 = []
    with Path("docs/task007d/d5/same_progress.csv").open() as stream:
        for r in csv.DictReader(stream):
            figure1.append(
                dict(
                    s_abs=r["A_s_abs"],
                    **{
                        h + "_" + name: r[h + "_" + old]
                        for h in ("A", "B")
                        for name, old in [
                            ("clearance", "clearance"),
                            ("ey", "e_y"),
                            ("nominal_ey", "nominal_ey"),
                            ("kind", "kind"),
                        ]
                    },
                )
            )
    csv_write(args.output / "figure1_data.csv", figure1)
    write(
        args.output / "summary.json",
        dict(
            audit=audit,
            benchmarks=benchmarks,
            predicted_boundary_crossings={
                m: sum(
                    r["predictions"][m]["predicted_center_clearance"] < 0
                    for r in rows
                    if r["predictions"][m]["predicted_center_clearance"] is not None
                )
                for m in METHODS
            },
            failures={
                m: sum(r["predictions"][m]["failure"] is not None for r in rows) for m in METHODS
            },
            contexts=len(rows),
            methods=list(METHODS),
            input_sha256={str(p): sha(p) for p in sorted(args.input.glob("*.json"))},
        ),
    )
    figures = render(args.output)
    write(
        args.output / "inventory.json",
        dict(
            figures=list(figures),
            files={p.name: sha(p) for p in sorted(args.output.iterdir())},
            report_sources={
                str(p): sha(p) for p in [Path(__file__), Path("scripts/task007dp/figures.py")]
            },
        ),
    )
    print(json.dumps(dict(contexts=len(rows), figure_files=list(figures), output=str(args.output))))


if __name__ == "__main__":
    main()
