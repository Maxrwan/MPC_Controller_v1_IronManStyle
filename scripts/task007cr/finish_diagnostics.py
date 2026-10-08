"""Offline comparison, exact NLP probes, then serialized one-event timing probes."""

import json
import subprocess
import sys
from pathlib import Path

OUT = Path("results/task007cr")


def main():
    from task007cr.compare import repetitions
    from task007cr.divergence import analyze, figure
    from task007cr.outcomes import summarize
    from task007cr.select_snapshots import select

    missing = [
        p.parent.name
        for p in OUT.glob("r[1234]_*/summary.json")
        if not (p.parent / "analysis.json").exists()
    ]
    if missing:
        raise RuntimeError(f"Complete offline case analysis first: {missing}")
    print("Comparisons", flush=True)
    repetitions()
    summarize()
    analyze()
    figure()
    select()
    print("Exact NLP diagnostics", flush=True)
    subprocess.run(
        [
            sys.executable,
            "scripts/task007cr/nlp_replay.py",
            "--selection",
            str(OUT / "snapshot_selection.json"),
        ],
        check=True,
    )
    records = json.loads((OUT / "r2_e_00/nlp_snapshots.json").read_text())
    record = next(r for r in records if r["plan_id"] > 0 and r["release_state"][4] >= 43)
    selection = dict(
        index=record["plan_id"] - 1,
        plan_id=record["plan_id"],
        release_time=record["release_time"],
        source_progress_m=record["release_state"][4],
        rationale=(
            "First nonstartup E planner release at or beyond 43 m, near sweeper entry; "
            "selected before perturbation outcomes"
        ),
        perturbations_ms=[-5, -2, -1, 0, 1, 2, 5],
        zero_case="r2_e_00",
    )
    (OUT / "timing_selection.json").write_text(json.dumps(selection, indent=2) + "\n")
    from task007cr.campaign import launch

    for delta in [-5, -2, -1, 1, 2, 5]:
        name = f"r7_e_{'minus' if delta < 0 else 'plus'}{abs(delta)}ms"
        launch(
            name,
            "e",
            "replay",
            "e",
            extra=["--perturb-index", str(selection["index"]), "--perturb-ms", str(delta)],
        )
    subprocess.run([sys.executable, "scripts/task007cr/analyze_all.py"], check=True)
    summarize()
    print("Diagnostic campaign complete", flush=True)


if __name__ == "__main__":
    main()
