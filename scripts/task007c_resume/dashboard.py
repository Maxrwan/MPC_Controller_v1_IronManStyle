"""Large sector-shaded principal-case dashboard with physical and prediction channels distinct."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from apex.coordinates.frenet import frenet_to_global
from apex.planning_reference.track import load_track


def dashboard(folder, sector=None):
    folder = Path(folder)
    t = pd.read_csv(folder / "diagnostic_telemetry.csv")
    f = pd.read_csv(folder / "physics_telemetry.csv")
    summary = json.loads((folder / "summary.json").read_text())
    events = json.loads((folder / "events.json").read_text())
    delay = {p["plan_id"]: p.get("physical_delay", float("nan")) for p in events["plans"]}
    t["planner_ready_delay"] = t.plan_id.map(delay)
    manifest = json.loads((folder / "fixture/planning_manifest.json").read_text())
    track, _, _ = load_track(folder / "fixture/track_source.json")
    if sector is not None:
        sectors = manifest["sectors"]
        index = next(i for i, item in enumerate(sectors) if item["name"] == sector)
        start = sectors[index]["start_s_m"]
        end = sectors[index + 1]["start_s_m"] if index + 1 < len(sectors) else track.length
        # First traversal only: do not connect separate laps in sector zooms.
        t = t[(t.s_abs >= start) & (t.s_abs < end)].copy()
        f = f[(f.s_abs >= start) & (f.s_abs < end)].copy()
        if t.empty:
            raise ValueError(f"No first-traversal coverage for {sector}: {folder}")
    fig, axes = plt.subplots(6, 4, figsize=(32, 34), layout="constrained")
    ax = axes.ravel()
    for label, ey in [
        ("Planning", t.planning_e_y),
        ("APEX", t.reference_e_y),
        ("actual", t.actual_e_y),
    ]:
        progress = t.reference_s_abs if label == "APEX" else t.s_abs
        poses = [frenet_to_global(track, s, y) for s, y in zip(progress, ey)]
        ax[0].plot([p.x for p in poses], [p.y for p in poses], label=label, lw=0.7)
    ax[0].set(
        title="Planning / active APEX / actual path", xlabel="x [m]", ylabel="y [m]", aspect="equal"
    )
    panels = [
        (1, ["planning_vx", "reference_vx", "actual_vx"], "Speed [m/s]"),
        (2, ["planning_e_y", "reference_e_y", "actual_e_y"], "ey [m]"),
        (3, ["planning_e_psi", "reference_e_psi", "actual_e_psi"], "epsi [rad]"),
        (4, ["reference_vy", "actual_vy"], "vy [m/s]"),
        (5, ["planned_beta", "actual_beta"], "beta [rad]"),
        (6, ["planning_r", "reference_r", "actual_r"], "Yaw rate [rad/s]"),
        (7, ["nominal_delta", "delta"], "Nominal / physical steering [rad]"),
        (8, ["steering_rate"], "Physical steering rate [rad/s]"),
        (9, ["nominal_a_cmd", "a_cmd"], "Acceleration command Fx/m [m/s²]"),
        (10, ["front_utilization", "rear_utilization"], "Combined tire utilization"),
        (
            14,
            ["node_adaptation_e_y", "node_adaptation_e_psi", "node_adaptation_vx"],
            "Planning → APEX [SI per channel]",
        ),
        (
            15,
            ["error_e_y", "error_e_psi", "error_vy", "error_r"],
            "APEX → vehicle [SI per channel]",
        ),
        (17, ["predicted_slack", "clearance"], "Predicted slack / physical clearance [m]"),
        (
            18,
            [
                "planner_solve_time",
                "planner_planner_total_time",
                "planner_ready_delay",
                "physical_latency",
            ],
            "Solver / preparation / ready / codriver delay [s]",
        ),
        (19, ["planner_iterations"], "Solver iterations"),
        (20, ["reserve"], "Trajectory reserve [s]"),
        (
            21,
            [
                "cost_state_tracking",
                "cost_terminal_tracking",
                "cost_input_reference",
                "cost_input_increment",
                "cost_slack_linear",
                "cost_slack_quadratic",
                "cost_progress_reward",
            ],
            "Objective decomposition",
        ),
        (
            22,
            ["rolling_TV_1s_reference_e_psi", "rolling_TV_1s_nominal_delta"],
            "Rolling 1 s heading / steering TV [rad]",
        ),
        (
            23,
            ["denominator", "steering_utilization", "steering_rate_utilization"],
            "Feasibility indicators (dimensionless)",
        ),
    ]
    for index, fields, title in panels:
        for field in fields:
            ax[index].plot(t.s_abs, t[field], label=field, lw=0.6)
        ax[index].set(title=title, xlabel="Unwrapped progress [m]")
    for index, fields, title in [
        (11, ["alpha_f", "alpha_r"], "Slip angles [rad]"),
        (12, ["fx_front", "fx_rear", "fyf", "fyr"], "Axle longitudinal / lateral forces [N]"),
        (13, ["fzf", "fzr"], "Axle normal loads [N]"),
        (
            16,
            ["one_step_vx", "one_step_vy", "one_step_r", "one_step_e_psi", "one_step_e_y"],
            "One-step prediction residual [SI per channel]",
        ),
    ]:
        for field in fields:
            ax[index].plot(f.s_abs, f[field], label=field, lw=0.6)
        ax[index].set(title=title, xlabel="Unwrapped progress [m]")
    sectors = manifest["sectors"]
    length = track.length
    for axis in ax[1:]:
        for lap in range(int(t.s_abs.max() // length) + 1):
            for i, sector_info in enumerate(sectors):
                start = lap * length + sector_info["start_s_m"]
                end = lap * length + (
                    sectors[i + 1]["start_s_m"] if i + 1 < len(sectors) else length
                )
                if start <= t.s_abs.max() and end >= t.s_abs.min():
                    axis.axvspan(
                        max(start, t.s_abs.min()),
                        min(end, t.s_abs.max()),
                        color=f"C{i % 10}",
                        alpha=0.055,
                    )
        axis.set_xlim(t.s_abs.min(), t.s_abs.max())
    for axis in ax:
        axis.grid(alpha=0.2)
        axis.legend(fontsize=6, loc="best")
    fig.legend(
        handles=[
            Patch(color=f"C{i % 10}", alpha=0.3, label=item["name"])
            for i, item in enumerate(sectors)
            if sector is None or item["name"] == sector
        ],
        loc="outside lower center",
        ncol=5,
        fontsize=10,
    )
    fig.suptitle(
        folder.name
        + "\nSector shading; physical commands at release time; synthetic experiment only\n"
        f"stop={summary['stop_reason']}, boundary samples={summary['boundary_violations']}, "
        f"solver failures={summary['solver_failures']}"
    )
    filename = "primary_dashboard.png" if sector is None else f"dashboard_{sector}.png"
    fig.savefig(folder / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
