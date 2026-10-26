"""O20 permission/resource logic through fakes; no actual scientific worker launched."""

import json

import pytest


def test_no_grant_no_execution(inputs, tmp_path):
    from ct1.contracts import Budget
    from ct1.guards import check_execution_grant

    p = tmp_path / "denied.json"
    p.write_text(json.dumps({"authorized_stage": "L1"}))
    assert check_execution_grant(p, inputs, Budget()).value is None


def test_budget_reserves_and_refuses_gain_overflow(monkeypatch):
    from ct1.contracts import BudgetToken

    monkeypatch.setattr("time.monotonic", lambda: 0.0)
    t = BudgetToken(300.0)
    t.reserve(960)
    with pytest.raises(TimeoutError):
        t.reserve(1)
    monkeypatch.setattr("time.monotonic", lambda: 295.0)
    with pytest.raises(TimeoutError):
        t.poll()


def test_unsupported_backend_fails_closed():
    from pathlib import Path

    from ct1.contracts import BackendIdentity, FileBinding
    from ct1.guards import configure_native_single

    b = BackendIdentity(
        "UNREVIEWED", Path("/missing"), None, "unknown", FileBinding("unknown", "0" * 64)
    )
    assert configure_native_single(b).value is None


@pytest.mark.parametrize(
    "now,rss,written,free",
    [
        (295.0, 0, 0, 2147483648),
        (0.0, 1073741824, 0, 2147483648),
        (0.0, 0, int(0.95 * 1073741824), 2147483648),
        (0.0, 0, 0, 1073741823),
    ],
)
def test_fake_resource_stops(now, rss, written, free):
    from ct1.contracts import Budget
    from ct1.guards import _resource_stop

    assert _resource_stop(now, 300.0, rss, written, free, Budget())
    assert not _resource_stop(0.0, 300.0, 0, 0, 2147483648, Budget())


def test_conflicting_guard_is_preserved(inputs, tmp_path, monkeypatch):
    from dataclasses import replace

    import ct1.guards as guards
    from ct1.contracts import Budget, ExecutionGrant
    from ct1.guards import preflight_resources

    marker = tmp_path / "results/foreign/MEASURED_ACTIVE"
    marker.parent.mkdir(parents=True)
    marker.write_text("external-owner")
    local = replace(inputs, spec=replace(inputs.spec, repo_root=tmp_path, archive_root=tmp_path))
    grant = ExecutionGrant(
        "a" * 40, "b" * 40, "L3", (), 300, "2099-01-01T00:00:00Z", tmp_path / "new"
    )
    monkeypatch.setattr(guards, "_git", lambda *a: "worktree " + str(tmp_path))
    monkeypatch.setattr(
        guards.shutil, "disk_usage", lambda *a: type("Usage", (), {"free": 2147483648})()
    )
    monkeypatch.setattr(guards.subprocess, "check_output", lambda *a, **k: "")
    assert preflight_resources(local, grant, Budget()).value is None
    assert marker.read_text() == "external-owner"


@pytest.mark.parametrize(
    "bad_sha,expiry", [(True, "2099-01-01T00:00:00Z"), (False, "2020-01-01T00:00:00Z")]
)
def test_wrong_sha_or_expired_grant_rejects(inputs, tmp_path, bad_sha, expiry):
    from ct1.contracts import ASSIGNMENT_REVISION, Budget
    from ct1.guards import check_execution_grant

    allow = json.loads((inputs.spec.assignment_root / "future_source_allowlist.json").read_text())
    raw = {
        "primary_authorized": True,
        "authorized_stage": "L3",
        "approval_reference": "SYNTHETIC_NEGATIVE_ONLY",
        "assignment_sha": ASSIGNMENT_REVISION,
        "implementation_sha": "0" * 40 if bad_sha else inputs.spec.expected_revision,
        "expiry_utc": expiry,
        "host_seconds": 300,
        "test_paths": [
            p
            for p in allow["allowed_create_paths"]
            if p.startswith("tests/ct1l/test_") and p.endswith(".py")
        ],
        "output_root": str(tmp_path / "fresh"),
    }
    path = tmp_path / "grant.json"
    path.write_text(json.dumps(raw))
    assert check_execution_grant(path, inputs, Budget()).value is None


class _FakeWorkBudget:
    def poll(self):
        pass


def test_local_invalid_then_independent_valid_without_retry_or_replacement():
    from ct1.worker import _LocalScientificFailure, _run_independent

    visits = []
    failed = []
    retained = []

    def run(candidate):
        visits.append(candidate)
        if candidate == "original_bad":
            retained.append(("original_bad", "failed-comparison", "literal retained observation"))
            raise _LocalScientificFailure(
                "CANDIDATE",
                "RICCATI_REPRODUCTION",
                (
                    {
                        "code": "RICCATI_OR_GAIN_CHECK_FAILED",
                        "detail": "literal failed original gain",
                    },
                ),
                "FAILED_COMPARISON",
            )
        retained.append((candidate, "independent-open-loop", "literal valid observation"))

    def failure(candidate, exc):
        failed.append((candidate, exc.stage, exc.status))

    _run_independent(
        ("original_bad", "original_good"), run, failure, scope="CANDIDATE", budget=_FakeWorkBudget()
    )
    assert visits == ["original_bad", "original_good"]
    assert failed == [("original_bad", "RICCATI_REPRODUCTION", "FAILED_COMPARISON")]
    assert retained == [
        ("original_bad", "failed-comparison", "literal retained observation"),
        ("original_good", "independent-open-loop", "literal valid observation"),
    ]


@pytest.mark.parametrize("mode", ("integrity", "timeout", "programming"))
def test_global_or_unknown_failure_stops_immediately(mode):
    from ct1.worker import _GlobalIntegrityFailure, _run_independent

    visits = []
    local = []

    def run(candidate):
        visits.append(candidate)
        if mode == "integrity":
            raise _GlobalIntegrityFailure(
                "SOURCE_IDENTITY_FAILURE", "literal changed pinned source"
            )
        if mode == "timeout":
            raise TimeoutError("literal aggregate deadline")
        raise KeyError("literal unexpected programming defect")

    expected = (
        _GlobalIntegrityFailure
        if mode == "integrity"
        else TimeoutError
        if mode == "timeout"
        else KeyError
    )
    with pytest.raises(expected):
        _run_independent(
            ("first", "must_not_run"),
            run,
            lambda *a: local.append(a),
            scope="CANDIDATE",
            budget=_FakeWorkBudget(),
        )
    assert visits == ["first"] and local == []


def test_map_local_failure_continues_other_original_map():
    from ct1.worker import _LocalScientificFailure, _run_independent

    visits = []
    failures = []

    def run(item):
        visits.append(item)
        if item == "original_map_1":
            raise _LocalScientificFailure(
                "MAP",
                "FD_STENCIL",
                ({"code": "INVALID_CENTRAL_STENCIL", "detail": "literal boundary"},),
            )

    _run_independent(
        ("original_map_1", "original_map_2"),
        run,
        lambda i, e: failures.append((i, e.stage)),
        scope="MAP",
        budget=_FakeWorkBudget(),
    )
    assert visits == ["original_map_1", "original_map_2"] and failures == [
        ("original_map_1", "FD_STENCIL")
    ]


def test_failed_common_trust_is_not_downgraded_by_local_handler():
    from ct1.worker import _GlobalIntegrityFailure, _LocalScientificFailure, _run_independent

    visits = []
    local = []
    checks = []

    def trust():
        checks.append("check")
        if len(checks) == 2:
            raise _GlobalIntegrityFailure("SOURCE_IDENTITY_FAILURE", "literal input disappeared")

    def run(item):
        visits.append(item)
        raise _LocalScientificFailure(
            "CANDIDATE",
            "PACKET_SUPPORT",
            ({"code": "PACKET_UNAVAILABLE", "detail": "literal unavailable"},),
        )

    with pytest.raises(_GlobalIntegrityFailure):
        _run_independent(
            ("first", "must_not_run"),
            run,
            lambda *a: local.append(a),
            scope="CANDIDATE",
            budget=_FakeWorkBudget(),
            check_trust=trust,
        )
    assert visits == ["first"] and local == []


def test_common_source_outcome_cannot_become_local_unavailability(monkeypatch):
    from ct1.contracts import Outcome
    from ct1.worker import _GlobalIntegrityFailure, _require_local

    with pytest.raises(_GlobalIntegrityFailure):
        _require_local(
            Outcome.unavailable("SOURCE_IDENTITY_FAILURE", "literal wrong source hash"),
            scope="MAP",
            stage="source",
        )

    from ct1.worker import _assert_l3_test_selection

    monkeypatch.setenv("PYTEST_ADDOPTS", "--lf")
    with pytest.raises(_GlobalIntegrityFailure, match="pytest"):
        _assert_l3_test_selection(None, None)


def test_failed_gain_audit_prevents_dependent_conclusion_only():
    from ct1.contracts import Outcome, OutcomeStatus, Reason
    from ct1.worker import _require_local, _run_independent

    records = []
    failures = []

    def run(candidate):
        records.append((candidate, "open_loop"))
        result = (
            Outcome(
                OutcomeStatus.FAILED_COMPARISON,
                (Reason("RICCATI_OR_GAIN_CHECK_FAILED", "literal failure"),),
                {"original_gains_replaced": False},
            )
            if candidate == "bad"
            else Outcome.available({"original_gains_replaced": False})
        )
        records.append((candidate, "gain_audit", result.status.value))
        _require_local(result, scope="CANDIDATE", stage="RICCATI_REPRODUCTION")
        records.append((candidate, "dependent_closed_loop"))

    _run_independent(
        ("bad", "good"),
        run,
        lambda c, e: failures.append(c),
        scope="CANDIDATE",
        budget=_FakeWorkBudget(),
    )
    assert records == [
        ("bad", "open_loop"),
        ("bad", "gain_audit", "FAILED_COMPARISON"),
        ("good", "open_loop"),
        ("good", "gain_audit", "AVAILABLE"),
        ("good", "dependent_closed_loop"),
    ]
    assert failures == ["bad"]
