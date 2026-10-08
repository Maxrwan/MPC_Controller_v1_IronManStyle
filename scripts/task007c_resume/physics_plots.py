"""Human-review physics figures; curves are the configured synthetic law, not measurements."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from apex.models.tire.grip import SmoothCombinedGripTire


def plots(folder):
    folder = Path(folder)
    f = pd.read_csv(folder / "physics_telemetry.csv")
    e = pd.read_csv(folder / "horizon_prediction_error.csv")
    e = e[e.handoff_accepted]
    fig, axes = plt.subplots(3, 3, figsize=(23, 18), layout="constrained")
    mu = float(f.mu.iloc[0])
    tire = SmoothCombinedGripTire(mu)
    for ax, axle in zip(axes[0, :2], ["f", "r"]):
        alpha = f["alpha_" + axle]
        fy = f["fy" + axle]
        sample = f.iloc[len(f) // 2]
        nominal = sample["c" + axle]
        load = sample["fz" + axle]
        static = sample["fz" + axle + "_static"]
        fx = sample["fx_front" if axle == "f" else "fx_rear"]
        capacity = np.sqrt((mu * load) ** 2 - fx**2)
        effective = nominal * load / static
        extent = max(abs(alpha).max(), 3 * capacity / effective)
        slip = np.linspace(-extent, extent, 350)
        curve = [tire.evaluate_combined(a, nominal, load, static, fx).lateral_force for a in slip]
        ax.scatter(alpha, fy, c=f.time, s=2, alpha=0.35, cmap="viridis")
        ax.plot(slip, curve, "k--", label="Configured law at middle-sample load/Fx")
        ax.set(xlabel=f"alpha_{axle} [rad]", ylabel=f"Fy_{axle} [N]")
        ax.axhline(capacity, color="grey", alpha=0.5, lw=0.7)
        ax.axhline(-capacity, color="grey", alpha=0.5, lw=0.7)
        ax.legend(fontsize=7)
    axes[0, 2].scatter(f.normalized_lateral_demand, f.beta, s=2, alpha=0.35)
    axes[0, 2].set(xlabel="|ay| / (mu g)", ylabel="beta [rad]")
    angle = np.linspace(0, 2 * np.pi, 361)
    for ax, axle in zip(axes[1, :2], ["front", "rear"]):
        ax.plot(np.cos(angle), np.sin(angle), "k--", label="Unit friction boundary")
        ax.scatter(f["normalized_" + axle + "_x"], f["normalized_" + axle + "_y"], s=2, alpha=0.35)
        ax.set(xlabel=f"{axle} Fx/(mu Fz)", ylabel=f"{axle} Fy/(mu Fz)", aspect="equal")
        ax.legend(fontsize=8)
    for name, mask in [("low slip", f.low_slip), ("higher slip/transient", ~f.low_slip)]:
        axes[1, 2].scatter(
            f.loc[mask, "yaw_pseudo_reference"], f.loc[mask, "r"], s=2, alpha=0.35, label=name
        )
    limits = [
        min(f.yaw_pseudo_reference.min(), f.r.min()),
        max(f.yaw_pseudo_reference.max(), f.r.max()),
    ]
    axes[1, 2].plot(limits, limits, "k--")
    axes[1, 2].legend(fontsize=8)
    axes[1, 2].set(xlabel="vx * racing kappa_ref [rad/s]", ylabel="Actual yaw rate [rad/s]")
    for field, label in [
        ("ay_force", "(Fyf+Fyr)/m"),
        ("ay_balance", "Model dvy/dt + r vx"),
        ("ay_finite_difference", "Finite difference + r vx"),
    ]:
        axes[2, 0].plot(f.time, f[field], label=label, lw=0.7)
    axes[2, 0].set(xlabel="Physical time [s]", ylabel="ay [m/s²]")
    axes[2, 0].legend(fontsize=7)
    for field in ["vx", "vy", "r", "e_psi", "e_y"]:
        axes[2, 1].plot(f.time, f["one_step_" + field], label=field, lw=0.7)
        grouped = e.groupby("step")[field].apply(lambda v: np.sqrt(np.mean(v**2)))
        axes[2, 2].plot(grouped.index, grouped, "o-", label=field)
    axes[2, 1].set(xlabel="Physical time [s]", ylabel="One-step residual [SI per channel]")
    axes[2, 2].set(
        xlabel="Prediction horizon step", ylabel="Realized prediction error RMS [SI per channel]"
    )
    axes[2, 1].legend(fontsize=8)
    axes[2, 2].legend(fontsize=8)
    for ax in axes.ravel():
        ax.grid(alpha=0.2)
    fig.suptitle(
        folder.name + " — INTERNAL SYNTHETIC CONSISTENCY ONLY\n"
        "Observed slip-force cloud has varying load/Fx; dashed curve is a conditioned model slice\n"
        "Horizon errors use accepted packets and include subsequent replans and feedback"
    )
    fig.savefig(folder / "physics_review.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def phase_portraits(folders, output):
    fig, axes = plt.subplots(2, 3, figsize=(23, 12), layout="constrained")
    for folder in map(Path, folders):
        t = pd.read_csv(folder / "telemetry.csv")
        for column, sector in enumerate(["hairpin", "fast_sweeper", "technical_section"]):
            group = t[t.sector == sector]
            for _, lap in group.groupby("lap"):
                axes[0, column].plot(lap.actual_beta, lap.actual_r, lw=0.8, label=folder.name)
                axes[1, column].plot(lap.actual_e_y, lap.actual_e_psi, lw=0.8, label=folder.name)
            axes[0, column].set(title=sector, xlabel="beta [rad]", ylabel="r [rad/s]")
            axes[1, column].set(xlabel="ey [m]", ylabel="epsi [rad]")
    for ax in axes.ravel():
        ax.grid(alpha=0.2)
    axes[0, 0].legend(fontsize=6)
    fig.suptitle(
        "Sector phase portraits — direction changes are descriptive, not a single oscillation score"
    )
    fig.savefig(output, dpi=170, bbox_inches="tight")
    plt.close(fig)
