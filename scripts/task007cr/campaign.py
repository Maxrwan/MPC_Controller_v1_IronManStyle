"""Serialize all closed-loop diagnostics in fresh SINGLE workers; preserve each repetition."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

CASES = {"e": ("b3_g2.5_w1", 2.5, 1), "f": ("b3_g2.5_w2", 2.5, 2), "c": ("b4_g2_w0", 2, 0)}


def launch(name, label, timing, trace=None, extra=()):
    output = Path("results/task007cr")
    folder = output / name
    if (folder / "summary.json").exists():
        print("Retained completed", name, flush=True)
        return
    old, gamma, weight = CASES[label]
    command = [
        sys.executable,
        "scripts/run_task007cr.py",
        "--case",
        name,
        "--fixture",
        f"results/task007b/{old}/fixture",
        "--gamma",
        str(gamma),
        "--progress-weight",
        str(weight),
        "--timing",
        timing,
        *extra,
    ]
    if trace:
        command += ["--trace", str(output / f"trace_{trace}.json")]
    subprocess.run(command, check=True)
    report = json.loads((folder / "summary.json").read_text())
    print(
        name,
        {
            k: report[k]
            for k in ["stop_reason", "failure", "lap_times", "planner_misses", "codriver_misses"]
        },
        flush=True,
    )
    if report["failure"] and report["stop_reason"] != "diagnostic_trace_exhausted":
        print("Retained failed physical run for analysis; no retuning", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["fixed", "replay", "cross", "measured"])
    phase = parser.parse_args().phase
    if phase == "fixed":
        for label in ["e", "f", "c"]:
            for i in range(10 if label != "c" else 2):
                launch(f"r1_{label}_{i:02d}", label, "fixed")
    elif phase == "replay":
        for label in ["e", "f", "c"]:
            for i in range(5 if label != "c" else 1):
                launch(f"r2_{label}_{i:02d}", label, "replay", label)
    elif phase == "cross":
        for label, trace in [("e", "f"), ("f", "e")]:
            launch(f"r3_{label}_trace_{trace}", label, "replay", trace)
    else:
        for i in range(10):
            for label in ["e", "f"]:
                launch(f"r4_{label}_{i:02d}", label, "normal")


if __name__ == "__main__":
    main()
