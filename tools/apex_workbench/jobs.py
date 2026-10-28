"""Local process supervision, append-only runs and retained execution provenance."""

import fcntl
import hashlib
import importlib.metadata
import os
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psutil

from tools.apex_workbench import lifecycle, storage
from tools.apex_workbench.configuration import ROOT, RUNS, validate, validate_note

LIMITS = {
    "wall_s": 60,
    "cpu_s": 30,
    "sampled_rss_bytes": 512 * 1024**2,
    "sampled_output_bytes": 64 * 1024**2,
    "single_file_bytes": 16 * 1024**2,
}


def timestamp():
    return datetime.now(UTC).isoformat()


write_json = storage.write_json
read_json = storage.read_json
sha256 = storage.sha256


def provenance():
    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True)

    names = git("ls-files", "-z").split("\0")
    source = {
        name: sha256(ROOT / name)
        for name in names
        if name
        and name.startswith(("src/", "scripts/", "configs/", "tools/apex_workbench/"))
        and (ROOT / name).is_file()
    }
    # Include tooling before its first commit as well.
    for path in Path(__file__).parent.glob("*.py"):
        source[str(path.relative_to(ROOT))] = sha256(path)
    return {
        "git_revision": git("rev-parse", "HEAD").strip(),
        "git_branch": git("branch", "--show-current").strip(),
        "working_tree_status": git("status", "--porcelain=v1", "--untracked-files=all"),
        "tracked_diff_sha256": hashlib.sha256(git("diff", "HEAD").encode()).hexdigest(),
        "source_sha256": source,
        "python_executable": sys.executable,
        "python_version": sys.version,
        "packages": {
            package: importlib.metadata.version(package)
            for package in (
                "numpy",
                "scipy",
                "pandas",
                "matplotlib",
                "streamlit",
                "plotly",
                "psutil",
                "threadpoolctl",
            )
        },
        "model": "apex.models.vehicle.dynamic_bicycle.DynamicBicycle",
        "tire": "LinearAxleTire (unsaturated; mu diagnostic only)",
        "parameter_classification": "synthetic, not measured or identified APEX data",
        "vehicle_source": "configs/vehicles/synthetic_dynamic_test_vehicle.yaml",
        "vehicle_yaml": (ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml").read_text(),
        "timing_mode": "ideal zero modeled delay; host runtime is not solver latency",
        "limits": LIMITS,
    }


def preflight():
    guards = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "results").rglob("*")
        if p.name in {"MEASURED_ACTIVE", "D3_ACTIVE"}
    ]
    if guards:
        raise RuntimeError(f"Repository measurement guards present; inspect their owners: {guards}")
    if shutil.disk_usage(ROOT).free < 1024**3:
        raise RuntimeError("At least 1 GiB of free disk is required")


def worker_environment(directory):
    env = os.environ.copy()
    env.update(
        {
            name: "1"
            for name in (
                "VECLIB_MAXIMUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "BLIS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    env.update(
        PYTHONPATH=os.pathsep.join((str(ROOT), str(ROOT / "scripts"), str(ROOT / "src"))),
        PYTHONHASHSEED="0",
        MPLCONFIGDIR=str(directory / "matplotlib-cache"),
    )
    return env


ACTIVE = {"queued", "running", "finalizing"}


def execution_lock():
    RUNS.mkdir(parents=True, exist_ok=True)
    lock = (RUNS / ".execution.lock").open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        lock.close()
        raise RuntimeError("Another Workbench experiment is running") from error
    return lock


def finalize(directory, outcome, **details):
    """Scientific outcome survives a failed evidence commit. Status commits last."""
    receipt = directory / "execution.json"
    if not receipt.exists():
        write_json(receipt, {"scientific_outcome": outcome, **details}, exclusive=True)
    elif read_json(receipt).get("scientific_outcome") != outcome:
        raise storage.IntegrityError("Refusing to change the recorded scientific outcome")
    status = {
        "record_version": 2,
        "state": "finalizing",
        "scientific_outcome": outcome,
        "evidence_state": "pending",
        "updated_utc": timestamp(),
        **details,
    }
    write_json(directory / "status.json", status)
    try:
        manifest = {
            str(p.relative_to(directory)): {"sha256": sha256(p), "bytes": p.stat().st_size}
            for p in directory.rglob("*")
            if p.is_file()
            and not p.name.startswith(".")
            and p.name not in {"status.json", "artifacts.json", "supervisor.log", "cancel.request"}
            and not p.name.startswith("notes-")
        }
        target = directory / "artifacts.json"
        if target.exists():
            # Interrupted finalization may have published the complete manifest already.
            if read_json(target) != manifest:
                raise storage.IntegrityError(
                    "Existing manifest differs; refusing to replace evidence"
                )
        else:
            write_json(target, manifest, exclusive=True)
        committed = sha256(target)
        status.update(state=outcome, evidence_state="valid", manifest_sha256=committed)
    except Exception as error:
        status.update(
            state="evidence_failed",
            evidence_state="failed",
            error=f"Evidence finalization failed: {type(error).__name__}: {error}",
        )
    status["updated_utc"] = timestamp()
    write_json(directory / "status.json", status)
    return status


def _owner(directory, name):
    try:
        return read_json(directory / f"{name}.json")
    except (OSError, ValueError):
        return {}


def _check_live_owners(directory, status):
    if lifecycle.legacy_worker_alive(status, directory):
        raise RuntimeError(f"A worker is still alive for {directory.name}")
    for name, role in (("worker", "worker"), ("supervisor", "jobs")):
        if lifecycle.owned_process(_owner(directory, name), role, directory) is not None:
            raise RuntimeError(f"Verified {name} is still alive for {directory.name}")


def _reconcile_locked(directory, status):
    status = storage.read_status(directory)
    if status.get("state") not in ACTIVE:
        return status
    _check_live_owners(directory, status)
    request = read_json(directory / "request.json")
    if not isinstance(request, dict):
        raise RuntimeError(f"Incomplete abandoned request needs inspection: {directory.name}")
    if request.get("record_version") != 2:
        # Never repair/overwrite historical evidence in place.
        return {
            **status,
            "state": "interrupted",
            "scientific_outcome": "unknown",
            "evidence_state": "incomplete",
            "error": "Legacy owner unavailable; record preserved",
        }
    abort = _owner(directory, "worker_abort")
    receipt = _owner(directory, "execution")
    return finalize(
        directory,
        abort.get("scientific_outcome", receipt.get("scientific_outcome", "interrupted")),
        error=abort.get(
            "error", receipt.get("error", "Execution owner disappeared; outcome is uncertain")
        ),
        recovered=True,
    )


def status_for(directory):
    try:
        status = storage.read_status(directory)
        if status.get("state") not in ACTIVE:
            return status
        try:
            with execution_lock():
                return _reconcile_locked(directory, status)
        except RuntimeError as error:
            return {**status, "owner_notice": str(error)}
    except (OSError, ValueError, TypeError) as error:
        return {
            "state": "quarantined",
            "scientific_outcome": "unknown",
            "evidence_state": "incomplete",
            "error": f"Incomplete record retained: {error}",
        }


def start_run(
    adapter,
    source,
    prediction="",
    *,
    runs=RUNS,
    qualification=False,
    reference=False,
    test_only=False,
):
    effective = validate(adapter, source)
    if adapter == "dynamic_lab":
        from tools.apex_workbench.lab_configuration import execution_context

        context = execution_context(
            effective, qualification=qualification, reference=reference, test_only=test_only
        )
    elif qualification or reference or test_only:
        raise ValueError("Qualification profiles are scoped to dynamic_lab")
    prediction = validate_note(prediction)
    runs = Path(runs)
    runs.mkdir(parents=True, exist_ok=True)
    with execution_lock() as lock:
        preflight()
        # With no lease holder, reconcile abandoned records before admission.
        for parent in {RUNS.resolve(), runs.resolve()}:
            # UI quarantine must not hide a legacy active owner from admission checks.
            for previous in storage.run_directories(parent):
                if not any(
                    (previous / name).exists()
                    for name in ("request.json", "status.json", "worker.json", "supervisor.json")
                ):
                    continue  # An unrelated output folder is not a retained execution record.
                try:
                    status = storage.read_status(previous, lifecycle_only=True)
                except (OSError, ValueError, TypeError) as error:
                    raise RuntimeError(
                        f"Cannot inspect retained lifecycle for {previous.name}; "
                        "record preserved, admission blocked: " + str(error)
                    ) from error
                _check_live_owners(previous, status)
                if status["state"] in ACTIVE:
                    _reconcile_locked(previous, status)
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex
        directory = runs / run_id
        staging = runs / (".pending-" + run_id)
        staging.mkdir(exist_ok=False)
        request = {
            "schema": "apex-workbench/0.1",
            "record_version": 2,
            "run_id": run_id,
            "timestamp_utc": timestamp(),
            "adapter": adapter,
            "adapter_version": "0.1.1",
            "source_configuration": source,
            "effective": effective,
            "prediction": prediction,
            "execution_lock": str((RUNS / ".execution.lock").resolve()),
            "controller": "none (predetermined command)"
            if adapter == "dynamic_demo"
            else "Task005 BaselineController / scheduled LQR + PI",
            "entry_point": "scripts/run_dynamic_bicycle_demo.py:main"
            if adapter == "dynamic_demo"
            else "scripts/run_lqr_baseline.py:run_case",
            "provenance": provenance(),
        }
        if adapter == "dynamic_lab":
            from tools.apex_workbench.lab_configuration import resolve
            from tools.apex_workbench.lab_sources import from_captured

            request.update(
                adapter_version="0.2.1",
                controller="none (prescribed integer-tick ZOH input)",
                entry_point="tools/apex_workbench/dynamic_lab.py:execute",
                lab_resolved=resolve(effective, vehicle_yaml=request["provenance"]["vehicle_yaml"]),
                execution_context=context,
                source_inventory=from_captured(request["provenance"]["source_sha256"]),
            )
        write_json(staging / "request.json", request, exclusive=True)
        write_json(
            staging / "status.json",
            {
                "record_version": 2,
                "state": "queued",
                "scientific_outcome": "pending",
                "evidence_state": "pending",
                "updated_utc": timestamp(),
            },
        )
        if directory.exists():
            raise FileExistsError("Refusing to replace an earlier run")
        staging.rename(directory)  # Initial request and status become selectable together.
        try:
            with (directory / "supervisor.log").open("xb") as log:
                subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "tools.apex_workbench.jobs",
                        str(directory),
                        str(lock.fileno()),
                    ],
                    cwd=ROOT,
                    env=worker_environment(directory),
                    pass_fds=(lock.fileno(),),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        except Exception as error:
            finalize(directory, "failed", error=f"Supervisor could not launch: {error}")
            raise
    return directory


def cancel_run(directory):
    status = status_for(directory)
    if status["state"] in ACTIVE:
        # The scientific worker independently consumes this even if its supervisor is gone.
        (directory / "cancel.request").touch(exist_ok=True)


def save_notes(directory, observation, explanation):
    record = {
        "timestamp_utc": timestamp(),
        "observation": validate_note(observation),
        "explanation": validate_note(explanation),
    }
    path = directory / f"notes-{time.time_ns()}-{uuid.uuid4().hex}.json"
    write_json(path, record, exclusive=True)
    return path


def supervise(directory, lock_fd=None):
    own_lock = execution_lock() if lock_fd is None else None
    lock_fd = own_lock.fileno() if own_lock else lock_fd
    process = None
    worker = None
    started = time.monotonic()
    peak_rss, peak_threads = 0, 0
    outcome, error, returncode = "failed", None, None
    interrupted = False

    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGTERM, interrupt)
    signal.signal(signal.SIGINT, interrupt)
    try:
        write_json(
            directory / "supervisor.json",
            lifecycle.identity(os.getpid(), "jobs", directory),
            exclusive=True,
        )
        with (
            (directory / "stdout.log").open("xb") as stdout,
            (directory / "stderr.log").open("xb") as stderr,
        ):
            process = subprocess.Popen(
                [sys.executable, "-m", "tools.apex_workbench.worker", str(directory), str(lock_fd)],
                cwd=ROOT,
                env=worker_environment(directory),
                pass_fds=(lock_fd,),
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            deadline = time.monotonic() + 2
            while worker is None and process.poll() is None:
                try:
                    worker = lifecycle.identity(process.pid, "worker", directory)
                except (RuntimeError, psutil.Error):
                    if time.monotonic() > deadline:
                        raise RuntimeError("Worker identity was not established") from None
                    time.sleep(0.01)
            write_json(
                directory / "status.json",
                {
                    "record_version": 2,
                    "state": "running",
                    "scientific_outcome": "running",
                    "evidence_state": "pending",
                    "pid": process.pid,
                    "supervisor_pid": os.getpid(),
                    "updated_utc": timestamp(),
                },
            )
            while process.poll() is None:
                try:
                    child = psutil.Process(process.pid)
                    peak_rss = max(peak_rss, child.memory_info().rss)
                    peak_threads = max(peak_threads, child.num_threads())
                except psutil.NoSuchProcess:
                    pass
                size = lifecycle.sampled_output_size(directory)
                if interrupted or (directory / "cancel.request").exists():
                    outcome, error = "cancelled", "Cancellation requested"
                    break
                if time.monotonic() - started > LIMITS["wall_s"]:
                    outcome, error = "timed_out", "Wall execution limit exceeded"
                    break
                if peak_rss > LIMITS["sampled_rss_bytes"] or size > LIMITS["sampled_output_bytes"]:
                    error = "Sampled worker resource safeguard exceeded"
                    break
                time.sleep(0.1)
            if error is None:
                returncode = process.wait()
                abort = _owner(directory, "worker_abort")
                outcome = abort.get(
                    "scientific_outcome", "completed" if returncode == 0 else "failed"
                )
                error = abort.get(
                    "error", None if returncode == 0 else f"Worker exited {returncode}"
                )
    except Exception as exception:
        error = f"Supervisor error: {type(exception).__name__}: {exception}"
    finally:
        try:
            if process is not None:
                if process.poll() is None and worker is not None:
                    try:
                        lifecycle.terminate_owned(worker, directory)
                    except psutil.Error as exception:
                        error = f"Worker termination unconfirmed: {exception}"
                returncode = process.poll()
            if process is not None and returncode is None:
                # Its inherited lease still blocks admission. Recovery cannot claim completion.
                write_json(
                    directory / "status.json",
                    {
                        "record_version": 2,
                        "state": "running",
                        "scientific_outcome": "unknown",
                        "evidence_state": "incomplete",
                        "error": error or "Worker ownership uncertain",
                    },
                )
            else:
                finalize(
                    directory,
                    outcome,
                    error=error,
                    returncode=returncode,
                    wall_runtime_s=time.monotonic() - started,
                    sampled_peak_worker_rss_bytes=peak_rss,
                    sampled_peak_worker_threads=peak_threads,
                    sampling_note=(
                        "100 ms supervisor samples; worker guard polls at 50 ms; soft bounds"
                    ),
                )
        finally:
            if own_lock:
                own_lock.close()
            else:
                os.close(lock_fd)  # Release admission after finalization, not interpreter teardown.


if __name__ == "__main__":
    supervise(Path(sys.argv[1]).resolve(), int(sys.argv[2]))
