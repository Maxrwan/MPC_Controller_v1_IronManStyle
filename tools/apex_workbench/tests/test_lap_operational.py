"""Policy/metadata fixtures only. Genuine execution is separately gated after independent PASS."""

import copy
import hashlib
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs, storage
from tools.apex_workbench.lap import capacity, config, evidence, execution, operational

ORIGINAL_OUTPUT = config.OUTPUT
ORIGINAL_RUNS = config.RUNS
SOURCE = "a" * 40


@pytest.mark.parametrize(
    "fault",
    [
        "duration",
        "full_duration",
        "field",
        "weight_nan",
        "weight_bool",
        "weight_string",
        "weight_zero",
    ],
)
def test_unsupported_values_never_reach_execution(fault):
    value = config.defaults("full_lap" if fault == "full_duration" else "extended", 5)
    if fault in {"duration", "full_duration"}:
        value["maximum_simulation_s"] = 6
    elif fault == "field":
        value["scratch"]["horizon"] = 4
    else:
        value["scratch"]["costs"]["lateral"] = {
            "weight_nan": float("nan"),
            "weight_bool": True,
            "weight_string": "3",
            "weight_zero": 0,
        }[fault]
    with pytest.raises(ValueError):
        config.validate(value)


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    """Real installers and byte checks, isolated writes; Git candidate is a software-test double."""
    before = (ORIGINAL_OUTPUT / "access.json").read_bytes()
    assert hashlib.sha256(before).hexdigest() == operational.HISTORY_SHA
    (tmp_path / "access.json").write_bytes(before)
    for run_id in operational.HISTORY.values():
        shutil.copytree(ORIGINAL_RUNS / run_id, tmp_path / "runs" / run_id)
    old_git = config.v1.frozen.git

    def safe(path):
        path = Path(path).absolute()
        if path.is_relative_to(tmp_path):
            return config.v1.frozen.safe(path, tmp_path)
        # Immutable original review/authority references may be read only.
        return config.v1.frozen.safe(path, ORIGINAL_OUTPUT)

    def git(*args):
        if args[0] == "show" and args[1].startswith(SOURCE + ":"):
            return (config.ROOT / args[1].split(":", 1)[1]).read_bytes()
        return old_git(*args)

    monkeypatch.setattr(config, "OUTPUT", tmp_path)
    monkeypatch.setattr(config, "RUNS", tmp_path / "runs")
    monkeypatch.setattr(config, "safe", safe)
    monkeypatch.setattr(config.v1.frozen, "git", git)
    monkeypatch.setattr(jobs, "LEASE_ROOT", tmp_path / "lease")
    review = tmp_path / "test_review.json"
    storage.write_json(review, {"outcome": "PASS", "candidate": SOURCE})
    policy = operational.prepare(review, tmp_path / "operational")
    yield policy
    assert (ORIGINAL_OUTPUT / "access.json").read_bytes() == before


def metadata_smoke(policy, *, run_id="metadata_smoke_NOT_SCIENTIFIC_EXECUTION", failed=False):
    """Serialize a tiny nonphysical fixture; never a producer run, benchmark or qualification."""
    value = config.defaults("extended", 5)
    if policy["stage"] == "reviewed-smoke":
        config.access(value, consume=run_id)
    directory = config.RUNS / run_id
    directory.mkdir()
    storage.write_json(directory / "admission.json", {"policy": policy, "host": {"status": "PASS"}})
    resolved = {
        "effective": value,
        "configuration": {"costs": value["scratch"]["costs"]},
        "simulation": {"duration": 5, "laps": 2},
        "track_length_m": 100,
        "initial_state": [1, 0, 0, 0, 1, 0],
    }
    environment = {"SOFTWARE_SERIALIZATION_FIXTURE": True}
    request = {
        "adapter": "nmpc_lap_v2",
        "run_id": run_id,
        "effective": value,
        "capture": {
            "resolved": resolved,
            "environment": environment,
            "source_sha256": config.v1.frozen.source_hashes(),
            "producer_sha256": config.producers(),
        },
        "provenance": {
            "git_revision": SOURCE,
            "review_sha256": policy["review_sha256"],
            "authority_sha256": policy["authority_sha256"],
            "limits": config.limits(value),
            "access_stage": policy["stage"],
            "admission_sha256": storage.sha256(directory / "admission.json"),
        },
    }
    storage.write_json(directory / "request.json", request)
    storage.write_json(
        directory / "pre_identity.json", {"resolved": resolved, "environment": environment}
    )
    storage.write_json(
        directory / "post_identity.json",
        {"raw_available": True, "source_unchanged": True, "environment_unchanged": True},
    )
    states = [
        {
            "time": t,
            "vx": 1,
            "vy": 0,
            "r": 0,
            "s_abs": 1,
            "e_y": 0,
            "e_psi": 0,
            "delta": 0,
            "a_cmd": 0,
        }
        for t in (0, 2.5, 4.995)
    ]
    evidence.store_raw(
        directory,
        {
            "states": states,
            "controls": [],
            "plans": [],
            "packets": [],
            "lap_times": [],
            "failure": None,
            "end_time": 5,
            "stop_reason": "duration",
        },
    )
    chunks = evidence.Chunks(directory / "derived")
    for state in states:
        chunks.append("states", {"time": state["time"], "racing_error_y_m": 0})
    chunks.close()
    storage.write_json(directory / "presentation.json", {"state_rows": len(states)})
    for name in ("worker.json", "supervisor.json"):
        storage.write_json(directory / name, {"SOFTWARE_SERIALIZATION_FIXTURE": True})
    for name in ("stdout.log", "stderr.log"):
        (directory / name).write_text("software fixture, no scientific execution\n")
    if not failed:
        summary = {
            "coverage_completed": True,
            "failure": None,
            "stop_reason": "duration",
            "native_end_time_s": 5,
        }
        for name in ("summary.json", "worker_result.json"):
            storage.write_json(directory / name, summary)
    execution.finalize(
        directory, "failed" if failed else "completed", returncode=2 if failed else 0
    )
    return directory


@pytest.fixture
def accepted(prepared):
    metadata_smoke(prepared)
    return operational.activate()


def test_conditional_smoke_is_once_only_and_does_not_reopen_research(prepared):
    historical = Path(operational.authority(prepared)["historical_policy"]["path"]).read_bytes()
    for value in [config.defaults(), config.defaults("extended", 20), config.defaults("full_lap")]:
        with pytest.raises(ValueError, match="baseline5s"):
            config.access(value)
    value = config.defaults("extended", 5)
    config.access(value, consume="metadata-smoke")
    assert config.access(value, run_id="metadata-smoke")["used"] == operational.HISTORY
    with pytest.raises((ValueError, FileExistsError)):
        config.access(value, consume="retry")
    with pytest.raises(ValueError):
        config.access(value, run_id="other")
    assert (
        Path(operational.authority(prepared)["historical_policy"]["path"]).read_bytes()
        == historical
    )


def test_interactive_all_modes_and_costs_do_not_mutate_slots(accepted):
    before = (config.OUTPUT / "access.json").read_bytes()
    for value in [
        *[config.defaults("extended", n) for n in (5, 10, 20)],
        config.defaults("full_lap"),
    ]:
        for field in value["scratch"]["costs"]:
            value["scratch"]["costs"][field] *= 1.1
        assert config.access(value, consume="metadata-only-user-id")["used"] == operational.HISTORY
    assert (config.OUTPUT / "access.json").read_bytes() == before
    assert accepted["stage"] == "accepted-interactive"


@pytest.mark.parametrize("fault", ["source", "primary", "history", "review", "smoke", "slots"])
def test_interactive_binding_changes_fail_closed(accepted, monkeypatch, fault):
    policy = copy.deepcopy(accepted)
    if fault == "source":
        monkeypatch.setattr(config, "producers", lambda: {})
    elif fault == "primary":
        Path(policy["authority_record"]).write_text("{}")
    elif fault == "history":
        Path(operational.authority(policy)["historical_policy"]["path"]).write_text("{}")
    elif fault == "review":
        Path(policy["review_record"]).write_text("{}")
    elif fault == "smoke":
        (config.RUNS / "metadata_smoke_NOT_SCIENTIFIC_EXECUTION" / "summary.json").unlink()
    else:
        policy["used"] = {}
        storage.write_json(config.OUTPUT / "access.json", policy)
    with pytest.raises((ValueError, OSError)):
        config.access(config.defaults("extended", 5))


def test_failed_smoke_cannot_activate(prepared):
    metadata_smoke(prepared, failed=True)
    with pytest.raises((ValueError, OSError)):
        operational.activate()
    assert storage.read_json(config.OUTPUT / "access.json")["stage"] == "reviewed-smoke"


@pytest.mark.parametrize(
    "command,conflict",
    [
        (["python", "-m", "streamlit", "run", "app.py"], False),
        (["python", "reference_view.py", "--serve"], False),
        (["python", "-m", execution.MODULE, "worker", "run-id"], True),
        (["python", "nmpc_scratch_worker.py"], True),
        (["pytest"], True),
    ],
)
def test_scientific_compute_is_distinct_from_presentation(command, conflict):
    assert capacity.scientific_command(command) is conflict


@pytest.mark.parametrize(
    "memory,disk,processes,expected",
    [
        (2**31, 2**32, [], "PASS"),
        (1610612736, 2**32, [], "memory"),
        (2**31, 1610612736, [], "disk"),
        (2**31, 2**32, [["python", "-m", execution.MODULE, "worker"]], "worker"),
    ],
)
def test_one_fresh_capacity_observation_keeps_exact_full_lap_floors(
    monkeypatch, memory, disk, processes, expected
):
    calls = []
    monkeypatch.setattr(
        capacity.psutil,
        "virtual_memory",
        lambda: calls.append(1) or SimpleNamespace(available=memory),
    )
    monkeypatch.setattr(capacity.shutil, "disk_usage", lambda _: SimpleNamespace(free=disk))
    monkeypatch.setattr(
        capacity.psutil,
        "process_iter",
        lambda _: [SimpleNamespace(pid=123, info={"cmdline": c}) for c in processes],
    )
    monkeypatch.setattr(capacity.os, "walk", lambda *a, **k: [])
    result = capacity.observe(config.defaults("full_lap"))
    assert result["required_available_ram_bytes"] == result["required_disk_bytes"] == 1610612736
    assert len(calls) == 1
    assert (
        result["status"] == "PASS"
        if expected == "PASS"
        else expected in " ".join(result["reasons"])
    )


def test_blocked_preflight_creates_no_run_or_claim(accepted, monkeypatch):
    before = set(config.RUNS.iterdir())
    policy = (config.OUTPUT / "access.json").read_bytes()
    monkeypatch.setattr(jobs, "preflight", lambda: None)
    monkeypatch.setattr(
        capacity,
        "require",
        lambda _: (_ for _ in ()).throw(RuntimeError("Insufficient available memory")),
    )
    with pytest.raises(RuntimeError, match="memory"):
        execution.start(config.defaults("full_lap"))
    assert set(config.RUNS.iterdir()) == before
    assert (config.OUTPUT / "access.json").read_bytes() == policy


def test_shared_lease_blocks_even_an_interactively_authorized_run(accepted, monkeypatch):
    monkeypatch.setattr(jobs, "preflight", lambda: None)
    lock = jobs.execution_lock()
    try:
        with pytest.raises(RuntimeError, match="running"):
            execution.start(config.defaults("extended", 5))
    finally:
        lock.close()


def test_failed_probe_does_not_lock_lab_and_capture_preserves_weights(accepted, monkeypatch):
    from tools.apex_workbench.lap import worker

    monkeypatch.setattr(jobs, "preflight", lambda: None)
    calls = []
    monkeypatch.setattr(capacity, "require", lambda _: calls.append(1) or {"status": "PASS"})
    monkeypatch.setattr(
        worker, "probe", lambda _: (_ for _ in ()).throw(RuntimeError("metadata probe failure"))
    )
    with pytest.raises(RuntimeError, match="metadata probe failure"):
        execution.start(config.defaults("extended", 5))
    failed = [p for p in config.RUNS.iterdir() if (p / "admission_error.txt").exists()]
    assert len(failed) == 1 and storage.read_status(failed[0])["state"] == "failed"
    value = config.defaults("extended", 5)
    value["scratch"]["costs"]["lateral"] = 3.0
    monkeypatch.setattr(
        worker,
        "probe",
        lambda v: {"resolved": {"effective": v}, "environment": {"software_fixture": True}},
    )
    real_popen = execution.subprocess.Popen

    def metadata_launch(command, *args, **kwargs):
        if command[1:3] == ["-m", execution.MODULE]:
            return None  # Never launch the scientific supervisor; preserve ordinary Git reads.
        return real_popen(command, *args, **kwargs)

    monkeypatch.setattr(execution.subprocess, "Popen", metadata_launch)
    directory = execution.start(value)
    request = storage.read_json(directory / "request.json")
    assert request["capture"]["resolved"]["effective"] == value
    assert request["provenance"]["limits"] == config.PROFILE["limits"]["extended"]
    assert storage.read_json(directory / "admission.json")["host"] == {"status": "PASS"}
    assert len(calls) == 2 and config.access(value)["used"] == operational.HISTORY


def test_new_failed_native_run_is_read_only_without_poisoning_acceptance(accepted):
    directory = metadata_smoke(
        accepted, run_id="metadata_failed_NOT_SCIENTIFIC_EXECUTION", failed=True
    )
    view = evidence.read_run(directory, recover_failed=True)
    assert view["status"]["state"] == "failed" and "summary" not in view
    assert view["recovery"]["mode"] == "failed-native-read-only"
    assert config.access(config.defaults("extended", 20))["stage"] == "accepted-interactive"


@pytest.mark.parametrize("duration", [5, 10, 20, 80])
def test_normal_run_screen_admits_four_selections_without_launching(
    accepted, monkeypatch, duration
):
    def forbidden(*a, **k):
        raise AssertionError(
            "No host-capacity polling or numerical launch authorized in UI metadata check"
        )

    monkeypatch.setattr(capacity, "observe", forbidden)
    monkeypatch.setattr(execution, "start", forbidden)
    mode = "full_lap" if duration == 80 else "extended"
    app = AppTest.from_string(
        "import streamlit as st\nfrom tools.apex_workbench.lap import config,ui_views\n"
        f"st.session_state['ui_configuration']=config.defaults({mode!r},{duration})\n"
        "ui_views.run()"
    ).run(timeout=20)
    assert not app.exception and not app.error
    assert next(b for b in app.button if b.label == "Run experiment").disabled is False
