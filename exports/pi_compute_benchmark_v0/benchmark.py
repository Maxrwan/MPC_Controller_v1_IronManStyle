#!/usr/bin/env python3
"""Bounded serial supervisor. The monitor never runs in the numerical worker."""

import argparse
import csv
import fcntl
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from common import ROOT, THREAD_ENV, distribution, verify_sources, write


def sensors():
    readings = {}
    for path in sorted(Path("/sys/class/thermal").glob("thermal_zone*/temp")):
        try:
            readings[str(path)] = {
                "temperature_c": float(path.read_text()) / 1000,
                "type": path.with_name("type").read_text().strip(),
            }
        except (OSError, ValueError):
            pass
    return readings


def summarize(plans, tracker, applied_controls=()):
    output = {}
    for phase, rows in (
        ("all", plans),
        ("startup", [p for p in plans if p.get("startup")]),
        ("recurring", [p for p in plans if not p.get("startup")]),
        ("warm", [p for p in plans if p.get("warm_start")]),
        ("cold", [p for p in plans if p.get("warm_start") is False]),
    ):
        output["ipopt_" + phase] = distribution(
            [(p.get("solver") or {}).get("solve_time") for p in rows], 0.1
        )
        output["preparation_" + phase] = distribution([p.get("prepare_wall_s") for p in rows], 0.1)
    output["tracker_update"] = distribution([t.get("update_wall_s") for t in tracker], 0.01)
    trajectory_controls = [c for c in applied_controls if c.get("mode") == "trajectory"]
    output["tracker_validated_applied"] = distribution(
        [c.get("total_time") for c in trajectory_controls], 0.01
    )
    output["command_validation_applied"] = distribution(
        [c.get("command_validation_time") for c in trajectory_controls], 0.01
    )
    return output


def completed_plans(folder):
    """Recover fully journaled calls after a worker timeout; never invent an end."""
    path = folder / "plans.json"
    if path.exists():
        return json.loads(path.read_text())
    path = folder / "progress.jsonl"
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue  # A killed worker can leave the final line incomplete.
            if event.get("event") == "prepare_end":
                rows.append({k: v for k, v in event.items() if k != "event"})
    return rows


def supervise(folder, scenario, timeout, self_check):
    import psutil

    command = [
        sys.executable,
        str(ROOT / "benchmark.py"),
        "--worker",
        scenario,
        "--output",
        str(folder),
    ]
    if self_check:
        command.append("--self-check")
    start = time.perf_counter()
    samples, timed_out = [], False
    previous = {}
    with (folder / "worker.log").open("x") as log:
        child = subprocess.Popen(
            command,
            stdout=log,
            stderr=subprocess.STDOUT,
            env={**os.environ, **THREAD_ENV},
            start_new_session=True,
        )
        process = psutil.Process(child.pid)
        try:
            while child.poll() is None:
                now = time.perf_counter()
                try:
                    threads = process.threads()
                    counters = {t.id: t.user_time + t.system_time for t in threads}
                    process_cpu = process.cpu_times()
                    samples.append(
                        {
                            "elapsed_wall_s": now - start,
                            "monotonic_s": now,
                            "rss_bytes": process.memory_info().rss,
                            "process_cpu_s": process_cpu.user + process_cpu.system,
                            "thread_count": len(threads),
                            "thread_cpu_s": counters,
                            "threads_with_cpu_delta": sum(
                                value > previous.get(tid, value) for tid, value in counters.items()
                            ),
                            "sensors": sensors(),
                        }
                    )
                    previous = counters
                except (psutil.Error, OSError):
                    pass
                if now - start >= timeout:
                    timed_out = True
                    os.killpg(child.pid, signal.SIGKILL)
                    break
                time.sleep(0.02)
            returncode = child.wait()
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    write(folder / "resource_samples.json", samples)
    peak = max((s["rss_bytes"] for s in samples), default=None)
    observed = {
        "exit_code": returncode,
        "timed_out": timed_out,
        "subprocess_wall_s": time.perf_counter() - start,
        "peak_sampled_rss_bytes": peak,
        "sample_count": len(samples),
        "nominal_sample_interval_s": 0.02,
        "observed_process_thread_counts": sorted({s["thread_count"] for s in samples}),
        "maximum_threads_with_cpu_delta": max(
            (s["threads_with_cpu_delta"] for s in samples), default=None
        ),
        "thread_observation_limit": "Sampled per-thread CPU deltas; not instantaneous "
        "parallelism or proof of a continuously exact count.",
    }
    write(folder / "supervisor.json", observed)
    return observed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repetitions", type=int, default=1, choices=range(1, 6))
    parser.add_argument("--timeout-seconds", type=int, default=180, choices=range(10, 601))
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="One real startup solve + TVLQR update, no closed-loop window",
    )
    parser.add_argument(
        "--worker",
        choices=["straight", "high_curvature", "curvature_transition"],
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    os.environ.update(THREAD_ENV)
    output = args.output or Path("results") / datetime.now(timezone.utc).strftime(
        "run-%Y%m%dT%H%M%SZ"
    )
    output = output.resolve()
    if not output.is_relative_to((ROOT / "results").resolve()):
        parser.error("All outputs must be inside this package's results directory")
    scenarios = json.loads((ROOT / "scenarios.json").read_text())
    if args.worker:
        from worker import run

        scenario = next(s for s in scenarios["windows"] if s["name"] == args.worker)
        try:
            return run(output, scenario, args.self_check)
        except Exception:
            write(
                output / "worker_fatal.json",
                {"status": "FAILED", "exception": traceback.format_exc()},
            )
            return 2
    (ROOT / "results").mkdir(exist_ok=True)
    with (ROOT / "results/.benchmark.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another benchmark owns this results directory's measurement lock")
        output.mkdir(parents=True, exist_ok=True)
        # Launcher may have already recorded read-only host identity here.
        if any(p.name != "host.txt" for p in output.iterdir()):
            parser.error("Refusing to overwrite an existing run")
        with (output / "RUNNING").open("x") as marker:
            marker.write(str(os.getpid()) + "\n")
        start, cpu = time.perf_counter(), time.process_time()
        manifest = verify_sources()
        write(
            output / "run_configuration.json",
            {
                "scientific_revision": manifest["scientific_revision"],
                "producer_reference": manifest["producer_reference"],
                "scenarios": scenarios,
                "repetitions": args.repetitions,
                "window_duration_s": 2.0,
                "timeout_per_window_s": args.timeout_seconds,
                "self_check": args.self_check,
                "single_thread_environment": THREAD_ENV,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "package_files_sha256": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in ROOT.rglob("*")
                    if p.is_file()
                    and "results" not in p.relative_to(ROOT).parts
                    and "__pycache__" not in p.parts
                },
                "hardware": {
                    "uname": list(platform.uname()),
                    "cpu_count": os.cpu_count(),
                    "device_tree_model": read_optional("/proc/device-tree/model"),
                    "cpuinfo": read_optional("/proc/cpuinfo"),
                    "initial_sensors": sensors(),
                },
                "scheduling": "Frozen measured-availability Architecture A "
                "discrete-event simulation: "
                "measured prepare and tracker+validation durations determine synthetic "
                "readiness; held-input plant advances through that interval with <=5 ms "
                "steps. No injected actuator/sensor/network/ROS delay. Serialized host "
                "execution is not concurrent on-board execution or wall-clock paced physics.",
                "claim_limit": "Empirical compute samples only; no WCET, guaranteed real-time, "
                "physical Safety, or deployment qualification.",
            },
        )
        if shutil.disk_usage(output).free < 1024**3:
            write(output / "BLOCKED.json", {"reason": "Less than 1 GiB free"})
            return 2
        if platform.system() != "Linux" or platform.machine() not in ("aarch64", "arm64"):
            write(output / "BLOCKED.json", {"reason": "Run in the supplied Linux ARM64 container"})
            return 2
        entries, plans, tracker, applied_controls = [], [], [], []
        selected = scenarios["windows"][:1] if args.self_check else scenarios["windows"]
        for repetition in range(args.repetitions):
            for scenario in selected:
                name = f"rep-{repetition + 1:02d}-{scenario['name']}"
                folder = output / name
                folder.mkdir()
                print("Running", name, flush=True)
                observation = supervise(
                    folder, scenario["name"], args.timeout_seconds, args.self_check
                )
                report_path = folder / "worker_summary.json"
                report = (
                    json.loads(report_path.read_text())
                    if report_path.exists()
                    else {
                        "status": "FAILED_OR_INCOMPLETE",
                        "reason": "Worker report missing; inspect logs/progress",
                    }
                )
                rows = completed_plans(folder)
                ticks = (
                    json.loads((folder / "tracker.json").read_text())
                    if (folder / "tracker.json").exists()
                    else []
                )
                for row in rows + ticks:
                    row.update(window=scenario["name"], repetition=repetition + 1)
                plans.extend(rows)
                tracker.extend(ticks)
                raw_path = folder / "raw_simulation.json"
                raw = json.loads(raw_path.read_text()) if raw_path.exists() else None
                controls = (raw or {}).get("controls", [])
                applied_controls.extend(controls)
                entries.append(
                    {
                        "window": scenario["name"],
                        "repetition": repetition + 1,
                        "observation": observation,
                        "worker": report,
                        "distributions": summarize(rows, ticks, controls),
                    }
                )
        import resource

        child_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
        status = (
            "COMPLETE"
            if all(
                e["observation"]["exit_code"] == 0 and e["worker"]["status"] == "COMPLETE"
                for e in entries
            )
            else "FAILED_OR_INCOMPLETE"
        )
        distributions = summarize(plans, tracker, applied_controls)
        summary = {
            "status": status,
            "self_check": args.self_check,
            "windows": entries,
            "whole_run_wall_s": time.perf_counter() - start,
            "supervisor_process_cpu_s": time.process_time() - cpu,
            "children_process_cpu_s": child_cpu.ru_utime + child_cpu.ru_stime,
            "peak_sampled_worker_rss_bytes": max(
                (e["observation"]["peak_sampled_rss_bytes"] or 0 for e in entries), default=0
            ),
            "distributions": distributions,
            "censoring": "Timeout/killed workers retain progress.jsonl and logs; no missing "
            "timing is imputed. Recorded failed solves remain in distributions. "
            "Raw simulation retains pending-at-end and unaccepted plans.",
            "claim_limit": "Empirical samples; no WCET or guaranteed real-time performance.",
        }
        write(output / "summary.json", summary)
        with (output / "timing_summary.csv").open("x", newline="") as file:
            writer = csv.DictWriter(
                file, ["population", *next(iter(distributions.values())).keys()]
            )
            writer.writeheader()
            for population, row in distributions.items():
                writer.writerow({"population": population, **row})
        (output / "RUNNING").rename(output / "FINISHED")
        print(json.dumps({"status": status, "output": str(output)}), flush=True)
        return 0 if status == "COMPLETE" else 2


def read_optional(path):
    try:
        return Path(path).read_text().strip("\0\n")
    except OSError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
