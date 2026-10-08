"""Large review dashboards: full-lap trends and common-axis comparisons."""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def shade(ax, ref):
    for i, sec in enumerate(ref.manifest["sectors"]):
        start = sec["start_s_m"]
        end = (
            ref.manifest["sectors"][i + 1]["start_s_m"]
            if i + 1 < len(ref.manifest["sectors"])
            else ref.length
        )
        ax.axvspan(start, end, color=f"C{i % 10}", alpha=0.065)
        ax.text(
            (start + end) / 2,
            1.015,
            sec["name"].replace("_", " "),
            rotation=35,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="bottom",
            fontsize=6,
        )
    ax.set_xlim(0, ref.length)
    ax.grid(alpha=0.2)
    ax.set_xlabel("Centerline progress [m]")


def dashboard(folder, telemetry, nodes, ref, track):
    case = folder.name
    last = int(telemetry.lap.max())
    t = telemetry[telemetry.lap == last].copy()
    if len(t) < 100:
        t = telemetry
    # Last complete comparable lap when a tiny seam tail exists.
    if np.ptp(t.progress) < 0.9 * ref.length and last > 1:
        t = telemetry[telemetry.lap == last - 1]
    x = t.progress
    fig, axes = plt.subplots(
        10,
        2,
        figsize=(26, 47),
        layout="constrained",
        gridspec_kw={"height_ratios": [2.2] + [1] * 9},
    )
    a = axes.ravel()
    g = np.array([track.centerline.geometry(s) for s in ref.s])
    normal = np.c_[-np.sin(g[:, 2]), np.cos(g[:, 2])]
    for sign in [-1, 1]:
        a[0].plot(*(g[:, :2] + sign * 0.55 * normal).T, "k-", lw=0.6)
    a[0].plot(ref.frame.x_ref_m, ref.frame.y_ref_m, label="Planning line", lw=1)
    geo = np.array([track.centerline.geometry(s) for s in t.s_abs])
    world = (
        geo[:, :2] + t.actual_e_y.to_numpy()[:, None] * np.c_[-np.sin(geo[:, 2]), np.cos(geo[:, 2])]
    )
    a[0].plot(*world.T, label="vehicle", lw=0.6)
    # Representative packets through all sectors, not a fictitious connected global APEX path.
    packets = json.loads((folder / "trajectory_packets.json").read_text())
    shown = False
    for packet in packets[:: max(1, len(packets) // 35)]:
        z = np.array(packet["states"])
        gg = np.array([track.centerline.geometry(s) for s in z[:, 4]])
        xy = gg[:, :2] + z[:, 5, None] * np.c_[-np.sin(gg[:, 2]), np.cos(gg[:, 2])]
        a[0].plot(*xy.T, color="C3", lw=1, label="APEX packets" if not shown else None)
        shown = True
    a[0].set_aspect("equal", adjustable="box")
    a[0].set(xlabel="World x [m]", ylabel="World y [m]", title="Track / Planning / APEX / vehicle")
    a[0].legend()
    for i, key, label in [
        (1, "vx", "Speed [m/s]"),
        (2, "e_y", "Lateral offset [m]"),
        (3, "e_psi", "Heading [rad]"),
    ]:
        for prefix, name in [
            ("planning_", "Planning"),
            ("reference_", "active APEX"),
            ("actual_", "vehicle"),
        ]:
            a[i].plot(x, t[prefix + key], label=name, lw=0.8)
        a[i].set_ylabel(label)
    for i, key, label in [(4, "vy", "Lateral velocity [m/s]"), (5, "r", "Yaw rate [rad/s]")]:
        for prefix, name in [
            ("reference_", "APEX"),
            ("actual_", "vehicle"),
            ("error_", "local error"),
        ]:
            a[i].plot(x, t[prefix + key], label=name, lw=0.8)
        a[i].set_ylabel(label)
    for key in ["planned_beta", "actual_beta"]:
        a[6].plot(x, t[key], label=key, lw=0.8)
    a[6].set_ylabel("Sideslip [rad]")
    a[7].plot(x, t.delta, label="applied")
    a[7].axhline(0.4, color="r", ls="--")
    a[7].axhline(-0.4, color="r", ls="--")
    a[7].set_ylabel("Steering [rad]")
    a[8].plot(x, t.steering_rate, label="applied rate")
    a[8].axhline(1, color="r", ls="--")
    a[8].axhline(-1, color="r", ls="--")
    a[8].set_ylabel("Steering rate [rad/s]")
    a[9].plot(x, t.a_cmd, label="a_cmd")
    a[9].axhline(2, color="r", ls="--")
    a[9].axhline(-3, color="r", ls="--")
    a[9].set_ylabel("Fx/m [m/s²]")
    for key in ["front_utilization", "rear_utilization"]:
        a[10].plot(x, t[key], label=key, lw=0.8)
    a[10].axhline(1, color="r", ls="--")
    a[10].set_ylabel("Combined tire utilization")
    a[11].plot(x, t.lateral_acceleration, label="dvy/dt + vx*r")
    a[11].set_ylabel("Lateral acceleration [m/s²]")
    for i, key, label in [
        (12, "e_y", "Planning→APEX lateral [m]"),
        (13, "vx", "Planning→APEX speed [m/s]"),
    ]:
        selected = nodes[(nodes.s_abs >= t.s_abs.min()) & (nodes.s_abs <= t.s_abs.max())]
        a[i].scatter(
            selected.progress,
            selected["adaptation_" + key],
            s=0.25,
            alpha=0.2,
            label="every predicted node",
        )
        a[i].plot(x, t["node_adaptation_" + key], lw=0.8, label="active packet node mean")
        a[i].set_ylabel(label)
    a[14].plot(x, t.error_e_y, label="ey [m]", lw=0.8)
    a[14].plot(x, t.error_e_psi, label="heading [rad]", lw=0.8)
    a[14].set_ylabel("APEX→vehicle error")
    a[15].plot(x, t.predicted_slack, label="predicted slack [m]")
    a[15].plot(x, t.clearance, label="physical clearance [m]")
    a[15].axhline(0.08, ls="--", color="r")
    a[15].set_ylabel("Slack / clearance [m]")
    a[16].plot(x, 1000 * t.planner_planner_total_time, label="full")
    a[16].plot(x, 1000 * t.planner_solve_time, label="solve")
    a[16].axhline(100, color="r", ls="--")
    a[16].set_ylabel("Planner time [ms]")
    a[17].plot(x, 1000 * t.total_time, label="full update")
    a[17].axhline(10, color="r", ls="--")
    a[17].set_ylabel("Codriver time [ms]")
    for key in ["reserve", "age"]:
        a[18].plot(x, t[key], label=key)
    a[18].set_ylabel("Trajectory timing [s]")
    for key in [
        "state_tracking",
        "input_reference",
        "input_increment",
        "terminal_tracking",
        "slack_linear",
        "slack_quadratic",
        "progress_reward",
        "total",
    ]:
        a[19].plot(x, t["cost_" + key], label=key, lw=0.8)
    a[19].set_ylabel("Objective contribution")
    for ax in a[1:]:
        shade(ax, ref)
        ax.legend(fontsize=7, loc="best")
    fig.suptitle(
        f"Task007B — {case} — complete trend, last available lap; units per panel", fontsize=20
    )
    path = folder.parent / f"task007b_telemetry_dashboard_{case}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    # Requested beta relationships retain point distributions, not only RMS bars.
    fig, ax = plt.subplots(1, 3, figsize=(18, 5), layout="constrained")
    ax[0].scatter(t.front_utilization, t.actual_beta, s=1, alpha=0.3)
    ax[0].set_xlabel("Front tire utilization")
    ax[1].scatter(t.racing_curvature, t.actual_beta, s=1, alpha=0.3)
    ax[1].set_xlabel("Racing curvature [1/m]")
    ax[2].plot(x, t.actual_vy, label="actual vy")
    ax[2].plot(x, t.reference_vy, label="APEX vy")
    ax[2].set_xlabel("Progress [m]")
    ax[2].legend()
    for aa in ax[:2]:
        aa.set_ylabel("Actual beta [rad]")
    ax[2].set_ylabel("Residual to nominal vy=0 [m/s]")
    fig.savefig(folder.parent / f"sideslip_{case}.png", dpi=150)
    plt.close(fig)
    return str(path)


def comparison(output, cases, ref):
    fig, axes = plt.subplots(5, 2, figsize=(24, 22), layout="constrained")
    panels = [
        ("actual_vx", "Speed [m/s]"),
        ("node_adaptation_vx", "Planning→APEX speed [m/s]"),
        ("node_adaptation_e_y", "Planning→APEX lateral [m]"),
        ("error_e_y", "APEX→vehicle lateral [m]"),
        ("steering_utilization", "Steering utilization"),
        ("steering_rate_utilization", "Steering-rate utilization"),
        ("front_utilization", "Front tire utilization"),
        ("planner_planner_total_time", "Planner full time [s]"),
        ("actual_beta", "Actual sideslip [rad]"),
    ]
    for case in cases:
        t = pd.read_csv(output / case / "telemetry.csv")
        last = int(t.lap.max())
        g = t[t.lap == last]
        if np.ptp(g.progress) < 0.9 * max(t.progress) and last > 1:
            g = t[t.lap == last - 1]
        for ax, (key, label) in zip(axes.ravel(), panels):
            ax.plot(g.progress, g[key], lw=0.7, alpha=0.8, label=case)
            ax.set(xlabel="Progress [m]", ylabel=label)
            ax.grid(alpha=0.2)
        s = json.loads((output / case / "summary.json").read_text())
        laps = s["lap_times"]
        axes.ravel()[9].plot(np.arange(1, len(laps) + 1), laps, "o-", label=case)
    for ax in axes.ravel()[:9]:
        shade(ax, ref)
    for ax in axes.ravel():
        ax.legend(fontsize=7)
    axes.ravel()[9].set(xlabel="Lap (first is startup)", ylabel="Lap time [s]")
    fig.suptitle("Task007B aggression / progress comparison", fontsize=18)
    fig.savefig(output / "task007b_aggression_comparison_dashboard.png", dpi=150)
    plt.close(fig)


def oscillation_review(output, ref):
    """Retain common-axis evidence for the rejected high-demand progress behavior."""
    cases = ["b1_g2", "b3_g2_w1", "b1_g2.5", "b3_g2.5_w1"]
    if not all((output / case / "telemetry.csv").exists() for case in cases):
        return
    fig, axes = plt.subplots(4, 1, figsize=(19, 15), layout="constrained", sharex=True)
    for case in cases:
        t = pd.read_csv(output / case / "telemetry.csv")
        t = t[t.lap == 1]
        for ax, field, unit in zip(
            axes,
            ["actual_vx", "actual_e_y", "actual_e_psi", "actual_vy"],
            ["Speed [m/s]", "Lateral offset [m]", "Heading [rad]", "Lateral speed [m/s]"],
        ):
            ax.plot(t.progress, t[field], lw=1, label=case)
            ax.set_ylabel(unit)
    for ax in axes:
        shade(ax, ref)
        ax.legend()
    fig.suptitle("High-demand oscillation review — retained startup screens")
    fig.savefig(output / "high_demand_oscillation_review.png", dpi=150)
    plt.close(fig)
