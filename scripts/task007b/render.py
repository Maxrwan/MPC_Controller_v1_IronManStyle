"""Render cached post-run telemetry; never run during latency benchmarks."""

import json
from pathlib import Path

import pandas as pd
from task007b.plots import comparison, dashboard, oscillation_review

from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track


def render(output, cases):
    output = Path(output)
    if not cases:
        cases = json.loads((output / "selection.json").read_text())["dashboard_cases"]
    paths = []
    for case in cases:
        folder = output / case
        fixture = folder / "fixture"
        track, _, identity = load_track(fixture / "track_source.json")
        ref = PlanningReference(fixture, track, identity, feasibility_policy="advisory")
        paths.append(
            dashboard(
                folder,
                pd.read_csv(folder / "telemetry.csv"),
                pd.read_csv(folder / "planning_apex_nodes.csv"),
                ref,
                track,
            )
        )
    comparison(output, cases, ref)
    oscillation_review(output, ref)
    (output / "dashboards.json").write_text(json.dumps(paths, indent=2) + "\n")

    import matplotlib.pyplot as plt
    import numpy as np

    frames = []
    labels = []
    for case in ["b0", "b1_g1.25", "b1_g1.5", "b1_g1.75", "b1_g2", "b1_g2.25", "b1_g2.5"]:
        path = output / case / "telemetry.csv"
        if path.exists():
            data = pd.read_csv(path)
            frames.append(data[data.lap == 1])
            labels.append(case.replace("b1_g", "").replace("b0", "1"))
    fig, axes = plt.subplots(1, 2, figsize=(15, 5), layout="constrained")
    axes[0].boxplot([f.actual_beta for f in frames], tick_labels=labels, showfliers=False)
    axes[0].set(xlabel="Gamma (lambda=0 startup screens)", ylabel="Actual beta [rad]")
    axes[1].plot(
        [float(v) for v in labels],
        [np.max(abs(f.actual_beta)) for f in frames],
        "o-",
        label="max |beta|",
    )
    axes[1].plot(
        [float(v) for v in labels],
        [np.quantile(abs(f.actual_beta), 0.95) for f in frames],
        "o-",
        label="p95 |beta|",
    )
    axes[1].set(xlabel="Gamma", ylabel="Absolute beta [rad]")
    axes[1].legend()
    fig.savefig(output / "sideslip_vs_aggression.png", dpi=150)
    plt.close(fig)
