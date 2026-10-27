"""Focused tooling contracts and real entry-point parity; no benchmark campaign."""

import csv
import fcntl
import subprocess
import sys
import time

import pytest

from tools.apex_workbench import jobs, plots
from tools.apex_workbench.configuration import DEFAULTS, ROOT, validate
from tools.apex_workbench.worker import execute


def wait_for_run(directory):
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        status = jobs.read_json(directory / "status.json")
        if status["state"] not in {"queued", "running"}:
            # Artifact hashes are written immediately after final status.
            if (directory / "artifacts.json").exists():
                return status
        time.sleep(0.1)
    jobs.cancel_run(directory)
    pytest.fail(f"Worker did not finish: {directory}")


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, 0, True, "2", None, 21])
def test_invalid_numeric_rejected(bad):
    with pytest.raises(ValueError):
        validate("dynamic_demo", {"duration": bad, "dt": 0.005})


def test_unknown_inputs_and_lqr_tick_validation():
    for adapter, values in [
        ("invented", {}),
        ("dynamic_demo", {**DEFAULTS["dynamic_demo"], "mass": 3}),
        ("dynamic_demo", {"duration": 1}),
        ("lqr_baseline", {**DEFAULTS["lqr_baseline"], "duration": 0.012}),
        ("lqr_baseline", {**DEFAULTS["lqr_baseline"], "speed": 3.1}),
        ("lqr_baseline", {**DEFAULTS["lqr_baseline"], "track": "new_track"}),
    ]:
        with pytest.raises(ValueError):
            validate(adapter, values)


def test_dynamic_original_cli_byte_parity(tmp_path):
    effective = {"duration": 0.05, "dt": 0.005}
    adapted = tmp_path / "adapted"
    execute("dynamic_demo", effective, adapted)
    original = tmp_path / "original"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_dynamic_bicycle_demo.py"),
            "--duration",
            "0.05",
            "--dt",
            "0.005",
            "--output-dir",
            str(original),
            "--no-plot",
        ],
        check=True,
        env=jobs.worker_environment(tmp_path),
        capture_output=True,
    )
    for name in ["states.csv", "summary.json"]:
        assert (adapted / name).read_bytes() == (original / name).read_bytes()
    with pytest.raises(FileExistsError):
        execute("dynamic_demo", effective, adapted)


def test_lqr_original_function_byte_parity(tmp_path):
    from run_lqr_baseline import run_case

    effective = {**DEFAULTS["lqr_baseline"], "duration": 0.1, "ey": 0.02}
    adapted = tmp_path / "adapted"
    actual = execute("lqr_baseline", effective, adapted)
    original = tmp_path / "original"
    expected = run_case(
        "original",
        "circle",
        2.0,
        tmp_path,
        duration=0.1,
        laps=None,
        ey=0.02,
        epsi=0.0,
        profile=False,
        plots=False,
    )
    assert actual == expected
    for name in ["states.csv", "controls.csv", "summary.json"]:
        assert (adapted / name).read_bytes() == (original / name).read_bytes()


def test_global_lock_and_notes_are_append_only(tmp_path):
    jobs.RUNS.mkdir(parents=True, exist_ok=True)
    with (jobs.RUNS / ".execution.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="Another Workbench"):
            jobs.start_run("dynamic_demo", DEFAULTS["dynamic_demo"], runs=tmp_path)
    request = tmp_path / "request.json"
    request.write_text('{"prediction":"original"}')
    before = request.read_bytes()
    first = jobs.save_notes(tmp_path, "observed A", "explanation A")
    second = jobs.save_notes(tmp_path, "observed B", "explanation B")
    assert first != second and first.exists() and second.exists()
    assert request.read_bytes() == before
    with pytest.raises(ValueError):
        jobs.save_notes(tmp_path, "a" * 8001, "")


def test_cancel_and_unique_run_directories(tmp_path):
    first = jobs.start_run("dynamic_demo", {"duration": 20.0, "dt": 0.001}, runs=tmp_path)
    with pytest.raises(RuntimeError, match="Another Workbench"):
        jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=tmp_path)
    jobs.cancel_run(first)
    assert wait_for_run(first)["state"] == "cancelled"
    original_request = (first / "request.json").read_bytes()
    second = jobs.start_run("dynamic_demo", {"duration": 0.01, "dt": 0.005}, runs=tmp_path)
    assert second != first
    assert wait_for_run(second)["state"] == "completed"
    assert (first / "request.json").read_bytes() == original_request
    assert (second / "numerical_environment.json").exists()
    assert (second / "experiment/geometry.csv").exists()


def test_measurement_guard_and_disk_floor(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "ROOT", tmp_path)
    guard = tmp_path / "results/another_experiment/MEASURED_ACTIVE"
    guard.parent.mkdir(parents=True)
    guard.write_text("owner evidence")
    with pytest.raises(RuntimeError, match="measurement guards"):
        jobs.preflight()
    assert guard.read_text() == "owner evidence"
    # The fixture's guard is test-owned. Production preflight never removes guards.
    guard.unlink()
    disk = type("Disk", (), {"free": 1024})()
    monkeypatch.setattr(jobs.shutil, "disk_usage", lambda path: disk)
    with pytest.raises(RuntimeError, match="1 GiB"):
        jobs.preflight()


def test_failure_logs_and_timeout_retained(tmp_path, monkeypatch):
    failed = tmp_path / "failed"
    failed.mkdir()
    jobs.write_json(failed / "request.json", {"adapter": "invalid", "effective": {}})
    jobs.supervise(failed)
    assert jobs.read_json(failed / "status.json")["state"] == "failed"
    assert "Unsupported experiment" in (failed / "stderr.log").read_text()
    assert (failed / "artifacts.json").exists()
    timed = tmp_path / "timed"
    timed.mkdir()
    jobs.write_json(
        timed / "request.json", {"adapter": "dynamic_demo", "effective": DEFAULTS["dynamic_demo"]}
    )
    monkeypatch.setitem(jobs.LIMITS, "wall_s", -1)
    jobs.supervise(timed)
    assert jobs.read_json(timed / "status.json")["state"] == "timed_out"
    assert (timed / "stderr.log").exists()


def test_plot_reads_actual_csv_and_leaves_missing_metrics_empty(tmp_path):
    output = tmp_path / "experiment"
    output.mkdir()
    (output / "states.csv").write_text("time,vx\n0,2\n0.1,2.125\n")
    figure = plots.series([("run", tmp_path)], ["vx"], "vx [m/s]")
    assert list(figure.data[0].y) == [2, 2.125]
    assert not plots.series([("run", tmp_path)], ["invented_metric"], "").data


def test_ui_real_run_and_invalid_input(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    import tools.apex_workbench.configuration as config

    original_start = jobs.start_run
    monkeypatch.setattr(config, "RUNS", tmp_path)
    monkeypatch.setattr(jobs, "start_run", lambda a, c, p: original_start(a, c, p, runs=tmp_path))
    app = AppTest.from_file(str(ROOT / "tools/apex_workbench/app.py"), default_timeout=30).run()
    assert not app.exception
    app.number_input[0].set_value(-1)
    app.button[0].click().run()
    assert any("duration" in item.value for item in app.error)
    assert not list(tmp_path.glob("*/request.json"))
    app.number_input[0].set_value(0.02)
    app.text_area[0].set_value("The speed should remain near its initial value.")
    app.button[0].click().run()
    directory = next(tmp_path.glob("*/request.json")).parent
    assert wait_for_run(directory)["state"] == "completed"
    app.run()
    assert not app.exception
    assert app.get("plotly_chart")
    request = jobs.read_json(directory / "request.json")
    assert request["effective"] == {"duration": 0.02, "dt": 0.005}
    assert request["prediction"].startswith("The speed")
    assert "numpy" in request["provenance"]["packages"]
    assert request["provenance"]["source_sha256"]
    with (directory / "experiment/states.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 5
