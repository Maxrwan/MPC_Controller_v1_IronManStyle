"""One predeclared bounded C pilot, in a fresh sequential SINGLE worker."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate, environment

PROTOCOL = ROOT / "docs/task007d/c/amended/protocol.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    protocol = json.loads(PROTOCOL.read_text())
    parser.add_argument("--case", choices=list(protocol["cases"]), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT / "results/task007d/c"):
        parser.error("C evidence must be under results/task007d/c")
    if args.worker:
        native = configure_accelerate(1)
        from task007dc.worker import run

        return 2 if run(args, protocol, native) else 0
    if (
        list((ROOT / "results").rglob("MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Active measurement guard")
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise RuntimeError("Need at least 1 GiB free")
    guard = ROOT / "results/task007d/D3_ACTIVE"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with guard.open("x") as f:
        f.write(str(args.output))
    try:
        args.output.mkdir(exist_ok=False)
        with (args.output / "worker.log").open("x") as log:
            p = subprocess.run(
                [sys.executable, __file__, *sys.argv[1:], "--worker"],
                cwd=ROOT,
                env=environment(1),
                stdout=log,
                stderr=log,
            )
        if (args.output / "summary.json").exists():
            s = json.loads((args.output / "summary.json").read_text())
            print(
                json.dumps(dict(case=args.case, stop_gate=s["stop_gate"], physical=s["physical"]))
            )
        return p.returncode
    finally:
        guard.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
