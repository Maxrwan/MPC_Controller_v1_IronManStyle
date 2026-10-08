"""High-resolution diagnostic figures with separate physical and numerical evidence."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path("results/task007cr")


def telemetry(case, old=False):
    return pd.read_csv((Path("results/task007b") if old else ROOT) / case / "telemetry.csv")


def save(fig, name):
    for ax in fig.axes:
        ax.grid(alpha=0.2)
    fig.savefig(ROOT / name, dpi=170, bbox_inches="tight")
    plt.close(fig)


def closed_loop_figures():
    outcomes = pd.read_csv(ROOT / "outcomes.csv")
    fig, axes = plt.subplots(4, 2, figsize=(20, 16), layout="constrained", sharex=True)
    for j, label in enumerate(["e", "f"]):
        for path in sorted(ROOT.glob(f"r1_{label}_*/telemetry.csv")):
            t = pd.read_csv(path)
            for ax, field, unit in zip(
                axes[:, j],
                ["actual_e_y", "actual_e_psi", "applied_delta", "actual_beta"],
                ["ey [m]", "epsi [rad]", "steering [rad]", "beta [rad]"],
            ):
                ax.plot(t.progress, t[field], alpha=0.45, lw=0.8, label=path.parent.name)
                ax.set_ylabel(unit)
                ax.set_xlabel("Progress [m]")
        axes[0, j].set_title(f"{label.upper()}: ten independent fixed-timing runs")
        axes[0, j].legend(fontsize=6, ncol=2)
    fig.suptitle("Fixed physical availability: planner 35 ms, codriver 1 ms — all repetitions")
    save(fig, "task007cr_fixed_latency_repeat_overlay.png")

    fig, axes = plt.subplots(5, 2, figsize=(22, 20), layout="constrained", sharex=True)
    for j, (label, old) in enumerate([("e", "b3_g2.5_w1"), ("f", "b3_g2.5_w2")]):
        measured = outcomes[(outcomes.family == "r4") & (outcomes.configuration == label)]
        # Transparent selection: lowest sweeper variation, not an omitted-outcome filter.
        smooth = measured.sort_values("fast_sweeper_heading_TV_rad").iloc[0]["case"]
        frames = [
            ("Task007B original", telemetry(old, True)),
            ("recorded-history replay", telemetry(f"r2_{label}_00")),
            ("measured minimum sweeper TV", telemetry(smooth)),
        ]
        for ax, field, unit in zip(
            axes[:, j],
            ["reference_e_psi", "actual_e_psi", "steering_rate", "predicted_slack", "actual_beta"],
            [
                "planned epsi [rad]",
                "actual epsi [rad]",
                "steering rate [rad/s]",
                "predicted slack [m]",
                "beta [rad]",
            ],
        ):
            for name, t in frames:
                ax.plot(t.progress, t[field], lw=1, label=name)
            ax.set_ylabel(unit)
            ax.set_xlabel("Progress [m]")
        if label == "e":
            axes[3, j].set_ylim(0, 1e-6)
        axes[0, j].set_title(f"{label.upper()} — measured comparator: {smooth}")
        axes[0, j].legend(fontsize=8)
    fig.suptitle("Original versus replay and measured history — unchanged control formulation")
    save(fig, "task007cr_original_latency_replay.png")

    metrics = [
        ("fast_sweeper_heading_TV_rad", "Sweeper heading TV [rad]"),
        ("technical_section_heading_TV_rad", "Technical heading TV [rad]"),
        ("planned_steering_TV_rad", "Planned steering TV [rad]"),
        ("rate_limit_s", "Rate-limit time [s]"),
        ("predicted_slack_m", "Maximum predicted slack [m]"),
        ("physical_clearance_m", "Minimum physical clearance [m]"),
        ("beta_max_rad", "Maximum |beta| [rad]"),
        ("lap_s", "Lap time [s]"),
        ("planner_p95_s", "Planner preparation p95 [s]"),
    ]
    measured = outcomes[outcomes.family == "r4"]
    fig, axes = plt.subplots(3, 3, figsize=(22, 16), layout="constrained")
    for ax, (field, title) in zip(axes.ravel(), metrics):
        values = [
            measured[measured.configuration == label][field].dropna().to_numpy()
            for label in ["e", "f"]
        ]
        ax.boxplot(values, tick_labels=["E", "F"], showfliers=False)
        for j, v in enumerate(values):
            ax.scatter(j + 1 + np.linspace(-0.1, 0.1, len(v)), v, s=22, alpha=0.7)
        ax.set_ylabel(title)
    fig.suptitle("Fresh measured repetitions — every outcome shown; boxes are quartiles")
    save(fig, "task007cr_measured_repeat_distribution.png")

    for label in ["e", "f"]:
        fig, axes = plt.subplots(7, 2, figsize=(23, 30), layout="constrained", sharex=True)
        columns = [
            ("actual_vx", "Speed [m/s]"),
            ("actual_e_y", "ey [m]"),
            ("actual_e_psi", "epsi [rad]"),
            ("actual_vy", "vy [m/s]"),
            ("actual_beta", "beta [rad]"),
            ("actual_r", "Yaw rate [rad/s]"),
            ("applied_delta", "Steering [rad]"),
            ("steering_rate", "Steering rate [rad/s]"),
            ("rear_utilization", "Front dashed / rear solid tire utilization"),
            ("predicted_slack", "Predicted slack [m]"),
            ("node_adaptation_e_y", "Planning → APEX ey [m]"),
            ("error_e_y", "APEX → vehicle ey [m]"),
            ("planner_planner_total_time", "Planner physical availability delay [s]"),
            ("planner_iterations", "Solver iterations"),
        ]
        for case in measured[measured.configuration == label]["case"]:
            t = telemetry(case)
            for ax, (field, unit) in zip(axes.ravel(), columns):
                ax.plot(t.progress, t[field], label=case, alpha=0.65, lw=0.65)
                if field == "rear_utilization":
                    ax.plot(
                        t.progress,
                        t.front_utilization,
                        ls="--",
                        lw=0.6,
                        color=ax.lines[-1].get_color(),
                        alpha=0.4,
                    )
                ax.set_ylabel(unit)
                ax.set_xlabel("Progress [m]")
        if label == "e":
            axes.ravel()[9].set_ylim(0, 1e-6)
        axes[0, 0].legend(fontsize=7, ncol=2)
        fig.suptitle(f"{label.upper()} — all ten fresh measured runs, common progress axes")
        save(fig, f"task007cr_telemetry_overlay_{label}.png")


def numerical_figures():
    records = json.loads((ROOT / "nlp_replay.json").read_text())
    fig, ax = plt.subplots(figsize=(19, 7), layout="constrained")
    for i, r in enumerate(records):
        base = np.array(r["exact"][0]["solution"])
        differences = [np.max(abs(np.array(v["solution"]) - base)) for v in r["exact"]]
        ax.plot(range(20), differences, "o-", label=r["selection"]["name"], alpha=0.7)
    ax.set(
        xlabel="Identical-NLP repetition",
        ylabel="Maximum decision-vector difference (mixed SI channels)",
    )
    ax.legend(fontsize=8, ncol=2)
    fig.suptitle("Exact captured input replay — zero means numerically identical")
    save(fig, "task007cr_exact_nlp_repeatability.png")

    fig, axes = plt.subplots(
        len(records), 2, figsize=(19, max(8, 4 * len(records))), layout="constrained", squeeze=False
    )
    for row, r in enumerate(records):
        base = r["exact"][0]
        variants = [base] + [v for v in r["sensitivity"] if not v["label"].startswith("state_")]
        labels = [
            v["label"].replace("_", " ") + (" [failed]" if not v["success"] else "")
            for v in variants
        ]
        for ax, key, title in [
            (axes[row, 0], "objective", "Objective"),
            (axes[row, 1], "first_control", "First steering [rad]"),
        ]:
            values = [v[key][0] if key == "first_control" else v[key] for v in variants]
            ax.bar(
                range(len(values)), values, color=["C0" if v["success"] else "C3" for v in variants]
            )
            ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right", fontsize=7)
            ax.set_ylabel(title)
            ax.set_title(r["selection"]["name"])
    fig.suptitle(
        "Same physical NLP; separately varied deterministic initialization — all outcomes retained"
    )
    save(fig, "task007cr_warmstart_sensitivity.png")

    fig, axes = plt.subplots(
        len(records),
        2,
        figsize=(19, max(8, 3.5 * len(records))),
        layout="constrained",
        squeeze=False,
    )
    for row, r in enumerate(records):
        base = r["exact"][0]
        variants = [v for v in r["sensitivity"] if v["label"].startswith("state_")]
        for ax, key, title in [
            (axes[row, 0], "first_control", "Change in first steering [rad]"),
            (axes[row, 1], "objective", "Change in objective"),
        ]:
            values = [
                v[key][0] - base[key][0] if key == "first_control" else v[key] - base[key]
                for v in variants
            ]
            ax.bar(
                range(len(values)), values, color=["C0" if v["success"] else "C3" for v in variants]
            )
            ax.set_xticks(
                range(len(values)),
                [v["label"].replace("state_", "") for v in variants],
                rotation=35,
                ha="right",
                fontsize=7,
            )
            ax.set_ylabel(title)
            ax.set_title(r["selection"]["name"])
    fig.suptitle(
        "Small deterministic state perturbations\nMagnitudes derived from observed early divergence"
    )
    save(fig, "task007cr_state_sensitivity.png")


def timing_figure():
    frame = pd.read_csv(ROOT / "outcomes.csv")
    group = frame[frame.family == "r7"].copy()
    group["delta_ms"] = [
        json.loads((ROOT / c / "summary.json").read_text())["diagnostic_timing"]["planner"]
        for c in group.case
    ]
    selection = json.loads((ROOT / "timing_selection.json").read_text())
    index = selection["index"]
    original = json.loads((ROOT / "trace_e.json").read_text())["planner"][index]
    group["delta_ms"] = group.delta_ms.map(lambda x: (x[index] - original) * 1000)
    base = frame[frame.case == "r2_e_00"].copy()
    base["delta_ms"] = 0
    group = pd.concat([group, base]).sort_values("delta_ms")
    fig, axes = plt.subplots(2, 4, figsize=(26, 12), layout="constrained")
    for ax, field in zip(
        axes.ravel(),
        [
            "fast_sweeper_heading_TV_rad",
            "planned_steering_TV_rad",
            "predicted_slack_m",
            "physical_clearance_m",
            "beta_max_rad",
            "lap_s",
            "end_progress",
            "end_time",
        ],
    ):
        ax.plot(group.delta_ms, group[field], "o-")
        labels = {
            "fast_sweeper_heading_TV_rad": "Sweeper heading TV [rad]",
            "planned_steering_TV_rad": "Observed-prefix steering TV [rad]",
            "predicted_slack_m": "Maximum predicted slack [m]",
            "physical_clearance_m": "Minimum physical clearance [m]",
            "beta_max_rad": "Maximum |beta| [rad]",
            "lap_s": "Completed lap time [s]",
            "end_progress": "Final recorded progress [m]",
            "end_time": "Final physical time [s]",
        }
        ax.set(xlabel="Single availability-delay change [ms]", ylabel=labels[field])
        ax.set_xlim(-5.5, 5.5)
        if field == "predicted_slack_m":
            ax.set_ylim(0, 1e-6)
    fig.suptitle(
        f"Only planner launch index {index} perturbed; all other recorded E delays held fixed\n"
        "Missing laps at −5, −2, +2 ms denote trace exhaustion; partial-run coverage is shown"
    )
    save(fig, "task007cr_timing_sensitivity.png")
