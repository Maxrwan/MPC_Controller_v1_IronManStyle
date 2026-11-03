"""Evidence integrity and administrative-limit checks; no controller construction."""

import json

import numpy as np
import pytest
from preintegration.evidence import assess, distribution, inventory, reconcile, write
from preintegration.launch import violated


def test_nested_numpy_json_and_missing_vs_null(tmp_path):
    path = tmp_path / "native.json"
    write(path, {"nested": {"flag": np.bool_(False)}, "x": np.array([1, 2]), "null": None})
    data = json.loads(path.read_text())
    assert data == {"nested": {"flag": False}, "x": [1, 2], "null": None}
    assert "absent" not in data
    with pytest.raises(ValueError):
        write(tmp_path / "invalid.json", {"x": float("nan")})
    with pytest.raises(TypeError):
        write(tmp_path / "opaque.json", {"x": object()})
    assert set(inventory(tmp_path)) == {"native.json"}


def test_failed_censored_missing_observations_are_not_success():
    for code, worker, guard in [
        (1, {"complete": True}, None),
        (0, None, None),
        (0, {"complete": False}, None),
        (0, {"complete": True}, "WALL_LIMIT"),
    ]:
        assert not reconcile(code, worker, guard)
    assert reconcile(0, {"complete": True}, None)
    empty = distribution([])
    assert empty["count"] == 0 and empty["median"] is None
    assert assess({"plans": [], "failure": "injected"}, [])["classification"] == (
        "INSUFFICIENT_EVIDENCE"
    )
    assert distribution([1, 2, 3, 4])["p95"] == 4


@pytest.mark.parametrize(
    "observed,reason",
    [
        ((60, 0, 0, 0), "WALL_LIMIT"),
        ((0, 30, 0, 0), "CPU_LIMIT"),
        ((0, 0, 2 * 1024**3, 0), "SAMPLED_RSS_LIMIT"),
        ((0, 0, None, 128 * 1024**2), "OUTPUT_LIMIT"),
    ],
)
def test_resource_boundaries(observed, reason):
    assert violated(*observed) == reason
    assert violated(1, 1, None, 1) is None


def test_wall_watchdog_is_not_armed_by_import_and_preserves_timeout(monkeypatch):
    from preintegration import launch

    monkeypatch.setattr(launch, "_owned_worker", None)
    with pytest.raises(TimeoutError, match="wall budget"):
        launch.wall_alarm(None, None)


@pytest.mark.parametrize("limit", [None, "WALL_LIMIT"])
def test_supervisor_owned_lifecycle_and_duplicate_claim_without_controller(
    tmp_path, monkeypatch, limit
):
    """Observable supervisor behavior with an explicitly stubbed worker; no real launch."""
    import time
    from types import SimpleNamespace

    import psutil
    from preintegration import launch

    monkeypatch.setattr(launch, "ROOT", tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.setattr(launch, "WORK", work)
    monkeypatch.setattr(launch, "START", time.monotonic())
    monkeypatch.setattr(launch, "DEADLINE", time.monotonic() + 60)
    monkeypatch.setattr(launch.signal, "signal", lambda *a: None)
    monkeypatch.setattr(launch.signal, "setitimer", lambda *a: None)
    monkeypatch.setattr(launch, "runtime_hashes", lambda: {"fixture": "SOFTWARE_STUB"})
    monkeypatch.setattr(
        launch,
        "bootstrap",
        lambda *a: SimpleNamespace(source={"head": "STUB"}, environment={}, native={}),
    )
    monkeypatch.setattr(launch, "admit_gate", lambda *a: None)
    monkeypatch.setattr(launch, "git", lambda *a: "")
    monkeypatch.setattr(psutil, "process_iter", lambda *a: [])
    monkeypatch.setattr(psutil, "disk_usage", lambda *a: SimpleNamespace(free=2 * 1024**3))

    class ObservedProcess:
        pid = 987654321

        def parents(self):
            return []

        def create_time(self):
            return 1

        def children(self, **kwargs):
            return []

        def cpu_times(self):
            return SimpleNamespace(user=0.01, system=0.01)

        def memory_info(self):
            return SimpleNamespace(rss=1024)

        def num_threads(self):
            return 1

    monkeypatch.setattr(psutil, "Process", lambda *a: ObservedProcess())
    launches, kills = [], []

    class StubWorker:
        pid = ObservedProcess.pid
        polls = 0

        def poll(self):
            self.polls += 1
            return None if self.polls == 1 else (0 if limit is None else -9)

        def wait(self, **kw):
            return 0 if limit is None else -9

    def start(command, **kwargs):
        launches.append(command)
        write(Path(command[-1]) / "worker-result.json", {"complete": True})
        return StubWorker()

    from pathlib import Path

    monkeypatch.setattr(launch.subprocess, "Popen", start)
    monkeypatch.setattr(launch.os, "killpg", lambda pid, sig: kills.append(pid))
    monkeypatch.setattr(launch, "violated", lambda *a: limit)
    first = tmp_path / "results/preintegration/w1/first"
    code = launch.main(["--case", "G0", "--output", str(first)])
    result = json.loads((first / "supervisor-result.json").read_text())
    assert result["complete"] is (limit is None)
    assert code == (0 if limit is None else 1)
    assert bool(kills) is (limit is not None)
    assert not json.loads((work / "MEASURED_ACTIVE").read_text())["active"]
    assert (first / "index.json").is_file() and (work / "attempts/G0.json").is_file()
    second = tmp_path / "results/preintegration/w1/second"
    assert launch.main(["--case", "G0", "--output", str(second)]) == 1
    assert len(launches) == 1


def test_missing_timing_is_retained_as_null_not_zero():
    result = distribution([0.01, None, 0.03])
    assert result["count"] == 2 and result["missing_count"] == 1
    assert result["samples_s"] == [0.01, None, 0.03]


def test_owned_inactive_fixture_guard_does_not_hide_foreign_guard(tmp_path):
    from preintegration.launch import guard_records

    owned = tmp_path / "owned"
    owned.mkdir()
    inactive = owned / "MEASURED_ACTIVE"
    foreign = tmp_path / "D3_ACTIVE"
    write(inactive, {"active": False})
    write(foreign, {"active": False})
    records = guard_records([inactive, foreign], owned)
    assert records[0]["blocking"] is False
    assert records[1]["blocking"] is True
    assert inactive.is_file() and foreign.is_file()
