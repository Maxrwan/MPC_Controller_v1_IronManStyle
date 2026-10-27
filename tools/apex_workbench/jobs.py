"""Local process supervision, append-only runs and retained execution provenance."""

import fcntl
import hashlib
import importlib.metadata
import json
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


def write_json(path: Path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def read_json(path: Path):
    return json.loads(path.read_text())


def sha256(path: Path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


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


def start_run(adapter, source, prediction="", *, runs=RUNS):
    effective = validate(adapter, source)
    prediction = validate_note(prediction)
    runs = Path(runs)
    runs.mkdir(parents=True, exist_ok=True)
    # One lock per checkout, even if a test/client supplies a different run directory.
    RUNS.mkdir(parents=True, exist_ok=True)
    with (RUNS / ".execution.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another Workbench experiment is running") from error
        preflight()
        identity = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex[:12]
        directory = runs / identity
        directory.mkdir(exist_ok=False)
        request = {
            "schema": "apex-workbench/0.1",
            "run_id": identity,
            "timestamp_utc": timestamp(),
            "adapter": adapter,
            "adapter_version": "0.1",
            "source_configuration": source,
            "effective": effective,
            "prediction": prediction,
            "controller": "none (predetermined command)"
            if adapter == "dynamic_demo"
            else "Task005 BaselineController / scheduled LQR + PI",
            "entry_point": "scripts/run_dynamic_bicycle_demo.py:main"
            if adapter == "dynamic_demo"
            else "scripts/run_lqr_baseline.py:run_case",
            "provenance": provenance(),
        }
        write_json(directory / "request.json", request)
        write_json(directory / "status.json", {"state": "queued", "updated_utc": timestamp()})
        try:
            with (directory / "supervisor.log").open("xb") as log:
                subprocess.Popen(
                    [sys.executable, "-m", "tools.apex_workbench.jobs", str(directory)],
                    cwd=ROOT,
                    env=worker_environment(directory),
                    pass_fds=(lock.fileno(),),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        except Exception as error:
            write_json(
                directory / "status.json",
                {
                    "state": "failed",
                    "error": str(error),
                    "updated_utc": timestamp(),
                },
            )
            raise
    return directory


def cancel_run(directory):
    if read_json(directory / "status.json")["state"] in {"queued", "running"}:
        (directory / "cancel.request").touch(exist_ok=True)


def save_notes(directory, observation, explanation):
    record = {
        "timestamp_utc": timestamp(),
        "observation": validate_note(observation),
        "explanation": validate_note(explanation),
    }
    path = directory / f"notes-{time.time_ns()}-{uuid.uuid4().hex[:8]}.json"
    with path.open("x") as stream:
        json.dump(record, stream, indent=2)
    return path


def terminate(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)


def supervise(directory):
    process = None
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
        with (
            (directory / "stdout.log").open("xb") as stdout,
            (directory / "stderr.log").open("xb") as stderr,
        ):
            process = subprocess.Popen(
                [sys.executable, "-m", "tools.apex_workbench.worker", str(directory)],
                cwd=ROOT,
                env=worker_environment(directory),
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            write_json(
                directory / "status.json",
                {
                    "state": "running",
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
                size = sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
                if interrupted or (directory / "cancel.request").exists():
                    outcome, error = (
                        "cancelled",
                        "Cancellation requested; partial evidence retained",
                    )
                    break
                if time.monotonic() - started > LIMITS["wall_s"]:
                    outcome, error = "timed_out", "Wall execution limit exceeded"
                    break
                if peak_rss > LIMITS["sampled_rss_bytes"]:
                    error = "Sampled worker RSS exceeded resource safeguard"
                    break
                if size > LIMITS["sampled_output_bytes"]:
                    error = "Sampled output size exceeded resource safeguard"
                    break
                time.sleep(0.1)
            if error is None:
                returncode = process.wait()
                outcome = "completed" if returncode == 0 else "failed"
                if returncode:
                    error = f"Scientific worker exited {returncode}; inspect stderr.log"
    except Exception as exception:
        error = f"Supervisor error: {type(exception).__name__}: {exception}"
    finally:
        if process is not None:
            terminate(process)
            returncode = process.returncode
        write_json(
            directory / "status.json",
            {
                "state": outcome,
                "error": error,
                "returncode": returncode,
                "updated_utc": timestamp(),
                "wall_runtime_s": time.monotonic() - started,
                "sampled_peak_worker_rss_bytes": peak_rss,
                "sampled_peak_worker_threads": peak_threads,
                "sampling_note": (
                    "100 ms samples; not hard peak bounds or proof of parallel computation"
                ),
            },
        )
        write_json(
            directory / "artifacts.json",
            {
                str(p.relative_to(directory)): {"sha256": sha256(p), "bytes": p.stat().st_size}
                for p in directory.rglob("*")
                if p.is_file() and p.name not in {"artifacts.json", "status.json", "supervisor.log"}
            },
        )


if __name__ == "__main__":
    supervise(Path(sys.argv[1]).resolve())
