"""Ten CX figures from compact numerical tables; never launch simulations."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

COLORS = {"A": "#345995", "C70": "#007f5f", "C80": "#bd5319"}
LABELS = {
    "vx": "vx [m/s]",
    "vy": "vy [m/s]",
    "r": "yaw rate [rad/s]",
    "e_psi": "heading error [rad]",
    "s_abs": "progress [m]",
    "e_y": "lateral [m]",
    "delta": "applied steering [rad]",
    "a_cmd": "applied acceleration [m/s²]",
}


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def build(tables, output):
    if list(Path("results").rglob("MEASURED_ACTIVE")):
        raise RuntimeError("Measurement still active")
    output.mkdir(parents=True, exist_ok=False)
    s = json.loads((tables / "summary.json").read_text())
    runs = [r for r in s["runs"] if r["study"] == 2]
    cycles = rows(tables / "cycles.csv")
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 140})

    def save(fig, name, title, note):
        fig.suptitle(
            title + "\nN8 / dt 0.1 s / gamma 2.0 / predictor A / codriver 5 ms", fontsize=13
        )
        fig.text(0.5, 0.012, note, ha="center", fontsize=9)
        fig.tight_layout(rect=(0, 0.05, 1, 0.92))
        fig.savefig(output / ("task007dcx_" + name + ".png"), dpi=160)
        plt.close(fig)

    for arch in ["A", "C70"]:
        data = rows(tables / f"jitter_{arch}_samples.csv")
        t = [float(r["time"]) for r in data]
        fig, axs = plt.subplots(3, 3, figsize=(12, 8.5))
        for ax, k in zip(axs.flat, LABELS):
            ax.plot(t, [float(r[k]) for r in data], color=COLORS[arch])
            ax.set(title=LABELS[k], xlabel="Physical time [s]")
            ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
        axs.flat[-1].plot(
            t, [float(r["reserve_a"]) - float(r["reserve_b"]) for r in data], color=COLORS[arch]
        )
        axs.flat[-1].set(title="Reserve difference [s]", xlabel="Physical time [s]")
        save(
            fig,
            "matched_jitter_" + ("C" if arch == "C70" else "A"),
            arch + ": steady minus jitter, recorded common-grid samples",
            "C70 reuses accepted C1 evidence; tiny residuals retain original RK4 partition effects."
            if arch == "C70"
            else "Same 30 ms steady versus 23/47/61/39 ms readiness histories as retained C1.",
        )
    fig, axs = plt.subplots(2, 4, figsize=(13, 7))
    for ax, k in zip(axs.flat, LABELS):
        values = [s["jitter"][a]["metrics"][k]["rms"] for a in ["A", "C70"]]
        ax.bar(["A", "C70"], values, color=[COLORS[a] for a in ["A", "C70"]])
        ax.set_yscale("log")
        ax.set(title=LABELS[k], ylabel="RMS difference")
    save(
        fig,
        "jitter_sensitivity_comparison",
        "Matched jitter sensitivity: separate physical channels",
        "Log scales; deterministic pair, not a statistical population. No C80 jitter experiment.",
    )
    fig, axs = plt.subplots(1, 2, figsize=(11, 5))
    for arch in COLORS:
        x = sorted(
            float(c["measured_preparation_duration"]) * 1000
            for c in cycles
            if c["case"].startswith("S2_") and c["architecture"] == arch
        )
        y = np.arange(1, len(x) + 1) / len(x)
        for ax in axs:
            ax.step(x, y, where="post", label=f"{arch} (n={len(x)})", color=COLORS[arch])
            ax.set(
                xlabel="Measured preparation [ms]",
                ylabel="Empirical cumulative fraction",
                ylim=(0, 1.01),
            )
            ax.axvline(70, color=COLORS["C70"], ls=":", alpha=0.6)
            ax.axvline(80, color=COLORS["C80"], ls=":", alpha=0.6)
    axs[0].set_xlim(40, 90)
    axs[0].set_title("Main distribution")
    axs[1].set_title("All outliers retained")
    axs[1].legend()
    save(
        fig,
        "measured_deadline_distribution",
        "Fresh measured runtime preparation, 10 runs per architecture",
        (
            "Prediction + solve + gain preparation; startup separate. "
            "Host observations, not real-time guarantees."
        ),
    )
    fig, axs = plt.subplots(1, 2, figsize=(11, 5))
    for arch in ["C70", "C80"]:
        cs = [c for c in cycles if c["case"].startswith("S2_") and c["architecture"] == arch]
        vals = sorted(float(c["deadline_margin"]) * 1000 for c in cs if c["deadline_margin"])
        axs[0].step(
            vals,
            np.arange(1, len(vals) + 1) / len(vals),
            where="post",
            color=COLORS[arch],
            label=arch,
        )
        rr = sorted([r for r in runs if r["architecture"] == arch], key=lambda r: r["repetition"])
        axs[1].plot(
            [r["repetition"] for r in rr],
            [100 * r["timing"]["miss_fraction"] for r in rr],
            "-o",
            label=arch,
            color=COLORS[arch],
        )
    axs[0].axvline(0, color="black", ls=":")
    axs[0].set(
        xlabel="Deadline margin [ms]",
        ylabel="Empirical cumulative fraction",
        title="Negative = late",
    )
    axs[0].legend()
    axs[1].set(
        xlabel="Repetition",
        ylabel="Missed / resolved deadlines [%]",
        title="Each retained repetition",
    )
    axs[1].legend()
    save(
        fig,
        "c70_vs_c80_deadline_margin",
        "Fresh fixed deadlines: margin and per-run misses",
        (
            "Distinct from planner-busy skipped releases; "
            "cycle correlations limit pooled fraction inference."
        ),
    )
    fig, axs = plt.subplots(2, 2, figsize=(11, 7))
    for arch in ["C70", "C80"]:
        mm = [m for m in s["misses"] if m["architecture"] == arch]
        for ax, key, label in zip(
            axs.flat,
            [
                "minimum_reserve_to_recovery",
                "recovery_latency",
                "steering_tv_to_recovery",
                "minimum_clearance_to_recovery",
            ],
            [
                "Minimum recorded reserve [s]",
                "Miss-to-recovery [s]",
                "Steering TV during miss window [rad]",
                "Minimum center clearance [m]",
            ],
        ):
            ax.scatter(
                range(1, len(mm) + 1),
                [m[key] for m in mm],
                label=arch,
                color=COLORS[arch],
                alpha=0.8,
            )
            ax.set(xlabel="Miss index within architecture", ylabel=label)
    axs[0, 0].axhline(0.2, ls=":", color="red", label="Existing warning reserve")
    axs[0, 0].legend()
    save(
        fig,
        "deadline_miss_consequences",
        "All measured misses: consequences through recovery",
        (
            f"{len(s['misses'])} retained misses. Unequal windows; "
            "TV is descriptive, not a no-miss counterfactual."
        ),
    )

    def run_panels(name, title, fields, shape=(2, 3)):
        fig, axs = plt.subplots(*shape, figsize=(12, 7))
        for ax, (path, label) in zip(np.asarray(axs).flat, fields):
            for j, arch in enumerate(COLORS):
                vals = []
                for r in runs:
                    if r["architecture"] != arch:
                        continue
                    v = r
                    for key in path.split("."):
                        v = v[key]
                    vals.append(v)
                ax.scatter(
                    np.full(len(vals), j) + np.linspace(-0.09, 0.09, len(vals)),
                    vals,
                    color=COLORS[arch],
                    alpha=0.7,
                    s=22,
                )
                ax.plot([j - 0.15, j + 0.15], [np.mean(vals)] * 2, color="black", lw=2)
            ax.set_xticks(range(3), COLORS)
            ax.set_ylabel(label)
            ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 3), useOffset=False)
        save(
            fig,
            name,
            title,
            (
                "Dots = 10 retained repetitions; black lines = means. "
                "Common 0–1.99 s grid for control quality."
            ),
        )

    run_panels(
        "smoothness_comparison",
        "Planned and actual smoothness remain distinct",
        [
            ("quality.planned_steering_tv", "Planned steering TV [rad]"),
            ("quality.applied_steering_tv", "Applied steering TV [rad]"),
            ("quality.steering_rate_limit_fraction", "Rate-limit time fraction"),
            ("quality.planned_heading_tv", "Planned heading TV [rad]"),
            ("quality.actual_heading_tv", "Actual heading TV [rad]"),
            ("quality.acceleration_tv", "Acceleration TV [m/s²]"),
        ],
    )
    run_panels(
        "tracking_comparison",
        "APEX-to-vehicle: canonical per-state RMS",
        [("quality.tracking." + k + ".rms", LABELS[k]) for k in list(LABELS)[:6]],
    )
    run_panels(
        "reserve_comparison",
        "Reserve and responsiveness tradeoffs",
        [
            ("physical.minimum_reserve", "Minimum recorded reserve [s]"),
            ("timing.accepted_latency.mean", "Mean accepted latency [s]"),
            ("physical.planner_busy_misses", "Planner-busy skipped releases"),
            ("timing.wait.mean", "Mean ready-to-target wait [s]"),
            ("extra.censored_cycles", "Censored cycles"),
            ("quality.progress_rate", "Observed progress rate [m/s]"),
        ],
    )
    run_panels(
        "physical_validity",
        "Full recorded physical extrema; no continuous swept-body guarantee",
        [
            ("physical.minimum_center_clearance", "Minimum center clearance [m]"),
            ("physical.max_predicted_slack", "Maximum predicted slack [m]"),
            ("extra.max_front_utilization", "Front tire utilization"),
            ("extra.max_rear_utilization", "Rear tire utilization"),
            ("extra.max_abs_beta", "Maximum |beta| [rad]"),
            ("extra.minimum_frenet_denominator", "Minimum Frenet denominator"),
        ],
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tables", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    build(args.tables, args.output)
