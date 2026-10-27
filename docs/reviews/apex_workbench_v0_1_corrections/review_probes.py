"""Review-only probes for pinned 219b935; never changes implementation or old evidence."""

import argparse
import json
import shutil
import signal
import subprocess
import time
from pathlib import Path

from tools.apex_workbench import configuration, jobs, lifecycle, plots, storage


def until(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.01)
    raise TimeoutError("Review probe exceeded bounded wait")


def lease_free():
    try:
        with jobs.execution_lock():
            return True
    except RuntimeError:
        return False


def app_snapshot(parent):
    from streamlit.testing.v1 import AppTest

    previous = configuration.RUNS
    configuration.RUNS = parent
    try:
        app = AppTest.from_file(
            str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=20
        ).run()
        return {
            "exceptions": [item.message for item in app.exception],
            "errors": [item.value for item in app.error],
            "warnings": [item.value for item in app.warning],
            "info": [item.value for item in app.info],
            "charts": len(app.get("plotly_chart")),
        }
    finally:
        configuration.RUNS = previous


def readers(evidence):
    seed = next((evidence / "pytest/genuine-workbench-outputs0").glob("*/request.json")).parent
    fixtures = evidence / "reader-probes"
    fixtures.mkdir()
    missing_prediction = fixtures / "missing-prediction/record"
    shutil.copytree(seed, missing_prediction)
    request = storage.read_json(missing_prediction / "request.json")
    del request["prediction"]
    storage.write_json(missing_prediction / "request.json", request)
    selected, excluded = storage.list_runs(missing_prediction.parent)
    prediction = app_snapshot(missing_prediction.parent)
    assert missing_prediction in selected and not excluded
    assert prediction["exceptions"] == ["'prediction'"]

    missing_geometry = fixtures / "missing-geometry/record"
    shutil.copytree(seed, missing_geometry)
    geometry = missing_geometry / "experiment/geometry.csv"
    manifest = storage.read_json(missing_geometry / "artifacts.json")
    assert "experiment/geometry.csv" in manifest
    geometry.unlink()
    figure = plots.trajectory(missing_geometry)
    trajectory = app_snapshot(missing_geometry.parent)
    assert [trace.name for trace in figure.data] == ["Plant trajectory"]
    assert not trajectory["exceptions"] and not trajectory["errors"]
    assert not trajectory["warnings"] and trajectory["charts"] > 0
    return {
        "seed": str(seed),
        "fixtures_resealed": False,
        "missing_prediction": prediction,
        "missing_prediction_selected": [str(path) for path in selected],
        "missing_geometry": trajectory,
        "missing_geometry_trace_names": [trace.name for trace in figure.data],
        "geometry_recorded_in_manifest": True,
    }


def recovery(evidence):
    failed = next(
        (evidence / "pytest/test_r1_real_sigkill_keeps_wor0").glob("*/status.json")
    ).parent
    shutil.copytree(failed, evidence / "r1-failed-test-raw")
    raw = storage.read_json(failed / "status.json")
    worker = storage.read_json(failed / "worker.json")
    supervisor = storage.read_json(failed / "supervisor.json")
    gone = {
        "worker": lifecycle.owned_process(worker, "worker", failed) is None,
        "supervisor": lifecycle.owned_process(supervisor, "jobs", failed) is None,
    }
    assert all(gone.values()) and lease_free()
    recovered = jobs.status_for(failed)
    assert recovered["scientific_outcome"] == "interrupted"
    assert recovered["state"] == "interrupted" and recovered["evidence_state"] == "valid"
    snapshot = (failed / "status.json").read_bytes()
    assert jobs.status_for(failed) == recovered
    assert (failed / "status.json").read_bytes() == snapshot

    directory = jobs.start_run(
        "dynamic_demo",
        {"duration": 20.0, "dt": 0.001},
        "Review: supervisor loss without worker suspension",
        runs=evidence / "natural-loss",
    )
    worker_record = supervisor_record = None
    observations = []
    try:
        until(lambda: (directory / "worker.json").exists())
        worker_record = storage.read_json(directory / "worker.json")
        supervisor_record = storage.read_json(directory / "supervisor.json")
        live_supervisor = lifecycle.owned_process(supervisor_record, "jobs", directory)
        assert live_supervisor is not None and not lease_free()
        live_supervisor.send_signal(signal.SIGKILL)
        live_supervisor.wait(timeout=3)

        def settled():
            status = jobs.status_for(directory)
            observations.append(
                {"state": status["state"], "owner_notice": status.get("owner_notice")}
            )
            return status if status["state"] not in jobs.ACTIVE else None

        natural = until(settled)
        assert natural["scientific_outcome"] == "interrupted"
        assert natural["evidence_state"] == "valid" and lease_free()
        assert lifecycle.owned_process(worker_record, "worker", directory) is None
    finally:
        if worker_record and lifecycle.owned_process(worker_record, "worker", directory):
            lifecycle.terminate_owned(worker_record, directory)
        if supervisor_record:
            live_supervisor = lifecycle.owned_process(supervisor_record, "jobs", directory)
            if live_supervisor:
                live_supervisor.send_signal(signal.SIGTERM)
                live_supervisor.wait(timeout=3)

    with subprocess.Popen(["/bin/sleep", "10"]) as unrelated:
        record = lifecycle.identity(unrelated.pid, "jobs", evidence)
        record["role"] = "worker"
        rejected = lifecycle.terminate_owned(record, evidence)
        alive = unrelated.poll() is None
        unrelated.terminate()
        unrelated.wait(timeout=3)
    assert rejected is False and alive
    return {
        "failed_test_raw_status": raw,
        "failed_test_owners_gone": gone,
        "failed_test_recovered_status": recovered,
        "recovery_idempotent": True,
        "natural_supervisor_loss": natural,
        "natural_status_observations": observations,
        "unrelated_live_process_not_signalled": alive and not rejected,
        "test_race_interpretation": (
            "owned_process absence can precede lease release; "
            "immediate status read is not a completion barrier"
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["readers", "recovery"])
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    assert (
        subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=configuration.ROOT, text=True
        ).strip()
        == "219b9358409fa73fc59f24a7755da66771883e6b"
    )
    result = globals()[args.mode](args.evidence)
    storage.write_json(args.evidence / ("probe-" + args.mode + ".json"), result, exclusive=True)
    print(json.dumps(result, indent=2))
