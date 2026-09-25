"""Scripted synthetic maneuvers and increasing-radius-demand snapshots."""

import json
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from check_mpc_parity import ConstantCurvatureChart

from apex.config import load_vehicle_parameters
from apex.control.baseline.references import cornering_reference
from apex.models.tire.config import RACING_TIRE_PHYSICS, TirePhysics
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.state import STATE_NAMES

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "results/tire_model"
    out.mkdir(parents=True, exist_ok=True)
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    rows = []
    summaries = {}
    for name, delta, duration in [("low", 0.005, 1.0), ("high", 0.4, 0.3)]:
        trajectories = {}
        for kind, physics in [
            ("linear", TirePhysics("linear", "normal_load_proportional")),
            ("grip", RACING_TIRE_PHYSICS),
        ]:
            model = DynamicBicycle(p, ConstantCurvatureChart(0), tire_physics=physics)
            x = np.array([3.0, 0, 0, 0, 1, 0])
            u = np.array([delta, 0.0])
            trajectory = []
            for tick in range(round(duration / 0.005) + 1):
                d = asdict(model.diagnostics(x, u))
                trajectory.append(x.copy())
                rows.append(
                    dict(case=name, model=kind, time=tick * 0.005, **dict(zip(STATE_NAMES, x)), **d)
                )
                if tick < round(duration / 0.005):
                    x = model.step(x, u, 0.005)
            trajectories[kind] = np.array(trajectory)
        summaries[name] = {
            "maximum_state_difference_by_channel": dict(
                zip(
                    STATE_NAMES,
                    np.max(abs(trajectories["linear"] - trajectories["grip"]), axis=0).tolist(),
                )
            )
        }
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "vehicle_comparison.csv", index=False)
    for name in summaries:
        for kind in ("linear", "grip"):
            sub = frame[(frame["case"] == name) & (frame.model == kind)]
            summaries[name][kind + "_max_utilization"] = float(
                sub[["front_combined_utilization", "rear_combined_utilization"]].max().max()
            )
    radius = 2.0
    snapshots = []
    for speed in np.linspace(1, 6, 101):
        ref = cornering_reference(p, speed, 1 / radius)
        x = np.array([speed, ref.vy, ref.yaw_rate, 0, 1, 0])
        u = np.array([ref.delta_dynamic, 0.0])
        for kind, physics in [
            ("linear", TirePhysics("linear", "normal_load_proportional")),
            ("grip", RACING_TIRE_PHYSICS),
        ]:
            d = asdict(
                DynamicBicycle(
                    p, ConstantCurvatureChart(1 / radius), tire_physics=physics
                ).diagnostics(x, u)
            )
            snapshots.append(dict(speed=speed, radius=radius, model=kind, **d))
    demand = pd.DataFrame(snapshots)
    demand.to_csv(out / "radius_demand.csv", index=False)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for kind in ("linear", "grip"):
        for j, name in enumerate(("low", "high")):
            sub = frame[(frame["case"] == name) & (frame.model == kind)]
            axes[0, j].plot(sub.time, sub.front_combined_utilization, label=kind + " front")
            axes[0, j].plot(sub.time, sub.rear_combined_utilization, "--", label=kind + " rear")
            axes[0, j].set(
                title=name + " scripted steering", xlabel="Time [s]", ylabel="Combined utilization"
            )
            axes[0, j].axhline(1, color="k", ls=":")
        sub = demand[demand.model == kind]
        axes[1, 0].plot(sub.speed, sub.fyf, label=kind + " front")
        axes[1, 1].plot(sub.speed, sub.front_combined_utilization, label=kind + " front")
    axes[1, 0].set(
        xlabel="Snapshot speed [m/s]",
        ylabel="Front lateral force [N]",
        title="R=2 m nominal linear-reference demand sweep",
    )
    axes[1, 1].set(xlabel="Snapshot speed [m/s]", ylabel="Front combined utilization")
    axes[1, 1].axhline(1, color="k", ls=":")
    for ax in axes.ravel():
        ax.grid(alpha=0.3)
        ax.legend()
    fig.tight_layout()
    fig.savefig(out / "vehicle_comparison.png", dpi=140)
    plt.close(fig)
    summaries["radius_sweep"] = {
        "radius": radius,
        "speed_range": [1, 6],
        "interpretation": (
            "Demand snapshots seeded by linear cornering references; "
            "NOT achieved steady grip-model circles or speed-ramp trajectories"
        ),
        "linear_max_utilization": float(
            demand[demand.model == "linear"][
                ["front_combined_utilization", "rear_combined_utilization"]
            ]
            .max()
            .max()
        ),
        "grip_max_utilization": float(
            demand[demand.model == "grip"][
                ["front_combined_utilization", "rear_combined_utilization"]
            ]
            .max()
            .max()
        ),
    }
    (out / "vehicle_comparison.json").write_text(json.dumps(summaries, indent=2) + "\n")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
