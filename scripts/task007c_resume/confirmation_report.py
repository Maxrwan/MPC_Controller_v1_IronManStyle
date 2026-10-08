"""Exact candidate repeat checks and per-lap sustained confirmation, offline only."""

import csv
import json
from pathlib import Path

from threading_study.config import configure_accelerate

ROOT = Path("results/task007c_resume")


def main():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not analyze during measured repetitions")
    configure_accelerate(1)
    from task007cr.compare import difference, pair

    for horizon in [6, 8]:
        original = ROOT / f"g2_w0_vy1_r1_n{horizon}_fixed_l1"
        repeated = ROOT / (original.name + "_rep00")
        report = pair(original, repeated)
        snapshots = [
            json.loads((f / "nlp_snapshots.json").read_text()) for f in [original, repeated]
        ]
        # The archived Task007C-R helper's first-control offset is frozen to N4.
        # Recompute this one channel from each candidate's canonical six-state layout.
        offset = 6 * (horizon + 1)
        report["first_apex_control"] = difference(
            [r["solution"][offset : offset + 2] for r in snapshots[0]],
            [r["solution"][offset : offset + 2] for r in snapshots[1]],
            1e-9,
        )
        report["snapshot_counts"] = [len(r) for r in snapshots]
        report["first_control_offset"] = offset
        report["cases"] = [original.name, repeated.name]
        assert report["state_grid_exact"]
        assert len(set(report["state_rows_original"])) == 1
        assert len(set(report["snapshot_counts"])) == 1
        assert report["accepted_handoff_plan_ids_identical"]
        for key, value in report.items():
            if isinstance(value, dict) and "max_abs" in value:
                assert value["lengths_equal"] and value["max_abs"] == 0, (horizon, key, value)
        report["exact_parity_passed"] = True
        (ROOT / f"n{horizon}_fixed_repeat_parity.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print("Exact repeat parity passed N", horizon, flush=True)

    fields = [
        "case",
        "lap",
        "segment",
        "crossing_duration_s",
        "planned_heading_total_variation",
        "planned_steering_total_variation",
        "actual_steering_total_variation",
        "actual_steering_reversals_db_0.001",
        "actual_rate_limit_s",
        "actual_beta_max_abs",
    ]
    rows = []
    for folder in sorted(ROOT.glob("g*_l3")):
        summary = json.loads((folder / "summary.json").read_text())
        assert len(summary["lap_times"]) == 3 and summary["stop_reason"] == "target_laps"
        for key in [
            "boundary_violations",
            "solver_failures",
            "planner_failures",
            "forecast_or_gain_failures",
            "fallback_events",
            "planner_misses",
            "codriver_misses",
        ]:
            assert summary[key] == 0, (folder, key)
        with (folder / "lap_oscillation.csv").open() as handle:
            laps = list(csv.DictReader(handle))
        assert len(laps) == 3
        for i, lap in enumerate(laps):
            row = {key: lap[key] for key in fields if key in lap}
            row.update(
                case=folder.name,
                segment="rolling" if i == 0 else "full geometric lap",
                crossing_duration_s=summary["lap_times"][i],
            )
            rows.append(row)
    with (ROOT / "sustained_per_lap.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Task007C sustained confirmation and deterministic repeats",
        "",
        "N6 and N8 gamma2 fixed-history repeats exactly match states, controls, physical "
        "availability, accepted handoffs, active references, predictions, NLP inputs, warm starts, "
        "solutions, objectives and iterations. Full snapshot and state counts match. "
        "The first-control offset is derived as 6(N+1), rather than the archived N4 offset.",
        "",
        "All eight sustained runs reach three lap-end crossings without boundary, solver, "
        "forecast, fallback or deadline failures. The first segment starts at s_abs=1m; "
        "only the following two are complete geometric laps. Oscillation metrics use native "
        "telemetry samples within each lap and reset at seams; crossing times are interpolated "
        "by the existing runner. The finite smooth trace was sufficient in all four cases.",
        "",
        "| Case | Lap | Segment | Time s | epsi TV rad | Nominal steering TV rad | "
        "Actual steering TV rad | Actual reversals (0.001 rad/s deadband) | Rate-limit s |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        keys = [
            "crossing_duration_s",
            "planned_heading_total_variation",
            "planned_steering_total_variation",
            "actual_steering_total_variation",
            "actual_steering_reversals_db_0.001",
            "actual_rate_limit_s",
        ]
        values = [f"{float(row[k]):.5f}" for k in keys]
        lines.append("| " + " | ".join([row["case"], row["lap"], row["segment"], *values]) + " |")
    lines += [
        "",
        "The sustained result is not a uniform improvement claim. At gamma2 under fixed "
        "timing, N6 and N8 reduce heading/steering variation and rate-limit time on both full "
        "laps. Under smooth timing, N6 improves the second lap but slightly worsens heading TV "
        "on the third (9.992 versus 9.855 rad), with nominal steering TV 6.520 versus 5.826 rad. "
        "N8 improves both full smooth laps. Actual small-amplitude reversal counts do not "
        "fall consistently; retain them alongside variation magnitude and rate-limit duration.",
        "",
        "At gamma2.2, N6 remains safe through both full laps under both histories, but the "
        "third smooth lap grows to heading TV 11.530 rad and nominal steering TV 7.518 rad "
        "from 8.957 and 5.446 on the second. This limits any claim of uniform sustained "
        "smoothness at the upper point. Fresh measured evidence must precede an envelope decision.",
        "",
        "These are sustained controlled-history checks, not fresh measured repetitions. "
        "Do not compare three-lap total variation with a one-segment screen. "
        "Exact artifacts: `n6_fixed_repeat_parity.json`, `n8_fixed_repeat_parity.json`, "
        "`sustained_per_lap.csv` under `results/task007c_resume/`.",
        "",
    ]
    Path("docs/TASK007C_SUSTAINED_CONFIRMATION.md").write_text("\n".join(lines))
    print("Sustained confirmation:", len(rows), "lap segments", flush=True)


if __name__ == "__main__":
    main()
