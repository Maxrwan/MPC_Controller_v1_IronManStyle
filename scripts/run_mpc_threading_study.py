"""Task006.2.2 isolated Accelerate ceiling experiments; never concurrent solves."""

import argparse
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from time import perf_counter, sleep

from threading_study.config import OUT, ROOT, environment, thread_count


def freeze():
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "frozen_candidates.json"
    source = ROOT / "results/mpc_parameter_study/selected_candidates.json"
    if not target.exists():
        target.write_text(source.read_text())
    current, frozen = json.loads(source.read_text()), json.loads(target.read_text())
    for key in ["C", "D"]:
        if current[key] != frozen[key]:
            raise RuntimeError("Frozen candidate changed; inspect before benchmarking")


def launch(workload, threads, replicate, samples, warmup, kind="benchmark"):
    import psutil

    folder = OUT / ("runs" if kind == "benchmark" else kind) / f"{workload}_t{threads}_r{replicate}"
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / "summary.json").exists() and (folder / "monitor.json").exists():
        saved = json.loads((folder / "summary.json").read_text())
        monitor = json.loads((folder / "monitor.json").read_text())
        if monitor["exit_code"] != 0:
            raise RuntimeError(f"Failed cached run retained at {folder}; use a new replicate")
        if kind == "benchmark" and (saved["samples"] != samples or saved["warmup"] != warmup):
            raise ValueError("Cached sample/warmup counts differ; use a new replicate")
        if kind == "benchmark":
            frozen = json.loads((OUT / "frozen_candidates.json").read_text())[workload]
            if saved["configuration"] != frozen:
                raise ValueError("Cached frozen configuration differs")
        print("REUSE", folder.name, flush=True)
        return
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "worker",
        "--workload",
        workload,
        "--threads",
        str(threads),
        "--replicate",
        str(replicate),
        "--samples",
        str(samples),
        "--warmup",
        str(warmup),
        "--folder",
        str(folder),
        "--kind",
        kind,
    ]
    measurements, errors = [], set()
    with (folder / "worker.log").open("w") as log:
        child = subprocess.Popen(
            command, cwd=ROOT, env=environment(threads), stdout=log, stderr=log
        )
        observer = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                measurements.append(
                    {
                        "time": perf_counter(),
                        "threads": observer.num_threads(),
                        "rss_bytes": observer.memory_info().rss,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied) as error:
                errors.add(type(error).__name__)
            sleep(0.01)
    (folder / "monitor.json").write_text(
        json.dumps(
            {
                "sample_interval_seconds": 0.01,
                "samples": measurements,
                "errors": sorted(errors),
                "exit_code": child.returncode,
            }
        )
        + "\n"
    )
    if child.returncode:
        raise RuntimeError(f"Worker failed; inspect {folder / 'worker.log'}")
    report = json.loads((folder / "summary.json").read_text())
    print("DONE", folder.name, report.get("statistics", {}).get("solve_time", {}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=[
            "components",
            "inspect",
            "probe",
            "benchmark",
            "worker",
            "closed-loop",
            "analyze",
            "audit",
            "all",
        ],
    )
    parser.add_argument("--workload", choices=["C", "D"], default="C")
    parser.add_argument("--threads", type=thread_count, default=1)
    parser.add_argument("--replicate", type=int, default=0)
    parser.add_argument("--samples", type=int, default=120)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--folder", type=Path)
    parser.add_argument("--kind", default="benchmark")
    args = parser.parse_args()
    if args.samples < 1 or args.warmup < 0:
        parser.error("samples must be positive; warmup nonnegative")
    if args.action == "worker":
        if args.kind == "benchmark":
            from threading_study.worker import run_worker

            run_worker(
                args.workload, args.threads, args.replicate, args.samples, args.warmup, args.folder
            )
        elif args.kind == "closed_loop":
            from threading_study.validation import closed_loop

            closed_loop(args.threads, args.replicate, args.folder)
        elif args.kind == "components":
            from threading_study.stack import component_probe

            component_probe(args.workload, args.threads, args.folder)
        elif args.kind == "probe":
            from threading_study.stack import probe

            probe(args.threads, args.folder)
        return
    freeze()
    if args.action == "inspect":
        from threading_study.stack import inspect_stack

        inspect_stack()
    elif args.action == "probe":
        for n in [1, 2, 4, os.cpu_count()]:
            launch("C", n, args.replicate, args.samples, args.warmup, "probe")
    elif args.action == "benchmark":
        launch(args.workload, args.threads, args.replicate, args.samples, args.warmup)
    elif args.action == "components":
        for workload in ["C", "D"]:
            for n in [1, 2, 4, os.cpu_count()]:
                launch(workload, n, args.replicate, 2, 0, "components")
    elif args.action == "closed-loop":
        launch("C", args.threads, args.replicate, args.samples, args.warmup, "closed_loop")
    elif args.action in ["analyze", "audit"]:
        from threading_study.analysis import analyze, audit

        (analyze if args.action == "analyze" else audit)()
    elif args.action == "all":
        conditions = [(w, n) for w in ["C", "D"] for n in [1, 2, 4, os.cpu_count()]]
        for replicate in range(3):
            order = conditions.copy()
            random.Random(6220 + replicate).shuffle(order)
            for workload, threads in order:
                launch(workload, threads, replicate, args.samples, args.warmup)
        from threading_study.analysis import analyze

        analyze()


if __name__ == "__main__":
    main()
