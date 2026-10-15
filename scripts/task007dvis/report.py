"""Offline VIS-1 compact tables and preliminary figures from saved scientific exports."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from task007dcx.worker import geometry

from task007dvis.analysis import physical_difference, window_metrics
from task007dvis.export import csv_rows, flatten, hashes, write
from task007dvis.protocol import CASES


def build(source, output):
    output.mkdir(parents=True, exist_ok=False)
    data = {}
    summaries = {}
    windows = []
    provenance = {}
    for case in CASES:
        folder = source / case.name
        if not (folder / "summary.json").exists():
            exit_path = folder / "exit.json"
            failure = json.loads(exit_path.read_text()) if exit_path.exists() else None
            summaries[case.name] = dict(
                status=(
                    "WORKER_FAILED_AFTER_PHYSICAL_RUN"
                    if (folder / "raw.json").exists()
                    else "PREFLIGHT_FAILED"
                    if failure is not None
                    else "NOT_EXECUTED"
                ),
                exit=failure,
                retained_artifacts=hashes(folder.glob("*")),
            )
            continue
        s = json.loads((folder / "summary.json").read_text())
        summaries[case.name] = dict(
            status="STOPPED_GATE" if s["stop_gate"] else "completed",
            stop_gate=s["stop_gate"],
            physical=s.get("physical"),
        )
        provenance[case.name] = s
        if not (folder / "analysis.json").exists():
            continue
        a = json.loads((folder / "analysis.json").read_text())
        summaries[case.name].update(timing=a["timing"], coverage=a["coverage"])
        windows.extend(dict(case=case.name, **flatten(w)) for w in a["windows"])
        frame = pd.read_csv(folder / "scientific/states.csv", float_precision="round_trip")
        data[case.name] = (frame, json.loads((folder / "raw.json").read_text()))
    csv_rows(output / "lap_sector_metrics.csv", windows, ("case", "kind", "index", "complete"))
    comparison = {}
    common_metrics = []
    pairs = [
        ("controlled_A", "controlled_C70"),
        ("measured_A_1", "measured_C70_1"),
        ("measured_A_2", "measured_C70_2"),
    ]
    for a, b in pairs:
        if a not in data or b not in data:
            continue
        aa, ar = data[a]
        bb, br = data[b]
        comparison[a + "_vs_C70"] = physical_difference(
            aa.to_dict("records"), bb.to_dict("records")
        )
        for kind in ["common_time", "common_progress"]:
            if kind == "common_time":
                end = min(aa.time.iloc[-1], bb.time.iloc[-1])
                lo = 0.0
            else:
                lo = max(aa.s_abs.iloc[0], bb.s_abs.iloc[0])
                end = min(aa.s_abs.iloc[-1], bb.s_abs.iloc[-1])
            for name, frame, raw in [(a, aa, ar), (b, bb, br)]:
                selected = frame[
                    (frame.time <= end)
                    if kind == "common_time"
                    else ((frame.s_abs >= lo) & (frame.s_abs <= end))
                ]
                w = dict(
                    kind=kind,
                    index=0,
                    start=float(selected.time.iloc[0]),
                    end=float(selected.time.iloc[-1]),
                    start_s=float(selected.s_abs.iloc[0]),
                    end_s=float(selected.s_abs.iloc[-1]),
                    complete=False,
                    status="common_observed_native_coverage",
                )
                common_metrics.append(
                    dict(
                        case=name,
                        pair=a + "_vs_C70",
                        **flatten(window_metrics(frame.to_dict("records"), raw, w)),
                    )
                )
    csv_rows(output / "common_coverage_metrics.csv", common_metrics, ("case", "pair", "kind"))
    write(output / "summary.json", summaries)
    write(output / "comparison.json", comparison)
    write(output / "provenance.json", provenance)
    if not any(a in data and b in data for a, b in pairs):
        write(
            output / "figures.json",
            dict(status="NOT_GENERATED", reason="No completed paired scientific exports"),
        )
        write(output / "artifact_hashes.json", hashes(p for p in output.iterdir() if p.is_file()))
        return summaries
    # Plot only available paired evidence. Native states form polylines; no synthetic truth.
    track, _, _ = geometry()
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), layout="constrained")
    for ax, (a, b) in zip(axes, pairs):
        ax.set_title(a.replace("_A", "") + " / A vs C70")
        if a not in data or b not in data:
            ax.text(0.5, 0.5, "NOT EXECUTED", transform=ax.transAxes, ha="center")
            continue
        fa = data[a][0]
        fb = data[b][0]
        ax.plot(fa.planning_x, fa.planning_y, ":", color="black", label="Planning")
        for name, f, color in [("A", fa, "#1476aa"), ("C70", fb, "#d26720")]:
            ax.plot(f.x_world, f.y_world, color=color, lw=1, label="vehicle " + name)
            ax.plot(
                f.reference_x,
                f.reference_y,
                color=color,
                lw=0.6,
                alpha=0.55,
                ls="--",
                label="active APEX " + name,
            )
        ax.set_aspect("equal")
        ax.set_xlabel("derived world x (m)")
        ax.set_ylabel("derived world y (m)")
        ax.legend(fontsize=7)
    fig.suptitle("VIS-1 | N8, gamma2, predictor A | native Frenet trajectories mapped to XY")
    fig.savefig(output / "trajectory_overlay.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(4, 3, figsize=(15, 12), layout="constrained")
    fields = [
        ("delta", "applied steering (rad)"),
        ("e_psi", "Frenet heading (rad)"),
        ("clearance", "recorded center clearance (m)"),
        ("reserve", "active trajectory reserve (s)"),
    ]
    for j, (a, b) in enumerate(pairs):
        for i, (field, label) in enumerate(fields):
            ax = axes[i, j]
            for name, color in [(a, "#1476aa"), (b, "#d26720")]:
                if name not in data:
                    continue
                f = data[name][0]
                if field == "delta":
                    ax.step(f.s_abs, f[field], where="post", color=color, lw=0.75, label=name)
                else:
                    ax.plot(f.s_abs, f[field], color=color, lw=0.75, label=name)
            ax.set_ylabel(label)
            ax.set_xlabel("unwrapped progress (m)")
            ax.grid(alpha=0.2)
            ax.axvline(track.length, color="gray", ls=":", lw=0.8)
            if i == 0:
                ax.legend(fontsize=7)
    fig.suptitle(
        "VIS-1 | native samples; dotted seam ends initial partial traversal | "
        "no unmatched-tail performance claim"
    )
    fig.savefig(output / "control_clearance_reserve.png", dpi=150)
    plt.close(fig)
    write(output / "artifact_hashes.json", hashes(p for p in output.iterdir() if p.is_file()))
    return summaries


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2))
