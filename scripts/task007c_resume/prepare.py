"""Immutable fixture derivation and retained-history selection before formulation outcomes."""

import json
from pathlib import Path

ROOT = Path("results/task007c_resume")


def main():
    from threading_study.config import configure_accelerate

    configure_accelerate(1)
    import task007b.references as refs

    refs.PACKAGES = Path("configs/planning/task007c_resume")
    gammas = [1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.1, 2.2, 2.5]
    missing = [
        g
        for g in gammas
        if not (refs.PACKAGES / refs.package_name(g) / "planning_manifest.json").exists()
    ]
    if missing:
        refs.generate(missing)
    # Do not call the old audit: original outputs are immutable. Derive a new representative trace.
    import numpy as np
    import pandas as pd

    candidates = []
    for p in sorted(Path("results/task007cr").glob("r4_e_*/analysis.json")):
        a = json.loads(p.read_text())
        candidates.append((a["tracking"]["apex_heading_total_variation"], p.parent))
    median = float(np.median([v for v, _ in candidates]))
    _, selected = min(candidates, key=lambda row: (abs(row[0] - median), row[1].name))
    events = json.loads((selected / "events.json").read_text())
    controls = pd.read_csv(selected / "controls.csv", float_precision="round_trip")
    trace = dict(
        planner=[p["physical_delay"] for p in events["plans"] if not p["startup"]],
        codriver=controls.physical_latency.tolist(),
        source=str(selected),
        selection="E measured history closest to median whole-run planned heading TV",
        median_heading_TV=median,
        exhaustion="Stop explicitly; never pad a finite trace",
    )
    (ROOT / "trace_median.json").write_text(json.dumps(trace, indent=2) + "\n")
    histories = dict(
        fixed=dict(mode="fixed", planner_s=0.035, codriver_s=0.001),
        smooth=dict(
            mode="replay",
            path="results/task007cr/trace_c.json",
            note="Retained stable C three-lap history; different demand when transferred",
        ),
        median=dict(mode="replay", path=str(ROOT / "trace_median.json"), source=str(selected)),
        pathological_e=dict(mode="replay", path="results/task007cr/trace_e.json"),
        pathological_f=dict(mode="replay", path="results/task007cr/trace_f.json"),
    )
    (ROOT / "histories.json").write_text(json.dumps(histories, indent=2) + "\n")
    print("Prepared histories", histories, flush=True)


if __name__ == "__main__":
    import subprocess
    import sys

    from threading_study.config import environment

    if "--worker" in sys.argv:
        main()
    else:
        subprocess.run([sys.executable, __file__, "--worker"], env=environment(1), check=True)
