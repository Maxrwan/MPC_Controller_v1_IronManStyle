"""Explicit pairwise differences and first-divergence channels; no opaque outcome score."""

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

STATE = ["vx", "vy", "r", "e_psi", "s_abs", "e_y"]
TOLERANCES = {
    "state": 1e-9,
    "control": 1e-9,
    "decision": 1e-8,
    "parameters": 1e-10,
    "objective": 1e-8,
    "time": 1e-10,
}


def difference(a, b, tolerance, times=None, progress=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    lengths_equal = len(a) == len(b)
    length = min(len(a), len(b))
    if length == 0:
        return dict(
            max_abs=None,
            rms=None,
            rows_compared=0,
            lengths_equal=lengths_equal,
            tolerance=tolerance,
            first_row=None,
            first_time=None,
            first_progress=None,
        )
    a, b = a[:length], b[:length]
    if a.shape != b.shape:
        raise ValueError("Channel dimension mismatch")
    delta = np.abs(a - b)
    by_row = delta.reshape(length, -1).max(axis=1)
    selected = np.flatnonzero(by_row > tolerance)
    first = int(selected[0]) if len(selected) else None
    return dict(
        max_abs=float(delta.max()),
        rms=float(np.sqrt(np.mean(delta**2))),
        rows_compared=length,
        lengths_equal=lengths_equal,
        tolerance=tolerance,
        first_row=first,
        first_time=None if first is None or times is None else float(times[first]),
        first_progress=None if first is None or progress is None else float(progress[first]),
    )


def pair(folder_a, folder_b):
    a = pd.read_csv(folder_a / "states.csv", float_precision="round_trip")
    b = pd.read_csv(folder_b / "states.csv", float_precision="round_trip")
    # Fixed/replayed identical histories should have matching physical sample grids.
    n = min(len(a), len(b))
    same_grid = np.array_equal(a.time[:n], b.time[:n])
    if same_grid:
        av, bv = a[STATE].to_numpy()[:n], b[STATE].to_numpy()[:n]
        times = a.time.to_numpy()[:n]
    else:
        times, ia, ib = np.intersect1d(
            np.round(a.time, 12), np.round(b.time, 12), return_indices=True
        )
        av, bv = a[STATE].to_numpy()[ia], b[STATE].to_numpy()[ib]
    result = {
        "state_grid_exact": same_grid,
        "state_comparison_basis": "common physical timestamps; no state interpolation",
        "state_rows_original": [len(a), len(b)],
        "state_channel_rms": dict(zip(STATE, np.sqrt(np.mean((av - bv) ** 2, axis=0)).tolist())),
        "state": difference(av, bv, TOLERANCES["state"], times, av[:, 4]),
        "state_channel_max": dict(zip(STATE, np.max(abs(av - bv), axis=0).tolist())),
    }
    for kind, fields, tol in [
        ("controls", ["requested_delta", "requested_a_cmd", "delta", "a_cmd"], 1e-9)
    ]:
        aa = pd.read_csv(folder_a / (kind + ".csv"), float_precision="round_trip")
        bb = pd.read_csv(folder_b / (kind + ".csv"), float_precision="round_trip")
        result[kind] = difference(
            aa[fields], bb[fields], tol, aa.time.to_numpy(), aa.reference_s_abs.to_numpy()
        )
        for field in ["physical_latency", "application_time"]:
            result[field] = difference(aa[field], bb[field], TOLERANCES["time"], aa.time.to_numpy())
    events_a = json.loads((folder_a / "events.json").read_text())
    events_b = json.loads((folder_b / "events.json").read_text())
    ha = [h for h in events_a["handoffs"] if h["accepted"]]
    hb = [h for h in events_b["handoffs"] if h["accepted"]]
    result["accepted_handoff_time"] = difference(
        [h["time"] for h in ha], [h["time"] for h in hb], 1e-10, [h["time"] for h in ha]
    )
    result["accepted_handoff_plan_ids_identical"] = [h["plan_id"] for h in ha] == [
        h["plan_id"] for h in hb
    ]
    for field in [
        "reference_vx",
        "reference_vy",
        "reference_r",
        "reference_e_psi",
        "reference_e_y",
    ]:
        result["active_" + field] = difference(aa[field], bb[field], 1e-9, aa.time.to_numpy())
    ea = json.loads((folder_a / "events.json").read_text())["plans"]
    eb = json.loads((folder_b / "events.json").read_text())["plans"]
    for field, tol in [
        ("physical_delay", 1e-10),
        ("predicted_state", 1e-9),
        ("source_state", 1e-9),
    ]:
        aa = [p.get(field, 0) for p in ea]
        bb = [p.get(field, 0) for p in eb]
        result[field] = difference(
            aa, bb, tol, [p["release_time"] for p in ea], [p["source_state"][4] for p in ea]
        )
    prediction_a = json.loads((folder_a / "predictions.json").read_text())
    prediction_b = json.loads((folder_b / "predictions.json").read_text())
    valid_a = [r for r in prediction_a if r["prediction"] and "states" in r["prediction"]]
    valid_b = [r for r in prediction_b if r["prediction"] and "states" in r["prediction"]]
    for field in ["states", "controls", "slacks"]:
        result["predicted_" + field] = difference(
            [np.asarray(r["prediction"][field]).ravel() for r in valid_a],
            [np.asarray(r["prediction"][field]).ravel() for r in valid_b],
            1e-8,
            [r["release_time"] for r in valid_a],
        )
    if (folder_a / "telemetry.csv").exists() and (folder_b / "telemetry.csv").exists():
        ta = pd.read_csv(folder_a / "telemetry.csv")
        tb = pd.read_csv(folder_b / "telemetry.csv")
        for channel in [
            "node_adaptation_e_y",
            "node_adaptation_e_psi",
            "node_adaptation_vx",
            "error_e_y",
            "error_e_psi",
            "error_vy",
            "error_r",
            "nominal_delta",
        ]:
            result[channel] = difference(ta[channel], tb[channel], 1e-9, ta.time.to_numpy())
        aa = json.loads((folder_a / "analysis.json").read_text())
        ab = json.loads((folder_b / "analysis.json").read_text())
        result["aggregate_coverage_note"] = (
            "Whole-run aggregate metrics are descriptive only when durations differ; "
            "original C covers three laps and its replay one lap."
        )
        result["lap_time"] = difference(aa["lap_times"], ab["lap_times"], 1e-9)
        for key in [
            "apex_heading_total_variation",
            "apex_ey_total_variation",
            "steering_rate_limit_seconds",
        ]:
            result[key] = difference([aa["tracking"][key]], [ab["tracking"][key]], 1e-9)
        result["maximum_slack"] = difference(
            [aa["predicted_slack_max"]], [ab["predicted_slack_max"]], 1e-10
        )
    if (folder_a / "nlp_snapshots.json").exists() and (folder_b / "nlp_snapshots.json").exists():
        ra = json.loads((folder_a / "nlp_snapshots.json").read_text())
        rb = json.loads((folder_b / "nlp_snapshots.json").read_text())
        count = min(len(ra), len(rb))
        ra, rb = ra[:count], rb[:count]
        for field, tol in [("initial", 1e-8), ("parameters", 1e-10), ("solution", 1e-8)]:
            if all(r[field] is not None for r in ra + rb):
                result[field] = difference(
                    [r[field] for r in ra],
                    [r[field] for r in rb],
                    tol,
                    [r["release_time"] for r in ra],
                    [r["parameters"][4] for r in ra],
                )
        if all(r["previous_solution"] is not None for r in ra[1:] + rb[1:]):
            result["previous_solution"] = difference(
                [r["previous_solution"] for r in ra[1:]],
                [r["previous_solution"] for r in rb[1:]],
                1e-8,
                [r["release_time"] for r in ra[1:]],
            )
        for field, tol in [("objective", 1e-8), ("iterations", 0)]:
            result[field] = difference(
                [r["statistics"][field] for r in ra],
                [r["statistics"][field] for r in rb],
                tol,
                [r["release_time"] for r in ra],
            )
        nstate = 30  # Frozen N4 canonical state block.
        result["first_apex_control"] = difference(
            [r["solution"][nstate : nstate + 2] for r in ra],
            [r["solution"][nstate : nstate + 2] for r in rb],
            1e-9,
            [r["release_time"] for r in ra],
        )
    return result


def repetitions(output=Path("results/task007cr")):
    reports = {}
    for family in ["r1", "r2"]:
        for label in ["e", "f", "c"]:
            folders = sorted(p.parent for p in output.glob(f"{family}_{label}_*/summary.json"))
            comparisons = [
                dict(a=a.name, b=b.name, metrics=pair(a, b))
                for a, b in itertools.combinations(folders, 2)
            ]
            reports[f"{family}_{label}"] = comparisons
    for label, old in [("e", "b3_g2.5_w1"), ("f", "b3_g2.5_w2"), ("c", "b4_g2_w0")]:
        reports[f"original_{label}_replay"] = pair(
            Path("results/task007b") / old, output / f"r2_{label}_00"
        )
    (output / "repeatability.json").write_text(json.dumps(reports, indent=2) + "\n")
    return reports
