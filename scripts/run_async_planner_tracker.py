"""Task006.3 sequential, native-single-thread asynchronous experiments."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate, environment

OUT = ROOT / "results/asynchronous_planner_tracker"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "suite", "analyze", "audit"])
    parser.add_argument("--name", default="async_measured")
    parser.add_argument(
        "--architecture", choices=["sync", "open_loop", "codriver"], default="codriver"
    )
    parser.add_argument("--mode", choices=["zero", "injected", "measured"], default="measured")
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--duration", type=float, default=80)
    parser.add_argument("--laps", type=int, default=2)
    parser.add_argument("--spike", action="store_true")
    parser.add_argument("--disturbance", action="store_true")
    parser.add_argument("--failure", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if args.action in ("analyze", "audit"):
        from async_study.analysis import analyze, audit

        (analyze if args.action == "analyze" else audit)(args.output)
        return
    if args.worker:
        native = configure_accelerate(1)
        from async_study.run import run

        run(args, native)
        return
    if args.action == "suite":
        cases = [
            ["--name", "sync_measured", "--architecture", "sync"],
            ["--name", "open_loop_measured", "--architecture", "open_loop"],
            ["--name", "async_measured"],
        ]
        for delay in [0, 0.025, 0.060, 0.100, 0.150, 0.250, 0.450]:
            for architecture in ["codriver", "sync"]:
                cases.append(
                    [
                        "--name",
                        f"{architecture}_{round(delay * 1000)}ms",
                        "--architecture",
                        architecture,
                        "--mode",
                        "injected",
                        "--delay",
                        str(delay),
                    ]
                )
        cases += [
            ["--name", "isolated_150ms", "--mode", "injected", "--delay", "0.025", "--spike"],
            [
                "--name",
                "disturbance_feedback",
                "--mode",
                "injected",
                "--delay",
                "0.025",
                "--disturbance",
            ],
            [
                "--name",
                "disturbance_playback",
                "--architecture",
                "open_loop",
                "--mode",
                "injected",
                "--delay",
                "0.025",
                "--disturbance",
            ],
            ["--name", "isolated_failure", "--mode", "injected", "--delay", "0.025", "--failure"],
        ]
        for case in cases:
            subprocess.run(
                [sys.executable, __file__, "run", *case, "--output", str(args.output)],
                check=True,
                cwd=ROOT,
            )
        return
    if (args.output / ".stop").exists():
        raise RuntimeError("Study stop requested before the next condition")
    folder = args.output / args.name
    if (folder / "summary.json").exists():
        raise ValueError(f"Existing case retained: {folder}; choose a fresh name/output")
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "worker.log").open("w") as log:
        result = subprocess.run(
            [sys.executable, __file__, *sys.argv[1:], "--worker"],
            cwd=ROOT,
            env=environment(1),
            stdout=log,
            stderr=log,
        )
    if result.returncode:
        raise RuntimeError(f"Worker failed: {folder / 'worker.log'}")
    print(
        args.name, json.loads((folder / "summary.json").read_text()).get("stop_reason"), flush=True
    )


if __name__ == "__main__":
    main()
