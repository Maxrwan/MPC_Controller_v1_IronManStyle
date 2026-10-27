"""Worker-owned execution lease and verified process identity; no scientific equations."""

import fcntl
import os
import signal
import stat
import threading
import time
from pathlib import Path

import psutil

from tools.apex_workbench.storage import read_json, write_json


def identity(pid, role, directory):
    process = psutil.Process(pid)
    record = {
        "pid": pid,
        "created": process.create_time(),
        "cmdline": process.cmdline(),
        "role": role,
        "directory": str(Path(directory).resolve()),
    }
    if owned_process(record, role, directory) is None:
        raise RuntimeError("Could not establish process ownership")
    return record


def owned_process(record, role, directory):
    """Never signal a PID unless birth time, command and unique run path still match."""
    try:
        if record["role"] != role or record["directory"] != str(Path(directory).resolve()):
            return None
        command = record["cmdline"]
        if role == "worker" and command[1:4] != [
            "-m",
            "tools.apex_workbench.worker",
            record["directory"],
        ]:
            return None
        process = psutil.Process(record["pid"])
        if process.create_time() != record["created"] or process.cmdline() != command:
            return None
        if process.status() == psutil.STATUS_ZOMBIE:
            return None
        return process
    except (psutil.Error, KeyError, TypeError, ValueError):
        return None


def terminate_owned(record, directory, timeout=2):
    process = owned_process(record, "worker", directory)
    if process is None:
        return False
    # psutil additionally checks PID reuse before sending its process-specific signal.
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=timeout)
    except psutil.TimeoutExpired:
        process = owned_process(record, "worker", directory)
        if process is None:
            return False
        process.send_signal(signal.SIGKILL)
        process.wait(timeout=timeout)
    return True


def legacy_worker_alive(status, directory):
    """Legacy PIDs lack a birth-time record: only block admission, never terminate them."""
    try:
        process = psutil.Process(status["pid"])
        return process.status() != psutil.STATUS_ZOMBIE and process.cmdline()[1:4] == [
            "-m",
            "tools.apex_workbench.worker",
            str(Path(directory).resolve()),
        ]
    except (psutil.Error, KeyError, TypeError):
        return False


def sampled_output_size(directory):
    total = 0
    for path in directory.rglob("*"):
        try:
            info = path.stat()
        except FileNotFoundError:
            continue  # An atomically published/cache temporary file can disappear during a scan.
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
    return total


def start_guard(directory, lock_fd):
    """Keep inherited flock until process exit; self-abort if supervisor or limits fail."""
    directory = Path(directory)
    request = read_json(directory / "request.json")
    lock_stat = os.fstat(lock_fd)
    expected = Path(request["execution_lock"]).stat()
    if (lock_stat.st_dev, lock_stat.st_ino) != (expected.st_dev, expected.st_ino):
        raise RuntimeError("Worker did not inherit the execution lease")
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    supervisor = read_json(directory / "supervisor.json")
    worker = identity(os.getpid(), "worker", directory)
    write_json(directory / "worker.json", worker, exclusive=True)
    stopped = threading.Event()
    started = time.monotonic()
    limits = request["provenance"]["limits"]

    def abort(outcome, reason):
        try:
            write_json(
                directory / "worker_abort.json",
                {
                    "scientific_outcome": outcome,
                    "error": reason,
                    "worker": worker,
                },
                exclusive=True,
            )
        finally:
            # Terminate this process itself, without signalling a potentially reused PID.
            os._exit(3)

    def watch():
        try:
            while not stopped.wait(0.05):
                if (directory / "cancel.request").exists():
                    abort("cancelled", "Cancellation requested (worker-owned guard)")
                if owned_process(supervisor, "jobs", directory) is None:
                    abort("interrupted", "Supervisor ownership lost; execution is uncertain")
                if time.monotonic() - started > limits["wall_s"]:
                    abort("timed_out", "Worker wall limit exceeded")
                if psutil.Process().memory_info().rss > limits["sampled_rss_bytes"]:
                    abort("failed", "Worker sampled RSS limit exceeded")
                size = sampled_output_size(directory)
                if size > limits["sampled_output_bytes"]:
                    abort("failed", "Worker sampled output limit exceeded")
        except Exception as error:
            abort("interrupted", f"Worker supervision failed: {type(error).__name__}: {error}")

    thread = threading.Thread(target=watch, name="workbench-owner-guard", daemon=True)
    thread.start()
    return stopped
