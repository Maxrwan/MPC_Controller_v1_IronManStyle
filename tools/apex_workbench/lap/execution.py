"""Separate finite V2 worker limits; reuse V1's shared lease, identities and atomic storage."""

import fcntl
import os
import resource
import signal
import subprocess
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

import psutil

from tools.apex_workbench import jobs, lifecycle, storage
from tools.apex_workbench.configuration import ROOT

from . import config

MODULE = "tools.apex_workbench.lap.execution"
ACTIVE = {"queued", "running", "finalizing"}


def owned(record, role, directory):
    expected = ["-m", MODULE, role, str(Path(directory).absolute())]
    if record.get("cmdline", [])[1:5] != expected:
        return None
    return lifecycle.owned_process(record, "lap-" + role, directory)


def identity(role, directory):
    record = lifecycle.identity(os.getpid(), "lap-" + role, directory)
    if owned(record, role, directory) is None:
        raise RuntimeError("V2 process identity does not match its unique run")
    return record


def worker_guard(directory, lock_fd, limits):
    expected = (jobs.LEASE_ROOT / ".execution.lock").stat()
    actual = os.fstat(lock_fd)
    if (expected.st_dev, expected.st_ino) != (actual.st_dev, actual.st_ino):
        raise RuntimeError("V2 worker did not inherit the common execution lease")
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    supervisor = storage.read_json(directory / "supervisor.json")
    if owned(supervisor, "supervisor", directory) is None:
        raise RuntimeError("V2 supervisor identity absent at worker startup")
    storage.write_json(directory / "worker.json", identity("worker", directory), exclusive=True)
    stopped = threading.Event()
    started = time.monotonic()

    threading.Thread(
        target=monitor, args=(directory, supervisor, limits, stopped, started), daemon=True
    ).start()
    return stopped


def monitor(directory, supervisor, limits, stopped, started):
    """After startup validation, continuously bind the same birth time and exact command."""
    while not stopped.wait(0.05):
        reason, outcome = None, "failed"
        try:
            if (directory / "cancel.request").exists():
                reason, outcome = "User cancellation", "cancelled"
            elif lifecycle.owned_process(supervisor, "lap-supervisor", directory) is None:
                reason, outcome = "Supervisor identity lost", "interrupted"
            elif time.monotonic() - started > limits["wall_s"]:
                reason, outcome = "Worker wall ceiling", "timed_out"
            elif psutil.Process().memory_info().rss > limits["sampled_rss_bytes"]:
                reason = "Worker sampled RSS ceiling"
            elif lifecycle.sampled_output_size(directory) > limits["sampled_output_bytes"]:
                reason = "Worker sampled output ceiling"
        except Exception as error:
            reason, outcome = "Ownership/resource guard failed: " + str(error), "interrupted"
        if reason:
            try:
                storage.write_json(
                    directory / "worker_abort.json",
                    {"outcome": outcome, "reason": reason},
                    exclusive=True,
                )
            finally:
                os._exit(3)


def finalize(directory, outcome, **details):
    storage.write_json(
        directory / "execution.json", {"scientific_outcome": outcome, **details}, exclusive=True
    )
    status = {
        "record_version": 2,
        "state": "finalizing",
        "scientific_outcome": outcome,
        "evidence_state": "pending",
        **details,
    }
    storage.write_json(directory / "status.json", status)
    try:
        manifest = {}
        for path in directory.rglob("*"):
            config.safe(path)
            if path.is_file() and path.name not in {"status.json", "artifacts.json"}:
                manifest[str(path.relative_to(directory))] = {
                    "bytes": path.stat().st_size,
                    "sha256": storage.sha256(path),
                }
        storage.write_json(directory / "artifacts.json", manifest, exclusive=True)
        status.update(
            state=outcome,
            evidence_state="valid",
            manifest_sha256=storage.sha256(directory / "artifacts.json"),
        )
    except Exception as error:
        status.update(state="evidence_failed", evidence_state="failed", error=str(error))
    storage.write_json(directory / "status.json", status)


def reconcile():
    """Under the shared lease, live owners block; stale active states become interrupted."""
    if not config.RUNS.exists():
        return
    for directory in config.RUNS.iterdir():
        config.safe(directory)
        if directory.name.startswith("."):
            continue
        status = storage.read_status(directory)
        for role in ("worker", "supervisor"):
            path = directory / (role + ".json")
            if path.exists() and owned(storage.read_json(path), role, directory):
                raise RuntimeError("Another owned V2 process is active")
        if status["state"] in ACTIVE:
            if (directory / "execution.json").exists():
                raise RuntimeError("V2 finalization interrupted; preserve evidence for review")
            finalize(
                directory,
                "interrupted",
                error="No live owned processes; previous execution interrupted",
            )


def start(value):
    value = config.validate(value)
    config.RUNS.mkdir(parents=True, exist_ok=True)
    config.safe(config.RUNS)
    jobs.preflight()
    lease = jobs.execution_lock()
    try:
        reconcile()
        config.access(value)
        run_id = jobs.timestamp().replace(":", "").replace("+", "_") + "_" + uuid.uuid4().hex
        directory = config.safe(config.RUNS / run_id)
        directory.mkdir(exist_ok=False)
        # Once-only admission is consumed before probing/launch. Any failure remains an attempt.
        policy = config.access(value, consume=run_id)
        storage.write_json(
            directory / "status.json",
            {
                "record_version": 2,
                "state": "queued",
                "scientific_outcome": "queued",
                "evidence_state": "pending",
            },
        )
        from .worker import probe

        resolved = probe(value)
        capture = {
            **resolved,
            "source_sha256": config.v1.frozen.source_hashes(),
            "producer_sha256": config.producers(),
            "runtime": str(config.v1.RUNTIME),
        }
        request = {
            "schema": "apex-lap-request/1",
            "record_version": 2,
            "adapter": "nmpc_lap_v2",
            "run_id": run_id,
            "effective": value,
            "capture": capture,
            "execution_lock": str(jobs.LEASE_ROOT / ".execution.lock"),
            "provenance": {
                "limits": config.limits(value),
                "git_revision": policy["reviewed_revision"],
                "review_sha256": policy["review_sha256"],
                "authority_sha256": policy["authority_sha256"],
            },
        }
        storage.write_json(directory / "request.json", request, exclusive=True)
        with (directory / "launcher.log").open("xb") as log:
            subprocess.Popen(
                [sys.executable, "-m", MODULE, "supervisor", str(directory), str(lease.fileno())],
                cwd=ROOT,
                env=jobs.worker_environment(directory),
                pass_fds=(lease.fileno(),),
                start_new_session=True,
                stdout=log,
                stderr=log,
            )
        return directory
    except Exception:
        if "directory" in locals() and directory.exists():
            (directory / "admission_error.txt").write_text(traceback.format_exc())
            for name in ("stdout.log", "stderr.log"):
                (directory / name).touch(exist_ok=False)
            if not (directory / "request.json").exists():
                storage.write_json(
                    directory / "request.json",
                    {
                        "adapter": "nmpc_lap_v2",
                        "run_id": run_id,
                        "effective": value,
                        "admission_only": True,
                    },
                    exclusive=True,
                )
            finalize(
                directory, "failed", error="Admission/probe failed; once-only attempt retained"
            )
        raise
    finally:
        lease.close()


def supervise(directory, lock_fd):
    limits = config.limits(storage.read_json(directory / "request.json")["effective"])
    storage.write_json(
        directory / "supervisor.json", identity("supervisor", directory), exclusive=True
    )
    started, peak, worker = time.monotonic(), 0, None
    outcome, error, returncode = "failed", None, None
    interrupted = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: interrupted.set())
    try:
        with (
            (directory / "stdout.log").open("xb") as stdout,
            (directory / "stderr.log").open("xb") as stderr,
        ):
            worker = subprocess.Popen(
                [sys.executable, "-m", MODULE, "worker", str(directory), str(lock_fd)],
                cwd=ROOT,
                env=jobs.worker_environment(directory),
                pass_fds=(lock_fd,),
                start_new_session=True,
                stdout=stdout,
                stderr=stderr,
            )
            storage.write_json(
                directory / "status.json",
                {
                    "record_version": 2,
                    "state": "running",
                    "scientific_outcome": "running",
                    "evidence_state": "pending",
                },
            )
            while worker.poll() is None:
                try:
                    peak = max(peak, psutil.Process(worker.pid).memory_info().rss)
                except psutil.NoSuchProcess:
                    pass
                if interrupted.is_set() or (directory / "cancel.request").exists():
                    outcome, error = "cancelled", "Cancellation requested"
                elif time.monotonic() - started > limits["wall_s"]:
                    outcome, error = "timed_out", "Supervisor wall ceiling"
                elif (
                    peak > limits["sampled_rss_bytes"]
                    or lifecycle.sampled_output_size(directory) > limits["sampled_output_bytes"]
                ):
                    error = "Supervisor sampled resource ceiling"
                if error:
                    break
                time.sleep(0.1)
            if worker.poll() is None:
                record_path = directory / "worker.json"
                process = (
                    owned(storage.read_json(record_path), "worker", directory)
                    if record_path.exists()
                    else None
                )
                if process is None:
                    raise RuntimeError(
                        "Worker ownership uncertain; inherited lease remains authoritative"
                    )
                process.terminate()
                try:
                    worker.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process = owned(storage.read_json(record_path), "worker", directory)
                    if process:
                        process.kill()
                    worker.wait(timeout=3)
            returncode = worker.wait()
            abort = directory / "worker_abort.json"
            if abort.exists():
                data = storage.read_json(abort)
                outcome, error = data["outcome"], data["reason"]
            elif error is None:
                outcome = "completed" if returncode == 0 else "failed"
                error = None if returncode == 0 else f"Worker exited{returncode}"
    except Exception as exception:
        error = "Supervisor failure: " + str(exception)
    finally:
        if worker is None or worker.poll() is not None:
            finalize(
                directory,
                outcome,
                error=error,
                returncode=returncode,
                wall_runtime_s=time.monotonic() - started,
                sampled_peak_worker_rss_bytes=peak,
            )
        # Live worker retains the same lease and self-aborts on supervisor loss.
        os.close(lock_fd)


def worker_main(directory, lock_fd):
    request = storage.read_json(directory / "request.json")
    limits = config.limits(request["effective"])
    if request["provenance"]["limits"] != limits:
        raise ValueError("V2 worker limits differ from the source profile")
    resource.setrlimit(resource.RLIMIT_CPU, (limits["cpu_s"], limits["cpu_s"] + 1))
    resource.setrlimit(
        resource.RLIMIT_FSIZE, (limits["single_file_bytes"], limits["single_file_bytes"])
    )
    worker_guard(directory, lock_fd, limits)
    from .worker import run

    try:
        config.access(request["effective"], run_id=directory.name)
        summary = run(directory, request)
        storage.write_json(directory / "worker_result.json", summary, exclusive=True)
        return 2 if summary["failure"] else 0
    except Exception:
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    role, name, descriptor = sys.argv[1:]
    directory = config.safe(Path(name))
    if role == "supervisor":
        supervise(directory, int(descriptor))
    elif role == "worker":
        raise SystemExit(worker_main(directory, int(descriptor)))
    else:
        raise SystemExit("Unknown V2 process role")
