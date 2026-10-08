"""Task007C reproduction gate: unchanged Task007B code and archived fixtures."""

import json
import subprocess
import sys
from pathlib import Path

ANCHORS = [
    ("a", "b0"),
    ("b", "b4_g1_w2"),
    ("c", "b4_g2_w0"),
    ("d", "b4_g2_w2"),
    ("e", "b3_g2.5_w1"),
    ("f", "b3_g2.5_w2"),
]


def main():
    output = Path("results/task007c")
    for letter, previous in ANCHORS:
        source = Path("results/task007b") / previous
        prior = json.loads((source / "summary.json").read_text())
        case = "anchor_" + letter
        subprocess.run(
            [
                sys.executable,
                "scripts/run_task007b.py",
                "run",
                "--output",
                str(output),
                "--case",
                case,
                "--fixture",
                str(source / "fixture"),
                "--gamma",
                str(prior["gamma"]),
                "--progress-weight",
                str(prior["progress_weight"]),
                "--laps",
                str(prior["config"]["laps"]),
                "--duration",
                str(prior["config"]["duration"]),
                "--mode",
                "measured",
            ],
            check=True,
        )
        result = json.loads((output / case / "summary.json").read_text())
        print(
            case,
            {
                k: result[k]
                for k in [
                    "lap_times",
                    "failure",
                    "solver_failures",
                    "planner_failures",
                    "fallback_events",
                    "boundary_violations",
                    "planner_misses",
                    "codriver_misses",
                ]
            },
            flush=True,
        )
        if result["failure"] or result["fallback_events"] or result["boundary_violations"]:
            raise RuntimeError("Anchor requires review before further experiments: " + case)


if __name__ == "__main__":
    main()
