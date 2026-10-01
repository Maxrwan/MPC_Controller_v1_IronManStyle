"""Regenerate measured tables and backend profiling from retained experimental logs."""

import json

import numpy as np
import pandas as pd
from parameter_study.common import OUT, ROOT, database, records


def markdown(frame):
    def cell(v):
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v).replace("|", "/")

    return "\n".join(
        [
            "| " + " | ".join(frame.columns) + " |",
            "| " + " | ".join(["---"] * len(frame.columns)) + " |",
        ]
        + [
            "| " + " | ".join(map(cell, row)) + " |"
            for row in frame.itertuples(index=False, name=None)
        ]
    )


def generate():
    frame = database()
    groups = {
        digest: {"count": len(group), "experiment_ids": group.experiment_id.tolist()}
        for digest, group in frame.groupby("semantic_configuration_hash")
    }
    (OUT / "equivalent_configuration_groups.json").write_text(json.dumps(groups, indent=2) + "\n")
    selected = json.loads((OUT / "selected_candidates.json").read_text())
    pareto = json.loads((OUT / "pareto.json").read_text())
    lines = [
        "# Task006.2 measured tables",
        "",
        "Generated from experiment.json records; SI units unless a column says ms or percent.",
        "Tracking metrics are full-run time-weighted RMS, including startup. Failed runs",
        "retain their shorter observation windows and must not be ranked as completed laps.",
        "Local timings are not deadline guarantees. See NMPC_PARAMETER_STUDY.md.",
    ]
    base = [
        "experiment_id",
        "status",
        "rms_e_y",
        "rms_e_psi",
        "rms_speed_error",
        "solve_time_mean",
        "solve_time_p95",
        "total_compute_time_p95",
        "compute_ratio_p95",
        "solver_failures",
        "max_slack",
    ]
    extra = {
        "A": [
            "track",
            "mode",
            "duration",
            "laps_completed",
            "effective_update_hz",
            "missed_deadline_fraction",
            "front_utilization",
            "rear_utilization",
        ],
        "B": [
            "horizon",
            "variables",
            "equalities",
            "inequalities",
            "solve_time_p50",
            "solve_time_max",
            "iterations_mean",
            "iterations_max",
            "steering_effort",
            "acceleration_effort",
            "steering_rate_activity",
            "boundary_violations",
            "laps_completed",
            "mean_lap_time",
        ],
        "C": ["horizon", "substeps", "prediction_error_max_scaled", "prediction_accuracy_pass"],
        "D": [
            "frequency_hz",
            "substeps",
            "mode",
            "effective_update_hz",
            "missed_deadline_fraction",
            "staleness_index_p95",
            "laps_completed",
        ],
        "E": [
            "cost_lateral",
            "cost_dynamic",
            "cost_speed",
            "cost_control",
            "cost_rate",
            "iterations_mean",
            "iterations_max",
        ],
        "F": ["cost_terminal", "iterations_mean", "iterations_max", "max_primal_residual"],
        "G": ["ipopt_settings", "iterations_mean", "iterations_max", "max_primal_residual"],
        "confirmation": [
            "track",
            "mode",
            "injected_latency",
            "duration",
            "laps_completed",
            "effective_update_hz",
            "missed_deadline_fraction",
            "staleness_index_p95",
        ],
    }
    for stage, columns in extra.items():
        data = frame[frame.stages.str.split(",").apply(lambda s: stage in s)]
        lines.extend(["", f"## Stage {stage}", "", markdown(data[base + columns])])
    lines.extend(
        [
            "",
            "## Nondominated screening configurations",
            "",
            markdown(frame[frame.experiment_id.isin(pareto["nondominated"])][base]),
        ]
    )
    lines.extend(
        ["", "## Selected configurations", "", "```json", json.dumps(selected, indent=2), "```"]
    )
    rejected = frame[frame.status == "rejected"]
    lines.extend(
        [
            "",
            "## Rejected observations",
            "",
            markdown(
                rejected[["experiment_id", "rejection_reasons", "duration", "laps_completed"]]
            ),
        ]
    )
    profile = {}
    all_records = {r["id"]: r for r in records()}
    for label, candidate in selected.items():
        identifier = candidate["experiment_id"]
        record = all_records[identifier]
        events = pd.read_csv(OUT / "runs" / identifier / "solver_events.csv")
        internal = {}
        with (OUT / "runs" / identifier / "predictions.jsonl").open() as stream:
            for line in stream:
                stats = json.loads(line)["solver_statistics"]["ipopt_statistics"]
                for key, value in stats.items():
                    if key.startswith("t_wall_nlp_") or key.startswith("n_call_nlp_"):
                        internal.setdefault(key, []).append(value)
        profile[label] = {
            "experiment_id": identifier,
            "timing_decomposition": record["summary"]["timing_decomposition"],
            "backend_function_statistics": {
                k: {
                    "mean": float(np.mean(v)),
                    "p95": float(np.percentile(v, 95)),
                    "max": float(max(v)),
                }
                for k, v in internal.items()
            },
            "cold_first": {
                k: float(events.iloc[0][k])
                for k in ("solve_time", "iterations", "total_compute_time")
            },
            "normal_shifted_warm": {
                k: {
                    "mean": float(events.loc[events.warm_start, k].mean()),
                    "p95": float(events.loc[events.warm_start, k].quantile(0.95)),
                }
                for k in ("solve_time", "iterations", "total_compute_time")
            },
            "prediction_reserve": record["prediction_reserve"],
        }
    (OUT / "selected_timing_profiles.json").write_text(json.dumps(profile, indent=2) + "\n")
    (ROOT / "docs/NMPC_PARAMETER_STUDY_RESULTS.md").write_text("\n".join(lines) + "\n")
    print("Wrote measured tables and selected timing profiles")


if __name__ == "__main__":
    generate()
