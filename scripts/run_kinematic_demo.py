"""Scripted CG kinematic propagation; all geometry is synthetic, no feedback control."""

import argparse
import csv
import json
from math import asin, atan, tan
from pathlib import Path

import numpy as np

from apex.config import load_vehicle_parameters
from apex.coordinates.frenet import frenet_to_global
from apex.models.vehicle.kinematic import DEFAULT_TIMESTEP, KinematicBicycle
from apex.state import CONTROL_NAMES, STATE_NAMES, StateIndex, state_vector
from apex.track import ClosedTrack
from apex.track.progress import lap_index
from apex.track.synthetic import circle_waypoints


def scripted_control(time: float, steering: float) -> np.ndarray:
    """Predetermined time schedule: accelerate for 2 s, cruise, brake after 6 s."""
    acceleration = 0.25 if time < 2.0 - 1e-12 else (-0.25 if time >= 6.0 - 1e-12 else 0.0)
    return np.array([steering, acceleration])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--dt", type=float, default=DEFAULT_TIMESTEP)
    parser.add_argument("--output-dir", type=Path, default=Path("results/kinematic_demo"))
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    if not np.isfinite(args.duration) or args.duration <= 0:
        parser.error("duration must be finite and positive")
    if not np.isfinite(args.dt) or args.dt <= 0:
        parser.error("dt must be finite and positive")
    root = Path(__file__).resolve().parents[1]
    parameters = load_vehicle_parameters(root / "configs/vehicles/synthetic_test_vehicle.yaml")
    radius = 5.0  # SYNTHETIC metres, not a physical circuit specification.
    track = ClosedTrack.from_waypoints(
        circle_waypoints(radius, count=128), left_width=0.6, right_width=0.9
    )
    model = KinematicBicycle(parameters, track, default_dt=args.dt)
    assert parameters.lr is not None and parameters.lf is not None
    # Analytical feedforward for an ideal circle, fixed before simulation starts.
    beta = asin(parameters.lr / radius)
    steering = atan((parameters.lf + parameters.lr) / parameters.lr * tan(beta))
    state = model.consistent_state(
        state_vector([2, 0, 0, -beta, track.length - 0.5, 0]), scripted_control(0, steering)
    )
    start = state.copy()
    rows = []
    time = 0.0
    step = 0
    while True:
        control = scripted_control(time, steering)
        # Instantaneous steering defines the algebraic channels of the logged state.
        state = model.consistent_state(state, control)
        d = model.diagnostics(state, control)
        rows.append([time, *state, *control, d.track_s, d.curvature])
        if time >= args.duration:
            break
        # Time schedules are sampled at step starts and held over each interval.
        next_time = min((step + 1) * args.dt, args.duration)
        state = model.step(state, control, next_time - time)
        time = next_time
        step += 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "states.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time", *STATE_NAMES, *CONTROL_NAMES, "track_s", "curvature"])
        writer.writerows(rows)
    data = np.array(rows)
    summary = {
        "label": "SYNTHETIC: not identified or representative of the final APEX vehicle",
        "duration_s": time,
        "dt_s": args.dt,
        "steps": step,
        "start_vx_m_per_s": float(start[StateIndex.VX]),
        "end_vx_m_per_s": float(state[StateIndex.VX]),
        "start_s_abs_m": float(start[StateIndex.S_ABS]),
        "end_s_abs_m": float(state[StateIndex.S_ABS]),
        "laps_crossed": lap_index(float(state[StateIndex.S_ABS]), track.length)
        - lap_index(float(start[StateIndex.S_ABS]), track.length),
        "max_abs_e_y_m": float(np.max(np.abs(data[:, 1 + StateIndex.E_Y]))),
        "track_length_m": track.length,
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not args.no_plot:
        plot_demo(track, data, args.output_dir / "trajectory.png")
    print(json.dumps(summary, indent=2))
    print(f"Results: {args.output_dir.resolve()}")


def plot_demo(track: ClosedTrack, data: np.ndarray, path: Path) -> None:
    """Render logged CG path and independent state channels without a GUI."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    samples = [track.sample(s) for s in np.linspace(0, track.length, 401)]
    xy = np.array([(p.x, p.y) for p in samples])
    normals = np.array([(-np.sin(p.heading), np.cos(p.heading)) for p in samples])
    left = xy + np.array([p.left_width for p in samples])[:, None] * normals
    right = xy - np.array([p.right_width for p in samples])[:, None] * normals
    poses = [
        frenet_to_global(
            track, row[1 + StateIndex.S_ABS], row[1 + StateIndex.E_Y], row[1 + StateIndex.E_PSI]
        )
        for row in data
    ]
    path_xy = np.array([(p.x, p.y) for p in poses])
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    ax = axes[0, 0]
    ax.plot(*xy.T, "k--", label="Centerline")
    ax.plot(*left.T, label="Left boundary")
    ax.plot(*right.T, label="Right boundary")
    ax.plot(*path_xy.T, color="tab:red", label="CG path")
    ax.scatter(*path_xy[0], marker="o", color="green", label="Start")
    ax.scatter(*path_xy[-1], marker="x", color="red", label="End")
    ax.set(xlabel="X [m]", ylabel="Y [m]", aspect="equal", title="Synthetic closed circuit")
    ax.legend(fontsize=8)
    axes[0, 1].plot(data[:, 0], data[:, 1 + StateIndex.VX])
    axes[0, 1].set(xlabel="Time [s]", ylabel="Body-longitudinal vx [m/s]")
    axes[1, 0].plot(data[:, 0], data[:, 1 + StateIndex.S_ABS])
    first_lap = lap_index(float(data[0, 1 + StateIndex.S_ABS]), track.length)
    last_lap = lap_index(float(data[-1, 1 + StateIndex.S_ABS]), track.length)
    for lap in range(first_lap + 1, last_lap + 1):
        axes[1, 0].axhline(lap * track.length, color="gray", linestyle=":")
    axes[1, 0].set(xlabel="Time [s]", ylabel="Continuous s_abs [m]")
    axes[1, 1].plot(data[:, 0], data[:, 1 + StateIndex.E_Y] * 1000)
    axes[1, 1].set(xlabel="Time [s]", ylabel="Lateral error e_y [mm]")
    for ax in axes.flat:
        ax.grid(alpha=0.25)
    fig.suptitle("Task 003 — SYNTHETIC scripted kinematic propagation (no feedback)")
    fig.savefig(path, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
