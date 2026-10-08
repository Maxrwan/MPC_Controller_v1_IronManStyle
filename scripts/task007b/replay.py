"""Replay archived fixtures and explicit configurations in serialized fresh workers."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("results/task007b"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cases", nargs="*")
    args = parser.parse_args()
    if args.archive.resolve() == args.output.resolve():
        raise ValueError("Replay into a separate output directory")
    records = json.loads((args.archive / "study_manifest.json").read_text())
    names = {record["case"] for record in records}
    if args.cases and not set(args.cases) <= names:
        raise ValueError("Unknown requested case")
    for record in records:
        if args.cases and record["case"] not in args.cases:
            continue
        command = [sys.executable, "scripts/run_task007b.py", "run"]
        for flag, value in {
            "output": args.output,
            "case": record["case"],
            "fixture": args.archive / record["case"] / "fixture",
            "gamma": record["gamma"],
            "progress-weight": record["progress_weight"],
            "mode": record["mode"],
            "laps": record["laps"],
            "duration": record["duration"],
            "injected-delay": record["injected_delay"],
        }.items():
            command.extend(["--" + flag, str(value)])
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
