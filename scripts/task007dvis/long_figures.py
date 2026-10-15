"""Preliminary native-evidence figures; no resampling of controls or packet authority."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from apex.state import STATE_NAMES

PAIRS = (("controlled_A", "controlled_C70"), ("measured_A_1", "measured_C70_1"))
COLORS = ("#176caa", "#cf541c")
LABELS = ("A", "C70")
TITLES = ("Controlled 35/55/45/25 ms", "Measured pair 1; C70 censored")
PREFIX = "VIS-1L | N8, gamma2, predictor A, driver 5 ms | "


def save(fig, output, name, title):
    fig.suptitle(PREFIX + title, fontsize=12)
    fig.savefig(output / name, dpi=150)
    plt.close(fig)


def common_frames(data, pair):
    frames = [data[n][0] for n in pair]
    end = min(f.s_abs.iloc[-1] for f in frames)
    return [f[f.s_abs <= end] for f in frames]


def style(ax, ylabel, xlabel="unwrapped progress (m)"):
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid(alpha=0.2)


def render(data, report, windows, cycles, output):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), layout="constrained")
    for ax, pair, title in zip(axes, PAIRS, TITLES):
        frames = [data[n][0] for n in pair]
        ax.plot(frames[0].planning_x, frames[0].planning_y, ":", color="black", label="Planning")
        for f, label, color in zip(frames, LABELS, COLORS):
            ax.plot(f.x_world, f.y_world, color=color, lw=0.9, label="vehicle " + label)
            ax.plot(
                f.reference_x,
                f.reference_y,
                "--",
                color=color,
                lw=0.7,
                alpha=0.6,
                label="active APEX " + label,
            )
            ax.plot(f.x_world.iloc[-1], f.y_world.iloc[-1], "x", color=color, ms=9)
        ax.set_title(title + "\nX = recorded endpoint; all observed path shown", fontsize=10)
        ax.set_aspect("equal")
        style(ax, "derived world y (m)", "derived world x (m)")
        ax.legend(fontsize=8)
    save(fig, output, "trajectory_overlay.png", "native Frenet states mapped to XY")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4), layout="constrained")
    for ax, pair, title in zip(axes, PAIRS, TITLES):
        for f, label, color in zip(common_frames(data, pair), LABELS, COLORS):
            ax.plot(f.s_abs, f.vx, color=color, lw=0.9, label="vehicle " + label)
            ax.plot(f.s_abs, f.reference_vx, "--", color=color, lw=0.5, label="APEX " + label)
        ax.plot(f.s_abs, f.planning_vx, ":", color="black", lw=0.8, label="Planning")
        ax.set_title(title, fontsize=10)
        style(ax, "longitudinal speed (m/s)")
        ax.legend(fontsize=7)
    save(fig, output, "speed_progress.png", "shared observed progress only")

    fig, axes = plt.subplots(4, 2, figsize=(13, 11), layout="constrained")
    channels = [
        ("delta", "nominal_delta", "steering (rad)"),
        ("a_cmd", "nominal_a_cmd", "a_cmd = Fx/m (m/s²)"),
        ("e_psi", "reference_e_psi", "Frenet heading (rad)"),
        ("r", "reference_r", "yaw rate (rad/s)"),
    ]
    for j, (pair, title) in enumerate(zip(PAIRS, TITLES)):
        axes[0, j].set_title(title, fontsize=10)
        for ax, (actual, nominal, units) in zip(axes[:, j], channels):
            for f, label, color in zip(common_frames(data, pair), LABELS, COLORS):
                if actual in ("delta", "a_cmd"):
                    ax.step(
                        f.s_abs,
                        f[actual],
                        where="post",
                        color=color,
                        lw=0.8,
                        label="applied " + label,
                    )
                else:
                    ax.plot(f.s_abs, f[actual], color=color, lw=0.8, label="vehicle " + label)
                ax.plot(
                    f.s_abs, f[nominal], "--", color=color, lw=0.5, alpha=0.6, label="APEX " + label
                )
            style(ax, units)
        axes[0, j].legend(fontsize=7)
    save(fig, output, "controls_heading.png", "shared progress; held applied commands")

    fig, axes = plt.subplots(6, 2, figsize=(13, 13), layout="constrained")
    units = ["m/s", "m/s", "rad/s", "rad", "m", "m"]
    for j, (pair, title) in enumerate(zip(PAIRS, TITLES)):
        axes[0, j].set_title(title, fontsize=10)
        for ax, key, unit in zip(axes[:, j], STATE_NAMES, units):
            for f, label, color in zip(common_frames(data, pair), LABELS, COLORS):
                ax.plot(f.s_abs, f["error_" + key], color=color, lw=0.65, label=label)
            style(ax, key + " error (" + unit + ")")
        axes[0, j].legend(fontsize=8)
    save(fig, output, "tracking_errors.png", "vehicle minus active APEX; heading wrapped")

    fig, axes = plt.subplots(4, 2, figsize=(13, 10), layout="constrained")
    for j, (pair, title) in enumerate(zip(PAIRS, TITLES)):
        axes[0, j].set_title(title, fontsize=10)
        for f, label, color in zip(common_frames(data, pair), LABELS, COLORS):
            for ax, field in zip(axes[:, j], ("clearance", "front_utilization", "beta", "reserve")):
                ax.plot(f.s_abs, f[field], color=color, lw=0.8, label=label)
            axes[1, j].plot(
                f.s_abs, f.rear_utilization, "--", color=color, lw=0.6, label=label + " rear"
            )
        axes[0, j].axhline(0.08, color="black", ls=":", lw=0.8, label="synthetic 0.08 m margin")
        axes[1, j].axhline(1, color="black", ls=":", lw=0.8)
        for ax, unit in zip(
            axes[:, j], ("center clearance (m)", "tire utilization", "beta (rad)", "reserve (s)")
        ):
            style(ax, unit)
        axes[0, j].legend(fontsize=7)
        axes[1, j].legend(fontsize=7, ncol=2)
    save(fig, output, "physical_validity.png", "native samples/endpoints; no swept-body claim")

    fig, axes = plt.subplots(3, 2, figsize=(13, 10), layout="constrained")
    for j, (pair, title) in enumerate(zip(PAIRS, TITLES)):
        axes[0, j].set_title(title, fontsize=10)
        for name, label, color in zip(pair, LABELS, COLORS):
            cs = [c for c in cycles if c["case"] == name]
            axes[0, j].scatter(
                [c["t_release"] for c in cs],
                [1000 * c["measured_preparation_duration"] for c in cs],
                color=color,
                s=5,
                label=label,
            )
            observed = [c for c in cs if c["t_accept"] is not None]
            axes[1, j].scatter(
                [c["t_release"] for c in observed],
                [1000 * c["accepted_latency"] for c in observed],
                color=color,
                s=5,
                label=label,
            )
            f = data[name][0]
            axes[2, j].plot(f.time, f.packet_age, color=color, lw=0.7, label=label)
            for c in cs:
                if c["status"] == "missed":
                    axes[2, j].axvline(c["miss_time"], color=color, alpha=0.25, lw=0.7)
        axes[0, j].axhline(70, color="black", ls=":", lw=0.8, label="C70 deadline")
        for ax, unit in zip(
            axes[:, j], ("host preparation (ms)", "accepted authority delay (ms)", "packet age (s)")
        ):
            style(ax, unit, "physical release/time (s)")
            ax.legend(fontsize=7)
    save(fig, output, "timing_authority.png", "all outliers retained; vertical lines = misses")

    f = data["measured_C70_1"][0]
    f = f[f.time >= 47.75]
    cs = [c for c in cycles if c["case"] == "measured_C70_1" and c["t_release"] >= 47.8]
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), layout="constrained")
    axes[0].step(f.time, f.plan_id, where="post", label="accepted packet ID")
    axes[1].plot(f.time, f.reserve, label="native-time reserve")
    axes[2].plot(f.time, f.vx, label="vehicle vx")
    for c in cs:
        for ax in axes:
            ax.axvline(
                c["valid_from"],
                color="#cf541c" if c["status"] == "missed" else "green",
                ls=":",
                lw=1,
            )
        axes[0].text(
            c["valid_from"],
            0.92,
            str(c["plan_id"]),
            transform=axes[0].get_xaxis_transform(),
            ha="center",
            fontsize=8,
        )
    for ax, unit in zip(axes, ("active packet ID", "reserve (s)", "vx (m/s)")):
        style(ax, unit, "physical time (s)")
        ax.set_xlim(47.75, 48.70)
        ax.axvline(48.67, color="black", ls="--", label="stop 48.670 s")
        ax.legend(fontsize=8)
    save(
        fig, output, "terminal_misses.png", "packet 477 persists; 478–485 miss; endpoint reserve 0"
    )

    names = [n for pair in PAIRS for n in pair]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), layout="constrained")
    for i, n in enumerate(names):
        lap = report[n]["complete_lap_seconds"]
        if lap is not None:
            axes[0].bar(i, lap, color=COLORS[i % 2])
            axes[0].text(i, lap + 0.4, f"{lap:.6f}", ha="center", fontsize=8)
        else:
            axes[0].text(i, 12, "CENSORED\nno lap time", ha="center", fontsize=9)
    axes[0].set_xticks(
        range(4), ["controlled A", "controlled C70", "measured A1", "measured C70/1"], rotation=15
    )
    axes[0].set_xlim(-0.6, 3.6)
    style(axes[0], "complete lap duration (s)", "first traversal excluded")
    sectors = list(dict.fromkeys(w["sector"] for w in windows if w["kind"] == "sector"))
    for i, n in enumerate(names):
        selected = {
            w["sector"]: w["duration"]
            for w in windows
            if w["case"] == n and w["kind"] == "sector" and w["lap_index"] == 1 and w["complete"]
        }
        x = np.arange(len(sectors)) + (i - 1.5) * 0.19
        axes[1].bar(
            x,
            [selected.get(s, np.nan) for s in sectors],
            width=0.18,
            color=COLORS[i % 2],
            alpha=1 if i < 2 else 0.5,
            label=n,
        )
    axes[1].set_xticks(range(len(sectors)), sectors, rotation=18)
    style(
        axes[1], "sector duration (s)", "lap index 1; complete sectors only; absent bars = censored"
    )
    axes[1].legend(fontsize=7)
    save(fig, output, "lap_sectors.png", "derived linear-in-progress crossing times")
