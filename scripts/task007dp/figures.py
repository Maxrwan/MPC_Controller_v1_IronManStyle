"""Exactly three scientific figures from compact retained/derived tables."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from task007dp.candidates import METHODS

FIGURES = ("figure1_clearance.png", "figure2_accuracy.png", "figure3_cost_accuracy.png")
COLORS = dict(zip(METHODS, ("#225ea8", "#d7301f", "#e6ab02", "#7a0177", "#009875")))


def read(folder, name):
    with (Path(folder) / name).open() as stream:
        return list(csv.DictReader(stream))


def render(folder):
    folder = Path(folder)
    if any((folder / f).exists() for f in FIGURES):
        raise FileExistsError("Do not overwrite figures")
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.2, "figure.dpi": 120})

    def finish(fig, name):
        fig.savefig(
            folder / name, dpi=160, bbox_inches="tight", metadata={"Software": "APEX Task007D-P"}
        )
        plt.close(fig)

    data = read(folder, "figure1_data.csv")
    s = [float(r["s_abs"]) for r in data]
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True, layout="constrained")
    for host, color in [("A", COLORS["A"]), ("B", COLORS["P2"])]:
        axes[0].plot(
            s,
            [float(r[host + "_clearance"]) for r in data],
            color=color,
            label=host + " physical center",
        )
        axes[1].plot(s, [float(r[host + "_ey"]) for r in data], color=color, label=host + " actual")
        axes[1].plot(
            s,
            [float(r[host + "_nominal_ey"]) for r in data],
            color=color,
            ls="--",
            label=host + " active nominal",
        )
        exact = [r for r in data if r[host + "_kind"] == "recorded_knot"]
        axes[0].scatter(
            [float(r["s_abs"]) for r in exact],
            [float(r[host + "_clearance"]) for r in exact],
            s=7,
            color=color,
            alpha=0.4,
        )
    axes[0].axhline(0.08, color="#b2182b", ls=":", label="0.08 m synthetic margin")
    axes[0].set(
        ylabel="Center clearance [m]",
        title="R4: retained 60/15 ms history — clearance loss survives progress alignment",
    )
    axes[0].set_ylim(0.04, 0.58)
    axes[0].legend(ncol=3, fontsize=9)
    axes[1].set(
        xlabel="Common observed absolute progress [m]",
        ylabel="Lateral position e_y [m]",
        title="Actual positions and active nominal positions at corresponding times",
    )
    axes[1].legend(ncol=4, fontsize=9)
    fig.supxlabel(
        "Dots: recorded knots. Lines: linear spatial estimates between knots; no extrapolation.",
        fontsize=9,
    )
    finish(fig, FIGURES[0])

    releases = read(folder, "release_errors.csv")
    fig, axes = plt.subplots(4, 2, figsize=(12, 11), sharex=True, layout="constrained")
    channels = [
        ("e_y", "Lateral error [m]"),
        ("e_psi", "Heading error [rad]"),
        ("delta", "Preceding steering error [rad]"),
        ("a_cmd", "Preceding a_cmd error [m/s²]"),
    ]
    for col, case in enumerate(("D4-R2_A", "D4-R4_A")):
        for row, (channel, label) in enumerate(channels):
            ax = axes[row, col]
            ax.axvspan(0.08, 0.22, color=".9", zorder=0)
            ax.axhline(0, color=".5", lw=0.6)
            for method in METHODS:
                series = [
                    r
                    for r in releases
                    if r["case"] == case and r["method"] == method and r["error_" + channel]
                ]
                ax.plot(
                    [float(r["release_time"]) for r in series],
                    [float(r["error_" + channel]) for r in series],
                    label=method,
                    color=COLORS[method],
                    marker=".",
                    ms=4,
                    lw=1.2,
                )
            ax.set_ylabel(label)
            if row == 0:
                ax.set_title(case + " — same-release forecasts on A-controlled history")
            if row == 3:
                ax.set_xlabel("Planner release time [s]")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=5)
    fig.supxlabel(
        "Signed error = prediction − target truth. Shading: first two releases. "
        "Columns: separate histories.",
        fontsize=9,
    )
    finish(fig, FIGURES[1])

    timing = read(folder, "benchmark_summary.csv")
    accuracy = read(folder, "accuracy.csv")
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
    x = np.arange(len(METHODS))
    colors = [COLORS[m] for m in METHODS]
    aggregate = {r["method"]: r for r in timing if r["group"] == "all"}
    for ax, clock in zip(axes[0, :2], ("wall", "cpu")):
        ax.bar(
            x, [float(aggregate[m][clock + "_median_ms"]) for m in METHODS], color=colors, alpha=0.8
        )
        ax.scatter(
            x,
            [float(aggregate[m][clock + "_p95_ms"]) for m in METHODS],
            marker="_",
            s=130,
            color="black",
            label="p95",
        )
        ax.scatter(
            x,
            [float(aggregate[m][clock + "_max_ms"]) for m in METHODS],
            marker="x",
            s=30,
            color="black",
            label="maximum",
        )
        ax.set(
            xticks=x,
            xticklabels=METHODS,
            ylabel="Time per complete candidate call [ms]",
            title=clock.upper() + " cost — 960 calls/method",
        )
        ax.legend(fontsize=8)
    ax = axes[0, 2]
    ax.bar(
        x,
        [float(aggregate[m]["initialization_wall_ms"]) for m in METHODS],
        color=colors,
        label="engine initialization",
    )
    ax.bar(
        x,
        [float(aggregate[m]["precomputation_wall_ms"]) for m in METHODS],
        bottom=[float(aggregate[m]["initialization_wall_ms"]) for m in METHODS],
        color=".6",
        label="Jacobian precompilation",
    )
    ax.set(
        xticks=x,
        xticklabels=METHODS,
        ylabel="Cold one-off wall time [ms]",
        title="Initialization is excluded from warm calls",
    )
    ax.legend(fontsize=8)
    for ax, channel, unit in zip(axes[1], ("e_y", "e_psi", "delta"), ("m", "rad", "rad")):
        for offset, case, alpha in [(-0.18, "D4-R2_A", 0.45), (0.18, "D4-R4_A", 1)]:
            by_method = {
                r["method"]: float(r["rms"])
                for r in accuracy
                if r["case"] == case and r["phase"] == "all" and r["channel"] == channel
            }
            ax.bar(
                x + offset,
                [by_method[m] for m in METHODS],
                width=0.34,
                color=colors,
                alpha=alpha,
                label=case,
            )
        ax.set(
            xticks=x,
            xticklabels=METHODS,
            ylabel=f"{channel} target RMS [{unit}]",
            title="RMS — separate histories, n=19 each",
        )
        ax.legend(fontsize=8)
    fig.supxlabel(
        "Fresh sequential SINGLE workers. Complete calls include input preview and domain checks. "
        "No solver runs.",
        fontsize=9,
    )
    finish(fig, FIGURES[2])
    return FIGURES
