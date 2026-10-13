"""Descriptive retained N8 preparation ECDF; no new solver or timing measurements."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def export(output):
    output.mkdir(parents=True, exist_ok=False)
    rows, hashes = [], {}
    for folder in sorted(Path("results/task007c_resume").glob("g2_w0_vy1_r1_n8_measured_l1_rep*")):
        source = folder / "events.json"
        hashes[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
        for p in json.loads(source.read_text())["plans"]:
            if not p["startup"]:
                rows.append(
                    dict(
                        case=folder.name,
                        plan_id=p["plan_id"],
                        preparation_ms=1000 * p["planner_total_time"],
                        completed=p["completed"],
                        success=p["success"],
                    )
                )
    values = np.array([r["preparation_ms"] for r in rows])
    if not len(values) or not np.isfinite(values).all():
        raise ValueError("Missing/invalid retained preparation records")
    result = dict(
        count=len(values),
        runs=len(hashes),
        sources=hashes,
        startup_excluded=True,
        includes_final_launched_preparation=True,
        failed_preparations=sum(not r["success"] for r in rows),
        mean_ms=float(np.mean(values)),
        minimum_ms=float(min(values)),
        maximum_ms=float(max(values)),
        quantiles_ms={str(q): float(np.percentile(values, q)) for q in [25, 50, 75, 90, 95, 99]},
        deadlines=[
            dict(
                offset_ms=d,
                exceedances=int(sum(values > d)),
                exceedance_fraction=float(np.mean(values > d)),
            )
            for d in [50, 60, 70, 80]
        ],
    )
    with (output / "samples.csv").open("x", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
