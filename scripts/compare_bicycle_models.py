"""Controlled SYNTHETIC low-slip comparison; different models, not an equivalence test."""

import argparse
import csv
import json
from math import atan, tan
from pathlib import Path

import numpy as np
from run_dynamic_bicycle_demo import synthetic_parameters, synthetic_track

from apex.coordinates.frenet import frenet_to_global
from apex.models.vehicle.dynamic_bicycle import DEFAULT_DYNAMIC_TIMESTEP, DynamicBicycle
from apex.models.vehicle.kinematic import KinematicBicycle
from apex.state import STATE_NAMES, StateIndex, state_vector


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results/bicycle_comparison"))
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    p, track = synthetic_parameters(), synthetic_track(15.0)
    dt, duration = DEFAULT_DYNAMIC_TIMESTEP, 4.0
    control = np.array([0.02, 0.0])
    beta = atan(0.5 * tan(control[0]))
    initial = state_vector([2, 2 * tan(beta), 2 / 0.15 * tan(beta), -beta, 1, 0])
    models = {"kinematic": KinematicBicycle(p, track), "dynamic": DynamicBicycle(p, track)}
    histories = {}
    for name, model in models.items():
        x = initial.copy()
        history = [x.copy()]
        for _ in range(round(duration / dt)):
            x = model.step(x, control, dt)
            history.append(x.copy())
        histories[name] = np.array(history)
    time = np.arange(round(duration / dt) + 1) * dt
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, history in histories.items():
        with (args.output_dir / f"{name}.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time", *STATE_NAMES, "delta", "a_cmd"])
            writer.writerows([[t, *x, *control] for t, x in zip(time, history, strict=True)])
    positions = {}
    for name, history in histories.items():
        poses = [
            frenet_to_global(track, x[StateIndex.S_ABS], x[StateIndex.E_Y], x[StateIndex.E_PSI])
            for x in history
        ]
        positions[name] = np.array([[p.x, p.y] for p in poses])
    dynamic, kinematic = histories["dynamic"], histories["kinematic"]
    difference = dynamic[-1] - kinematic[-1]
    diagnostic = [models["dynamic"].diagnostics(x, control) for x in dynamic]
    summary = {
        "label": "SYNTHETIC low-slip comparison; neither output establishes physical truth",
        "duration_s": duration,
        "dt_s": dt,
        "delta_rad": float(control[0]),
        "a_cmd": 0.0,
        "same_initial_state": initial.tolist(),
        "final_dynamic_minus_kinematic": dict(zip(STATE_NAMES, difference.tolist(), strict=True)),
        "max_position_separation_m": float(
            np.max(np.linalg.norm(positions["dynamic"] - positions["kinematic"], axis=1))
        ),
        "dynamic_vx_range_m_per_s": [
            float(min(dynamic[:, StateIndex.VX])),
            float(max(dynamic[:, StateIndex.VX])),
        ],
        "max_abs_dynamic_front_slip_rad": max(abs(d.alpha_f) for d in diagnostic),
        "max_abs_dynamic_rear_slip_rad": max(abs(d.alpha_r) for d in diagnostic),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    if not args.no_plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
        for name in histories:
            axes[0, 0].plot(*positions[name].T, label=name)
        axes[0, 0].set(xlabel="X [m]", ylabel="Y [m]", aspect="equal", title="CG trajectory")
        channels = [
            (StateIndex.VX, "vx [m/s]"),
            (StateIndex.VY, "vy [m/s]"),
            (StateIndex.YAW_RATE, "r [rad/s]"),
            (StateIndex.S_ABS, "s_abs [m]"),
            (StateIndex.E_Y, "e_y [m]"),
        ]
        for ax, (index, label) in zip(list(axes.flat)[1:], channels, strict=True):
            for name, history in histories.items():
                ax.plot(time, history[:, index], label=name)
            ax.set(xlabel="Time [s]", ylabel=label)
        for ax in axes.flat:
            ax.legend()
            ax.grid(alpha=0.25)
        fig.suptitle("SYNTHETIC low-slip comparison — same initial state and held input")
        fig.savefig(args.output_dir / "comparison.png", dpi=140)
        plt.close(fig)
    print(json.dumps(summary, indent=2))
    print(f"Results: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
