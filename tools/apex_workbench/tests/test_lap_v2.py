"""V2 protocol, preservation and analysis checks; no optimizer or plant execution."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import storage
from tools.apex_workbench.lap import analysis, config, evidence, execution, panels


@pytest.mark.parametrize(
    "mode,duration", [("extended", 5), ("extended", 10), ("extended", 20), ("full_lap", 80)]
)
def test_only_approved_finite_modes(mode, duration):
    assert config.validate(config.defaults(mode, duration))["maximum_simulation_s"] == duration
    assert config.limits(config.defaults(mode, duration))["wall_s"] > 60


@pytest.mark.parametrize(
    "key,value",
    [
        ("maximum_simulation_s", True),
        ("maximum_simulation_s", 0),
        ("maximum_simulation_s", 81),
        ("mode", "unbounded"),
        ("scientific_source", "changed"),
        ("mass", 5),
    ],
)
def test_configuration_rejects_unsupported_semantics(key, value):
    selected = config.defaults()
    selected[key] = value
    with pytest.raises(ValueError):
        config.validate(selected)


def test_first_crossing_from_one_metre_never_counts_as_full_lap():
    partial = analysis.laps({"lap_times": [9.9], "stop_reason": "duration"}, 100, 1)
    assert partial["completed_laps"] == 0 and partial["lap_time_s"] is None
    full = analysis.laps({"lap_times": [9.9, 10], "stop_reason": "target_laps"}, 100, 1)
    assert full["completed_laps"] == 1 and full["lap_time_s"] == 10
    assert full["native_crossings"][-1]["time_s"] == 19.9
    assert full["native_crossings"][-1]["s_abs_m"] == 200


def test_native_crossing_convention_and_incomplete_sector():
    # Serialization/clock fixture only; this is not a physical vehicle trajectory.
    segments = [
        {
            "start": 1.0,
            "end": 1.005,
            "state_before": [0, 0, 0, 0, 99.9, 0],
            "state_after": [0, 0, 0, 0, 100.1, 0],
        }
    ]
    assert analysis.crossing(segments, 100) == 1.0025
    assert analysis.crossing(segments, 125) is None


def test_chunks_roll_without_dropping_native_tokens(tmp_path):
    target = tmp_path / "chunks"
    writer = evidence.Chunks(target, maximum=60)
    original = [{"time": i * 0.005, "value": -0.0} for i in range(10)]
    for row in original:
        writer.append("states", row)
    writer.close()
    assert len(list(target.iterdir())) > 1
    restored = [
        json.loads(row) for p in sorted(target.iterdir()) for row in p.read_bytes().splitlines()
    ]
    assert restored == original
    assert all(p.stat().st_size <= 60 for p in target.iterdir())
    assert b"-0.0" in next(target.iterdir()).read_bytes()
    with pytest.raises(FileExistsError):
        evidence.Chunks(target)


def test_chunk_cannot_overwrite_link_or_oversized_observation(tmp_path):
    writer = evidence.Chunks(tmp_path / "journal", maximum=50)
    protected = tmp_path / "protected"
    protected.write_text("original")
    (tmp_path / "journal/states-00000.jsonl").symlink_to(protected)
    with pytest.raises(FileExistsError):
        writer.append("states", {"time": 0.0})
    assert protected.read_text() == "original"
    with pytest.raises(ValueError):
        writer.append("plans", {"long": "x" * 100})


def policy(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT", tmp_path)
    monkeypatch.setattr(config, "RUNS", tmp_path / "runs")
    source = b"reviewed source fixture"
    digest = hashlib.sha256(source).hexdigest()
    monkeypatch.setattr(config, "producers", lambda: {"fixture.py": digest})
    monkeypatch.setattr(config.v1.frozen, "git", lambda *_: source)
    storage.write_json(
        tmp_path / "review.json", {"outcome": "PASS", "candidate": "fixture-revision"}
    )
    storage.write_json(tmp_path / "authority.json", {"decision": "Bounded WORK fixture"})
    value = {
        "schema": "apex-lap-access/1",
        "stage": "reviewed-work",
        "reviewed_revision": "fixture-revision",
        "used": {},
        "review_record": str(tmp_path / "review.json"),
        "review_sha256": storage.sha256(tmp_path / "review.json"),
        "producer_sha256": {"fixture.py": digest},
        "authority_record": str(tmp_path / "authority.json"),
        "authority_sha256": storage.sha256(tmp_path / "authority.json"),
    }
    storage.write_json(tmp_path / "access.json", value)
    return value


def test_once_only_policy_and_exact_worker_binding(tmp_path, monkeypatch):
    policy(tmp_path, monkeypatch)
    config.access(config.defaults(), consume="one-pilot")
    assert config.access(config.defaults(), run_id="one-pilot")["used"] == {"pilot": "one-pilot"}
    with pytest.raises(ValueError):
        config.access(config.defaults(), consume="retry")
    with pytest.raises(ValueError):
        config.access(config.defaults(), run_id="other-worker")
    with pytest.raises(ValueError):
        config.access(config.defaults("extended", 5))


@pytest.mark.parametrize("fault", ["review", "source", "git", "authority", "premature_acceptance"])
def test_admission_fails_closed(tmp_path, monkeypatch, fault):
    value = policy(tmp_path, monkeypatch)
    if fault == "review":
        (tmp_path / "review.json").write_text("{}")
    elif fault == "source":
        monkeypatch.setattr(config, "producers", lambda: {"fixture.py": "changed"})
    elif fault == "git":
        monkeypatch.setattr(config.v1.frozen, "git", lambda *_: b"changed")
    elif fault == "authority":
        (tmp_path / "authority.json").write_text("{}")
    else:
        value["stage"] = "accepted-interactive"
        storage.write_json(tmp_path / "access.json", value)
    with pytest.raises(ValueError):
        config.access(config.defaults())


def test_explicit_later_acceptance_does_not_consume_more_work_slots(tmp_path, monkeypatch):
    value = policy(tmp_path, monkeypatch)
    storage.write_json(
        tmp_path / "authority.json",
        {"schema": "apex-lap-primary-acceptance/1", "accepted_revision": "fixture-revision"},
    )
    value.update(
        stage="accepted-interactive",
        used={"pilot": "historical"},
        authority_sha256=storage.sha256(tmp_path / "authority.json"),
    )
    storage.write_json(tmp_path / "access.json", value)
    before = (tmp_path / "access.json").read_bytes()
    config.access(config.defaults("extended", 20), consume="user-triggered")
    assert (tmp_path / "access.json").read_bytes() == before


def test_source_identity_binds_complete_new_producer_set():
    producers = config.producers()
    assert "tools/apex_workbench/lap/worker.py" in producers
    assert "Launch_APEX_Workbench_V2.command" in producers
    assert "tools/apex_workbench/scratch_replay_web/index.html" in producers
    assert set(config.v1.PRODUCERS) <= producers.keys()


def test_display_reduction_does_not_change_scientific_rows():
    rows = [{"time": i * 0.005, "value": i} for i in range(16000)]
    before = copy.deepcopy(rows)
    display = panels.reduced(rows)
    assert len(display) <= 2000 and display[0] is rows[0] and display[-1] is rows[-1]
    assert rows == before and all(r in rows for r in display)


def test_prediction_association_uses_target_clock_not_nearest_unrelated_sample():
    raw = {
        "states": [{"time": 0.0}, {"time": 0.005}],
        "packets": [
            {
                "plan_id": 4,
                "timestamps": [0.0, 0.003, 0.005],
                "states": [[0] * 6] * 3,
                "actual_completion_time": 0.1,
            }
        ],
        "handoffs": [],
    }
    nodes = analysis.predictions({"raw": raw}, 4)["nodes"]
    assert nodes[0]["actual_native_time_s"] == 0
    assert nodes[1]["actual"] is None
    assert nodes[2]["actual_native_time_s"] == 0.005


def test_pilot_budget_is_finite_and_rejects_unjustified_ceiling():
    pilot = {
        "directory": Path("pilot"),
        "request": {"effective": config.defaults()},
        "raw": {"failure": None},
        "status": {"wall_runtime_s": 20, "sampled_peak_worker_rss_bytes": 200_000_000},
        "summary": {
            "coverage_completed": True,
            "worker_cpu_s": 10,
            "retained_native_bytes": 5_000_000,
            "total_recorded_bytes": 6_000_000,
        },
    }
    budget = analysis.resource_budget(pilot)
    assert budget["conservative_extrapolation"]["wall_s"] == 320
    pilot["status"]["wall_runtime_s"] = 100
    with pytest.raises(ValueError):
        analysis.resource_budget(pilot)


def test_protected_v1_producers_and_launcher_remain_exact_accepted_source():
    for name in (*config.v1.PRODUCERS, "Launch_APEX_Workbench.command"):
        old = config.v1.frozen.git("show", "511b0a884e0f8474760817620fcdef46e7860142:" + name)
        assert hashlib.sha256(old).hexdigest() == storage.sha256(config.ROOT / name)


def test_source_isolated_configuration_uses_native_dataclasses_without_solve(tmp_path):
    # One fresh process: genuine frozen configuration loaders, no optimizer/controller/plant runs.
    source = """
import json
from tools.apex_workbench.lap import config, worker
from tools.apex_workbench import nmpc_weight_worker as native
guard, control, environment = native.bootstrap(config.v1.RUNTIME)
import casadi
from apex.simulation.asynchronous import AsyncRunner
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
def forbidden(*args, **kwargs): raise AssertionError("Numerical execution forbidden")
casadi.nlpsol = forbidden
AsyncRunner.run = forbidden
DynamicBicycle.step = forbidden
from dataclasses import asdict
original = worker.short.resolve(config.v1.defaults())
for value in [config.defaults(), config.defaults("extended", 20), config.defaults("full_lap")]:
    parts = worker.resolve(value)
    assert asdict(parts[3]) == asdict(original[3])
    assert parts[6] == original[6]
    assert parts[4].duration == value["maximum_simulation_s"]
    assert parts[4].laps == 2
    a, b = asdict(parts[4]), asdict(original[4])
    a.pop("duration"); b.pop("duration")
    assert a == b
    assert parts[-1]["track_length_m"] == parts[0].length
assert control["mode_name"] == "single"
print("3 native configuration compositions, zero solves/plant steps")
"""
    process = subprocess.run(
        [sys.executable, "-B", "-c", source],
        capture_output=True,
        text=True,
        cwd=config.ROOT,
        timeout=60,
    )
    (tmp_path / "configuration.log").write_text(process.stdout + process.stderr)
    assert process.returncode == 0, process.stderr


def test_standard_ui_keeps_v1_and_bounds_v2_without_execution(monkeypatch):
    def forbidden(*_, **__):
        raise AssertionError("No execution/probe authorized by UI software test")

    monkeypatch.setattr(execution, "start", forbidden)
    monkeypatch.setattr(config.v1, "probe", forbidden)
    app = AppTest.from_file(str(config.HERE / "app.py")).run(timeout=30)
    assert not app.exception
    app.button[0].click().run(timeout=30)
    assert not app.exception
    mode = next(s for s in app.selectbox if s.label == "Experiment mode")
    assert mode.options == ["Transient (accepted V1)", "Extended", "Full Lap"]
    mode.select("Extended").run(timeout=30)
    assert not app.exception
    assert next(
        s for s in app.selectbox if s.label == "Maximum simulated duration [s]"
    ).options == ["5", "10", "20"]
    assert next(b for b in app.button if b.label == "Run V2 experiment").disabled


def archive_fixture(tmp_path, monkeypatch):
    """Serialization fixture only; not vehicle evidence or numerical qualification."""
    monkeypatch.setattr(config, "OUTPUT", tmp_path)
    monkeypatch.setattr(config, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(config.v1.frozen, "source_hashes", lambda: {})
    directory = tmp_path / "runs/fixture"
    directory.mkdir(parents=True)
    value = config.defaults()
    resolved = {
        "effective": value,
        "configuration": {"costs": value["scratch"]["costs"]},
        "simulation": {"duration": 10, "laps": 2},
        "track_length_m": 100,
        "initial_state": [1, 0, 0, 0, 1, 0],
    }
    request = {
        "adapter": "nmpc_lap_v2",
        "run_id": "fixture",
        "effective": value,
        "capture": {"resolved": resolved, "environment": {"fixture": True}, "source_sha256": {}},
    }
    storage.write_json(directory / "request.json", request)
    storage.write_json(
        directory / "pre_identity.json", {"resolved": resolved, "environment": {"fixture": True}}
    )
    storage.write_json(
        directory / "post_identity.json", {"source_unchanged": True, "environment_unchanged": True}
    )
    states = [
        {
            "time": i * 0.005,
            "vx": 1,
            "vy": 0,
            "r": 0,
            "s_abs": 1 + i * 0.005,
            "e_y": 0,
            "e_psi": 0,
            "delta": 0,
            "a_cmd": 0,
            "front_utilization": 0,
            "rear_utilization": 0,
            "boundary_violation": False,
        }
        for i in range(3)
    ]
    raw = {
        "states": states,
        "controls": [],
        "plans": [],
        "packets": [],
        "triggers": [],
        "handoffs": [],
        "fallbacks": [],
        "misses": [],
        "releases": [],
        "lap_times": [],
        "end_time": 10,
        "failure": None,
        "stop_reason": "duration",
    }
    evidence.store_raw(directory, raw)
    derived = evidence.Chunks(directory / "derived")
    for row in states:
        derived.append(
            "states",
            {
                "time": row["time"],
                "x": 0,
                "y": 0,
                "racing_error_y_m": 0,
                "racing_error_heading_rad": 0,
                "body_ax_mps2": 0,
                "body_ay_mps2": 0,
            },
        )
    derived.close()
    storage.write_json(
        directory / "presentation.json", {"state_rows": 3, "applied_disturbances": []}
    )
    storage.write_json(directory / "summary.json", {"coverage_completed": True})
    for name in ["worker.json", "supervisor.json", "worker_result.json"]:
        storage.write_json(directory / name, {"fixture": True})
    for name in ["stdout.log", "stderr.log"]:
        (directory / name).write_text("")
    execution.finalize(directory, "completed")
    return directory


def test_production_archive_roundtrip_and_changed_epoch(tmp_path, monkeypatch):
    directory = archive_fixture(tmp_path, monkeypatch)
    view = evidence.read_run(directory)
    assert len(view["raw"]["states"]) == 3
    assert len(view["presentation"]["states"]) == 3
    (directory / "native/states-00000.jsonl").write_text("changed")
    with pytest.raises(ValueError):
        evidence.current(view)
    with pytest.raises(ValueError):
        evidence.read_run(directory)


def test_missing_required_artifact_quarantines(tmp_path, monkeypatch):
    directory = archive_fixture(tmp_path, monkeypatch)
    (directory / "presentation.json").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        evidence.read_run(directory)


def test_reader_rejects_concurrent_replacement_after_decoding(tmp_path, monkeypatch):
    directory = archive_fixture(tmp_path, monkeypatch)
    original = storage.artifact_json

    def replace_after_decode(path, name, **kwargs):
        result = original(path, name, **kwargs)
        if name == "presentation.json":
            (directory / "presentation.json").write_text("{}")
        return result

    monkeypatch.setattr(storage, "artifact_json", replace_after_decode)
    with pytest.raises(ValueError):
        evidence.read_run(directory)


@pytest.mark.parametrize("fault", ["cost_only", "initial", "scheduling", "coverage", "source"])
def test_controlled_comparison_requires_same_scientific_conditions_and_coverage(
    tmp_path, monkeypatch, fault
):
    view = evidence.read_run(archive_fixture(tmp_path, monkeypatch))
    other = copy.deepcopy(view)
    if fault == "cost_only":
        other["request"]["effective"]["scratch"]["costs"]["lateral"] = 1
        other["request"]["capture"]["resolved"]["effective"]["scratch"]["costs"]["lateral"] = 1
        other["request"]["capture"]["resolved"]["configuration"]["costs"]["lateral"] = 1
    elif fault == "initial":
        other["request"]["capture"]["resolved"]["initial_state"][4] = 2
    elif fault == "scheduling":
        other["request"]["capture"]["resolved"]["simulation"]["codriver_delay"] = 0.01
    elif fault == "source":
        other["request"]["capture"]["source_sha256"] = {"changed": "source"}
    else:
        other["summary"]["coverage_completed"] = False
    decision = analysis.comparison(view, other)
    assert decision["classification"].startswith(
        "Controlled" if fault == "cost_only" else "Noncontrolled"
    )


def test_v1_and_v2_share_the_actual_execution_lease():
    from tools.apex_workbench import jobs

    lease = jobs.execution_lock()
    try:
        code = "from tools.apex_workbench import jobs; jobs.execution_lock()"
        result = subprocess.run(
            [sys.executable, "-B", "-c", code],
            capture_output=True,
            text=True,
            cwd=config.ROOT,
            timeout=10,
        )
        assert result.returncode != 0 and "Another Workbench experiment" in result.stderr
    finally:
        lease.close()


@pytest.mark.parametrize(
    "failure,outcome",
    [("supervisor_sigkill", "interrupted"), ("cancel", "cancelled"), ("output", "failed")],
)
def test_live_guard_loss_cancel_and_resource_retains_lease_until_worker_exit(
    tmp_path, failure, outcome
):
    """Real metadata-only helper processes exercise the monitor, not an optimizer or plant.

    Production worker_guard separately validates the module/role/run command prefix before
    passing a supervisor identity to this same monitor. Helpers use their actual birth/command.
    """
    import time

    from tools.apex_workbench import jobs, lifecycle

    owner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    helper = None
    lease = jobs.execution_lock()
    try:
        identity = lifecycle.identity(owner.pid, "lap-supervisor", tmp_path)
        storage.write_json(tmp_path / "supervisor.json", identity)
        limits = config.limits(config.defaults())
        if failure == "output":
            limits["sampled_output_bytes"] = 1
        code = """
import sys, threading, time
from pathlib import Path
from tools.apex_workbench.lap.execution import monitor
from tools.apex_workbench import storage
d=Path(sys.argv[1]); limits=__import__('json').loads(sys.argv[2])
(d/'ready').touch()
monitor(d,storage.read_json(d/'supervisor.json'),limits,threading.Event(),time.monotonic())
"""
        helper = subprocess.Popen(
            [sys.executable, "-B", "-c", code, str(tmp_path), json.dumps(limits)],
            cwd=config.ROOT,
            pass_fds=(lease.fileno(),),
        )
        lease.close()
        deadline = time.monotonic() + 5
        while not (tmp_path / "ready").exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert (tmp_path / "ready").exists()
        if failure != "output":
            with pytest.raises(RuntimeError):
                jobs.execution_lock()
        if failure == "supervisor_sigkill":
            owner.kill()
            owner.wait(timeout=3)
        elif failure == "cancel":
            (tmp_path / "cancel.request").touch()
        assert helper.wait(timeout=5) == 3
        assert storage.read_json(tmp_path / "worker_abort.json")["outcome"] == outcome
        released = jobs.execution_lock()
        released.close()
    finally:
        if not lease.closed:
            lease.close()
        for process in (helper, owner):
            if process and process.poll() is None:
                process.kill()
                process.wait(timeout=3)
