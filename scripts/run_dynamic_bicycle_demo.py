"""SYNTHETIC dynamic cornering, acceleration and braking; predetermined inputs only."""

import argparse
import csv
import json
from dataclasses import asdict
from math import atan2
from pathlib import Path

import numpy as np

from apex.config import load_vehicle_parameters
from apex.coordinates.frenet import frenet_to_global
from apex.models.vehicle.dynamic_bicycle import DEFAULT_DYNAMIC_TIMESTEP, DynamicBicycle
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import STATE_NAMES, state_vector
from apex.track import ClosedTrack
from apex.track.progress import lap_index
from apex.track.synthetic import circle_waypoints


def synthetic_parameters() -> VehicleParameters:
    return load_vehicle_parameters(
        Path(__file__).resolve().parents[1] / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml"
    )


def synthetic_track(radius: float = 5.0) -> ClosedTrack:
    """Explicit synthetic circle and widths, not physical track data."""
    return ClosedTrack.from_waypoints(
        circle_waypoints(radius, count=128), left_width=0.6, right_width=0.9
    )


def command(time: float) -> np.ndarray:
    """Fixed steering; near-steady, acceleration and braking intervals."""
    acceleration = (
        0.5 if 2 - 1e-12 <= time < 4 - 1e-12 else (-0.5 if 6 - 1e-12 <= time < 8 - 1e-12 else 0.0)
    )
    return np.array([0.06, acceleration])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dt", type=float, default=DEFAULT_DYNAMIC_TIMESTEP)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--output-dir", type=Path, default=Path("results/dynamic_demo"))
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    if not np.isfinite(args.duration) or args.duration <= 0:
        parser.error("duration must be finite and positive")
    track = synthetic_track()
    model = DynamicBicycle(synthetic_parameters(), track, default_dt=args.dt)
    # Explicit near-steady synthetic seed, not a solved controller equilibrium.
    x = state_vector([2, 0.024, 0.4, -atan2(0.024, 2), track.length - 0.5, 0])
    rows = []
    time, step = 0.0, 0
    while True:
        u = command(time)
        d = model.diagnostics(x, u)
        row = {"time": time, **dict(zip(STATE_NAMES, x, strict=True)), "delta": u[0], **asdict(d)}
        rows.append(row)
        if time >= args.duration:
            break
        next_time = min((step + 1) * args.dt, args.duration)
        x = model.step(x, u, next_time - time)
        time, step = next_time, step + 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "states.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    series = {key: np.array([row[key] for row in rows]) for key in rows[0]}
    summary = {
        "label": "SYNTHETIC validation only; not experimentally identified APEX parameters",
        "duration_s": time,
        "dt_s": args.dt,
        "steps": step,
        "vx_range_m_per_s": [float(min(series["vx"])), float(max(series["vx"]))],
        "max_abs_vy_m_per_s": float(max(abs(series["vy"]))),
        "max_abs_r_rad_per_s": float(max(abs(series["r"]))),
        "max_abs_alpha_f_rad": float(max(abs(series["alpha_f"]))),
        "max_abs_alpha_r_rad": float(max(abs(series["alpha_r"]))),
        "max_abs_e_y_m": float(max(abs(series["e_y"]))),
        "start_s_abs_m": float(series["s_abs"][0]),
        "end_s_abs_m": float(series["s_abs"][-1]),
        "seams_crossed": lap_index(series["s_abs"][-1], track.length)
        - lap_index(series["s_abs"][0], track.length),
    }
    for key in [
        "fzf",
        "fzr",
        "cf_eff",
        "cr_eff",
        "front_lateral_utilization",
        "rear_lateral_utilization",
    ]:
        summary[key + "_range"] = [float(min(series[key])), float(max(series[key]))]
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not args.no_plot:
        plot_demo(track, series, args.output_dir / "dynamic_demo.png")
    print(json.dumps(summary, indent=2))
    print(f"Results: {args.output_dir.resolve()}")


def plot_demo(track: ClosedTrack, data: dict[str, np.ndarray], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(4, 3, figsize=(15, 16), layout="constrained")
    ax = axes.flat[0]
    samples = [track.sample(s) for s in np.linspace(0, track.length, 401)]
    center = np.array([(p.x, p.y) for p in samples])
    normal = np.array([(-np.sin(p.heading), np.cos(p.heading)) for p in samples])
    ax.plot(*center.T, "k--", label="Centerline")
    ax.plot(*(center + 0.6 * normal).T, label="Left boundary")
    ax.plot(*(center - 0.9 * normal).T, label="Right boundary")
    poses = [
        frenet_to_global(track, s, y, e)
        for s, y, e in zip(data["s_abs"], data["e_y"], data["e_psi"], strict=True)
    ]
    ax.plot([p.x for p in poses], [p.y for p in poses], label="Dynamic CG path")
    ax.scatter([poses[0].x], [poses[0].y], marker="o", label="Start")
    ax.scatter([poses[-1].x], [poses[-1].y], marker="x", label="End")
    ax.set(xlabel="X [m]", ylabel="Y [m]", aspect="equal")
    plots = [
        (["vx", "vy"], "Body CG velocity [m/s]"),
        (["r"], "Yaw rate [rad/s]"),
        (["alpha_f", "alpha_r"], "Slip angle [rad]"),
        (["fyf", "fyr"], "Lateral axle force [N]"),
        (["fzf", "fzr"], "Normal axle load [N]"),
        (["cf_eff", "cr_eff"], "Axle stiffness [N/rad]"),
        (["s_abs"], "Unwrapped progress [m]"),
        (["e_y"], "Lateral error [m]"),
        (["a_cmd"], "Commanded Fx/m [m/s²]"),
        (
            ["front_lateral_utilization", "rear_lateral_utilization"],
            "Lateral utilization (diagnostic)",
        ),
        (["e_psi"], "Heading error [rad]"),
    ]
    for ax, (keys, ylabel) in zip(list(axes.flat)[1:], plots, strict=True):
        if keys == ["vx", "vy"]:
            ax.plot(data["time"], data["vx"], label="vx", color="tab:blue")
            ax.set(xlabel="Time [s]", ylabel="vx [m/s]")
            lateral_axis = ax.twinx()
            lateral_axis.plot(data["time"], data["vy"], label="vy", color="tab:orange")
            lateral_axis.set_ylabel("vy [m/s]", color="tab:orange")
            lateral_axis.legend(loc="lower right", fontsize=7)
        else:
            for key in keys:
                ax.plot(data["time"], data[key], label=key)
            ax.set(xlabel="Time [s]", ylabel=ylabel)
    for ax in axes.flat:
        ax.grid(alpha=0.25)
        ax.legend(fontsize=7)
    fig.suptitle("Task 004 — SYNTHETIC dynamic bicycle, unsaturated linear tires, no feedback")
    fig.savefig(path, dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
