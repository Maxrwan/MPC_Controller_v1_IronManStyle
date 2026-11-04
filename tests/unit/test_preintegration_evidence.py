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


@pytest.mark.parametrize(
    "limit,late",
    [
        (None, None),
        ("WALL_LIMIT", None),
        (None, "supervisor-result.json"),
        (None, "index.json"),
        (None, "G0-result.json"),
        (None, "late-limit"),
    ],
)
def test_supervisor_owned_lifecycle_and_duplicate_claim_without_controller(
    tmp_path, monkeypatch, limit, late
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
    monkeypatch.setattr(launch.os, "kill", lambda pid, sig: kills.append(pid))

    def limits(*args):
        return (
            "WALL_LIMIT"
            if late == "late-limit" and (work / "attempts/G0-result.json").exists()
            else limit
        )

    monkeypatch.setattr(launch, "violated", limits)

    def final_write(path, data):
        if Path(path).name == late:
            raise TimeoutError("Controlled late timeout during final serialization")
        write(path, data)

    monkeypatch.setattr(launch, "write", final_write)
    first = tmp_path / "results/preintegration/w1/first"
    if late and late != "late-limit":
        with pytest.raises(TimeoutError):
            launch.main(["--case", "G0", "--output", str(first)])
        assert len(launches) == 1
        assert (work / "attempts/G0.json").exists()
        monkeypatch.setattr(launch, "write", write)
        assert not launch.witness_exit("G0", first, 1, 60.1, 0.1)["complete"]
        return
    code = launch.main(["--case", "G0", "--output", str(first)])
    result = json.loads((first / "supervisor-result.json").read_text())
    assert result["complete"] is (limit is None)
    assert result["samples"][0]["rss_bytes"] == 3072
    assert result["samples"][0]["supervisor_rss_bytes"] == 1024
    assert json.loads((first / "worker-start.json").read_text())["pid"] == 987654321
    assert code == (0 if limit is None and late is None else 1)
    assert bool(kills) is (limit is not None)
    assert not json.loads((work / "MEASURED_ACTIVE").read_text())["active"]
    assert (first / "index.json").is_file() and (work / "attempts/G0.json").is_file()
    # A PASS file is provisional: a late failure is rejected by its exit witness.
    receipt = launch.witness_exit("G0", first, code, 1, 0.1)
    assert receipt["complete"] is (limit is None and late is None)
    second = tmp_path / "results/preintegration/w1/second"
    assert launch.main(["--case", "G0", "--output", str(second)]) == 1
    assert len(launches) == 1


def test_native_tracker_and_enclosing_runner_populations_remain_distinct():
    raw = {"controls": [{"total_time": 0.009, "kernel_time": 0.001}]}
    boundary = [
        {"operation": "propose", "native_seconds": 0.001, "wall_seconds": 0.005},
        {"operation": "propose", "native_seconds": None, "wall_seconds": 0.006},
    ]
    report = assess(raw, boundary)
    assert report["native_tracker"]["samples_s"] == [0.001, None]
    assert report["native_tracker"]["missing_count"] == 1
    assert report["runner_control_envelope"]["samples_s"] == [0.009]
    assert report["boundary_envelopes"] == boundary


@pytest.mark.parametrize("failure", ["write", "timeout", "cpu", "output"])
def test_witness_publication_itself_fails_closed(tmp_path, monkeypatch, failure):
    from preintegration import launch

    work = tmp_path / "work"
    (work / "attempts").mkdir(parents=True)
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(launch, "WORK", work)
    monkeypatch.setattr(launch, "git", lambda *a: "STUB")
    write(output / "supervisor-result.json", {"complete": True, "output": str(output)})
    write(output / "index.json", inventory(output))
    write(
        work / "attempts/G0-result.json",
        {
            "complete": True,
            "output": str(output),
            "index_sha256": launch.sha(output / "index.json"),
        },
    )
    receipt_path = work / "attempts/G0-exit.json"

    def late_write(path, data):
        write(path, data)
        if failure == "write":
            raise OSError("Controlled write failure after atomic publication")

    monkeypatch.setattr(launch, "write", late_write)
    if failure == "write":
        with pytest.raises(OSError):
            launch.witness_exit("G0", output, 0, 1, 1)
        assert not receipt_path.exists()
        assert receipt_path.with_name(receipt_path.name + ".unadmitted").exists()
    else:
        clock = iter([0, 61] if failure == "timeout" else [0, 0])
        monkeypatch.setattr(launch.time, "monotonic", lambda: next(clock))
        cpu = iter([0, 31] if failure == "cpu" else [0, 0])
        monkeypatch.setattr(launch.time, "process_time", lambda: next(cpu))
        if failure == "output":
            monkeypatch.setattr(launch, "output_bytes", lambda *a: 128 * 1024**2)
        assert not launch.witness_exit("G0", output, 0, 1, 1)["complete"]
        assert not json.loads(receipt_path.read_text())["complete"]


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


def test_successor_requires_reviewed_clean_source_and_witnessed_final_inventory(
    tmp_path, monkeypatch
):
    from preintegration import launch

    work = tmp_path / "work"
    (work / "attempts").mkdir(parents=True)
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(launch, "WORK", work)
    monkeypatch.setattr(launch, "_driver_child", True)
    monkeypatch.setattr(launch, "_predecessors", {})
    monkeypatch.setattr(
        launch, "git", lambda root, *args: "SOURCE" if args[0] == "rev-parse" else ""
    )
    report = work / "review.json"
    write(report, {"verdict": "PASS", "producer": "SOURCE"})
    hashes = {"fixture": "literal"}
    gate = {
        "passed": True,
        "hashes": hashes,
        "producer": "SOURCE",
        "independent_review": {
            "verdict": "PASS",
            "producer": "SOURCE",
            "report": str(report),
            "sha256": launch.sha(report),
        },
    }
    write(work / "software-gate.json", gate)
    launch.admit_gate("G0", hashes)
    # A valid inner PASS plus index/ledger is deliberately insufficient.
    result = {"complete": True, "output": str(output), "hashes": hashes}
    write(output / "supervisor-result.json", result)
    write(output / "index.json", inventory(output))
    write(
        work / "attempts/G0-result.json",
        {**result, "index_sha256": launch.sha(output / "index.json")},
    )
    with pytest.raises(FileNotFoundError):
        launch.admit_gate("G1", hashes)
    launch.witness_exit("G0", output, 0, 1, 1)
    with pytest.raises(ValueError, match="live driver"):
        launch.admit_gate("G1", hashes)
    launch._predecessors["G0"] = launch.sha(work / "attempts/G0-exit.json")
    launch.admit_gate("G1", hashes)
    write(output / "supervisor-result.json", {**result, "complete": False})
    with pytest.raises(ValueError, match="raw member changed"):
        launch.admit_gate("G1", hashes)
    monkeypatch.setattr(
        launch, "git", lambda root, *args: "SOURCE" if args[0] == "rev-parse" else " M dirty.py"
    )
    with pytest.raises(ValueError, match="clean committed"):
        launch.admit_gate("G0", hashes)


def test_terminated_witness_cannot_restore_live_successor_grant(tmp_path, monkeypatch):
    import os

    from preintegration import launch

    work = tmp_path / "work"
    (work / "attempts").mkdir(parents=True)
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(launch, "WORK", work)
    monkeypatch.setattr(launch, "_driver_child", True)
    monkeypatch.setattr(launch, "_predecessors", {})
    monkeypatch.setattr(
        launch, "git", lambda root, *args: "SOURCE" if args[0] == "rev-parse" else ""
    )
    review = work / "review.json"
    write(review, {"verdict": "PASS"})
    hashes = {"fixture": "literal"}
    write(
        work / "software-gate.json",
        {
            "passed": True,
            "hashes": hashes,
            "producer": "SOURCE",
            "independent_review": {
                "verdict": "PASS",
                "producer": "SOURCE",
                "report": str(review),
                "sha256": launch.sha(review),
            },
        },
    )
    result = {"complete": True, "output": str(output), "hashes": hashes}
    write(output / "supervisor-result.json", result)
    write(output / "index.json", inventory(output))
    write(
        work / "attempts/G0-result.json",
        {**result, "index_sha256": launch.sha(output / "index.json")},
    )
    pid = os.fork()
    if pid == 0:

        def terminate(path, data):
            write(path, data)
            if path.name == "G0-exit.json":
                os._exit(137)

        launch.write = terminate
        launch.witness_exit("G0", output, 0, 1, 1)
        os._exit(0)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 137
    assert json.loads((work / "attempts/G0-exit.json").read_text())["complete"]
    with pytest.raises(ValueError, match="live driver"):
        launch.admit_gate("G1", hashes)


@pytest.mark.parametrize(
    "failed_case,expected",
    [(None, ["G0", "G1", "measured-smoke"]), ("G0", ["G0"]), ("G1", ["G0", "G1"])],
)
def test_live_conditional_sequence_uses_kernel_exit_and_stops_without_retry(
    tmp_path, monkeypatch, failed_case, expected
):
    from pathlib import Path

    from preintegration import launch

    work = tmp_path / "work"
    (work / "attempts").mkdir(parents=True)
    monkeypatch.setattr(launch, "WORK", work)
    monkeypatch.setattr(launch, "_predecessors", {})
    monkeypatch.setattr(launch, "git", lambda *a: "SOURCE")

    def stub_main(argv):
        case, output = argv[1], Path(argv[3])
        assert launch._driver_child
        for preceding in launch.CASES[: launch.CASES.index(case)]:
            assert preceding in launch._predecessors
        output.mkdir(parents=True)
        with (work / "attempts" / (case + ".json")).open("x") as stream:
            json.dump({"output": str(output)}, stream)
        result = {"complete": True, "output": str(output)}
        write(output / "supervisor-result.json", result)
        write(output / "index.json", inventory(output))
        write(
            work / "attempts" / (case + "-result.json"),
            {**result, "index_sha256": launch.sha(output / "index.json")},
        )
        return 1 if case == failed_case else 0

    monkeypatch.setattr(launch, "main", stub_main)
    code = launch.execute(
        ["--case", "conditional-sequence", "--output", str(tmp_path / "sequence")]
    )
    assert code == (0 if failed_case is None else 1)
    assert [c for c in launch.CASES if (work / "attempts" / (c + ".json")).exists()] == expected
    assert set(launch._predecessors) == set(expected) - {failed_case}
