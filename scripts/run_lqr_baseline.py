"""Reproducible synthetic Task 005 validation; no physical APEX parameter claims."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from apex.config import load_vehicle_parameters
from apex.control.baseline import BaselineController, ConstantSpeed, cornering_reference
from apex.control.baseline.lqr import continuous_matrices, discrete_matrices
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.metrics import tracking_metrics
from apex.simulation.runner import RunConfig, SimulationRunner
from apex.track import ClosedTrack
from apex.track.synthetic import circle_waypoints

ROOT = Path(__file__).resolve().parents[1]


def make_track(name):
    points = (
        circle_waypoints(5, count=64)
        if name == "circle"
        else circle_waypoints(1, count=72) * [7, 3]
    )
    return ClosedTrack.from_waypoints(
        points,
        left_width=0.6 if name == "circle" else 0.3,
        right_width=0.9 if name == "circle" else 0.5,
    )


def plot_result(track, result, path):
    rows, controls = result.states, result.controls
    t = np.array([r["time"] for r in rows])
    tc = np.array([r["time"] for r in controls])
    fig, axes = plt.subplots(4, 2, figsize=(14, 15))
    axes = axes.ravel()
    samples = [track.sample(s) for s in np.linspace(0, track.length, 500)]
    for label, offset in (("centerline", 0), ("left boundary", 1), ("right boundary", -1)):
        xy = np.array(
            [
                (
                    g.x
                    - (g.left_width if offset > 0 else g.right_width) * offset * np.sin(g.heading),
                    g.y
                    + (g.left_width if offset > 0 else g.right_width) * offset * np.cos(g.heading),
                )
                for g in samples
            ]
        )
        axes[0].plot(*xy.T, label=label, linewidth=1)
    xy = []
    for row in rows[::5]:
        g = track.sample(row["track_s"])
        xy.append([g.x - row["e_y"] * np.sin(g.heading), g.y + row["e_y"] * np.cos(g.heading)])
    axes[0].plot(*np.array(xy).T, label="nonlinear plant")
    axes[0].set(xlabel="X [m]", ylabel="Y [m]", aspect="equal")
    for ax, name, unit in (
        (axes[1], "e_y", "m"),
        (axes[2], "e_psi", "rad"),
        (axes[3], "vx", "m/s"),
        (axes[5], "r", "rad/s"),
        (axes[6], "vy", "m/s"),
        (axes[7], "s_abs", "m"),
    ):
        ax.plot(t, [r[name] for r in rows], label=name)
        ax.set(xlabel="time [s]", ylabel=f"{name} [{unit}]")
    for index, name in ((3, "reference_speed"), (5, "r_ref"), (6, "vy_ref")):
        axes[index].plot(tc, [r[name] for r in controls], "--", label=name)
    for name in ("delta", "delta_feedforward", "delta_feedback"):
        axes[4].plot(tc, [r[name] for r in controls], label=name)
    axes[4].set(xlabel="time [s]", ylabel="steering [rad]")
    for lap in range(1, int(rows[-1]["lap_index"]) + 1):
        axes[7].axhline(lap * track.length, color="gray", linestyle=":")
    for ax in axes:
        ax.legend(fontsize=8)
        ax.grid(alpha=0.25)
    fig.suptitle("Synthetic LQR/PI baseline — perfect state; nonlinear Task 004 plant")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def run_case(
    name,
    track_name,
    speed,
    output,
    *,
    duration=80.0,
    laps=2,
    ey=0.0,
    epsi=0.0,
    profile=False,
    plots=True,
):
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track(track_name)
    reference = (
        (lambda s: 2 + 0.5 * np.sin(2 * np.pi * s / track.length))
        if profile
        else ConstantSpeed(speed)
    )
    controller = BaselineController(p, track, reference)
    ref = cornering_reference(p, speed, track.sample(0).curvature)
    initial = np.array([speed, ref.vy, ref.yaw_rate, epsi, 0.0, ey])
    runner = SimulationRunner(
        DynamicBicycle(p, track),
        controller,
        track,
        RunConfig(duration=duration, target_laps=laps),
        controller_diagnostics=controller.diagnostics,
        reset_controller=controller.reset,
    )
    result = runner.run(initial)
    metrics = tracking_metrics(result, track.length, reference)
    metrics.update(
        {
            "track": track_name,
            "track_length": track.length,
            "initial_state": initial.tolist(),
            "reference": "2+0.5*sin(2*pi*s/L)" if profile else speed,
            "dt_plant": 0.005,
            "dt_control": 0.01,
        }
    )
    directory = output / name
    result.write_csv(directory)
    (directory / "summary.json").write_text(json.dumps(metrics, indent=2) + "\n")
    if plots:
        plot_result(track, result, directory / "baseline.png")
    print(json.dumps({"case": name, **metrics}), flush=True)
    return metrics


def linear_analysis(output):
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    controller = BaselineController(p, make_track("circle"))
    nodes = []
    for v, gain in zip(controller.lqr.nodes, controller.lqr.gains):
        a, b = continuous_matrices(p, v)
        ad, bd = discrete_matrices(p, v)
        poles = np.linalg.eigvals(ad - bd @ gain[None, :])
        nodes.append(
            {
                "speed": float(v),
                "gain": gain.tolist(),
                "controllability_rank": int(
                    np.linalg.matrix_rank(
                        np.hstack([np.linalg.matrix_power(a, j) @ b for j in range(4)])
                    )
                ),
                "poles_real_imag": [[float(z.real), float(z.imag)] for z in poles],
            }
        )
    spectral_radii = []
    for v in np.linspace(1, 3, 201):
        ad, bd = discrete_matrices(p, v)
        gain, _, _ = controller.lqr.gain(v)
        spectral_radii.append(float(max(abs(np.linalg.eigvals(ad - bd @ gain[None, :])))))
    analysis = {
        "nodes": nodes,
        "Q": controller.lqr.q.tolist(),
        "R": controller.lqr.r.tolist(),
        "kp": 1.0,
        "ki": 0.5,
        "max_interpolated_spectral_radius": max(spectral_radii),
        "interpolation_check_speeds": 201,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "linear_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite", action="store_true", help="Six two-lap runs, five disturbances, profile"
    )
    parser.add_argument("--track", choices=["circle", "oval"], default="circle")
    parser.add_argument("--speed", type=float, default=2.0)
    parser.add_argument("--duration", type=float, default=80.0)
    parser.add_argument("--laps", type=int, default=2)
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "results/lqr_baseline")
    args = parser.parse_args()
    linear_analysis(args.output)
    summaries = {}
    if args.suite:
        for track in ("circle", "oval"):
            for speed in (1.0, 2.0, 3.0):
                name = f"{track}_{speed:g}mps"
                summaries[name] = run_case(name, track, speed, args.output, plots=not args.no_plots)
        for name, ey, epsi in (
            ("ey_positive", 0.1, 0),
            ("ey_negative", -0.1, 0),
            ("heading_positive", 0, 0.05),
            ("heading_negative", 0, -0.05),
            ("combined", 0.08, -0.04),
        ):
            summaries[name] = run_case(
                name,
                "circle",
                2.0,
                args.output,
                duration=80.0 if name == "combined" else 12.0,
                laps=2 if name == "combined" else None,
                ey=ey,
                epsi=epsi,
                plots=not args.no_plots,
            )
        summaries["oval_profile"] = run_case(
            "oval_profile", "oval", 2.0, args.output, profile=True, plots=not args.no_plots
        )
    else:
        name = f"{args.track}_{args.speed:g}mps"
        summaries[name] = run_case(
            name,
            args.track,
            args.speed,
            args.output,
            duration=args.duration,
            laps=args.laps,
            plots=not args.no_plots,
        )
    filename = "suite_summary.json" if args.suite else "latest_summary.json"
    (args.output / filename).write_text(json.dumps(summaries, indent=2) + "\n")


if __name__ == "__main__":
    main()
