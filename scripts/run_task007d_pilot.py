"""D3 only: bounded, sequential, imposed-delay SINGLE worker; never overwrite evidence."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate, environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--architecture", choices=["A", "B"], required=True)
    parser.add_argument("--gamma", type=float, choices=[2.0, 1.8], required=True)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 0 < args.duration <= 2:
        parser.error("D3 pilot duration must be in (0, 2] seconds")
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT / "results/task007d"):
        parser.error("New outputs must be under results/task007d")
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
