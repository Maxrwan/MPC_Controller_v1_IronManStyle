"""Bounded D3/D4 imposed-delay SINGLE worker; never overwrite evidence."""

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate, environment


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--architecture", choices=["A", "B"], required=True)
    parser.add_argument("--gamma", type=float, choices=[2.0, 1.8], required=True)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--planner-delay", type=float, default=0.035, help="Imposed seconds")
    parser.add_argument("--codriver-delay", type=float, default=0.015, help="Imposed seconds")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not 0 < args.duration <= 2:
        parser.error("Pilot duration must be in (0, 2] seconds")
    if any(not math.isfinite(v) or v < 0 for v in (args.planner_delay, args.codriver_delay)):
        parser.error("Imposed delays must be finite nonnegative seconds")
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT / "results/task007d"):
        parser.error("New outputs must be under results/task007d")
    return args


def main():
    args = parse_args()
    if args.worker:
        native = configure_accelerate(1)
        from task007d.worker import run

        return 2 if run(args, native) else 0
    guards = list((ROOT / "results").rglob("MEASURED_ACTIVE"))
    if guards:
        raise RuntimeError(f"Measurement guard present: {guards}")
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise RuntimeError("Need at least 1 GiB free before a pilot")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive guard for D3 launchers, including the whole parent subprocess wait.
    guard = ROOT / "results/task007d/D3_ACTIVE"
    with guard.open("x") as stream:
        stream.write(str(args.output))
    try:
        args.output.mkdir(exist_ok=False)
        with (args.output / "worker.log").open("x") as log:
            status = subprocess.run(
                [sys.executable, __file__, *sys.argv[1:], "--worker"],
                cwd=ROOT,
                env=environment(1),
                stdout=log,
                stderr=log,
            )
        if (args.output / "summary.json").exists():
            summary = json.loads((args.output / "summary.json").read_text())
            print(
                json.dumps(
                    {
                        "output": str(args.output),
                        "stop_gate": summary["stop_gate"],
                        "comparable": summary["matched"]["comparable"],
                    }
                )
            )
        return status.returncode
    finally:
        guard.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
