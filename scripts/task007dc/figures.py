"""Nine C figures from compact retained numerical tables; no simulation or solver calls."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAMES = ["vx", "vy", "r", "e_psi", "s_abs", "e_y"]
UNITS = ["m/s", "m/s", "rad/s", "rad", "m", "m"]
COLORS = ["#405b73", "#007f73", "#b65425"]
LABELS = ["Variable A", "Fixed A 70 ms", "Fixed A 80 ms"]


def render(tables, ecdf, output):
    output.mkdir(parents=True, exist_ok=False)
    s = json.loads((tables / "summary.json").read_text())
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    def read(name, kind):
        return pd.read_csv(tables / (name + "_" + kind + ".csv"))

    def finish(fig, name, title, subtitle="Synthetic N8 / dt=0.1 s / A predictor / driver=5 ms"):
        fig.suptitle(title + "\n" + subtitle, fontsize=13)
        fig.tight_layout(rect=(0, 0, 1, 0.91))
        fig.savefig(output / ("task007dc_" + name + ".png"), dpi=170)
        plt.close(fig)

    def cases(g):
        return [f"C3_g{g}_" + suffix for suffix in ["variable", "fixed70", "fixed80"]]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    rows = [
        ("C1_steady", 0, "Early ready"),
        ("C2_miss", 3, "Controlled miss"),
        ("C2_miss", 4, "Recovery"),
    ]
    for y, (name, i, label) in enumerate(rows):
        c = read(name, "cycles").iloc[i]
        tr, ready, target = 1000 * c["t_release"], 1000 * c["t_ready"], 1000 * c["valid_from"]
        ax.plot([tr, ready], [y, y], color=COLORS[0], lw=6)
        if ready <= target:
            ax.plot([ready, target], [y, y], color="#c0dcd5", lw=6)
        ax.scatter(
            [tr, ready, target],
            [y] * 3,
            marker="o",
            s=45,
            color=[COLORS[0], "#997900", COLORS[1] if ready <= target else "#b02e44"],
            zorder=3,
        )
        ax.annotate(
            f"release {tr:.0f}", (tr, y), xytext=(0, 16), textcoords="offset points", ha="center"
        )
        ax.annotate(
            f"ready {ready:.0f}", (ready, y), xytext=(0, -24), textcoords="offset points", ha="left"
        )
        ax.annotate(
            ("accept" if ready <= target else "MISS") + f" {target:.0f}",
            (target, y),
            xytext=(0, 16),
            textcoords="offset points",
            ha="center",
        )
    ax.set(
        yticks=range(3),
        yticklabels=[r[2] for r in rows],
        xlabel="Recorded physical time [ms]",
        ylim=(-0.65, 2.7),
    )
    finish(
        fig, "fixed_handoff_timeline", "Readiness, deliberate waiting and authority are distinct"
    )

    values = np.sort(pd.read_csv(ecdf / "samples.csv")["preparation_ms"])
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.step(values, np.arange(1, len(values) + 1) / len(values), where="post", color=COLORS[0])
    for d, col in zip([50, 60, 70, 80], ["#999", "#997900", COLORS[1], COLORS[2]]):
        ax.axvline(
            d, color=col, ls="--", label=f"{d} ms: {100 * np.mean(values > d):.2f}% exceeded"
        )
    ax.set(
        xlabel="Retained measured preparation [ms]",
        ylabel="Empirical cumulative fraction",
        xlim=(40, 190),
        ylim=(0, 1.02),
    )
    ax.legend(loc="lower right")
    finish(
        fig,
        "deadline_ecdf",
        f"Historical Mac N8 preparation ECDF: n={len(values)}, maximum={max(values):.2f} ms",
        "Retained Task007C variable-target measurements; not a hard-real-time guarantee",
    )

    a, b = [read(n, "states").set_index("time") for n in ["C1_steady", "C1_jitter"]]
    a.index = a.index.round(10)
    b.index = b.index.round(10)
    times = sorted(set(a.index) & set(b.index))
    times = [t for t in times if abs(t - round(t / 0.01) * 0.01) < 1e-10]
    fig, axes = plt.subplots(3, 2, figsize=(10, 7.5))
    for ax, k, u in zip(axes.flat, NAMES, UNITS):
        ax.plot(times, a.loc[times, k] - b.loc[times, k], color=COLORS[1])
        ax.set(xlabel="Common recorded 10 ms samples [s]", ylabel=f"Steady − jitter {k} [{u}]")
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    finish(
        fig,
        "jitter_decoupling",
        "C1: identical handoff grid; small RK4 partition differences remain",
    )

    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    for name, label, col in [
        ("C1_steady", "No miss", COLORS[0]),
        ("C2_miss", "75 ms miss", COLORS[2]),
    ]:
        states = read(name, "states")
        reserve = read(name, "reserve")
        controls = read(name, "controls")
        axes[0, 0].step(states.time, states.plan_id, where="post", label=label, color=col)
        axes[0, 1].plot(states.time, states.e_y, label=label, color=col)
        axes[1, 0].plot(reserve.time, reserve.reserve, label=label, color=col)
        axes[1, 1].step(
            controls.application_time, controls.delta, where="post", label=label, color=col
        )
    for ax, y in zip(
        axes.flat,
        ["Active plan ID", "Recorded e_y [m]", "Trajectory reserve [s]", "Applied steering [rad]"],
    ):
        ax.set(xlim=(0.35, 0.65), xlabel="Physical time [s]", ylabel=y)
        for t in [0.47, 0.475, 0.57]:
            ax.axvline(t, color="#999", ls=":", lw=1)
    axes[0, 0].set_ylim(2.5, 5.5)
    axes[0, 1].set_ylim(-0.03, 0.003)
    axes[1, 1].set_ylim(-0.012, 0.01)
    axes[0, 0].legend()
    finish(fig, "deadline_miss", "C2: miss 470 ms, discard 475 ms, next authority 570 ms")

    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    for row, g in enumerate(["2.0", "1.8"]):
        for name, label, col in zip(cases(g), LABELS, COLORS):
            cy = read(name, "cycles")
            st = read(name, "states")
            axes[row, 0].plot(
                cy.t_release, 1000 * (cy.t_accept - cy.t_release), ".-", color=col, label=label
            )
            axes[row, 1].plot(st.time, st.e_y, color=col, label=label)
        axes[row, 0].set(ylabel=f"γ={g} accepted latency [ms]", xlabel="Release time [s]")
        axes[row, 1].set(ylabel=f"γ={g} recorded e_y [m]", xlabel="Physical time [s]")
    axes[0, 0].legend(loc="lower right", fontsize=8)
    finish(
        fig,
        "variable_vs_fixed_handoff",
        "C3: fixed activation AND changed forecast target (joint intervention)",
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    for ax, g in zip(axes, ["2.0", "1.8"]):
        for name, label, col in zip(cases(g), LABELS, COLORS):
            c = read(name, "clearance")
            ax.plot(c.time, np.minimum(c.left, c.right), color=col, label=label)
        ax.axhline(0.08, color="#b02e44", ls="--", label="Synthetic margin 0.08 m")
        ax.set(
            xlabel="Physical time [s]",
            ylabel="Recorded center clearance [m]",
            title=f"γ={g}",
            ylim=(0, 0.6),
        )
    axes[0].legend(fontsize=8)
    finish(fig, "track_clearance", "Same minimum at initial state; no swept-body safety claim")

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5))
    for row, g in enumerate(["2.0", "1.8"]):
        for col, (nominal, actual, title) in enumerate(
            [
                ("nominal_steering_tv", "actual_steering_tv", "Steering TV [rad]"),
                ("nominal_heading_tv", "actual_heading_tv", "World heading TV [rad]"),
            ]
        ):
            ax = axes[row, col]
            x = np.arange(3)
            ax.bar(
                x - 0.17,
                [s["extra"][n][nominal] for n in cases(g)],
                width=0.34,
                color="#91b9aa",
                label="Sampled nominal",
            )
            ax.bar(
                x + 0.17,
                [s["runs"][n]["physical"][actual] for n in cases(g)],
                width=0.34,
                color=COLORS[0],
                label="Actual",
            )
            ax.set(
                xticks=x, xticklabels=["Variable", "70 ms", "80 ms"], ylabel=title, title=f"γ={g}"
            )
    axes[0, 0].legend()
    finish(fig, "smoothness", "Common two-second coverage: smoothness improvements are mixed")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    for ax, g in zip(axes, ["2.0", "1.8"]):
        for name, label, col in zip(cases(g), LABELS, COLORS):
            r = read(name, "reserve")
            ax.plot(r.time, r.reserve, color=col, label=label)
        ax.set(
            xlabel="Physical time [s]",
            ylabel="Remaining accepted trajectory [s]",
            title=f"γ={g}",
            ylim=(0.55, 0.85),
        )
    axes[0].legend(fontsize=8)
    finish(fig, "reserve", "Longer waiting reduces initial old-packet reserve; no exhaustion")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    ds = [50, 60, 70, 80]
    axes[0].plot(ds, [100 * np.mean(values > d) for d in ds], "o-", color=COLORS[0])
    axes[0].set(
        xlabel="Candidate offset [ms]",
        ylabel="Historical preparations exceeding offset [%]",
        title="Descriptive ECDF, not real-time guarantee",
    )
    for v, col in zip([1.5, 3.0, 6.0], COLORS):
        axes[1].plot(ds, [v * d / 1000 for d in ds], "o-", color=col, label=f"{v:g} m/s")
    axes[1].set(
        xlabel="Candidate offset [ms]",
        ylabel="Derived distance before scheduled authority [m]",
        title="v × T_h; excludes busy/grid wait and misses",
    )
    axes[1].legend()
    finish(
        fig,
        "responsiveness_tradeoff",
        "Reliability versus high-level reaction: TVLQR remains active",
        "Historical N8 ECDF and derived constant-speed distance; no new measurements",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tables", type=Path, required=True)
    p.add_argument("--ecdf", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    render(args.tables, args.ecdf, args.output)
