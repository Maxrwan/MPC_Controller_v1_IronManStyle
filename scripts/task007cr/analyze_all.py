"""Offline-only parallel analysis; never run beside measured benchmarks."""

import argparse
import concurrent.futures
import os
from pathlib import Path


def case(path):
    from task007b.analysis import analyze_case
    from task007cr.decode_snapshots import decode

    analyze_case(path)
    decode(path)
    return path.name


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--cases", nargs="*")
    p.add_argument("--refresh", action="store_true")
    a = p.parse_args()
    root = Path("results/task007cr")
    folders = [
        p.parent
        for p in sorted(root.glob("r*/summary.json"))
        if (not a.cases or p.parent.name in a.cases)
        and (a.refresh or not (p.parent / "analysis.json").exists())
    ]
    # Pure offline work. Use native SINGLE in each spawned process before numerical imports.
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=a.workers, initializer=initialize
    ) as pool:
        for name in pool.map(case, folders):
            print("Analyzed", name, flush=True)


def initialize():
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    from threading_study.config import configure_accelerate

    configure_accelerate(1)


if __name__ == "__main__":
    main()
