"""M0 source/configuration/accounting and disposable evidence checks; never solve/run a plant."""

import copy
import json
import os
import subprocess
from pathlib import Path

import pytest

from tools.apex_workbench import jobs, lifecycle, storage
from tools.apex_workbench import nmpc_weight_lab as lab
from tools.apex_workbench import nmpc_weight_worker as worker
from tools.apex_workbench.configuration import validate

FIXTURE_IDS = {
    "nominal": "20261103T000000000000Z_" + "a" * 32,
    "exploratory": "20261103T000000000000Z_" + "b" * 32,
}


def fixture_authority(tmp_path, monkeypatch):
    monkeypatch.setattr(
        lab,
        "ORIGINAL_ANCHORS",
        {
            name: storage.sha256(tmp_path / name)
            for name in ("BLOCKED.json", "claims/nominal.json", "software_gate.json")
        },
    )


@pytest.fixture(scope="session")
def preflights():
    result = {p: lab.probe(p, checks=True) for p in lab.PRESETS}
    return result


def test_actual_frozen_imports_dependencies_and_algebra(preflights):
    expected = lab.source_hashes()
    for report in preflights.values():
        assert report["software_checks"] == {
            "stage_unit_error_tracking": [409.0, 209.0],
            "terminal_same_input": 8.0,
            "bounds_identical": True,
            "optimizer_solves": 0,
            "plant_steps": 0,
            "fixture": "algebraic unit-error cost test, not a physical trajectory",
        }
        assert report["native"]["mode_name"] == "single" and report["native"]["set_status"] == 0
        assert report["environment"]["packages"]["casadi"]["version"] == "3.8.1"
        assert report["environment"]["packages"]["numpy"]["installed_files"] > 0
        modules = report["imports"]
        for name, identity in modules.items():
            if name.split(".")[0] not in worker.PREFIXES:
                continue
            if "path" in identity:
                path = Path(identity["path"])
                assert path.is_relative_to(lab.RUNTIME)
                assert expected[str(path.relative_to(lab.RUNTIME))] == identity["sha256"]
            else:
                assert all(Path(p).is_relative_to(lab.RUNTIME) for p in identity["namespace_paths"])
        assert "apex.control.mpc.controller" in modules
        assert "apex.simulation.asynchronous" in modules
        assert modules["numpy"]["path"] != str(lab.ROOT / "src/numpy.py")


def test_exact_only_treatment_and_original_scenario(preflights):
    a, b = [copy.deepcopy(preflights[p]["resolved"]) for p in lab.PRESETS]
    assert a["stage_coefficients"] == [4, 4, 1, 200, 200] and b["stage_coefficients"] == [
        4,
        4,
        1,
        100,
        100,
    ]
    assert (
        a["configuration"]["costs"]["lateral"] == 2.0
        and b["configuration"]["costs"]["lateral"] == 1.0
    )
    for resolved in (a, b):
        assert resolved["configuration"]["horizon"] == 8 and resolved["configuration"]["dt"] == 0.1
        assert (
            resolved["configuration"]["substeps"] == 4
            and resolved["configuration"]["costs"]["terminal"] == 1
        )
        assert (
            resolved["simulation"]["duration"] == 2.0
            and resolved["simulation"]["committed_prefix_prediction"] is False
        )
        assert resolved["timing"]["planner_pattern_s"] == [0.035, 0.055, 0.045, 0.025]
        assert resolved["timing"]["codriver_delay_s"] == 0.005
        assert resolved["initial_state"] == [
            5.253846582838669,
            0.0,
            0.9966576677921577,
            0.034598592705642695,
            1.0,
            -0.11268618155631815,
        ]
        assert resolved["warm_start"] is True
        resolved.pop("preset")
        resolved.pop("stage_coefficients")
        resolved["configuration"]["costs"].pop("lateral")
    assert a == b


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"preset": "other"},
        {"preset": []},
        {"preset": "nominal", "lateral": 3},
        {"preset": "../nominal"},
    ],
)
def test_unsupported_configuration_is_rejected(values):
    with pytest.raises(ValueError):
        validate(lab.ADAPTER, values)


def test_import_guards_reject_other_checkout_namespace_and_dependency(tmp_path):
    path = tmp_path / "src/apex/example.py"
    path.parent.mkdir(parents=True)
    path.write_text("value=1\n")
    expected = {"src/apex/example.py": storage.sha256(path)}
    guard = worker.FrozenImports(tmp_path, expected)
    guard.check(path)
    with pytest.raises(ImportError):
        guard.check(lab.ROOT / "src/apex/control/mpc/controller.py")
    with pytest.raises(ImportError):
        guard.namespace([str(path.parent), str(lab.ROOT / "src/apex")])
    with pytest.raises(ImportError):
        guard.namespace([str(lab.ROOT / "src/apex")])
    with pytest.raises(ImportError):
        guard.check_dependency(path)
    path.write_text("value=2\n")
    with pytest.raises(ImportError):
        guard.check(path)


def test_runtime_change_and_missing_file_reject_disposable_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "RUNTIME", tmp_path)
    path = tmp_path / "example.py"
    path.write_text("original\n")
    expected = {"example.py": storage.sha256(path)}
    lab.verify_runtime(tmp_path, expected)
    path.write_text("altered!\n")
    with pytest.raises(ValueError):
        lab.verify_runtime(tmp_path, expected)
    path.unlink()
    with pytest.raises(ValueError):
        lab.verify_runtime(tmp_path, expected)


def test_one_attempt_claim_each_and_no_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(lab, "verify_gate", lambda **kwargs: {"run_ids": FIXTURE_IDS})
    authority = lab.authority_root()
    authority.mkdir(parents=True)
    storage.write_json(authority / "authorization.json", {"software_fixture": True})
    lab.claim("nominal", FIXTURE_IDS["nominal"])
    with pytest.raises(FileExistsError):
        lab.claim("nominal", FIXTURE_IDS["nominal"])
    with pytest.raises(ValueError):
        lab.claim("nominal", "unreserved_identity")
    with pytest.raises(FileNotFoundError):
        lab.claim("exploratory", FIXTURE_IDS["exploratory"])
    with pytest.raises(ValueError):
        lab.claim("../outside", "bad")
    assert len(list((authority / "claims").glob("*.json"))) == 1


def test_objective_accounting_never_carries_stale_success_to_failure():
    event = {
        "plan_id": 3,
        "solver_attempted": True,
        "success": True,
        "release_time": 0.3,
        "status": "Solve_Succeeded",
        "objective_components": {"state_tracking": 2.0, "total": 2.0},
    }
    prediction = {"states": [[1, 0, 0, 0, 0, 0]], "controls": [[0, 0]]}
    observed = worker.solution_observation(event, prediction)
    assert (
        observed["plan_id"] == 3
        and observed["objective_components"] == event["objective_components"]
    )
    assert observed["prediction"] == prediction and "not native IPOPT" in observed["accounting"]
    for failed in [
        dict(event, plan_id=4, success=False),
        dict(event, plan_id=5, solver_attempted=False),
    ]:
        result = worker.solution_observation(failed, prediction)
        assert result["objective_components"] is None and "prediction" not in result


def test_native_tracker_proposal_is_not_relabeled_as_applied():
    diagnostics = {"desired": [0.02, 0.0], "error": [0, 0, 0, 0, 0, 0]}
    record = worker.request_observation(0.1, 3, [0.01, 0.0], diagnostics)
    assert record["time"] == 0.1 and record["plan_id"] == 3 and record["proposed"] == [0.01, 0.0]
    assert record["diagnostics"] is diagnostics
    assert "not an applied command" in record["availability"]
    assert "application_time" not in record and "applied" not in record


def test_native_early_stop_is_distinct_from_requested_duration_completion():
    assert lab.coverage({"end_time": 2.0, "stop_reason": "duration", "failure": None})[
        "requested_duration_completed"
    ]
    assert not lab.coverage(
        {"end_time": 0.8, "stop_reason": "fallback_outside_validity_domain", "failure": None}
    )["requested_duration_completed"]
    assert lab.coverage({"failure": "source/native failure"})["native_end_time_s"] is None


def test_shared_lease_and_actual_pid_birth_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "LEASE_ROOT", tmp_path)
    with jobs.execution_lock() as lease:
        assert os.fstat(lease.fileno()).st_ino == (tmp_path / ".execution.lock").stat().st_ino
        with pytest.raises(RuntimeError):
            jobs.execution_lock()
    record = lifecycle.identity(os.getpid(), "jobs", tmp_path)
    assert lifecycle.owned_process(record, "jobs", tmp_path) is not None
    assert (
        lifecycle.owned_process(dict(record, created=record["created"] - 1), "jobs", tmp_path)
        is None
    )
    assert lifecycle.owned_process(record, "jobs", tmp_path / "other") is None


def fixture_run(tmp_path, preflights, preset="nominal"):
    root = tmp_path / "runs"
    directory = root / ("software_fixture_" + preset)
    directory.mkdir(parents=True)
    gate = {
        "status": "SOFTWARE_GATES_PASSED",
        "source": lab.SOURCE,
        "profile_sha256": lab.PROFILE_SHA,
        "adapter_sha256": lab.adapter_hashes(),
        "environment": preflights[preset]["environment"],
        "resolved_snapshots": {p: r["resolved"] for p, r in preflights.items()},
    }
    storage.write_json(tmp_path / "software_gate.json", gate)
    (tmp_path / "claims").mkdir(exist_ok=True)
    storage.write_json(
        tmp_path / "claims" / (preset + ".json"),
        {"preset": preset, "run_id": directory.name, "source": lab.SOURCE},
    )
    storage.write_json(tmp_path / "BLOCKED.json", {"software_fixture_original_block": True})
    request = {
        "record_version": 2,
        "run_id": directory.name,
        "adapter": lab.ADAPTER,
        "effective": {"preset": preset},
        "prediction": "software fixture; no scientific execution",
        "nmpc_capture": {
            "runtime": str(lab.RUNTIME),
            "source": lab.SOURCE,
            "profile_sha256": lab.PROFILE_SHA,
            "source_sha256": lab.source_hashes(),
            "adapter_sha256": lab.adapter_hashes(),
            "environment": preflights[preset]["environment"],
            "resolved": preflights[preset]["resolved"],
            "software_gate_sha256": storage.sha256(tmp_path / "software_gate.json"),
        },
    }
    for name, value in [("request.json", request), ("worker.json", {}), ("supervisor.json", {})]:
        storage.write_json(directory / name, value)
    (directory / "experiment").mkdir()
    (directory / "experiment/plant_segments.jsonl").write_text('{"software_fixture":true}\n')
    jobs.finalize(directory, "cancelled", error="software fixture cancellation; no controller")
    return directory


def test_partial_cancellation_and_fresh_hash_currentness(tmp_path, monkeypatch, preflights):
    directory = fixture_run(tmp_path, preflights)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(lab, "RUNS", tmp_path / "runs")
    fixture_authority(tmp_path, monkeypatch)
    view = lab.read_run(directory)
    assert view["raw"] is None and view["status"]["state"] == "cancelled"
    lab.current(view)
    path = directory / "experiment/plant_segments.jsonl"
    info = path.stat()
    path.write_bytes(path.read_bytes().replace(b"true", b"null"))
    os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns))
    with pytest.raises(ValueError):
        lab.current(view)


def test_external_authority_and_claim_changes_quarantine(tmp_path, monkeypatch, preflights):
    directory = fixture_run(tmp_path, preflights)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(lab, "RUNS", tmp_path / "runs")
    fixture_authority(tmp_path, monkeypatch)
    view = lab.read_run(directory)
    claim = tmp_path / "claims/nominal.json"
    claim.write_text("{}")
    with pytest.raises(ValueError):
        lab.current(view)


def test_completed_missing_native_result_cannot_be_promoted(tmp_path, monkeypatch, preflights):
    directory = fixture_run(tmp_path, preflights)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(lab, "RUNS", tmp_path / "runs")
    fixture_authority(tmp_path, monkeypatch)
    status = storage.read_json(directory / "status.json")
    status.update(state="completed", scientific_outcome="completed")
    storage.write_json(directory / "status.json", status)
    with pytest.raises(ValueError):
        lab.read_run(directory)


@pytest.mark.parametrize("failure", [False, True])
def test_worker_guard_precedes_isolated_branch_and_source_failure_blocks(
    tmp_path, monkeypatch, failure
):
    from tools.apex_workbench import worker as entry

    directory = tmp_path / "software_worker_fixture"
    directory.mkdir()
    storage.write_json(directory / "request.json", {"adapter": lab.ADAPTER, "nmpc_capture": {}})
    monkeypatch.setattr(jobs, "LEASE_ROOT", tmp_path)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(entry.resource, "setrlimit", lambda *args: None)
    events = []
    with jobs.execution_lock() as lease:

        def guarded(path, fd):
            assert os.fstat(fd).st_ino == os.fstat(lease.fileno()).st_ino
            events.append("guard")

        def isolated(path, captured):
            assert events == ["guard"]
            events.append("frozen_adapter")
            if failure:
                raise ValueError("software fixture source mismatch; no numeric execution")
            return {"software_fixture": True}

        monkeypatch.setattr(lifecycle, "start_guard", guarded)
        monkeypatch.setattr(worker, "run", isolated)
        assert entry.main(directory, lease.fileno()) == (2 if failure else 0)
    assert events == ["guard", "frozen_adapter"]
    assert (tmp_path / "BLOCKED.json").exists() is failure
    assert (directory / "worker_result.json").exists() is not failure


@pytest.mark.parametrize("legacy_kind", ["absent", "invalid_file"])
def test_m0_admission_with_absent_legacy_root_never_launches_before_capture(
    tmp_path, monkeypatch, legacy_kind
):
    legacy = tmp_path / "legacy"
    if legacy_kind == "invalid_file":
        legacy.write_text("invalid retained root")
    monkeypatch.setattr(jobs, "RUNS", legacy)
    monkeypatch.setattr(jobs, "LEASE_ROOT", tmp_path / "lease")
    monkeypatch.setattr(lab, "RUNS", tmp_path / "m0")
    monkeypatch.setattr(lab, "authorized_run_id", lambda preset: FIXTURE_IDS[preset])
    monkeypatch.setattr(jobs, "provenance", lambda: {"limits": jobs.LIMITS})
    called = []

    def captured(values):
        called.append(values)
        raise RuntimeError("software sentinel before claim or numerical launch")

    def forbidden(*args, **kwargs):
        raise AssertionError("No worker may launch before validated source capture")

    monkeypatch.setattr(lab, "capture", captured)
    monkeypatch.setattr(jobs.subprocess, "Popen", forbidden)
    match = "software sentinel" if legacy_kind == "absent" else "not a directory"
    with pytest.raises(RuntimeError, match=match):
        jobs.start_run(lab.ADAPTER, {"preset": "nominal"}, runs=lab.RUNS)
    assert bool(called) is (legacy_kind == "absent")


def test_real_capture_to_execution_boundary_without_optimizer(tmp_path, monkeypatch, preflights):
    """Actual capture uses a fresh frozen probe; the fresh worker calls run's exact helper."""
    gate = {
        "resolved_snapshots": {p: r["resolved"] for p, r in preflights.items()},
        "environment": preflights["nominal"]["environment"],
    }
    root = tmp_path / "authority"
    root.mkdir()
    storage.write_json(root / "software_gate.json", gate)
    storage.write_json(root / "authorization.json", {"software_fixture_only": True})
    monkeypatch.setattr(lab, "verify_gate", lambda: gate)
    monkeypatch.setattr(lab, "authority_root", lambda identifier=lab.SUCCESSOR: root)
    captured = json.loads(json.dumps(lab.capture({"preset": "nominal"})))
    assert captured["resolved"]["simulation"]["failed_plan_ids"] == []
    report = lab.probe("nominal", captured=captured)
    assert report["boundary"] == {
        "native_failed_plan_ids_is_tuple": True,
        "optimizer_solves": 0,
        "plant_steps": 0,
    }
    lab.same_configuration(report["resolved"], captured["resolved"])
    changed = copy.deepcopy(captured)
    changed["resolved"]["vehicle"]["mass"] += 1
    with pytest.raises(RuntimeError, match="Actual frozen resolved configuration differs"):
        lab.probe("nominal", captured=changed)


@pytest.mark.parametrize("replacement", [True, "2.0", 3.0, None, float("nan"), float("inf")])
def test_strict_configuration_rejects_non_treatment_mutations(preflights, replacement):
    native = copy.deepcopy(preflights["nominal"]["resolved"])
    captured = copy.deepcopy(native)
    native["simulation"]["failed_plan_ids"] = ()
    lab.same_configuration(native, captured)
    captured["vehicle"]["mass"] = replacement
    with pytest.raises(ValueError):
        lab.same_configuration(native, captured)


@pytest.mark.parametrize("malformed", [{1: 0}, {"x": {1, 2}}, {"x": object()}, [], None])
def test_malformed_configuration_representations_rejected(malformed):
    with pytest.raises(ValueError):
        lab.canonical_snapshot(malformed)


def test_canonical_snapshot_keeps_numeric_identity():
    assert lab.canonical_snapshot({"x": (0.0, -0.0, 1, 1.0)}) == {"x": [0.0, -0.0, 1, 1.0]}
    for a, b in [(1, True), (1, 1.0), (0.0, -0.0)]:
        with pytest.raises(ValueError):
            lab.same_configuration({"x": a}, {"x": b})


def test_successor_requires_review_and_preserves_original_block(tmp_path, monkeypatch):
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    blocked = tmp_path / "BLOCKED.json"
    blocked.write_text('{"original":"immutable"}')
    monkeypatch.setattr(lab, "ORIGINAL_ANCHORS", {"BLOCKED.json": storage.sha256(blocked)})
    with pytest.raises(FileNotFoundError):
        lab.verify_successor()
    root = lab.authority_root()
    root.mkdir(parents=True)
    decision = root / "PRIMARY_DECISION.md"
    decision.write_text("explicit software fixture authority")
    monkeypatch.setattr(lab, "PRIMARY_DECISION_SHA", storage.sha256(decision))
    storage.write_json(root / "authorization.json", {})
    storage.write_json(root / "corrective_review.json", {"outcome": "BLOCKED"})
    with pytest.raises(ValueError):
        lab.verify_successor()
    lab.record_block(
        tmp_path / "runs/new", RuntimeError("retained"), {"authorization_id": lab.SUCCESSOR}
    )
    assert storage.read_json(root / "BLOCKED.json")["reason"] == "RuntimeError('retained')"
    assert blocked.read_text() == '{"original":"immutable"}'


def successor_authority_fixture(tmp_path, monkeypatch, preflights=None):
    """Disposable real Git source identities and fake authority; never a real execution grant."""
    frozen = lab.source_hashes()
    source = tmp_path / "source"
    source.mkdir()
    for name in lab.PRODUCERS:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((lab.ROOT / name).read_bytes())

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=source)

    git("init", "-q")
    git("add", *lab.PRODUCERS)
    git(
        "-c",
        "user.name=M0 fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "Disposable source identity only",
    )
    candidate = git("rev-parse", "HEAD").decode().strip()
    monkeypatch.setattr(lab, "git", git)
    monkeypatch.setattr(lab, "source_hashes", lambda: frozen)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    blocked = tmp_path / "BLOCKED.json"
    storage.write_json(blocked, {"original": "unchanged"})
    monkeypatch.setattr(lab, "ORIGINAL_ANCHORS", {"BLOCKED.json": storage.sha256(blocked)})
    root = lab.authority_root()
    root.mkdir(parents=True)
    decision = root / "PRIMARY_DECISION.md"
    decision.write_text("explicit disposable fixture; no numerical authority")
    monkeypatch.setattr(lab, "PRIMARY_DECISION_SHA", storage.sha256(decision))
    gate = {
        "status": "SOFTWARE_GATES_PASSED",
        "source": lab.SOURCE,
        "adapter_sha256": lab.adapter_hashes(),
        "implementation_revision": candidate,
        "run_ids": FIXTURE_IDS,
        "evidence_sha256": {},
        "profile_sha256": lab.PROFILE_SHA,
        "environment": preflights["nominal"]["environment"] if preflights else {},
        "resolved_snapshots": {p: r["resolved"] for p, r in (preflights or {}).items()},
    }
    storage.write_json(root / "software_gate.json", gate)
    review = {
        "candidate": candidate,
        "outcome": "PASS",
        "scientific_source": lab.SOURCE,
        "adapter_sha256": lab.adapter_hashes(),
        "evidence_sha256": {},
        "software_gate_sha256": storage.sha256(root / "software_gate.json"),
    }
    storage.write_json(root / "corrective_review.json", review)
    authority = {
        "schema": "apex-m0-successor-authorization/1",
        "id": lab.SUCCESSOR,
        "primary_decision_sha256": lab.PRIMARY_DECISION_SHA,
        "original_anchors": lab.ORIGINAL_ANCHORS,
        "maximum_attempts": {"nominal": 1, "exploratory": 1},
        "corrective_review_sha256": storage.sha256(root / "corrective_review.json"),
    }
    storage.write_json(root / "authorization.json", authority)
    return root, gate, review, blocked


def test_successor_positive_gate_exact_git_binding_and_consumed_claim(tmp_path, monkeypatch):
    root, gate, review, blocked = successor_authority_fixture(tmp_path, monkeypatch)
    assert lab.verify_gate(check_environment=False) == gate
    assert lab.authorized_run_id("nominal") == FIXTURE_IDS["nominal"]
    lab.claim("nominal", FIXTURE_IDS["nominal"], captured=True)
    with pytest.raises(FileExistsError):
        lab.claim("nominal", FIXTURE_IDS["nominal"], captured=True)
    with pytest.raises(FileNotFoundError):
        lab.claim("exploratory", FIXTURE_IDS["exploratory"], captured=True)
    storage.write_json(root / "software_gate.json", dict(gate, environment={"forged": True}))
    with pytest.raises(ValueError, match="independently reviewed identity"):
        lab.verify_gate(check_environment=False)
    storage.write_json(root / "software_gate.json", gate)
    changed = dict(review, outcome="BLOCKED")
    storage.write_json(root / "corrective_review.json", changed)
    with pytest.raises(ValueError):
        lab.verify_gate(check_environment=False)
    assert storage.read_json(blocked) == {"original": "unchanged"}
