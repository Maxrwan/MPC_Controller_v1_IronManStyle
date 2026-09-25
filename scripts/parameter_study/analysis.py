"""Explicit Pareto relations and selected-candidate confirmation, without a score."""

import json
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from parameter_study.common import OUT, ROOT, canonical, database, design, records, run
from run_lqr_baseline import make_track

from apex.config import load_vehicle_parameters
from apex.control.baseline import BaselineController, cornering_reference
from apex.control.mpc.cost import CostScales, TerminalSchedule
from apex.control.mpc.preview import make_preview
from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.control.mpc.warm_start import shift_solution
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.optimization.base import NLPRequest
from apex.optimization.solvers.ipopt import IpoptSolver


def nondominated(values):
    a = np.asarray(values, dtype=float)
    return [
        i
        for i in range(len(a))
        if not any(np.all(a[j] <= a[i]) and np.any(a[j] < a[i]) for j in range(len(a)) if j != i)
    ]


def candidates():
    zero = [
        r
        for r in records()
        if r["configuration"]["track"] == "oval"
        and r["configuration"]["mode"] == "zero"
        and r["configuration"]["laps"] == 1
        and r["quality_pass"]
    ]
    if not zero:
        raise RuntimeError("No quality-qualified screening candidate")
    values = [
        [
            r["summary"]["solve_time"]["p95"],
            r["summary"]["full_run"]["rms_e_y"],
            r["summary"]["full_run"]["rms_speed_error"],
            r["summary"]["full_run"]["rms_e_psi"],
        ]
        for r in zero
    ]
    front = [zero[i] for i in nondominated(values)]
    reasonable = [r for r in front if r["compute_ratio_p95"] <= 1.0] or front
    a = min(reasonable, key=lambda r: r["summary"]["full_run"]["rms_e_y"])
    b = min(front, key=lambda r: r["summary"]["solve_time"]["p95"])
    c = min(front, key=lambda r: r["compute_ratio_p95"])
    measured = [
        r
        for r in records()
        if r["configuration"]["mode"] == "measured"
        and r["configuration"]["track"] == "oval"
        and r["configuration"]["laps"] == 2
        and r["quality_pass"]
        and r["summary"]["timing"]["missed_deadline_fraction"] <= 0.05
    ]
    if measured:
        best = min(measured, key=lambda r: r["summary"]["full_run"]["rms_e_y"])
        matches = [r for r in zero if canonical(design(r)) == canonical(design(best))]
        if matches:
            c = matches[0]
    d = next(
        r
        for r in records()
        if "A" in r["stages"]
        and r["configuration"]["track"] == "oval"
        and r["configuration"]["mode"] == "zero"
    )
    return {"A": a, "B": b, "C": c, "D": d}, front, zero


def analyze():
    frame = database()
    selected, front, zero = candidates()
    chosen = {
        k: {
            "experiment_id": r["id"],
            "configuration": r["configuration"],
            "configuration_hash": r["configuration_hash"],
            "compute_ratio_p95": r["compute_ratio_p95"],
            "quality_pass": r["quality_pass"],
        }
        for k, r in selected.items()
    }
    (OUT / "selected_candidates.json").write_text(json.dumps(chosen, indent=2) + "\n")
    ids = {r["id"] for r in front}
    result = {
        "criteria": [
            "p95_solve_time",
            "full_run_rms_e_y",
            "full_run_rms_speed_error",
            "full_run_rms_e_psi",
        ],
        "scope": (
            "Quality-qualified oval one-lap zero-latency screening only. "
            "Failure/slack/bounds are hard gates, not tiny numerical slack tie breakers."
        ),
        "nondominated": [r["id"] for r in front],
        "dominated": [r["id"] for r in zero if r["id"] not in ids],
        "selection_policy": (
            "A=min lateral RMS among front with p95/period<=1 when available; B=min p95 "
            "among quality front; C initially min compute ratio, then min measured "
            "lateral RMS among confirmed two-lap measured quality passes with <=5% "
            "misses; D=reference. No weighted score."
        ),
    }
    result["measured_deadline_fronts"] = {}
    for laps in (1, 2):
        measured = [
            r
            for r in records()
            if r["quality_pass"]
            and r["configuration"]["track"] == "oval"
            and r["configuration"]["mode"] == "measured"
            and r["configuration"]["laps"] == laps
        ]
        values = [
            [
                r["summary"]["timing"]["missed_deadline_fraction"],
                r["summary"]["full_run"]["rms_e_y"],
            ]
            for r in measured
        ]
        result["measured_deadline_fronts"][str(laps)] = {
            "criteria": ["missed_deadline_fraction", "full_run_rms_e_y"],
            "nondominated": [measured[i]["id"] for i in nondominated(values)],
            "scope": f"Quality-qualified measured oval {laps}-lap runs only",
        }
    (OUT / "pareto.json").write_text(json.dumps(result, indent=2) + "\n")
    z = frame[
        (frame.track == "oval")
        & (frame["mode"] == "zero")
        & (frame.stages.str.contains("B|C|D|E|F|G"))
    ]
    figs = [
        (
            "control_vs_computation",
            "solve_time_p95",
            "rms_e_y",
            "p95 solve [s]",
            "Full-run RMS lateral [m]",
            z,
        ),
        (
            "horizon_vs_time",
            "horizon",
            "solve_time_p95",
            "N",
            "p95 solve [s]",
            frame[frame.stages.str.split(",").apply(lambda s: "B" in s)],
        ),
        (
            "horizon_vs_tracking",
            "horizon",
            "rms_e_y",
            "N",
            "Full-run RMS lateral [m]",
            frame[frame.stages.str.split(",").apply(lambda s: "B" in s)],
        ),
        (
            "frequency_vs_deadlines",
            "frequency_hz",
            "missed_deadline_fraction",
            "Nominal frequency [Hz]",
            "Missed release fraction",
            frame[frame.stages.str.split(",").apply(lambda s: "D" in s)],
        ),
        (
            "frequency_vs_tracking",
            "frequency_hz",
            "rms_e_y",
            "Nominal frequency [Hz]",
            "Full-run RMS lateral [m]",
            frame[frame.stages.str.split(",").apply(lambda s: "D" in s)],
        ),
        (
            "compute_ratio_vs_tracking",
            "compute_ratio_p95",
            "rms_e_y",
            "p95 solve / period",
            "Full-run RMS lateral [m]",
            z,
        ),
        (
            "control_vs_deadlines",
            "missed_deadline_fraction",
            "rms_e_y",
            "Missed release fraction",
            "Full-run RMS lateral [m]",
            frame[(frame.track == "oval") & (frame["mode"] == "measured")],
        ),
    ]
    for name, x, y, xlabel, ylabel, data in figs:
        fig, ax = plt.subplots(figsize=(9, 6))
        groups = ["status", "mode"]
        if name.startswith("frequency_"):
            groups += ["horizon_seconds", "substeps"]
        for keys, group in data.groupby(groups):
            status, mode = keys[:2]
            label = f"{status}, {mode}"
            if len(keys) > 2:
                label += f", H={keys[2]:.2g}s, RK4={keys[3]}"
            ax.scatter(
                group[x],
                group[y],
                label=label,
                marker="x" if status == "rejected" else "o",
            )
        ax.set(xlabel=xlabel, ylabel=ylabel, title=name.replace("_", " "))
        ax.grid(alpha=0.25)
        ax.legend(fontsize=8)
        if "deadlines" in name or "frequency" in name:
            ax.text(
                0.01,
                0.01,
                "Failed runs retain shorter observed windows; compare completion status.",
                transform=ax.transAxes,
                fontsize=8,
            )
        fig.tight_layout()
        fig.savefig(OUT / (name + ".png"), dpi=150)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 6))
    for r in zero:
        ax.scatter(
            r["summary"]["solve_time"]["p95"] * 1000,
            r["summary"]["full_run"]["rms_e_y"],
            color="tab:blue" if r["id"] in ids else "lightgray",
        )
    for offset, (label, r) in enumerate(selected.items()):
        x = r["summary"]["solve_time"]["p95"] * 1000
        y = r["summary"]["full_run"]["rms_e_y"]
        ax.scatter(x, y, s=100, marker="*")
        ax.annotate(label, (x, y), xytext=(6, 6 + 12 * offset), textcoords="offset points")
    ax.set(
        xlabel="p95 solve [ms]",
        ylabel="Full-run RMS lateral [m]",
        title="Four-criterion Pareto set projected into two dimensions",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "pareto_selected.png", dpi=150)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 6))
    for r in records():
        if "C" in r["stages"] and "prediction_accuracy" in r:
            f = r["prediction_accuracy"]
            ax.scatter(
                f["maximum_scaled_error"],
                r["summary"]["solve_time"]["p95"] * 1000,
                marker="o" if f["accuracy_pass"] else "x",
            )
            ax.annotate(
                f"N{r['configuration']['n']}, s{r['configuration']['substeps']}",
                (f["maximum_scaled_error"], r["summary"]["solve_time"]["p95"] * 1000),
                fontsize=8,
            )
    ax.set(
        xscale="log",
        xlabel="Maximum scaled one-step error versus DOP853",
        ylabel="p95 solve [ms]",
        title="Prediction fidelity versus computation; crosses fail accuracy gate",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "prediction_error_vs_time.png", dpi=150)
    plt.close(fig)
    print("SELECTED", json.dumps({k: r["id"] for k, r in selected.items()}), flush=True)
    return selected


def validate_selected():
    selected = analyze()
    for label, r in selected.items():
        d = design(r)
        for track in ("circle", "oval"):
            run(
                "confirmation",
                f"candidate_{label}_{track}_zero",
                **d,
                track=track,
                laps=2,
                duration=80.0,
            )
        run(
            "confirmation",
            f"candidate_{label}_disturbance",
            **d,
            track="circle",
            ey=0.08,
            epsi=-0.04,
            laps=None,
            duration=12.0,
        )
        run(
            "confirmation",
            f"candidate_{label}_measured",
            **d,
            mode="measured",
            laps=2,
            duration=80.0,
        )
    # Re-evaluate C using actual measured confirmations, then preserve repeatable delay evidence.
    selected = analyze()
    d = design(selected["C"])
    for ms in (25, 45, 60):
        run(
            "confirmation",
            f"candidate_C_{ms}ms",
            **d,
            mode="injected",
            latency=ms / 1000,
            laps=2,
            duration=80.0,
        )
    future_data(selected)


def warm_benchmark():
    selected = analyze()
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track("circle")
    report = {}
    for label in ("C", "D"):
        c = selected[label]["configuration"]
        config = MPCConfig(
            horizon=c["n"],
            dt=1 / c["hz"],
            substeps=c["substeps"],
            costs=CostScales(**c["costs"]),
            tire_physics=RACING_TIRE_PHYSICS,
        )
        problem = MPCProblem(p, config)
        solver = IpoptSolver(problem, c["solver"])
        ref = cornering_reference(p, 2, track.sample(0).curvature)
        state = np.array([2.0, ref.vy, ref.yaw_rate, -0.04, 0, 0.08])
        preview = make_preview(track, p, lambda s: 2, 0, config.horizon, config.dt)
        params = problem.parameter_vector(
            state, np.zeros(2), preview, TerminalSchedule(p).matrix(2)
        )
        cold_guess = problem.pack(*problem.cold_start(state, np.zeros(2), preview))
        seed = solver.solve(NLPRequest(cold_guess, params))
        if not seed.success:
            raise RuntimeError("Warm benchmark initialization failed")
        warm_guess = problem.pack(*shift_solution(*problem.unpack(seed.solution), state))
        pairs = []
        for i in range(8):
            results = {}
            for name in ("cold", "warm") if i % 2 == 0 else ("warm", "cold"):
                result = solver.solve(
                    NLPRequest(cold_guess if name == "cold" else warm_guess, params)
                )
                results[name] = {
                    "success": result.success,
                    **{
                        k: result.statistics[k]
                        for k in ("solve_time", "iterations", "objective", "primal_infeasibility")
                    },
                }
            pairs.append(results)
        report[label] = {
            "configuration": c,
            "method": (
                "Eight alternating-order pairs; identical NLP/parameters; fixed cold and "
                "shifted-primal guesses, one backend construction"
            ),
            "cold_first_solve": {
                k: seed.statistics[k]
                for k in ("solve_time", "iterations", "objective", "primal_infeasibility")
            },
            "all_pairs_successful": all(
                pair[mode]["success"] for pair in pairs for mode in ("cold", "warm")
            ),
            "pairs": pairs,
        }
    (OUT / "warm_start_pairs.json").write_text(json.dumps(report, indent=2) + "\n")


def future_data(selected):
    c = selected["C"]
    folder = OUT / "runs" / c["id"]
    frame = pd.read_csv(folder / "states.csv")
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track("oval")
    baseline = BaselineController(p, track)
    times = []
    corrections = []
    for row in frame.iloc[np.linspace(0, len(frame) - 1, 300, dtype=int)].itertuples():
        state = np.array([row.vx, row.vy, row.r, row.e_psi, row.s_abs, row.e_y])
        baseline.reset()
        start = perf_counter()
        command = baseline.compute_control(state, {"dt": 0.01})
        times.append(perf_counter() - start)
        corrections.append(float(command[0] - row.delta))
    report = {
        "candidate_C": c["id"],
        "codriver_frequency_options_hz": [100, 200],
        "proposed_interpolation_hz": 100,
        "lateral_state_order": ["e_y", "e_psi", "v_y_error", "r_error"],
        "lateral_state_dimension": 4,
        "steering_input_dimension": 1,
        "observed_state_ranges": c["state_ranges"],
        "baseline_command_minus_nmpc_command_rad": {
            "rms": float(np.sqrt(np.mean(np.array(corrections) ** 2))),
            "max_abs": float(max(abs(np.array(corrections)))),
        },
        "correction_interpretation": (
            "Offline baseline command difference on selected NMPC states, not measured "
            "future trajectory-tracker corrections"
        ),
        "lqr_controller_wall_time": {
            "mean": float(np.mean(times)),
            "p95": float(np.percentile(times, 95)),
            "max": float(max(times)),
        },
        "lqr_timing_interpretation": (
            "Existing full BaselineController including geometry/reference lookup; reset "
            "outside timer; not isolated matrix multiplication and not a Pi benchmark"
        ),
        "trajectory_data": (
            "Every predictions.jsonl stores timestamps, sampled state, actual completion "
            "state/time, applied flag and nominal horizon reserve. Negative reserve is "
            "preserved; pending results have no actual completion state."
        ),
    }
    (OUT / "future_codriver_data.json").write_text(json.dumps(report, indent=2) + "\n")
