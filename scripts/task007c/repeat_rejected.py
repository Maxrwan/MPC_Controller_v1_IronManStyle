"""One bounded repeat of each unmatched rejected anchor; no formulation changes."""

import json
import subprocess
import sys
from pathlib import Path


def main():
    output = Path("results/task007c")
    for letter, previous in [("e", "b3_g2.5_w1"), ("f", "b3_g2.5_w2")]:
        source = Path("results/task007b") / previous
        prior = json.loads((source / "summary.json").read_text())
        case = f"anchor_{letter}_repeat"
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
                "1",
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
                    "fallback_events",
                    "boundary_violations",
                    "planner_misses",
                    "codriver_misses",
                ]
            },
            flush=True,
        )


if __name__ == "__main__":
    main()
