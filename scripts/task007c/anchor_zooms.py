"""Common-axis sector review of archived and repeated rejected anchors."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PANELS = [
    ("planning_vx", "Planning speed [m/s]"),
    ("reference_vx", "APEX speed [m/s]"),
    ("reference_e_psi", "APEX heading error [rad]"),
    ("actual_e_psi", "Actual heading error [rad]"),
    ("reference_e_y", "APEX lateral offset [m]"),
    ("actual_e_y", "Actual lateral offset [m]"),
    ("reference_vy", "APEX lateral velocity [m/s]"),
    ("actual_beta", "Actual sideslip [rad]"),
    ("reference_r", "APEX yaw rate [rad/s]"),
    ("applied_delta", "Applied steering [rad]"),
    ("steering_rate", "Applied steering rate [rad/s]"),
    ("applied_a_cmd", "Applied Fx/m [m/s²]"),
    ("front_utilization", "Front tire utilization"),
    ("rear_utilization", "Rear tire utilization"),
    ("clearance", "Physical track clearance [m]"),
    ("predicted_slack", "Predicted track slack [m]"),
    ("error_e_y", "APEX → vehicle lateral error [m]"),
    ("cost_total", "APEX objective"),
    ("planner_planner_total_time", "Full plan preparation [s]"),
    ("planner_iterations", "Solver iterations"),
]


def render(output=Path("results/task007c"), *, sectors=None, letters=("e", "f")):
    paths = []
    for letter, old in [("e", "b3_g2.5_w1"), ("f", "b3_g2.5_w2")]:
        if letter not in letters:
            continue
        frames = [
            ("Task007B original", pd.read_csv(Path("results/task007b") / old / "telemetry.csv")),
            ("Task007C first", pd.read_csv(output / f"anchor_{letter}" / "telemetry.csv")),
            ("Task007C repeat", pd.read_csv(output / f"anchor_{letter}_repeat" / "telemetry.csv")),
        ]
        selected = sectors or ["hairpin", "technical_section", "fast_sweeper"]
        if sectors is None and letter == "f":
            selected = [*selected, "long_straight"]
        for sector in selected:
            fig, axes = plt.subplots(10, 2, figsize=(22, 34), layout="constrained")
            for ax, (column, label) in zip(axes.ravel(), PANELS):
                for name, frame in frames:
                    selection = frame[frame.sector == sector]
                    ax.plot(selection.progress, selection[column], label=name, linewidth=1)
                ax.set_ylabel(label)
                ax.set_xlabel("Centerline progress [m]")
                ax.grid(alpha=0.25)
            axes[0, 0].legend()
            fig.suptitle(
                f"Anchor {letter.upper()} — {sector.replace('_', ' ')} — unchanged formulation\n"
                "Original and both measured repetitions; reproduction review only",
                fontsize=17,
            )
            path = output / f"task007c_anchor_{letter}_{sector}_zoom.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            paths.append(str(path))
    return paths


if __name__ == "__main__":
    render()
