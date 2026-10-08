"""Historical timing reconstruction and explicit missing-data inventory."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

CASES = {"e": "b3_g2.5_w1", "f": "b3_g2.5_w2", "c": "b4_g2_w0"}


def audit(output=Path("results/task007cr")):
    output.mkdir(exist_ok=True, parents=True)
    records = {}
    for label, case in CASES.items():
        folder = Path("results/task007b") / case
        events = json.loads((folder / "events.json").read_text())
        summary = json.loads((folder / "summary.json").read_text())
        controls = pd.read_csv(folder / "controls.csv", float_precision="round_trip")
        plans = [p for p in events["plans"] if not p["startup"]]
        # Prefer logged physical_delay, avoiding subtraction-induced rounding changes.
        plan_delays = [p["physical_delay"] for p in plans]
        np.testing.assert_allclose(
            plan_delays,
            [p["completion_time"] - p["release_time"] for p in plans],
            atol=1e-12,
            rtol=0,
        )
        driver_delays = controls.physical_latency.tolist()
        np.testing.assert_allclose(
            controls.application_time - controls.time, driver_delays, atol=1e-12, rtol=0
        )
        trace = dict(
            planner=plan_delays,
            codriver=driver_delays,
            planner_release_times=[p["release_time"] for p in plans],
            codriver_release_times=controls.time.tolist(),
            original_end_time=summary["end_time"],
            original_case=case,
            indexing="Launched work, not nominal releases; startup planner excluded",
            exhaustion="Stop explicitly; no padding, cycling, extrapolation or invented tail",
        )
        (output / f"trace_{label}.json").write_text(json.dumps(trace, indent=2) + "\n")
        records[label] = dict(
            case=case,
            files={
                str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in folder.rglob("*")
                if p.is_file()
            },
            available=[
                "planner release/completion/physical delay/full preparation/solver/preview/gain",
                "applied codriver releases/physical delays/command application times",
                "skipped releases/handoffs/state history/active packet IDs",
                "iterations/status/objective components/predictions/previews/commands",
            ],
            missing=[
                "exact NLP initial guesses and previous warm-start vectors",
                "exact numeric NLP parameter/bound snapshot and dual multipliers",
                "unapplied in-flight codriver command at termination, if any",
            ],
            planning_lookup="Per-solve preview/progress and immutable complete fixture retained",
            planner_launches=len(plans),
            codriver_applied=len(controls),
            last_codriver_release=float(controls.time.iloc[-1]),
            end_time=summary["end_time"],
            configuration=summary["config"],
            runtime_hashes=summary["source_sha256"],
            fixture_hashes=summary["fixture_sha256"],
        )
    (output / "historical_audit.json").write_text(json.dumps(records, indent=2) + "\n")
    print("Historical artifacts hashed and E/F/C traces reconstructed")


if __name__ == "__main__":
    audit()
