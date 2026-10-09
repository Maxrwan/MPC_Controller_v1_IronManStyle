"""Measured gamma2 outcome and compute distributions, retaining failed repetitions."""

import csv
import json
from pathlib import Path

from threading_study.config import configure_accelerate

ROOT = Path("results/task007c_resume")


def main():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not render during measured repetitions")
    configure_accelerate(1)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads((ROOT / "measured_distributions.json").read_text())
    common = next(r for r in report["common_by_gamma"] if r["gamma"] == 2)
    prefix = {r["case"]: r for r in common["rows"]}
    with (ROOT / "measured_per_run.csv").open() as handle:
        rows = [r for r in csv.DictReader(handle) if float(r["gamma"]) == 2]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), constrained_layout=True)
    axes = axes.ravel()
    for i, n in enumerate([4, 6, 8]):
        members = [r for r in rows if int(float(r["horizon"])) == n]
        complete = sum(float(r["completed_laps"]) >= 1 for r in members)
        axes[5].bar(i, complete, color="#167a73", width=0.55)
        axes[5].bar(i, len(members) - complete, bottom=complete, color="#c63d47", width=0.55)
        axes[5].text(i, len(members) + 0.12, f"{complete}/{len(members)}", ha="center")
        for j, row in enumerate(members):
            x = i + 0.05 * (j - (len(members) - 1) / 2)
            good = float(row["completed_laps"]) >= 1 and float(row["boundary_count"]) == 0
            color, marker = ("#167a73", "o") if good else ("#c63d47", "X")
            p = prefix[row["case"]]
            for ax, value in zip(
                axes[:3], [p["heading_tv"], p["steering_tv"], 1000 * p["tracking_ey_rms"]]
            ):
                ax.scatter(x, value, c=color, marker=marker, s=55, zorder=3)
            p95, maximum = [1000 * float(row["preparation_" + key]) for key in ["p95", "max"]]
            axes[3].plot([x, x], [p95, maximum], color=color, alpha=0.5)
            axes[3].scatter(x, p95, c=color, marker="o", s=25)
            axes[3].scatter(x, maximum, c=color, marker=marker, s=55)
            axes[4].scatter(x, float(row["reserve_min"]), c=color, marker=marker, s=55)
    titles = [
        "Shared-prefix planned epsi TV [rad]",
        "Shared-prefix nominal steering TV [rad]",
        "Shared-prefix tracking ey RMS [mm]",
        "Preparation p95 and max per run [ms]",
        "Whole-record minimum trajectory reserve [s]",
        "Rolling segment completions / attempts",
    ]
    for ax, title in zip(axes, titles):
        ax.set(title=title, xticks=[0, 1, 2], xticklabels=["N4", "N6", "N8"])
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    axes[3].axhline(100, color="#555555", ls="--", lw=1, label="100 ms planner period")
    axes[3].legend(fontsize=8)
    axes[3].set_yscale("log")
    axes[4].set_ylim(bottom=-0.025)
    axes[5].set_ylim(0, max(5, len(rows) / 3) + 0.7)
    fig.suptitle(
        "Task007C measured gamma2 • alpha_vy=alpha_r=1, lambda=0, dt=0.1s\n"
        f"Shared native progress {common['shared_progress'][0]:.3f}–"
        f"{common['shared_progress'][1]:.3f}m • red X retains failed run • no invented tail",
        fontsize=14,
    )
    fig.savefig(ROOT / "measured_gamma2_comparison.png", dpi=160)
    plt.close(fig)
    print("Rendered measured gamma2 comparison", flush=True)


if __name__ == "__main__":
    main()
