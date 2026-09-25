"""Task 006 nonlinear-plant NMPC, latency experiments and fair LQR comparisons."""

import argparse
import json
import platform
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from run_lqr_baseline import make_track

from apex.config import load_tire_physics, load_vehicle_parameters
from apex.control.baseline import BaselineController, ConstantSpeed, cornering_reference
from apex.control.mpc.controller import make_mpc
from apex.control.mpc.problem import MPCConfig
from apex.models.tire.config import RACING_TIRE_PHYSICS, TirePhysics
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.latency_metrics import summarize_run
from apex.simulation.runner import RunConfig, SimulationRunner
from apex.simulation.timing import LatencyConfig

ROOT = Path(__file__).resolve().parents[1]


def plot_case(directory, track):
    rows = pd.read_csv(directory / "states.csv")
    (
        pd.read_csv(directory / "controls.csv")
        if (directory / "controls.csv").exists()
        else pd.DataFrame()
    )
    event = (
        pd.read_csv(directory / "solver_events.csv")
        if (directory / "solver_events.csv").exists()
        else pd.DataFrame()
    )
    summary = json.loads((directory / "summary.json").read_text())
    fig, axes = plt.subplots(7, 2, figsize=(14, 24))
    axes = axes.ravel()
    g = [track.sample(s) for s in np.linspace(0, track.length, 500)]
    axes[0].plot([s.x for s in g], [s.y for s in g], label="centerline")
    for side in ("left", "right"):
        sign = 1 if side == "left" else -1
        width = np.array([s.left_width if side == "left" else s.right_width for s in g]) * sign
        axes[0].plot(
            [s.x - w * np.sin(s.heading) for s, w in zip(g, width)],
            [s.y + w * np.cos(s.heading) for s, w in zip(g, width)],
            "--",
            label=side,
        )
    trajectory = []
    for row in rows.iloc[::5].itertuples():
        sample = track.sample(row.track_s)
        trajectory.append(
            [
                sample.x - row.e_y * np.sin(sample.heading),
                sample.y + row.e_y * np.cos(sample.heading),
            ]
        )
    axes[0].plot(*np.asarray(trajectory).T, label="NumPy plant")
    axes[0].axis("equal")
    axes[0].set(xlabel="X [m]", ylabel="Y [m]")
    for ax, key, unit in [
        (axes[1], "e_y", "m"),
        (axes[2], "e_psi", "rad"),
        (axes[3], "vx", "m/s"),
        (axes[4], "delta", "rad"),
        (axes[5], "a_cmd", "m/s²"),
        (axes[13], "s_abs", "m"),
    ]:
        ax.plot(rows.time, rows[key], label=key)
        ax.set(xlabel="physical time [s]", ylabel=f"{key} [{unit}]")
    axes[3].axhline(summary["speed_reference"], linestyle="--", label="reference")
    if not event.empty:
        axes[7].plot(event.release_time, event.max_slack, label="max predicted slack [m]")
        axes[8].plot(event.release_time, event.solve_time * 1000, label="wall solve [ms]")
        axes[8].axhline(50, color="red", linestyle="--", label="50 ms period")
        axes[9].plot(event.release_time, event.latency * 1000, label="physical latency [ms]")
        axes[9].axhline(50, color="red", linestyle="--", label="50 ms period")
        axes[10].plot(event.application_time, event.staleness_index, label="normalized staleness")
        for key in ("delta_e_y", "delta_e_psi", "delta_s_abs"):
            axes[11].plot(event.application_time, event[key], label=key)
        axes[11].set_ylabel("SI components (m, rad, m)")
        axes[12].step(
            event.release_time,
            event.missed_releases.cumsum(),
            where="post",
            label="cumulative misses",
        )
        axes[12].set_title(f"Effective updates: {summary['timing']['effective_update_hz']:.2f} Hz")
        predfile = directory / "predictions.jsonl"
        if predfile.exists():
            lines = predfile.read_text().splitlines()
            for i in np.linspace(0, len(lines) - 1, min(4, len(lines)), dtype=int):
                pred = json.loads(lines[i])
                if "states" in pred:
                    x = np.asarray(pred["states"])
                    axes[6].plot(
                        np.arange(x.shape[1]) * pred.get("prediction_dt", 0.05),
                        x[5],
                        label=f"release {pred['release_time']:.2f}s",
                    )
            axes[6].set(xlabel="prediction time [s]", ylabel="predicted ey [m]")
    else:
        for ax in axes[6:13]:
            ax.text(0.5, 0.5, "Not applicable: LQR", ha="center", transform=ax.transAxes)
    for ax in axes:
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=7)
        ax.grid(alpha=0.25)
    fig.suptitle(f"{directory.name} — synthetic vehicle, independent nonlinear plant")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    fig.savefig(directory / "diagnostics.png", dpi=110)
    plt.close(fig)


def run_case(
    name,
    track_name="oval",
    controller_kind="mpc",
    mode="zero",
    latency=0.0,
    duration=80.0,
    laps=2,
    speed=2.0,
    ey=0.0,
    epsi=0.0,
    output=None,
    plots=True,
    tire_physics=RACING_TIRE_PHYSICS,
    mpc_config=None,
    solver_options=None,
    warm_start=True,
):
    output = ROOT / "results/mpc_grip" if output is None else Path(output)
    directory = output / name
    directory.mkdir(parents=True, exist_ok=True)
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track(track_name)
    reference = ConstantSpeed(speed)
    is_mpc = controller_kind == "mpc"
    mpc_config = mpc_config or MPCConfig(tire_physics=tire_physics)
    if mpc_config.tire_physics != tire_physics:
        raise ValueError("Plant/prediction tire physics must match for this benchmark")
    period = mpc_config.dt if is_mpc else (0.01 if controller_kind == "lqr100" else 0.05)
    construction_start = perf_counter()
    c = (
        make_mpc(
            p,
            track,
            config=mpc_config,
            speed_reference=reference,
            solver_options=solver_options,
            warm_start=warm_start,
        )
        if is_mpc
        else BaselineController(p, track, reference, dt=period)
    )
    construction_seconds = perf_counter() - construction_start
    plant = DynamicBicycle(p, track, tire_physics=tire_physics)
    ref = cornering_reference(p, speed, track.sample(0).curvature)
    initial = np.array([speed, ref.vy, ref.yaw_rate, epsi, 0.0, ey])
    runner = SimulationRunner(
        plant,
        c,
        track,
        RunConfig(
            duration=duration,
            target_laps=laps,
            dt_control=period,
            latency=LatencyConfig(mode, latency) if is_mpc else None,
        ),
        controller_diagnostics=c.diagnostics,
        reset_controller=c.reset,
        finalize_control=c.finalize_control if is_mpc else None,
        prediction_diagnostics=(lambda: c.last_prediction) if is_mpc else None,
    )
    result = runner.run(initial)
    # Postprocess diagnostics so characterization does not alter measured solve latency.
    from apex.state import STATE_NAMES

    for row in result.states:
        d = plant.diagnostics([row[k] for k in STATE_NAMES], [row["delta"], row["a_cmd"]])
        row.update({"tire_" + key: value for key, value in asdict(d).items()})
    for event, prediction in zip(result.events, result.predictions):
        offsets = prediction.get("prediction_offsets", [])
        prediction.update(
            prediction_timestamps=[event["release_time"] + v for v in offsets],
            completion_time=event["application_time"],
            scheduled_completion_time=event["scheduled_completion_time"],
            nominal_horizon_remaining_at_completion=(
                mpc_config.horizon * period - event["latency"]
            ),
            solve_start_state=[event[f"x_sample_{k}"] for k in STATE_NAMES],
            actual_state_at_completion=[event[f"x_apply_{k}"] for k in STATE_NAMES],
            completed=event["completed"],
            applied=event["applied"],
        )
    result.write_csv(directory)
    summary = summarize_run(result, track.length, reference)
    summary.update(
        mpc_config=asdict(mpc_config) if is_mpc else None,
        solver_options=c.solver.options if is_mpc else None,
        nlp_dimensions={
            "variables": len(c.problem.lbx),
            "equalities": c.problem.equality_count,
            "inequalities": c.problem.inequality_count,
        }
        if is_mpc
        else None,
        timing_decomposition={
            key: {
                "mean": float(np.mean([e[key] for e in result.events])),
                "p95": float(np.percentile([e[key] for e in result.events], 95)),
                "max": float(max(e[key] for e in result.events)),
            }
            for key in (
                "preview_time",
                "preview_geometry_time",
                "reference_generation_time",
                "warm_start_preparation_time",
                "parameter_update_time",
                "solver_adapter_time",
                "postprocessing_time",
                "total_compute_time",
            )
            if result.events and key in result.events[0]
        },
        maximum_primal_residual=max(
            (e.get("primal_infeasibility") or 0 for e in result.events), default=0
        ),
        tire_physics=asdict(tire_physics),
        controller_construction_seconds=construction_seconds,
        nlp_construction_seconds=c.problem.construction_seconds if is_mpc else None,
        solver_construction_seconds=c.solver.construction_seconds if is_mpc else None,
        max_front_combined_utilization=max(
            (r["tire_front_combined_utilization"] or 0) for r in result.states
        ),
        max_rear_combined_utilization=max(
            (r["tire_rear_combined_utilization"] or 0) for r in result.states
        ),
        name=name,
        track=track_name,
        controller=controller_kind,
        speed_reference=speed,
        initial_state=initial.tolist(),
        latency_mode=mode,
        injected_latency=latency,
        host={
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        rates={"plant": 0.005, "controller": period},
        track_length=track.length,
    )
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if plots:
        plot_case(directory, track)
    print(
        json.dumps(
            {
                "name": name,
                "settled": summary["settled"],
                "duration": summary["duration"],
                "laps": summary["distance_laps"],
                "solver_failures": summary["solver_failures"],
                "stop_reason": summary["stop_reason"],
                "timing": summary["timing"],
                "solve_time": summary["solve_time"],
            }
        ),
        flush=True,
    )
    return summary


def aggregate(output):
    summaries = {p.parent.name: json.loads(p.read_text()) for p in output.glob("*/summary.json")}
    base = summaries.get("oval_zero")
    for name, summary in summaries.items():
        period = summary["rates"]["controller"]
        for key in ("solve_time", "latency"):
            summary[key + "_percent_of_period"] = {
                stat: value / period * 100 if value is not None else None
                for stat, value in summary[key].items()
            }
        if base and name.startswith("oval_") and summary["controller"] == "mpc":
            end_time = min(summary["duration"], base["duration"])

            def window_metrics(case_name):
                frame = pd.read_csv(output / case_name / "states.csv")
                times = frame.time.to_numpy()
                grid = np.r_[0.0, times[(times > 0) & (times < end_time)], end_time]
                values = np.column_stack(
                    [np.interp(grid, times, frame[key]) for key in ("e_y", "e_psi", "vx")]
                )
                values[:, 2] -= summary["speed_reference"]
                rms = np.sqrt(np.trapezoid(values**2, grid, axis=0) / end_time)
                indices = np.searchsorted(times, grid[:-1], side="right") - 1
                inputs = frame[["delta", "a_cmd"]].to_numpy()[indices]
                effort = np.sum(inputs**2 * np.diff(grid)[:, None], axis=0)
                return dict(
                    zip(
                        (
                            "rms_e_y",
                            "rms_e_psi",
                            "rms_speed_error",
                            "steering_squared_integral",
                            "acceleration_squared_integral",
                        ),
                        map(float, np.r_[rms, effort]),
                    )
                )

            zero_window = window_metrics("oval_zero")
            case_window = window_metrics(name)
            comparisons = {key: case_window[key] - zero_window[key] for key in zero_window}
            comparisons["window_start"] = 0.0
            comparisons["window_end"] = end_time
            comparisons["case_metrics"] = case_window
            comparisons["zero_metrics"] = zero_window
            comparisons["max_slack_whole_run_change"] = summary["max_slack"] - base["max_slack"]
            comparisons["mean_lap_time"] = (
                float(np.mean(summary["lap_times"]) - np.mean(base["lap_times"]))
                if summary["lap_times"] and base["lap_times"]
                else None
            )
            summary["change_vs_zero"] = comparisons
        (output / name / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "suite_summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    cases = [
        summaries[name]
        for name in ("oval_zero", "oval_10ms", "oval_25ms", "oval_45ms", "oval_60ms", "oval_100ms")
        if name in summaries
    ]
    if cases:
        fig, axes = plt.subplots(2, 2, figsize=(11, 8))
        latency = [r["injected_latency"] * 1000 for r in cases]
        common_end = min(r["duration"] for r in cases)
        common_rms = []
        for case in cases:
            frame = pd.read_csv(output / case["name"] / "states.csv")
            times = frame.time.to_numpy()
            grid = np.r_[0.0, times[(times > 0) & (times < common_end)], common_end]
            lateral = np.interp(grid, times, frame.e_y)
            common_rms.append(float(np.sqrt(np.trapezoid(lateral**2, grid) / common_end)))
        values = [
            common_rms,
            [np.mean(r["lap_times"]) if r["lap_times"] else np.nan for r in cases],
            [r["staleness_index"]["mean"] for r in cases],
            [r["timing"].get("missed_deadline_fraction", 0) * 100 for r in cases],
        ]
        for ax, data, label in zip(
            axes.ravel(),
            values,
            [
                f"RMS ey [m], common 0–{common_end:g} s window",
                "Mean complete lap time [s]",
                "Mean normalized staleness",
                "Missed releases [%]",
            ],
        ):
            ax.plot(latency, data, "o-")
            ax.set(xlabel="Injected latency [ms]", ylabel=label)
            ax.grid(alpha=0.3)
        fig.suptitle(
            "Tracking compared over a common window; missing lap times mean no completed lap"
        )
        fig.tight_layout()
        fig.savefig(output / "latency_sweep.png", dpi=140)
        plt.close(fig)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite", choices=["zero", "latency", "comparisons", "disturbances", "speeds", "all"]
    )
    tire_selection = parser.add_mutually_exclusive_group()
    tire_selection.add_argument("--tire-model", choices=["linear", "smooth_combined_grip"])
    tire_selection.add_argument("--tire-config", type=Path)
    parser.add_argument("--mode", choices=["zero", "measured", "injected"], default="zero")
    parser.add_argument("--latency-ms", type=float, default=0.0)
    parser.add_argument("--controller", choices=["mpc", "lqr100", "lqr20"], default="mpc")
    parser.add_argument("--track", choices=["circle", "oval"], default="oval")
    parser.add_argument("--speed", type=float, default=2.0)
    parser.add_argument("--duration", type=float, default=80.0)
    parser.add_argument("--laps", type=int, default=2, help="0 selects duration-only")
    parser.add_argument("--name")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--plots-only", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "results/mpc_grip")
    args = parser.parse_args()
    physics = (
        TirePhysics(args.tire_model, "normal_load_proportional")
        if args.tire_model
        else load_tire_physics(
            args.tire_config or ROOT / "configs/models/synthetic_racing_tires.yaml"
        )
    )
    args.output.mkdir(parents=True, exist_ok=True)
    if args.plots_only:
        for path in args.output.glob("*/summary.json"):
            summary = json.loads(path.read_text())
            plot_case(path.parent, make_track(summary["track"]))
    elif args.suite:
        tasks = []
        if args.suite in ("zero", "all"):
            tasks += [dict(name=f"{track}_zero", track_name=track) for track in ("circle", "oval")]
        if args.suite in ("latency", "all"):
            tasks += [
                dict(
                    name="oval_zero" if ms == 0 else f"oval_{ms}ms",
                    mode="injected",
                    latency=ms / 1000,
                )
                for ms in (0, 10, 25, 45, 60, 100)
                if ms != 0 or args.suite != "all"
            ]
        if args.suite in ("comparisons", "all"):
            tasks += [
                dict(name=f"{track}_{controller}", track_name=track, controller_kind=controller)
                for track in ("circle", "oval")
                for controller in ("lqr100", "lqr20")
            ]
        if args.suite in ("disturbances", "all"):
            tasks += [
                dict(name=name, track_name="circle", ey=ey, epsi=epsi, duration=12.0, laps=None)
                for name, ey, epsi in [
                    ("ey_positive", 0.1, 0),
                    ("ey_negative", -0.1, 0),
                    ("heading_positive", 0, 0.05),
                    ("heading_negative", 0, -0.05),
                    ("combined", 0.08, -0.04),
                    ("constraint_active", 0.59, 0),
                ]
            ]
        if args.suite in ("speeds", "all"):
            tasks += [
                dict(name=f"circle_{speed}mps", track_name="circle", speed=speed)
                for speed in (1, 3)
            ]
        if args.suite in ("latency", "all"):
            tasks += [dict(name="oval_measured", mode="measured")]
        for task in tasks:
            run_case(**task, output=args.output, plots=not args.no_plots, tire_physics=physics)
    else:
        name = args.name or f"{args.track}_{args.controller}_{args.mode}_{args.latency_ms:g}ms"
        run_case(
            name,
            args.track,
            args.controller,
            args.mode,
            args.latency_ms / 1000,
            args.duration,
            args.laps or None,
            args.speed,
            output=args.output,
            plots=not args.no_plots,
            tire_physics=physics,
        )
    aggregate(args.output)


if __name__ == "__main__":
    main()
