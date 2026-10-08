"""Separate effects of pseudo-reference, horizon and static progress experiments."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path("results/task007c_resume")
PAIRS = [(1, 1), (0.5, 1), (0.25, 1), (0, 1), (1, 0.5), (1, 0.25), (1, 0), (0.25, 0.25), (0, 0)]


def plot(phase):
    t = pd.read_csv(ROOT / "comparison.csv")
    t = t[(t.laps == 1) & t["repeat"].isna() & t.history.isin(["fixed", "smooth"])].copy()
    if phase == "c2":
        t = t[(t.horizon == 4) & (t.progress_weight == 0) & t.gamma.isin([1.8, 2.0])].copy()
        t["x"] = [PAIRS.index((a, b)) for a, b in zip(t.alpha_vy, t.alpha_r)]
        ticks, labels, xlabel = range(9), [f"{a:g},{b:g}" for a, b in PAIRS], "alpha_vy, alpha_r"
    elif phase == "c3":
        t = t[(t.alpha_vy == 1) & (t.alpha_r == 1) & (t.progress_weight == 0)].copy()
        t["x"] = t.horizon
        ticks, labels, xlabel = [4, 6, 8], ["4", "6", "8"], "N (dt=0.1 s)"
    else:
        t = t[(t.alpha_vy == 1) & (t.alpha_r == 1) & (t.horizon == 4)].copy()
        t["x"] = t.progress_weight
        ticks, labels, xlabel = [0, 0.5, 1, 2, 4], ["0", ".5", "1", "2", "4"], "Static lambda_s"
    t = t[t.gamma.isin([1.8, 1.9, 2.0, 2.1])]
    fields = [
        ("clearance", "Minimum clearance [m]"),
        ("slack", "Maximum slack [m]"),
        ("heading_tv", "Active planned heading TV [rad]"),
        ("steering_tv", "Active nominal steering TV [rad]"),
        ("rate_limit_s", "Physical rate-limit time [s]"),
        ("beta_p95", "p95 |beta| [rad]"),
        ("rear_util_max", "Rear tire utilization max"),
        ("tracking_ey_rms", "Local tracking ey RMS [m]"),
        ("iterations_per_call_mean", "Iterations per call mean"),
        (
            "accepted_prediction_mean_common_0p4_heading_total_variation",
            "Prediction first0.4s heading TV [rad]",
        ),
        (
            "accepted_prediction_mean_common_0p4_steering_total_variation",
            "Prediction first0.4s steering TV [rad]",
        ),
        ("lap_s", "Completed lap [s]"),
    ]
    fig, axes = plt.subplots(4, 3, figsize=(24, 22), layout="constrained")
    for ax, (field, title) in zip(axes.ravel(), fields):
        for (gamma, history), g in t.groupby(["gamma", "history"]):
            g = g.sort_values("x")
            ax.plot(
                g.x, g[field], "o-" if history == "fixed" else "s--", label=f"g{gamma:g} {history}"
            )
            failed = g[g.boundary_count > 0]
            ax.scatter(failed.x, failed[field], marker="x", c="red", s=100, zorder=4)
        ax.set(title=title, xlabel=xlabel)
        if field == "slack":
            # Keep numerical barrier-scale slack from looking like material track use.
            maximum = float(t[field].max())
            ax.set_ylim(0, max(0.001, 1.05 * maximum))
            ax.text(
                0.98,
                0.96,
                f"Observed max={maximum:.3g} m",
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=8,
            )
        ax.set_xticks(ticks, labels, rotation=25 if phase == "c2" else 0)
        ax.grid(alpha=0.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        f"{phase.upper()} isolated formulation comparison — red crosses retain boundary failures\n"
        "Controlled availability; wall-time benchmark reported separately"
    )
    fig.savefig(ROOT / f"{phase}_formulation_comparison.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["c2", "c3", "c4"])
    plot(p.parse_args().phase)
