"""Reproducible synchronous study records, metrics and explicit acceptance gates."""

import hashlib
import json
import os
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from run_mpc_baseline import run_case

from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.models.tire.config import RACING_TIRE_PHYSICS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/mpc_parameter_study"
QUALITY = {"rms_e_y": 0.025, "rms_e_psi": 0.06, "rms_speed_error": 0.08}
DEFAULT = {
    "hz": 20.0,
    "n": 20,
    "substeps": 5,
    "costs": asdict(CostScales()),
    "solver": {},
    "warm_start": True,
    "track": "oval",
    "mode": "zero",
    "latency": 0.0,
    "laps": 1,
    "duration": 45.0,
    "ey": 0.0,
    "epsi": 0.0,
}


def canonical(config):
    return json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False)


def semantic_config(config):
    """Treat JSON 1 and 1.0 as the same numeric setting, preserving booleans."""
    if isinstance(config, dict):
        return {k: semantic_config(v) for k, v in config.items()}
    if isinstance(config, list):
        return [semantic_config(v) for v in config]
    if isinstance(config, (int, float)) and not isinstance(config, bool):
        return float(config)
    return config


def semantic_hash(config):
    return hashlib.sha256(canonical(semantic_config(config)).encode()).hexdigest()


def records():
    return [json.loads(p.read_text()) for p in sorted((OUT / "runs").glob("*/experiment.json"))]


def run(stage, label, **changes):
    spec = {**DEFAULT, **changes}
    if os.environ.get("APEX_STUDY_REPLICATE"):
        spec["replicate"] = os.environ["APEX_STUDY_REPLICATE"]
    serialized = canonical(spec)
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in records():
        if semantic_hash(old["configuration"]) == semantic_hash(spec):
            if stage not in old["stages"]:
                old["stages"].append(stage)
                (OUT / "runs" / old["id"] / "experiment.json").write_text(
                    json.dumps(old, indent=2) + "\n"
                )
            print("REUSE", stage, old["id"], flush=True)
            return old
    identifier = f"{label}_{digest[:10]}"
    folder = OUT / "runs" / identifier
    folder.mkdir(parents=True, exist_ok=True)
    metadata = {
        "id": identifier,
        "stages": [stage],
        "configuration_hash": digest,
        "configuration": spec,
        "environment": {
            "OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS"),
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            **{k: version(k) for k in ("numpy", "scipy", "casadi")},
        },
    }
    (folder / "configuration.json").write_text(json.dumps(metadata, indent=2) + "\n")
    config = MPCConfig(
        horizon=spec["n"],
        dt=1 / spec["hz"],
        substeps=spec["substeps"],
        costs=CostScales(**spec["costs"]),
        tire_physics=RACING_TIRE_PHYSICS,
    )
    summary = run_case(
        identifier,
        track_name=spec["track"],
        mode=spec["mode"],
        latency=spec["latency"],
        laps=spec["laps"],
        duration=spec["duration"],
        ey=spec["ey"],
        epsi=spec["epsi"],
        output=OUT / "runs",
        plots=False,
        mpc_config=config,
        solver_options=spec["solver"],
        warm_start=spec["warm_start"],
    )
    metadata["summary"] = summary
    states = pd.read_csv(folder / "states.csv")
    events = pd.read_csv(folder / "solver_events.csv")
    increments = np.diff(
        np.r_[0.0, states.loc[states.delta.ne(states.delta.shift()), "delta"].to_numpy()]
    )
    metadata["steering_rate_active_updates"] = int(
        np.isclose(abs(increments), 1 / spec["hz"], atol=1e-6, rtol=0).sum()
    )
    metadata["state_ranges"] = {
        k: [float(states[k].min()), float(states[k].max())]
        for k in ("vy", "r", "e_y", "e_psi", "delta")
    }
    metadata["prediction_reserve"] = {
        k: float(v)
        for k, v in zip(
            ("minimum", "mean"),
            [
                np.min(spec["n"] / spec["hz"] - events.latency),
                np.mean(spec["n"] / spec["hz"] - events.latency),
            ],
        )
    }
    reject = []
    if summary["failure"]:
        reject.append(summary["failure"])
    if spec["laps"] and len(summary["lap_times"]) < spec["laps"]:
        reject.append("required_laps_incomplete")
    if summary["solver_failures"]:
        reject.append("solver_failure")
    if summary["boundary_violations"]:
        reject.append("physical_boundary_violation")
    if summary["max_slack"] > 1e-4:
        reject.append("material_predicted_slack")
    if (
        max(summary["max_front_combined_utilization"], summary["max_rear_combined_utilization"])
        > 1 + 1e-12
    ):
        reject.append("grip_violation")
    metadata["rejection_reasons"] = reject
    metadata["quality_pass"] = not reject and all(
        summary["full_run"][k] <= v for k, v in QUALITY.items()
    )
    metadata["compute_ratio_mean"] = summary["solve_time"]["mean"] * spec["hz"]
    metadata["compute_ratio_p95"] = summary["solve_time"]["p95"] * spec["hz"]
    metadata["status"] = (
        "rejected"
        if reject
        else ("quality_pass" if metadata["quality_pass"] else "outside_quality_envelope")
    )
    (folder / "experiment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        "RESULT",
        identifier,
        metadata["status"],
        "ratio95",
        metadata["compute_ratio_p95"],
        flush=True,
    )
    database()
    return metadata


def database():
    rows = []
    for r in records():
        c, s = r["configuration"], r["summary"]
        row = {
            "experiment_id": r["id"],
            "stages": ",".join(r["stages"]),
            "configuration_hash": r["configuration_hash"],
            "configuration_json": canonical(c),
            "semantic_configuration_hash": semantic_hash(c),
            "frequency_hz": c["hz"],
            "period": 1 / c["hz"],
            "horizon": c["n"],
            "horizon_seconds": c["n"] / c["hz"],
            "substeps": c["substeps"],
            "track": c["track"],
            "mode": c["mode"],
            "injected_latency": c["latency"],
            "status": r["status"],
            "quality_pass": r["quality_pass"],
            "rejection_reasons": " | ".join(r["rejection_reasons"]),
            **{f"cost_{k}": v for k, v in c["costs"].items()},
            "ipopt_settings": canonical(s["solver_options"]),
            **s["nlp_dimensions"],
            **s["full_run"],
            "duration": s["duration"],
            "laps_completed": len(s["lap_times"]),
            "lap_times": json.dumps(s["lap_times"]),
            "mean_lap_time": float(np.mean(s["lap_times"])) if s["lap_times"] else None,
            "steering_effort": s["steering_squared_integral"],
            "acceleration_effort": s["acceleration_squared_integral"],
            "steering_rate_activity": r["steering_rate_active_updates"],
            "max_slack": s["max_slack"],
            "nonzero_slack_solves": s["nonzero_slack_solves"],
            "slack_above_1um_solves": s["slack_above_1um_solves"],
            "boundary_violations": s["boundary_violations"],
            "solver_failures": s["solver_failures"],
            "fallbacks": s["fallbacks"],
            "max_primal_residual": s["maximum_primal_residual"],
            "front_utilization": s["max_front_combined_utilization"],
            "rear_utilization": s["max_rear_combined_utilization"],
            "compute_ratio_mean": r["compute_ratio_mean"],
            "compute_ratio_p95": r["compute_ratio_p95"],
            **s["timing"],
        }
        if "prediction_accuracy" in r:
            row["prediction_error_max_scaled"] = r["prediction_accuracy"]["maximum_scaled_error"]
            row["prediction_accuracy_pass"] = r["prediction_accuracy"]["accuracy_pass"]
        for group in (
            "solve_time",
            "iterations",
            "staleness_index",
            "absolute_delta_e_y",
            "absolute_delta_e_psi",
            "absolute_delta_s_abs",
        ):
            row.update({group + "_" + k: v for k, v in s[group].items()})
        for group, stats in s["timing_decomposition"].items():
            row.update({group + "_" + k: v for k, v in stats.items()})
        rows.append(row)
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_csv(OUT / "experiments.csv", index=False)
    return frame


def select_stage(stage):
    return [r for r in records() if stage in r["stages"]]


def design(record):
    return {
        k: record["configuration"][k]
        for k in ("hz", "n", "substeps", "costs", "solver", "warm_start")
    }


def save_choice(key, record):
    path = OUT / "stage_choices.json"
    d = json.loads(path.read_text()) if path.exists() else {}
    d[key] = record["id"]
    path.write_text(json.dumps(d, indent=2) + "\n")


def choice(key):
    identifier = json.loads((OUT / "stage_choices.json").read_text())[key]
    return next(r for r in records() if r["id"] == identifier)
