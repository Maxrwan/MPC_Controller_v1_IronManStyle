"""Summarize numerical probes without treating failed solves as valid branches."""

import json
from pathlib import Path

import numpy as np


def summarize(root=Path("results/task007cr")):
    records = json.loads((root / "nlp_replay.json").read_text())
    rows = []
    for r in records:
        base = r["exact"][0]
        row = dict(
            name=r["selection"]["name"],
            exact_max_difference=r["exact_max_difference"],
            captured_max_difference=r["captured_max_difference"],
            fresh_backend_max_difference=r["fresh_backend_max_difference"],
            exact_statuses=sorted({v["status"] for v in r["exact"]}),
            exact_iterations=sorted({v["iterations"] for v in r["exact"]}),
            exact_objective_range=float(np.ptp([v["objective"] for v in r["exact"]])),
            exact_primal_max=max(v["primal_residual"] for v in r["exact"]),
            exact_stationarity_max=max(v["stationarity_inf"] for v in r["exact"]),
            variants=[],
        )
        for v in r["sensitivity"]:
            row["variants"].append(
                dict(
                    label=v["label"],
                    success=v["success"],
                    status=v["status"],
                    primal_residual=v["primal_residual"],
                    stationarity_inf=v["stationarity_inf"],
                    eligible_solution_evidence=bool(v["success"] and v["primal_residual"] <= 1e-6),
                    delta_objective=v["objective"] - base["objective"],
                    delta_first_control=(
                        np.array(v["first_control"]) - base["first_control"]
                    ).tolist(),
                    max_solution_difference=float(
                        np.max(abs(np.array(v["solution"]) - base["solution"]))
                    ),
                    iterations=v["iterations"],
                )
            )
        rows.append(row)
    (root / "numerical_summary.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rows


if __name__ == "__main__":
    summarize()
