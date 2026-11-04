"""Bounded W1 supervisor. Startup is stdlib-only until source/environment admission."""

import argparse
import fcntl
import json
import os
import resource
import signal
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

START = time.monotonic()
DEADLINE = START + 60
_owned_worker = None


def wall_alarm(signum, frame):
    """Cover admission, sampling and final serialization independently of polling."""
    if _owned_worker is not None and _owned_worker.poll() is None:
        try:
            os.killpg(_owned_worker.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    raise TimeoutError("Launch-through-cleanup wall budget expired")


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "results/preintegration/w1/correction-20261104T160319Z"
HISTORICAL_WORK = ROOT / "results/preintegration/w1/work-20261103T123702Z-532aa226"
CASES = ("G0", "G1", "measured-smoke")
for member in (ROOT / "src", ROOT / "scripts"):
    sys.path.insert(0, str(member))
from apex.preintegration.profile import bootstrap, git, sha  # noqa: E402
from preintegration.evidence import inventory, reconcile, write  # noqa: E402


def runtime_hashes(root=ROOT):
    import re

    text = (root / "docs/pre_sid/preintegration/PREINTEGRATION_PLAN.md").read_text()
    table = text.split("### 5.2", 1)[1].split("### 5.3", 1)[0]
    paths = re.findall(r"^\| `([^`]+)` \|", table, re.M)
    return {p: sha(root / p) for p in paths if p.endswith(".py")}


def violated(wall, cpu, rss, output):
    if wall >= 60:
        return "WALL_LIMIT"
    if cpu >= 30:
        return "CPU_LIMIT"
    if rss is not None and rss >= 2 * 1024**3:
        return "SAMPLED_RSS_LIMIT"
    if output >= 128 * 1024**2:
        return "OUTPUT_LIMIT"
    return None


def guard_records(paths, owned_root):
    records = []
    for path in paths:
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError):
            data = {}
        inactive_owned = (
            path.resolve().is_relative_to(owned_root.resolve()) and data.get("active") is False
        )
        records.append(
            {
                "path": str(path),
                "sha256": sha(path),
                "blocking": not inactive_owned,
                "disposition": "OWNED_INACTIVE_RECORD"
                if inactive_owned
                else "FOREIGN_OR_UNKNOWN_REQUIRES_INVESTIGATION",
            }
        )
    return records


def admit_gate(case, hashes):
    gate = json.loads((WORK / "software-gate.json").read_text())
    head = git(ROOT, "rev-parse", "HEAD")
    if (
        gate.get("passed") is not True
        or gate.get("hashes") != hashes
        or gate.get("producer") != head
        or git(ROOT, "status", "--porcelain")
        or gate.get("independent_review", {}).get("verdict") != "PASS"
        or gate["independent_review"].get("producer") != head
        or sha(Path(gate["independent_review"]["report"]))
        != gate["independent_review"].get("sha256")
    ):
        raise ValueError("Missing clean committed producer/software/independent-review gate")
    predecessors = {"G0": (), "G1": ("G0",), "measured-smoke": ("G0", "G1")}[case]
    for previous in predecessors:
        result = json.loads((WORK / "attempts" / (previous + "-result.json")).read_text())
        if result.get("complete") is not True or result.get("hashes") != hashes:
            raise ValueError("Prerequisite not complete at current executable bytes: " + previous)
        folder = Path(result["output"])
        witness = json.loads((WORK / "attempts" / (previous + "-exit.json")).read_text())
        if (
            witness.get("complete") is not True
            or witness.get("producer") != head
            or witness.get("exit_code") != 0
            or witness.get("ledger_sha256") != sha(WORK / "attempts" / (previous + "-result.json"))
            or witness.get("index_sha256") != sha(folder / "index.json")
        ):
            raise ValueError("Prerequisite lacks normal-exit finalization witness")
        if sha(folder / "index.json") != result["index_sha256"]:
            raise ValueError("Prerequisite inventory changed")
        for p, expected in json.loads((folder / "index.json").read_text()).items():
            member = (folder / p).resolve()
            if (
                not member.is_relative_to(folder.resolve())
                or member.stat().st_size != expected["bytes"]
                or sha(member) != expected["sha256"]
            ):
                raise ValueError("Prerequisite raw member changed")


def main(argv=None):
    global _owned_worker
    signal.signal(signal.SIGALRM, wall_alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, DEADLINE - time.monotonic()))
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    evidence_root = (ROOT / "results/preintegration/w1").resolve()
    if not output.is_relative_to(evidence_root) or output == evidence_root:
        raise ValueError("Output outside W1 root")
    output.mkdir(parents=True, exist_ok=False)
    cpu_origin = time.process_time()
    child_origin = resource.getrusage(resource.RUSAGE_CHILDREN)
    process, lock, guard = None, None, None
    samples, reason, worker, code = [], None, None, None
    hashes = runtime_hashes()
    claim = WORK / "attempts" / (args.case + ".json")
    claimed = False
    try:
        site = Path(sys.executable).parent.parent / "lib/python3.12/site-packages"
        admitted = bootstrap(ROOT, site)
        write(
            output / "admission.json",
            {
                "source": admitted.source,
                "environment": admitted.environment,
                "native": admitted.native,
                "hashes": hashes,
            },
        )
        admit_gate(args.case, hashes)
        import psutil

        me = psutil.Process()
        excluded = {p.pid for p in me.parents()} | {me.pid}
        competing = []
        for p in psutil.process_iter(["pid", "cmdline", "create_time"]):
            try:
                cmd = " ".join(p.info["cmdline"] or [])
                if p.pid not in excluded and any(
                    t in cmd
                    for t in (
                        "pytest",
                        "run_task007",
                        "profile1/run_phase",
                        "nmpc_weight_worker",
                        "preintegration/worker.py",
                        "preintegration/launch.py",
                    )
                ):
                    competing.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        guards = []
        roots = [
            Path(line[9:])
            for line in git(ROOT, "worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        ]
        for root in roots:
            result_root = root / "results"
            for pattern in ("**/MEASURED_ACTIVE", "**/D3_ACTIVE"):
                guards.extend(
                    p
                    for p in result_root.glob(pattern)
                    if p.is_file() and p != WORK / "MEASURED_ACTIVE"
                )
        guard_observations = guard_records(guards, WORK)
        # The original inactive owned records are preserved, including fixture guards.
        for record in guard_observations:
            path = Path(record["path"])
            if path.resolve().is_relative_to(HISTORICAL_WORK.resolve()):
                historical = guard_records([path], HISTORICAL_WORK)[0]
                record.update(historical)
        write(
            output / "competition.json",
            {
                "processes": competing,
                "guard_files": guard_observations,
                "sampling_limit": "point-in-time admission",
            },
        )
        if competing or any(record["blocking"] for record in guard_observations):
            raise ValueError(
                "Competing measurement/process or foreign guard requires investigation"
            )
        free = psutil.disk_usage(ROOT).free
        if free < 1024**3:
            raise ValueError("DISK_ADMISSION")
        lock = (WORK / "measurement.lock").open("a+")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        guard = WORK / "MEASURED_ACTIVE"
        write(
            guard,
            {
                "pid": me.pid,
                "birth": me.create_time(),
                "active": True,
                "case": args.case,
                "output": str(output),
            },
        )
        claim.parent.mkdir(exist_ok=True)
        with claim.open("x") as stream:
            json.dump(
                {
                    "case": args.case,
                    "output": str(output),
                    "hashes": hashes,
                    "head": admitted.source["head"],
                    "consumed": True,
                },
                stream,
            )
        claimed = True
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("PYTHON")
            and k
            not in (
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "BLIS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
        env.update(
            PYTHONHASHSEED="0",
            PYTHONDONTWRITEBYTECODE="1",
            VECLIB_MAXIMUM_THREADS="1",
            MPLCONFIGDIR=str(output / "cache/mpl"),
            XDG_CACHE_HOME=str(output / "cache"),
        )
        command = [
            sys.executable,
            "-P",
            "-S",
            str(ROOT / "scripts/preintegration/worker.py"),
            "--case",
            args.case,
            "--output",
            str(output),
        ]
        write(
            output / "invocation.json",
            {
                "argv": command,
                "cwd": str(ROOT),
                "utc": datetime.now(timezone.utc).isoformat(),
                "monotonic_origin": START,
                "free_disk_bytes": free,
                "supervisor_identity": {"pid": me.pid, "birth": me.create_time()},
                "native": admitted.native,
                "caps": {
                    "wall_s": 60,
                    "cpu_s": 30,
                    "rss_bytes": 2 * 1024**3,
                    "output_bytes": 128 * 1024**2,
                },
                "sample_interval_s": 0.02,
            },
        )
        if time.monotonic() - START >= 60:
            raise ValueError("Wall budget exhausted before worker launch")
        with (output / "worker.log").open("wb") as log:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            _owned_worker = process
            try:
                birth = psutil.Process(process.pid).create_time()
            except psutil.NoSuchProcess:
                birth = None
            write(
                output / "worker-start.json", {"pid": process.pid, "birth": birth, "argv": command}
            )
            observed_cpu = {}
            while process.poll() is None:
                members = []
                try:
                    child = psutil.Process(process.pid)
                    members = [child] + child.children(recursive=True)
                except psutil.NoSuchProcess:
                    pass
                rss, threads, unavailable, departed = 0, [], [], []
                for member in members:
                    try:
                        key = (member.pid, member.create_time())
                        cpu = member.cpu_times()
                        observed_cpu[key] = cpu.user + cpu.system
                        rss += member.memory_info().rss
                        threads.append(member.num_threads())
                    except psutil.NoSuchProcess:
                        departed.append(member.pid)
                    except psutil.AccessDenied:
                        unavailable.append(member.pid)
                cpu = time.process_time() - cpu_origin + sum(observed_cpu.values())
                worker_rss = rss
                try:
                    supervisor_rss = me.memory_info().rss
                    rss += supervisor_rss
                    witness_rss = psutil.Process(os.getppid()).memory_info().rss
                    rss += witness_rss
                except psutil.AccessDenied:
                    supervisor_rss = None
                    witness_rss = None
                    unavailable.append(me.pid)
                row = {
                    "wall_s": time.monotonic() - START,
                    "cpu_s": cpu,
                    "rss_bytes": rss if members and not unavailable else None,
                    "thread_counts": threads,
                    "worker_tree_rss_bytes": worker_rss,
                    "supervisor_rss_bytes": supervisor_rss,
                    "exit_witness_rss_bytes": witness_rss,
                    "unavailable_pids": unavailable,
                    "exited_between_samples": departed,
                }
                samples.append(row)
                size = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
                reason = violated(row["wall_s"], cpu, row["rss_bytes"], size)
                if unavailable:
                    reason = reason or "RESOURCE_COVERAGE_LOST"
                if reason:
                    os.killpg(process.pid, signal.SIGKILL)
                    break
                time.sleep(0.02)
            code = process.wait(timeout=max(0.1, 60 - (time.monotonic() - START)))
        if (output / "worker-result.json").is_file():
            worker = json.loads((output / "worker-result.json").read_text())
    except Exception as error:
        reason = reason or "SUPERVISOR_FAILURE"
        write(
            output / "supervisor-failure.json",
            {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
                "claimed": claimed,
            },
        )
    finally:
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=1)
        if guard is not None:
            write(
                guard,
                {
                    "active": False,
                    "case": args.case,
                    "output": str(output),
                    "pid": me.pid,
                    "birth": me.create_time(),
                },
            )
        if lock is not None:
            lock.close()
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (
        time.process_time()
        - cpu_origin
        + child_usage.ru_utime
        - child_origin.ru_utime
        + child_usage.ru_stime
        - child_origin.ru_stime
    )
    elapsed = time.monotonic() - START
    size = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
    reason = reason or violated(elapsed, cpu, None, size)
    result = {
        "complete": reconcile(code, worker, reason),
        "case": args.case,
        "exit_code": code,
        "guard_reason": reason,
        "samples": samples,
        "total_wall_s": elapsed,
        "total_process_tree_cpu_s": cpu,
        "rss_observation": "sampled, not continuous peak",
        "cleanup_observed": True,
        "hashes": hashes,
        "output": str(output),
        "claimed": claimed,
    }
    if not samples or not any(s["rss_bytes"] is not None for s in samples):
        result["complete"] = False
        result["guard_reason"] = result["guard_reason"] or "RESOURCE_NOT_OBSERVED"
    write(output / "supervisor-result.json", result)
    write(output / "index.json", inventory(output))
    if claimed:
        write(
            WORK / "attempts" / (args.case + "-result.json"),
            {**result, "index_sha256": sha(output / "index.json")},
        )
    # The provisional PASS above is deliberately unusable without an exit witness.
    # Include all result/index/ledger writes in the final resource disposition.
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    final_cpu = (
        time.process_time()
        - cpu_origin
        + usage.ru_utime
        - child_origin.ru_utime
        + usage.ru_stime
        - child_origin.ru_stime
    )
    final_rss = (
        me.memory_info().rss + psutil.Process(os.getppid()).memory_info().rss if claimed else None
    )
    final_reason = violated(
        time.monotonic() - START, final_cpu, final_rss, output_bytes(output, args.case)
    )
    print(json.dumps({k: result[k] for k in ("complete", "case", "guard_reason", "output")}))
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if result["complete"] and final_reason is None else 1


def output_bytes(output, case):
    paths = list(Path(output).rglob("*")) + list((WORK / "attempts").glob(case + "*.json"))
    return sum(p.stat().st_size for p in paths if p.is_file())


def witness_exit(case, output, exit_code, elapsed, cpu):
    """Called by the waiting parent only AFTER supervisor exit and all its final writes.

    An inner PASS is provisional. No successor may use it without this separate witness.
    Kernel child CPU includes the supervisor's descendants and final bookkeeping.
    """
    output = Path(output)
    accounting_wall, accounting_cpu = time.monotonic(), time.process_time()
    ledger = WORK / "attempts" / (case + "-result.json")
    reason, result = None, None
    try:
        result = json.loads(ledger.read_text())
        index = json.loads((output / "index.json").read_text())
        if result["output"] != str(output) or result["index_sha256"] != sha(output / "index.json"):
            raise ValueError("Final index/ledger binding")
        if index != inventory(output):
            raise ValueError("Final inventory incomplete or changed")
        if json.loads((output / "supervisor-result.json").read_text()) != {
            k: v for k, v in result.items() if k != "index_sha256"
        }:
            raise ValueError("Final supervisor/ledger mismatch")
    except (ValueError, OSError, KeyError) as error:
        reason = "FINALIZATION_INTEGRITY: " + str(error)
    reason = reason or violated(elapsed, cpu, None, output_bytes(output, case))
    if exit_code != 0:
        reason = reason or "SUPERVISOR_EXIT_NONZERO"
    receipt = {
        "complete": exit_code == 0
        and result is not None
        and result.get("complete") is True
        and reason is None,
        "case": case,
        "producer": git(ROOT, "rev-parse", "HEAD"),
        "exit_code": exit_code,
        "observed_launch_through_exit_wall_s": elapsed,
        "observed_process_tree_cpu_s": cpu,
        "guard_reason": reason,
        "ledger_sha256": sha(ledger) if ledger.is_file() else None,
        "index_sha256": sha(output / "index.json") if (output / "index.json").is_file() else None,
        "output": str(output),
    }
    path = WORK / "attempts" / (case + "-exit.json")
    # Serialize in memory before budget disposition. Atomic write failure leaves no witness.
    extra = len(json.dumps(receipt, indent=2, sort_keys=True).encode()) + 1
    if output_bytes(output, case) + extra >= 128 * 1024**2:
        receipt.update(complete=False, guard_reason="OUTPUT_LIMIT")
    finalized = False
    try:
        write(path, receipt)
        final_wall = elapsed + time.monotonic() - accounting_wall
        final_cpu = cpu + time.process_time() - accounting_cpu
        late = violated(final_wall, final_cpu, None, output_bytes(output, case))
        if late:
            receipt.update(complete=False, guard_reason=late)
            write(path, receipt)
        finalized = True
    finally:
        if not finalized and path.exists():
            # Retain a failed publication for audit, but never as an admission witness.
            path.replace(path.with_name(path.name + ".unadmitted"))
    return receipt


def execute(argv=None):
    """Stdlib waiting parent: observe actual supervisor exit, never launch a second worker."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_start = time.process_time()
    command = [
        sys.executable,
        "-P",
        "-S",
        str(Path(__file__).resolve()),
        "--supervise",
        "--case",
        args.case,
        "--output",
        str(output),
    ]
    process = subprocess.Popen(command, cwd=ROOT, start_new_session=True)
    try:
        code = process.wait(timeout=max(0.001, DEADLINE - time.monotonic()))
    except subprocess.TimeoutExpired:
        # The inner alarm kills its owned worker. Trigger it before terminating the group.
        os.kill(process.pid, signal.SIGALRM)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        code = -signal.SIGALRM
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (
        time.process_time()
        - cpu_start
        + after.ru_utime
        - before.ru_utime
        + after.ru_stime
        - before.ru_stime
    )
    # No witness is published on a preclaim failure. A claim stays consumed on any later failure.
    claim = WORK / "attempts" / (args.case + ".json")
    if not claim.is_file() or json.loads(claim.read_text())["output"] != str(output):
        return 1
    receipt = witness_exit(args.case, output, code, time.monotonic() - START, cpu)
    print(json.dumps(receipt))
    return 0 if receipt["complete"] else 1


if __name__ == "__main__":
    if "--supervise" in sys.argv:
        sys.argv.remove("--supervise")
        raise SystemExit(main())
    raise SystemExit(execute())
