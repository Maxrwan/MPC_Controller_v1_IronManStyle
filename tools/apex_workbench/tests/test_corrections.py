"""R1–R6 regressions: real workers, bounded fault injection and copied test records."""

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import psutil
import pytest

from tools.apex_workbench import comparison, configuration, jobs, lifecycle, plots, storage
from tools.apex_workbench.worker import execute


def until(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.02)
    raise TimeoutError("Bounded correction test condition did not arrive")


def finished(directory):
    def terminal():
        status = jobs.read_json(directory / "status.json")
        if status["state"] in jobs.ACTIVE:
            return None
        try:
            with jobs.execution_lock():
                return status
        except RuntimeError:
            return None

    return until(terminal, 65)


@pytest.fixture(scope="module")
def completed_runs(tmp_path_factory):
    base = tmp_path_factory.mktemp("genuine-workbench-outputs")
    result = []
    for duration in (0.01, 0.02):
        directory = jobs.start_run(
            "dynamic_demo",
            {"duration": duration, "dt": 0.005},
            "Regression seed: actual original demo output",
            runs=base,
        )
        assert finished(directory)["state"] == "completed"
        result.append(directory)
    return result


def copied(directory, target):
    # Fresh copies only: scientific/historical run records are never rewritten by these tests.
    shutil.copytree(directory, target)
    return target


def reseal_fixture(directory):
    """Rebind deliberately changed metadata in a disposable comparison fixture."""
    manifest = storage.read_json(directory / "artifacts.json")
    for relative in list(manifest):
        path = directory / relative
        manifest[relative] = {"sha256": storage.sha256(path), "bytes": path.stat().st_size}
    storage.write_json(directory / "artifacts.json", manifest)
    status = storage.read_json(directory / "status.json")
    status["manifest_sha256"] = storage.sha256(directory / "artifacts.json")
    storage.write_json(directory / "status.json", status)


@pytest.mark.parametrize("cancel", [False, True])
def test_r1_real_sigkill_keeps_worker_lease_and_recovers(tmp_path, cancel):
    directory = jobs.start_run(
        "dynamic_demo",
        {"duration": 20.0, "dt": 0.001},
        "Process-loss injection only; no physics conclusions",
        runs=tmp_path,
    )
    worker_record = supervisor_record = None
    worker = supervisor = None
    try:
        until(lambda: (directory / "worker.json").exists())
        until(lambda: jobs.read_json(directory / "status.json")["state"] == "running")
        worker_record = jobs.read_json(directory / "worker.json")
        supervisor_record = jobs.read_json(directory / "supervisor.json")
        worker = lifecycle.owned_process(worker_record, "worker", directory)
        supervisor = lifecycle.owned_process(supervisor_record, "jobs", directory)
        assert worker is not None and supervisor is not None
        # Brief suspension makes the ownership race deterministic; no latency claim is made.
        worker.send_signal(signal.SIGSTOP)
        until(lambda: worker.status() == psutil.STATUS_STOPPED)
        supervisor.send_signal(signal.SIGKILL)
        supervisor.wait(timeout=3)
        assert lifecycle.owned_process(worker_record, "worker", directory) is not None
        with pytest.raises(RuntimeError, match="Another Workbench"):
            jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=tmp_path)
        assert len(list(tmp_path.glob("*/request.json"))) == 1  # No overlapping worker admitted.
        if cancel:
            jobs.cancel_run(directory)
            assert (directory / "cancel.request").exists()
        worker.send_signal(signal.SIGCONT)
        until(lambda: lifecycle.owned_process(worker_record, "worker", directory) is None, 5)

        # Identity may cease matching during exit before the inherited FD is released.
        # Keep the admission-blocking assertion above; recover only after the lease is free.
        def lease_released():
            try:
                with jobs.execution_lock():
                    return True
            except RuntimeError:
                return False

        until(lease_released, 5)
        recovered = jobs.status_for(directory)
        assert recovered["scientific_outcome"] == ("cancelled" if cancel else "interrupted")
        assert recovered["state"] != "completed" and recovered["evidence_state"] == "valid"
        assert recovered["recovered"] is True
        snapshot = (directory / "status.json").read_bytes()
        assert jobs.status_for(directory) == recovered
        assert (directory / "status.json").read_bytes() == snapshot
        with jobs.execution_lock():
            pass
    finally:
        if worker_record and lifecycle.owned_process(worker_record, "worker", directory):
            worker.send_signal(signal.SIGCONT)
            lifecycle.terminate_owned(worker_record, directory)
        if supervisor_record:
            remaining = lifecycle.owned_process(supervisor_record, "jobs", directory)
            if remaining:
                remaining.send_signal(signal.SIGTERM)
                remaining.wait(timeout=3)


@pytest.mark.parametrize("field", ["created", "cmdline", "directory", "role"])
def test_r1_pid_reuse_or_wrong_owner_is_never_signalled(tmp_path, field):
    command = ["python", "-m", "tools.apex_workbench.worker", str(tmp_path), "3"]
    record = {
        "pid": 12345,
        "created": 1.0,
        "cmdline": command,
        "role": "worker",
        "directory": str(tmp_path),
    }
    fake = Mock()
    fake.create_time.return_value = 1.0
    fake.cmdline.return_value = command
    fake.status.return_value = psutil.STATUS_RUNNING
    changes = {"created": 0.0, "cmdline": ["other"], "directory": "/other", "role": "jobs"}
    record[field] = changes[field]
    with patch.object(lifecycle.psutil, "Process", return_value=fake):
        assert lifecycle.terminate_owned(record, tmp_path) is False
    fake.send_signal.assert_not_called()


def test_r1_stale_legacy_record_is_read_only(tmp_path):
    jobs.write_json(tmp_path / "request.json", {"adapter": "dynamic_demo", "effective": {}})
    jobs.write_json(tmp_path / "status.json", {"state": "running", "pid": 999999})
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = jobs.status_for(tmp_path)
    assert result["state"] == "interrupted" and result["scientific_outcome"] == "unknown"
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_r2_two_sessions_during_initial_publication(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    entered, release = threading.Event(), threading.Event()
    original = jobs.write_json
    captured = {}

    def paused(path, value, **kwargs):
        if path.name == "status.json" and value.get("state") == "queued":
            entered.set()
            assert release.wait(15)
        return original(path, value, **kwargs)

    def submit():
        captured["run"] = jobs.start_run(
            "dynamic_demo", {"duration": 0.01, "dt": 0.005}, "Publication regression", runs=tmp_path
        )

    monkeypatch.setattr(configuration, "RUNS", tmp_path)
    with patch.object(jobs, "write_json", paused):
        writer = threading.Thread(target=submit)
        writer.start()
        try:
            assert entered.wait(5)
            assert not storage.list_runs(tmp_path)[0]
            readers = [
                AppTest.from_file(
                    str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=15
                ).run()
                for _ in range(2)
            ]
            assert all(not app.exception for app in readers)
            assert not list(tmp_path.glob("[!.]*/request.json"))
        finally:
            release.set()
            writer.join(timeout=10)
    assert not writer.is_alive()
    assert finished(captured["run"])["state"] == "completed"
    for app in readers:
        app.run()
        assert not app.exception


def test_r2_interrupted_initial_publication_is_not_selectable(tmp_path):
    original = jobs.write_json

    def interrupted(path, value, **kwargs):
        if path.name == "status.json":
            raise OSError("Injected publication interruption")
        return original(path, value, **kwargs)

    with patch.object(jobs, "write_json", interrupted), pytest.raises(OSError):
        jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=tmp_path)
    assert not storage.list_runs(tmp_path)[0]
    assert list(tmp_path.glob(".pending-*/request.json"))  # Preserve unpublished evidence.


def test_r3_note_atomicity_interruption_and_append_only(tmp_path):
    original = jobs.save_notes(tmp_path, "original observation", "original explanation")
    before = original.read_bytes()
    entered, release = threading.Event(), threading.Event()
    link = storage.os.link
    saved = []

    def paused(source, destination):
        entered.set()
        assert release.wait(5)
        return link(source, destination)

    with patch.object(storage.os, "link", paused):
        writer = threading.Thread(
            target=lambda: saved.append(jobs.save_notes(tmp_path, "new", "new"))
        )
        writer.start()
        try:
            assert entered.wait(3)
            for _ in range(20):
                latest, problems = storage.latest_note(tmp_path)
                assert latest["observation"] == "original observation" and not problems
        finally:
            release.set()
            writer.join(timeout=3)
    assert not writer.is_alive() and len(saved) == 1
    with patch.object(storage.os, "link", side_effect=OSError("Injected note interruption")):
        with pytest.raises(OSError):
            jobs.save_notes(tmp_path, "interrupted", "interrupted")
    assert original.read_bytes() == before
    assert len(list(tmp_path.glob("notes-*.json"))) == 2
    assert not list(tmp_path.glob(".pending-*"))
    assert storage.latest_note(tmp_path)[0]["observation"] == "new"


def test_r3_concurrent_note_writers_and_readers(tmp_path):
    errors = []

    def write():
        try:
            for index in range(12):
                jobs.save_notes(tmp_path, str(index), "User interpretation")
        except Exception as error:
            errors.append(error)

    writers = [threading.Thread(target=write) for _ in range(2)]
    for writer in writers:
        writer.start()
    while any(writer.is_alive() for writer in writers):
        assert not storage.latest_note(tmp_path)[1]
    for writer in writers:
        writer.join()
    assert not errors and len(list(tmp_path.glob("notes-*.json"))) == 24


def test_r4_controlled_varied_inputs_and_documentation_revision(completed_runs, tmp_path):
    first = copied(completed_runs[0], tmp_path / "first")
    second = copied(completed_runs[1], tmp_path / "second")
    request = jobs.read_json(second / "request.json")
    request["provenance"]["git_revision"] = "f" * 40  # Only documentation identity differs.
    jobs.write_json(second / "request.json", request)
    reseal_fixture(second)
    result = comparison.eligibility(first, second)
    assert result["classification"] == "controlled"
    assert result["varied_inputs"] == {"duration": [0.01, 0.02]}
    assert not result["differences"]


@pytest.mark.parametrize(
    "dimension", ["scientific_source", "model", "tire", "controller", "vehicle", "timing", "track"]
)
def test_r4_mismatches_are_explicitly_illustrative(completed_runs, tmp_path, dimension):
    first = copied(completed_runs[0], tmp_path / "first")
    second = copied(completed_runs[0], tmp_path / "second")
    request = jobs.read_json(second / "request.json")
    if dimension == "scientific_source":
        request["provenance"]["source_sha256"]["src/apex/state.py"] = "0" * 64
    elif dimension in {"model", "tire"}:
        request["provenance"][dimension] = "Different declared test composition"
    elif dimension == "controller":
        request[dimension] = "Different declared test controller"
    elif dimension == "vehicle":
        request["provenance"]["vehicle_yaml"] += "\n# Deliberately different fixture definition"
    elif dimension == "timing":
        request["provenance"]["timing_mode"] = "Different declared timing fixture"
    else:
        geometry = second / "experiment/geometry.csv"
        geometry.write_text(geometry.read_text() + "\n")
    jobs.write_json(second / "request.json", request)
    reseal_fixture(second)
    result = comparison.eligibility(first, second)
    assert result["classification"] == "illustrative" and result["differences"]


def test_r4_incompatible_units_are_invalid(completed_runs, tmp_path):
    first = copied(completed_runs[0], tmp_path / "first")
    second = copied(completed_runs[0], tmp_path / "second")
    contract = jobs.read_json(second / "experiment/telemetry_contract.json")
    contract["state_units"][0] = "km/h"
    jobs.write_json(second / "experiment/telemetry_contract.json", contract)
    reseal_fixture(second)
    assert comparison.eligibility(first, second)["classification"] == "invalid"


def test_r5_hash_failure_keeps_scientific_outcome_separate(tmp_path):
    jobs.write_json(
        tmp_path / "request.json",
        {
            "adapter": "dynamic_demo",
            "effective": {"duration": 0.01, "dt": 0.005},
            "execution_lock": str(jobs.RUNS / ".execution.lock"),
            "provenance": {"limits": jobs.LIMITS},
        },
    )
    with patch.object(jobs, "sha256", side_effect=OSError("Injected manifest hash failure")):
        jobs.supervise(tmp_path)
    status = jobs.read_json(tmp_path / "status.json")
    assert status["scientific_outcome"] == "completed"
    assert status["state"] == "evidence_failed" and status["evidence_state"] == "failed"
    assert "Injected manifest hash failure" in status["error"]
    assert jobs.read_json(tmp_path / "execution.json")["scientific_outcome"] == "completed"
    with pytest.raises(storage.IntegrityError):
        storage.artifact_bytes(tmp_path, "experiment/states.csv")


def test_r5_interrupted_final_commit_recovers_known_outcome(completed_runs, tmp_path):
    directory = copied(completed_runs[0], tmp_path / "record")
    original = jobs.write_json

    def interrupted(path, value, **kwargs):
        if path.name == "status.json" and value.get("state") == "completed":
            raise OSError("Injected final status interruption")
        return original(path, value, **kwargs)

    with patch.object(jobs, "write_json", interrupted), pytest.raises(OSError):
        jobs.finalize(directory, "completed")
    assert jobs.read_json(directory / "status.json")["state"] == "finalizing"
    assert jobs.status_for(directory)["scientific_outcome"] == "completed"
    assert jobs.read_json(directory / "status.json")["evidence_state"] == "valid"


@pytest.mark.parametrize("relative", ["experiment/states.csv", "request.json", "artifacts.json"])
def test_r6_altered_artifact_is_quarantined(completed_runs, tmp_path, relative):
    directory = copied(completed_runs[0], tmp_path / "record")
    if relative == "experiment/states.csv":
        assert not plots.read_frame(directory, "states.csv").empty  # Prime the verified cache.
    path = directory / relative
    previous = path.stat()
    data = path.read_bytes()
    path.write_bytes(data.replace(b"2.0", b"9.0", 1) if b"2.0" in data else data + b" ")
    os.utime(
        path, ns=(previous.st_atime_ns, previous.st_mtime_ns)
    )  # ctime still invalidates cache.
    with pytest.raises(storage.IntegrityError):
        plots.read_frame(directory, "states.csv")
    assert comparison.eligibility(directory, directory)["classification"] == "invalid"


def test_r6_missing_manifest_and_unverified_legacy_are_rejected(completed_runs, tmp_path):
    directory = copied(completed_runs[0], tmp_path / "record")
    (directory / "artifacts.json").unlink()
    with pytest.raises(storage.IntegrityError):
        plots.read_frame(directory, "states.csv")


def test_existing_lqr_still_executes_under_owned_worker(tmp_path, monkeypatch):
    config = {**configuration.DEFAULTS["lqr_baseline"], "duration": 0.01}
    directory = jobs.start_run(
        "lqr_baseline", config, "Original baseline smoke check", runs=tmp_path
    )
    status = finished(directory)
    assert status["state"] == "completed" and status["evidence_state"] == "valid"
    assert not plots.read_frame(directory, "states.csv").empty
    assert not plots.read_frame(directory, "controls.csv").empty
    original = tmp_path / "original-entry-point"
    execute("lqr_baseline", config, original)
    for name in ("states.csv", "controls.csv", "summary.json"):
        assert (directory / "experiment" / name).read_bytes() == (original / name).read_bytes()
    damaged = copied(directory, tmp_path / "damaged-records/missing-controls")
    (damaged / "experiment/controls.csv").unlink()
    with pytest.raises(storage.IntegrityError, match="controls.csv"):
        plots.read_frame(damaged, "controls.csv")
    app = retained_app(damaged.parent, monkeypatch)
    assert not app.exception and not app.get("plotly_chart")
    assert any("controls.csv" in error.value for error in app.error)


def test_sampler_tolerates_removed_temporary_file(tmp_path):
    stable = tmp_path / "stable.log"
    stable.write_text("1234")
    transient = tmp_path / "temporary.lock"
    transient.touch()
    original = Path.stat

    def disappearing(path, *args, **kwargs):
        if path == transient:
            raise FileNotFoundError("Removed cache lock")
        return original(path, *args, **kwargs)

    with patch.object(Path, "stat", disappearing):
        assert lifecycle.sampled_output_size(tmp_path) == 4


def test_full_worker_dynamic_parity(completed_runs, tmp_path):
    output = tmp_path / "original-entry-point"
    execute("dynamic_demo", {"duration": 0.01, "dt": 0.005}, output)
    for name in ("states.csv", "summary.json"):
        assert (completed_runs[0] / "experiment" / name).read_bytes() == (
            output / name
        ).read_bytes()


def test_r4_r6_ui_eligibility_and_quarantine(completed_runs, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    first = copied(completed_runs[0], tmp_path / "first")
    second = copied(completed_runs[1], tmp_path / "second")
    monkeypatch.setattr(configuration, "RUNS", tmp_path)
    app = AppTest.from_file(
        str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=20
    ).run()
    app.radio[0].set_value("Compare runs").run()
    app.multiselect[0].set_value(["first", "second"]).run()
    assert not app.exception
    assert any("Controlled comparison" in entry.value for entry in app.success)
    assert len(app.get("plotly_chart")) == 3
    request = jobs.read_json(second / "request.json")
    request["provenance"]["timing_mode"] = "Declared timing difference in disposable fixture"
    jobs.write_json(second / "request.json", request)
    reseal_fixture(second)
    app.run()
    assert any("Illustrative comparison" in entry.value for entry in app.warning)
    assert len(app.get("plotly_chart")) == 3
    path = second / "experiment/states.csv"
    path.write_bytes(path.read_bytes().replace(b"2.0", b"9.0", 1))
    app.run()
    assert not app.exception and not app.get("plotly_chart")
    assert any("quarantined" in entry.value for entry in app.error)
    assert (first / "experiment/states.csv").read_bytes() == (
        completed_runs[0] / "experiment/states.csv"
    ).read_bytes()


def test_selected_artifacts_only_are_read(completed_runs, tmp_path):
    directory = copied(completed_runs[0], tmp_path / "record")
    unrelated = directory / "unrelated.bin"
    unrelated.write_bytes(b"not a selected telemetry artifact")
    original = Path.read_bytes

    def selected_only(path):
        assert path != unrelated
        return original(path)

    with patch.object(Path, "read_bytes", selected_only):
        assert not plots.read_frame(directory, "states.csv").empty


def test_r5_scientific_receipt_cannot_be_rewritten(completed_runs, tmp_path):
    directory = copied(completed_runs[0], tmp_path / "record")
    before = (directory / "execution.json").read_bytes()
    with pytest.raises(storage.IntegrityError, match="Refusing to change"):
        jobs.finalize(directory, "failed")
    assert (directory / "execution.json").read_bytes() == before


def retained_app(parent, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(configuration, "RUNS", parent)
    return AppTest.from_file(
        str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=20
    ).run()


@pytest.mark.parametrize(
    "damage", ["prediction_missing", "prediction_type", "effective", "adapter", "array", "json"]
)
def test_incomplete_request_is_excluded_without_ui_crash(
    completed_runs, tmp_path, monkeypatch, damage
):
    directory = copied(completed_runs[0], tmp_path / "damaged")
    path = directory / "request.json"
    request = storage.read_json(path)
    if damage == "prediction_missing":
        del request["prediction"]
    elif damage == "prediction_type":
        request["prediction"] = None
    elif damage == "effective":
        request["effective"] = {"duration": -1}
    elif damage == "adapter":
        request["adapter"] = ["dynamic_demo"]
    elif damage == "array":
        request = []
    if damage == "json":
        path.write_text('{"adapter":')
    else:
        storage.write_json(path, request)
    before = {
        str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()
    }
    assert not storage.list_runs(tmp_path)[0]
    app = retained_app(tmp_path, monkeypatch)
    assert not app.exception and not app.get("plotly_chart")
    assert any("Incomplete record preserved" in warning.value for warning in app.warning)
    assert {
        str(p.relative_to(directory)): p.read_bytes() for p in directory.rglob("*") if p.is_file()
    } == before


@pytest.mark.parametrize(
    "content", ["[]", "null", '{"state": []}', '{"state":"running","evidence_state":{}}']
)
def test_malformed_status_is_quarantined(completed_runs, tmp_path, monkeypatch, content):
    directory = copied(completed_runs[0], tmp_path / "damaged")
    (directory / "status.json").write_text(content)
    assert jobs.status_for(directory)["state"] == "quarantined"
    app = retained_app(tmp_path, monkeypatch)
    assert not app.exception and app.warning
    assert (directory / "status.json").read_text() == content


def test_request_changed_after_listing_is_quarantined(completed_runs, tmp_path, monkeypatch):
    directory = copied(completed_runs[0], tmp_path / "record")
    original = storage.list_runs

    def interleaved(parent):
        result = original(parent)
        (directory / "request.json").write_text('{"prediction":')
        return result

    monkeypatch.setattr(storage, "list_runs", interleaved)
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(configuration, "RUNS", tmp_path)
    app = AppTest.from_file(
        str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=20
    )
    # Skip the ordinary first-terminal rerun so this forces the selected-record read race.
    app.session_state["last_terminal"] = "record"
    app.run()
    assert not app.exception and not app.get("plotly_chart")
    assert any("record quarantined" in error.value for error in app.error)


@pytest.mark.parametrize(
    "relative",
    [
        "experiment/geometry.csv",
        "experiment/trajectory_xy.csv",
        "experiment/states.csv",
        "experiment/summary.json",
        "experiment/telemetry_contract.json",
        "worker_result.json",
        "numerical_environment.json",
        "stdout.log",
        "stderr.log",
    ],
)
def test_missing_retained_artifact_is_visible(completed_runs, tmp_path, monkeypatch, relative):
    directory = copied(completed_runs[0], tmp_path / "record")
    assert relative in storage.artifact_manifest(directory)
    (directory / relative).unlink()
    with pytest.raises(storage.IntegrityError):
        storage.artifact_bytes(directory, relative, optional=True)
    app = retained_app(tmp_path, monkeypatch)
    assert not app.exception
    assert any(relative in error.value for error in app.error)
    if relative not in {"stdout.log", "stderr.log"}:
        assert not app.get("plotly_chart")
        assert comparison.eligibility(directory, completed_runs[1])["classification"] == "invalid"


def test_optional_unproduced_controls_stay_unavailable(completed_runs, tmp_path):
    directory = copied(completed_runs[0], tmp_path / "record")
    assert "experiment/controls.csv" not in storage.artifact_manifest(directory)
    assert plots.read_frame(directory, "controls.csv").empty
    assert not plots.series(
        [("actual", directory)], ["vx"], "vx", reference="reference_speed"
    ).data[1:]
    assert comparison.eligibility(directory, completed_runs[1])["classification"] == "controlled"


def test_failed_execution_with_no_exports_remains_inspectable(tmp_path, monkeypatch):
    request = {
        "record_version": 2,
        "adapter": "dynamic_demo",
        "effective": {"duration": 0.01, "dt": 0.005},
        "prediction": "Failure fixture",
    }
    directory = tmp_path / "failed"
    directory.mkdir()
    storage.write_json(directory / "request.json", request)
    jobs.finalize(directory, "failed", error="Review fixture: worker never produced exports")
    app = retained_app(tmp_path, monkeypatch)
    assert not app.exception and not app.get("plotly_chart")
    assert [error.value for error in app.error] == ["Review fixture: worker never produced exports"]
    assert any("Trajectory unavailable" in info.value for info in app.info)
    assert jobs.status_for(directory)["scientific_outcome"] == "failed"


def test_ui_quarantine_does_not_hide_legacy_active_owner(tmp_path):
    directory = tmp_path / "legacy-active"
    directory.mkdir()
    storage.write_json(directory / "request.json", {"adapter": "dynamic_demo", "effective": {}})
    storage.write_json(directory / "status.json", {"state": "running", "pid": 12345})
    assert not storage.list_runs(tmp_path)[0]
    with patch.object(lifecycle, "legacy_worker_alive", return_value=True):
        with pytest.raises(RuntimeError, match="worker is still alive"):
            jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=tmp_path)
    assert len(list(tmp_path.glob("*/request.json"))) == 1


@pytest.mark.parametrize("damage", ["evidence", "outcome", "array", "json"])
def test_malformed_legacy_status_cannot_admit_over_live_process(tmp_path, monkeypatch, damage):
    # A real sleeping sentinel with the legacy command contract; no scientific module runs.
    package = tmp_path / "sentinel-package"
    worker = package / "tools/apex_workbench/worker.py"
    worker.parent.mkdir(parents=True)
    worker.write_text("import time\ntime.sleep(10)\n")
    (package / "tools/__init__.py").touch()
    (worker.parent / "__init__.py").touch()
    runs = tmp_path / "runs"
    directory = runs / "legacy-active"
    directory.mkdir(parents=True)
    monkeypatch.setattr(jobs, "RUNS", runs)
    with subprocess.Popen(
        [sys.executable, "-m", "tools.apex_workbench.worker", str(directory)],
        cwd=package,
        env={**os.environ, "PYTHONPATH": str(package)},
    ) as process:
        try:
            status = {"state": "running", "pid": process.pid}
            until(lambda: lifecycle.legacy_worker_alive(status, directory), 3)
            if damage == "evidence":
                status["evidence_state"] = {}
            elif damage == "outcome":
                status["scientific_outcome"] = []
            storage.write_json(directory / "status.json", [] if damage == "array" else status)
            if damage == "json":
                (directory / "status.json").write_text('{"state":')
            storage.write_json(
                directory / "request.json", {"adapter": "dynamic_demo", "effective": {}}
            )
            before = {p.name: p.read_bytes() for p in directory.iterdir()}
            with patch.object(jobs, "provenance", side_effect=AssertionError("Admission escaped")):
                with pytest.raises(RuntimeError, match="still alive|admission blocked"):
                    jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=runs)
            assert process.poll() is None
            assert {p.name: p.read_bytes() for p in directory.iterdir()} == before
            assert len(list(runs.glob("*/request.json"))) == 1
        finally:
            process.terminate()
            process.wait(timeout=3)


def test_status_replaced_before_locked_recovery_is_quarantined(tmp_path, monkeypatch):
    directory = tmp_path / "record"
    directory.mkdir()
    storage.write_json(directory / "status.json", {"state": "running"})
    original = storage.read_status

    def raced(path, **kwargs):
        status = original(path, **kwargs)
        storage.write_json(directory / "status.json", [])
        return status

    monkeypatch.setattr(storage, "read_status", raced)
    status = jobs.status_for(directory)
    assert status["state"] == "quarantined"
    assert status["scientific_outcome"] == "unknown"
    assert (directory / "status.json").read_text().strip() == "[]"
