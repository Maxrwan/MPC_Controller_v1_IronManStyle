"""Synthetic smooth-envelope characterization; no fitted real-tire claims."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from apex.config import load_vehicle_parameters
from apex.models.tire.grip import SmoothCombinedGripTire
from apex.models.tire.linear import LinearAxleTire
from apex.models.vehicle.force_allocation import NormalLoadProportionalAllocation
from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "results/tire_model"
    out.mkdir(parents=True, exist_ok=True)
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    tire = SmoothCombinedGripTire(p.tire_road_friction_coefficient)
    linear = LinearAxleTire()
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for j, load in enumerate((5, 9.81, 15)):
        for a in (0, 1, 2, 6, -3):
            alpha = np.linspace(-1, 1, 501)
            fx = a / 9.81 * load
            ds = [tire.evaluate_combined(v, 45, load, 9.81, fx) for v in alpha]
            axes[0, j].plot(alpha, [d.lateral_force for d in ds], label=f"a={a:g} m/s²")
            axes[1, j].plot(alpha, [d.combined_utilization for d in ds], label=f"a={a:g}")
            for v, d in zip(alpha, ds):
                rows.append(
                    dict(
                        load=load,
                        a=a,
                        alpha=v,
                        fx=fx,
                        fy=d.lateral_force,
                        capacity=d.lateral_capacity,
                        utilization=d.combined_utilization,
                        linear=linear.evaluate(v, 45, load, 9.81).lateral_force,
                    )
                )
        axes[0, j].plot(alpha, 45 * load / 9.81 * alpha, "k--", label="linear reference")
        axes[0, j].set(
            title=f"Normal load {load:g} N", ylabel="Axle Fy [N]", ylim=(-load * 1.6, load * 1.6)
        )
        axes[1, j].axhline(1, color="k", ls="--")
        axes[1, j].set(ylabel="Combined utilization", ylim=(0, 1.05))
    for ax in axes.ravel():
        ax.set_xlabel("Slip angle [rad]")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Synthetic smooth combined grip: fixed-load longitudinal tradeoff")
    fig.tight_layout()
    fig.savefig(out / "force_slip.png", dpi=140)
    plt.close(fig)
    frame = pd.DataFrame(rows)
    frame.to_csv(out / "force_slip.csv", index=False)
    load_rows = []
    for a in (-3, 0, 1, 2):
        loads = QuasiStaticLongitudinalLoadTransfer().evaluate(p, a)
        forces = NormalLoadProportionalAllocation().allocate(p.mass * a, loads.front, loads.rear)
        ds = [
            tire.evaluate_combined(0.2, 45, fz, fz0, fx)
            for fz, fz0, fx in zip(
                (loads.front, loads.rear), (loads.front_static, loads.rear_static), forces
            )
        ]
        load_rows.append(
            dict(
                a=a,
                front_load=loads.front,
                rear_load=loads.rear,
                front_fx=forces[0],
                rear_fx=forces[1],
                front_capacity=ds[0].lateral_capacity,
                rear_capacity=ds[1].lateral_capacity,
                front_limit=ds[0].friction_capacity,
                rear_limit=ds[1].friction_capacity,
            )
        )
    small = []
    for a in (0, 1, 2, -3):
        d = tire.evaluate_combined(1e-5, 45, 9.81, 9.81, a)
        small.append(abs(d.lateral_force / (45e-5) - 1))
    report = {
        "synthetic_mu": 1.0,
        "force_curve_note": (
            "a=6 is a tire-only force-demand example beyond the vehicle "
            "actuator bound; no plant limit was changed"
        ),
        "maximum_combined_utilization": float(frame.utilization.max()),
        "maximum_bound_excess": float(max(0, frame.utilization.max() - 1)),
        "maximum_small_slip_relative_loss_alpha_1e_5": max(small),
        "load_transfer": load_rows,
    }
    (out / "characterization.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
