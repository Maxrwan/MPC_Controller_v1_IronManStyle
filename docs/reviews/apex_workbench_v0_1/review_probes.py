"""Bounded review harness only. Never alters delivered implementation or canonical files.

Scheduling barriers and failing I/O are injected in this harness, not in source files.
Comparison records are deliberately conflicting test fixtures, not scientific run claims.
"""

import copy
import csv
import fcntl
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import psutil

from tools.apex_workbench import configuration, jobs, plots

EVIDENCE = Path(sys.argv[2]).resolve()
MODE = sys.argv[1]
PIN = "a0b4a98b14f53469735ca4dd9f7a93a7b0651860"
assert str(configuration.ROOT) == "/private/tmp/apex-workbench-review-a0b4a98-20261027"


def wait_until(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise TimeoutError("Bounded review condition did not arrive")


def live(pid):
    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def stop_group(pid):
    if not pid or not live(pid):
        return
    os.killpg(pid, signal.SIGTERM)
    try:
        psutil.Process(pid).wait(timeout=3)
    except psutil.TimeoutExpired:
        os.killpg(pid, signal.SIGKILL)
        psutil.Process(pid).wait(timeout=3)
    except psutil.NoSuchProcess:
        pass


def terminal(directory):
    status = jobs.read_json(directory / "status.json")
    return status if status["state"] not in {"queued", "running"} else None


def orphan():
    runs = EVIDENCE / "orphan/runs"
    directory = jobs.start_run(
        "dynamic_demo",
        {"duration": 20.0, "dt": 0.001},
        "Review supervisor-loss injection; no scientific interpretation",
        runs=runs,
    )
    supervisor_pid = worker_pid = None
    try:

        def running():
            row = jobs.read_json(directory / "status.json")
            return row if row["state"] == "running" else None

        status = wait_until(running)
        supervisor_pid, worker_pid = status["supervisor_pid"], status["pid"]
        assert live(worker_pid)
        os.kill(supervisor_pid, signal.SIGKILL)

        def lock_released():
            with (jobs.RUNS / ".execution.lock").open("a+") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
                except BlockingIOError:
                    return False

        wait_until(lock_released, seconds=3)
        survived = live(worker_pid)
        jobs.cancel_run(directory)
        time.sleep(0.2)
        ignored_cancellation = live(worker_pid)
        launch_accepted = False
        # Do not execute a second scientific worker: intercept at the actual launch boundary.
        with patch.object(
            jobs.subprocess, "Popen", side_effect=OSError("review: launch intercepted")
        ):
            try:
                jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=runs)
            except OSError as error:
                launch_accepted = str(error) == "review: launch intercepted"
        result = {
            "worker_survived_supervisor_sigkill": survived,
            "execution_lock_released_while_worker_alive": survived and lock_released(),
            "new_launch_reached_popen_while_orphan_alive": launch_accepted,
            "cancellation_marker_did_not_stop_orphan": ignored_cancellation,
            "retained_status": jobs.read_json(directory / "status.json"),
            "artifact_manifest_present": (directory / "artifacts.json").exists(),
            "directory": str(directory),
        }
        assert survived and ignored_cancellation and launch_accepted
        return result
    finally:
        stop_group(worker_pid)
        stop_group(supervisor_pid)


def publication():
    from streamlit.testing.v1 import AppTest

    runs = EVIDENCE / "publication/runs"
    entered, release = threading.Event(), threading.Event()
    original = jobs.write_json
    captured = {}

    def paused_write(path, value):
        if path.name == "status.json" and value.get("state") == "queued":
            entered.set()
            if not release.wait(20):
                raise TimeoutError("Review publication barrier")
        return original(path, value)

    def launch():
        try:
            captured["directory"] = jobs.start_run(
                "dynamic_demo",
                {"duration": 0.01, "dt": 0.005},
                "Review publication race",
                runs=runs,
            )
        except Exception as error:
            captured["error"] = repr(error)

    with patch.object(jobs, "write_json", paused_write):
        thread = threading.Thread(target=launch)
        thread.start()
        try:
            assert entered.wait(5)
            directory = next(runs.glob("*/request.json")).parent
            missing_status = not (directory / "status.json").exists()
            with patch.object(configuration, "RUNS", runs):
                app = AppTest.from_file(
                    str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=10
                ).run()
                exceptions = [item.message for item in app.exception]
            assert missing_status and exceptions
        finally:
            release.set()
            thread.join(timeout=10)
    assert not thread.is_alive() and "error" not in captured, captured
    final = wait_until(lambda: terminal(captured["directory"]))
    wait_until(lambda: (captured["directory"] / "artifacts.json").exists())
    return {
        "request_visible_without_status": missing_status,
        "second_ui_session_exceptions": exceptions,
        "writer_completed_after_barrier_release": final["state"],
        "directory": str(directory),
    }


def notes():
    directory = EVIDENCE / "notes"
    directory.mkdir()
    (directory / "request.json").write_text('{"prediction":"preserved"}')
    request_before = (directory / "request.json").read_bytes()
    original = jobs.json.dump
    entered, release = threading.Event(), threading.Event()
    captured = {}

    def paused_dump(*args, **kwargs):
        entered.set()
        if not release.wait(5):
            raise TimeoutError("Review note-write barrier")
        return original(*args, **kwargs)

    def save():
        captured["path"] = jobs.save_notes(directory, "Reviewer fixture", "Persistence only")

    with patch.object(jobs.json, "dump", paused_dump):
        thread = threading.Thread(target=save)
        thread.start()
        try:
            assert entered.wait(3)
            visible = sorted(directory.glob("notes-*.json"))[-1]
            try:
                jobs.read_json(visible)
                error = None
            except json.JSONDecodeError as exception:
                error = type(exception).__name__
        finally:
            release.set()
            thread.join(timeout=3)
    assert error == "JSONDecodeError"
    assert (directory / "request.json").read_bytes() == request_before
    assert jobs.read_json(captured["path"])["observation"] == "Reviewer fixture"
    return {
        "unfinished_note_visible_to_readers": True,
        "reader_error": error,
        "prediction_preserved": True,
        "completed_note_valid_after_release": True,
    }


def comparison():
    # Preserve the executed import order in this AST-identical evidence copy.
    from streamlit.testing.v1 import AppTest  # noqa: I001

    import shutil

    runs = EVIDENCE / "comparison/runs"
    actual = next((EVIDENCE / "pytest").glob("test_lqr_original_function_byt*/adapted"))
    base = {
        "adapter": "lqr_baseline",
        "effective": {**configuration.DEFAULTS["lqr_baseline"], "duration": 0.1},
        "prediction": "Eligibility fixture only",
        "controller": "Task005 LQR/PI",
        "provenance": jobs.provenance(),
        "fixture_classification": "Review-only conflicting metadata; not a scientific run",
    }
    for identity in ("run-a", "run-b"):
        directory = runs / identity
        directory.mkdir(parents=True)
        shutil.copytree(actual, directory / "experiment")
        request = copy.deepcopy(base)
        if identity == "run-b":
            request["effective"]["track"] = "oval"
            request["controller"] = "incompatible test controller"
            request["provenance"]["git_revision"] = "0" * 40
            request["provenance"]["source_sha256"]["src/apex/models/vehicle/dynamic_bicycle.py"] = (
                "0" * 64
            )
            request["provenance"]["vehicle_yaml"] = "name: incompatible_fixture\nmass: 999\n"
            request["provenance"]["timing_mode"] = "injected delay fixture"
        jobs.write_json(directory / "request.json", request)
        jobs.write_json(directory / "status.json", {"state": "completed"})
        jobs.write_json(
            directory / "artifacts.json",
            {"experiment/states.csv": {"sha256": jobs.sha256(directory / "experiment/states.csv")}},
        )
    altered = runs / "run-b/experiment/states.csv"
    expected_hash = jobs.read_json(runs / "run-b/artifacts.json")["experiment/states.csv"]["sha256"]
    with altered.open() as stream:
        rows = list(csv.DictReader(stream))
    rows[0]["vx"] = "123.456"
    with altered.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with patch.object(configuration, "RUNS", runs):
        app = AppTest.from_file(
            str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=15
        ).run()
        app.radio[0].set_value("Compare runs").run()
        app.multiselect[0].set_value(["run-a", "run-b"]).run()
        errors = [e.message for e in app.exception]
        warnings = [e.value for e in app.warning]
        charts = len(app.get("plotly_chart"))
    first = float(
        plots.series([("altered fixture", runs / "run-b")], ["vx"], "vx [m/s]").data[0].y[0]
    )
    assert not errors and not warnings and charts == 3 and first == 123.456
    return {
        "fixture_not_scientific_data": True,
        "mismatched_fields": [
            "track",
            "source_revision",
            "source_hash",
            "vehicle_yaml",
            "timing_mode",
            "controller",
        ],
        "ui_warnings": warnings,
        "ui_errors": errors,
        "overlay_chart_count": charts,
        "expected_states_sha256": expected_hash,
        "actual_states_sha256": jobs.sha256(altered),
        "altered_sample_plotted_without_integrity_warning": first,
    }


def finalization():
    directory = EVIDENCE / "hash_failure"
    directory.mkdir()
    jobs.write_json(
        directory / "request.json",
        {"adapter": "dynamic_demo", "effective": {"duration": 0.01, "dt": 0.005}},
    )
    error = None
    with patch.object(jobs, "sha256", side_effect=OSError("review: artifact hash read failed")):
        try:
            jobs.supervise(directory)
        except OSError as exception:
            error = str(exception)
    status = jobs.read_json(directory / "status.json")
    assert status["state"] == "completed" and error and not (directory / "artifacts.json").exists()
    return {
        "injected_fault": error,
        "status_after_manifest_failure": status,
        "artifact_manifest_present": False,
        "failure_exposed_in_status": bool(status.get("error")),
    }


result = globals()[MODE]()
output = EVIDENCE / f"probe-{MODE}.json"
output.write_text(
    json.dumps({"reviewed_sha": PIN, "probe": MODE, "observations": result}, indent=2) + "\n"
)
print(json.dumps({"probe": MODE, "defect_reproduced": True, "evidence": str(output)}))
