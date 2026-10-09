"""Sequential offline accuracy and predictor-only benchmark; never run the controller."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from threading_study.config import ROOT, configure_accelerate, environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--worker", choices=["score", "A", "P0", "P1a", "P1b", "P2"], help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT / "results/task007d/p"):
        parser.error("New evidence must be under results/task007d/p")
    if args.worker:
        native = configure_accelerate(1)
        from task007dp.evaluation import dataset, evaluate, sha, write

        track, cases = dataset()
        if args.worker == "score":
            rows, audit = evaluate(track, cases)
            write(args.output / "predictions.json", rows)
            write(
                args.output / "audit.json",
                dict(
                    audit=audit,
                    source_sha256={
                        str(p): sha(p)
                        for p in [
                            *Path("scripts/task007dp").glob("*.py"),
                            Path(__file__),
                            Path("docs/TASK007D_LIGHTWEIGHT_PREDICTION_STUDY.md"),
                        ]
                    },
                    evidence_sha256={n: c["provenance"] for n, c in cases.items()},
                    native=native,
                ),
            )
            print(json.dumps(dict(contexts=len(rows), audit=audit)), flush=True)
        else:
            from task007dp.benchmark import run

            value = run(args.worker, track, cases, native)
            write(args.output / f"benchmark_{args.worker}.json", value)
            print(
                json.dumps(
                    {
                        k: value[k]
                        for k in ("method", "wall_ms", "cpu_ms", "observed_process_threads")
                    }
                ),
                flush=True,
            )
        return
    if (
        list((ROOT / "results").rglob("MEASURED_ACTIVE"))
        or (ROOT / "results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Active measurement/campaign guard")
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise RuntimeError("Need at least 1 GiB free")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    guard = ROOT / "results/task007d/p/MEASURED_ACTIVE"
    with guard.open("x") as stream:
        stream.write(f"{os.getpid()} {args.output}\n")
    try:
        args.output.mkdir(exist_ok=False)
        for phase in ("score", "A", "P0", "P1a", "P1b", "P2"):
            with (args.output / f"{phase}.log").open("x") as log:
                result = subprocess.run(
                    [sys.executable, __file__, "--output", str(args.output), "--worker", phase],
                    cwd=ROOT,
                    env=environment(1),
                    stdout=log,
                    stderr=log,
                )
            print(
                f"{phase}: exit={result.returncode}; log={args.output / (phase + '.log')}",
                flush=True,
            )
            if result.returncode:
                raise RuntimeError("Stopped; failure evidence retained")
    finally:
        guard.unlink()


if __name__ == "__main__":
    main()
