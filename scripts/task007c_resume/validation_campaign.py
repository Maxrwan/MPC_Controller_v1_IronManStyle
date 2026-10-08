"""Explicit follow-up cells selected from the completed isolated C1-C4 grids."""

import argparse
import json
import subprocess
import sys

from task007c_resume.campaign import ROOT, launch, requires_review


def reviewed_launch(**kwargs):
    folder, summary = launch(**kwargs)
    if requires_review(folder, summary):
        (ROOT / "review_required.json").write_text(
            json.dumps(
                dict(case=folder.name, reason="Review retained follow-up failure before extending"),
                indent=2,
            )
            + "\n"
        )
        raise RuntimeError(f"Review retained failure: {folder}")
    # Finish offline extraction before the next controlled-history cell. This
    # phase never launches measured timing and records no isolated compute claim.
    subprocess.run(
        [sys.executable, "scripts/task007c_resume/analyze.py", "--cases", folder.name],
        check=True,
    )


def run(phase):
    if phase == "horizon-coverage":
        # C1 identified a nonmonotonic gamma1.9 pocket; test rather than interpolate.
        for history in ["fixed", "smooth"]:
            for horizon in [6, 8]:
                reviewed_launch(gamma=1.9, history=history, horizon=horizon)
        # Original protocol requests a known oscillatory stress case if feasible.
        # Only the smallest promising horizon extension is tested at rejected baseline2.2.
        for history in ["fixed", "smooth"]:
            reviewed_launch(gamma=2.2, history=history, horizon=6)
    elif phase == "representative-g2":
        # Full-model half-vy benefit is confined to g2/lambda0 in the initial grid.
        # Keep this narrow candidate beside baseline and both isolated horizon changes.
        for history in ["median", "pathological_e", "pathological_f"]:
            for vy, horizon, weight in [(1, 4, 0), (0.5, 4, 0), (1, 6, 0), (1, 8, 0), (1, 4, 4)]:
                reviewed_launch(gamma=2, history=history, vy=vy, horizon=horizon, weight=weight)
    elif phase == "representative-g2p1":
        for history in ["median", "pathological_e", "pathological_f"]:
            for horizon in [4, 6, 8]:
                reviewed_launch(gamma=2.1, history=history, horizon=horizon)
        # N6 passed the separately reviewed gamma2.2 fixed/smooth stress pair.
        # Check this candidate history sensitivity without accepting a larger envelope.
        for history in ["median", "pathological_e", "pathological_f"]:
            reviewed_launch(gamma=2.2, history=history, horizon=6)
    elif phase == "repeat-fixed":
        for horizon in [6, 8]:
            reviewed_launch(gamma=2, horizon=horizon, repeat=0)
        subprocess.run([sys.executable, "scripts/task007c_resume/latency_checks.py"], check=True)
        # Existing initial s_abs=1m makes the first counted lap a rolling segment.
        # Three lap-end crossings give two subsequent complete geometric laps.
        print("Starting two-full-lap confirmations after rolling segment", flush=True)
        for history in ["fixed", "smooth"]:
            for horizon in [4, 6, 8]:
                reviewed_launch(gamma=2, history=history, horizon=horizon, laps=3)
            reviewed_launch(gamma=2.2, history=history, horizon=6, laps=3)
    else:
        raise ValueError(phase)
    print("Follow-up phase complete", phase, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=["horizon-coverage", "representative-g2", "representative-g2p1", "repeat-fixed"],
    )
    run(parser.parse_args().phase)
