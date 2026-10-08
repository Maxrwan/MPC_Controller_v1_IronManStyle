"""Separate aggression indicators; no opaque onset score or automatic acceptance cutoff."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path("results/task007c_resume")


def plot():
    data = pd.read_csv(ROOT / "comparison.csv")
    data = data[
        (data.alpha_vy == 1)
        & (data.alpha_r == 1)
        & (data.horizon == 4)
        & (data.progress_weight == 0)
        & (data.laps == 1)
    ]
    fields = [
        ("beta_p95", "p95 |beta| [rad]"),
        ("beta_max", "Max |beta| [rad]"),
        ("front_util_max", "Front utilization"),
        ("rear_util_max", "Rear utilization"),
        ("rate_limit_s", "Rate-limit time [s]"),
        ("heading_tv", "Planned heading TV [rad]"),
        ("steering_tv", "Nominal steering TV [rad]"),
        ("planned_reversals", "Planned steering reversals"),
        ("adaptation_ey_rms", "Planning → APEX ey RMS [m]"),
        ("tracking_ey_rms", "APEX → vehicle ey RMS [m]"),
        ("iterations_mean", "Iterations (time-sampled mean)"),
        ("slack", "Maximum predicted slack [m]"),
        ("clearance", "Minimum physical clearance [m]"),
        ("denominator_min", "Frenet denominator minimum"),
        ("lap_s", "Completed lap [s]"),
        ("progress_rate", "Progress rate [m/s]"),
    ]
    fig, axes = plt.subplots(4, 4, figsize=(26, 20), layout="constrained")
    for axis, (field, title) in zip(axes.ravel(), fields):
        for history, group in data.groupby("history"):
            group = group.sort_values("gamma")
            axis.plot(group.gamma, group[field], "o-", label=history)
        axis.set(xlabel="Gamma", ylabel=title)
        axis.grid(alpha=0.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        "C1 transition indicators — frozen Candidate C, lambda=0\n"
        "Separate physical, smoothness and tracking evidence; missing histories remain untested"
    )
    fig.savefig(ROOT / "c1_transition_map.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    plot()
