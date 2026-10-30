"""O20 permission/resource logic through fakes; no actual scientific worker launched."""

import json

import pytest


def test_no_grant_no_execution(inputs, tmp_path):
    from ct1.contracts import Budget
    from ct1.guards import check_execution_grant

    p = tmp_path / "denied.json"
    p.write_text(json.dumps({"authorized_stage": "L1"}))
    assert check_execution_grant(p, inputs, Budget()).value is None


def test_budget_reserves_and_refuses_gain_overflow(monkeypatch, tmp_path, capsys):
    from ct1.contracts import BudgetToken

    monkeypatch.setattr("time.monotonic", lambda: 0.0)
    t = BudgetToken(300.0)
    t.reserve(960)
    with pytest.raises(TimeoutError):
        t.reserve(1)
    monkeypatch.setattr("time.monotonic", lambda: 295.0)
    with pytest.raises(TimeoutError):
        t.poll()
    _deadline_cli_literals(monkeypatch, tmp_path, capsys)
    _deadline_supervisor_literals(monkeypatch, tmp_path)


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
    from ct1.guards import _AggregateDeadline

    monkeypatch.setattr(guards.time, "monotonic", lambda: 0.0)
    assert (
        preflight_resources(local, grant, Budget(), deadline=_AggregateDeadline(0.0, 300.0)).value
        is None
    )
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


# Independent L2D literal subcases remain under existing node selectors. UNEXECUTED.
def _deadline_cli_literals(monkeypatch, tmp_path, capsys):
    from types import SimpleNamespace

    from ct1 import cli
    from ct1.contracts import ExecutionGrant, Outcome, OutcomeStatus, Reason, SupervisorReport

    baseline_env = cli.os.environ.get("PYTHONPATH")
    for case in (
        "success",
        "expired_source",
        "missing_grant",
        "invalid_grant",
        "source_failure",
        "resource_failure",
        "environment_failure",
        "zero_exit_failure",
    ):
        clock = {"now": 1000.0}
        seen = []
        launched = []
        root = tmp_path / ("cli_" + case)
        root.mkdir()
        output = root / "fresh_run"
        inputs = SimpleNamespace(candidates=("literal",) * 12, spec=SimpleNamespace(repo_root=root))
        grant = ExecutionGrant("a" * 40, "b" * 40, "L3", (), 300, "2099-01-01T00:00:00Z", output)

        def git(*args, **kwargs):
            assert kwargs["timeout"] == 295.0
            return "b" * 40 + "\n"

        def source(spec):
            clock["now"] = 1296.0 if case in ("expired_source", "source_failure") else 1040.0
            if case == "source_failure":
                return Outcome(
                    OutcomeStatus.INVALID,
                    (Reason("SOURCE_IDENTITY_FAILURE", "literal changed source"),),
                )
            return Outcome.available(inputs)

        def authorize(path, value, budget, *, deadline):
            assert value is inputs and deadline.cli_start_monotonic_s == 1000.0
            assert deadline.deadline_monotonic_s == 1300.0
            seen.append(deadline)
            clock["now"] = 1060.0
            return (
                Outcome.unavailable("L3_AUTHORIZATION_REQUIRED", "literal denied")
                if case == "invalid_grant"
                else Outcome.available(grant)
            )

        def resources(value, accepted, budget, *, deadline):
            assert deadline is seen[0] and accepted == grant
            seen.append(deadline)
            clock["now"] = 1080.0
            if case == "environment_failure":
                raise ImportError("literal missing psutil")
            return (
                Outcome.unavailable("RESOURCE_PREFLIGHT_FAILED", "literal unavailable disk")
                if case == "resource_failure"
                else Outcome.available("literal preflight")
            )

        def supervise(command, path, accepted, budget, *, deadline, inputs, grant_path):
            assert deadline is seen[0] and deadline.deadline_monotonic_s == 1300.0
            assert deadline.work_remaining_s("literal launch") == 215.0
            launched.append(command)
            return SupervisorReport(
                0,
                "SOURCE_IDENTITY_FAILURE" if case == "zero_exit_failure" else "COMPLETE",
                80.0,
                0,
                False,
                0.0,
                None,
                ("worker_RSS_NOT_OBSERVED",),
            )

        with monkeypatch.context() as patch:
            patch.setattr(cli.time, "monotonic", lambda: clock["now"])
            patch.setattr(cli.subprocess, "check_output", git)
            patch.setattr(cli, "verify_inputs", source)
            patch.setattr(cli, "check_execution_grant", authorize)
            patch.setattr(cli, "preflight_resources", resources)
            patch.setattr(cli, "supervise_worker", supervise)
            args = [
                "run",
                "--repo-root",
                str(root),
                "--archive-root",
                str(root),
                "--assignment-root",
                str(root / "docs"),
            ]
            if case != "missing_grant":
                args += ["--grant", str(root / "grant.json"), "--output", str(output)]
            code = cli.main(args)
            record = __import__("json").loads(capsys.readouterr().out)
        assert code == (0 if case == "success" else 2)
        assert cli.os.environ.get("PYTHONPATH") == baseline_env
        if case in ("success", "zero_exit_failure"):
            assert len(launched) == 1 and record["deadline_monotonic_s"] == 1300.0
            assert record["peak_observed_worker_RSS_bytes"] is None
            assert record["worker_rss_observation"] == "NOT_OBSERVED"
        else:
            assert launched == [] and record["worker_started"] is False and not output.exists()
            assert record["worker_rss_bytes"] is None and not record["hard_RSS_enforcement"]
        expected = {
            "success": "COMPLETE",
            "expired_source": "RESOURCE_CENSORED",
            "missing_grant": "AUTHORIZATION_FAILURE",
            "invalid_grant": "AUTHORIZATION_FAILURE",
            "source_failure": "SOURCE_IDENTITY_FAILURE",
            "resource_failure": "RESOURCE_PREFLIGHT_FAILED",
            "environment_failure": "ENVIRONMENT_FAILURE",
            "zero_exit_failure": "SOURCE_IDENTITY_FAILURE",
        }
        assert record["termination"] == expected[case]
        if case == "expired_source":
            assert record["elapsed_cli_s"] == 296.0 and record["remaining_work_s"] == 0.0
            assert record["remaining_total_s"] == 4.0 and not record["primary_grant_validated"]
        if case == "source_failure":
            assert not record["source_verified"]


def _deadline_supervisor_literals(monkeypatch, tmp_path):
    import signal
    import sys
    from types import SimpleNamespace

    import ct1.evidence as evidence
    import ct1.guards as guards
    from ct1.contracts import Budget, ExecutionGrant, Outcome

    # Literal origin 0/deadline 300. Preflight has already consumed 40 s.
    for case, startup_end in (
        ("startup_delay", 80.0),
        ("reserve_and_grace", 299.5),
        ("expired_before_supervisor", 296.0),
        ("expired_during_output_setup", 296.0),
        ("invalid_primary", 80.0),
        ("finalization_failure", 80.0),
    ):
        clock = {"now": 296.0 if case == "expired_before_supervisor" else 40.0}
        timeline = guards._AggregateDeadline(0.0, 300.0)
        root = tmp_path / ("supervisor_" + case)
        inputs = SimpleNamespace(spec=SimpleNamespace(repo_root=tmp_path))
        grant = ExecutionGrant("a" * 40, "b" * 40, "L3", (), 300, "2099-01-01T00:00:00Z", root)
        command = (
            "python",
            "-m",
            "ct1.worker",
            "--repo-root",
            str(tmp_path),
            "--grant",
            str(tmp_path / "grant.json"),
        )
        envs = []
        waits = []
        signals = []
        finals = []
        auth = []

        class ProcessError(Exception):
            pass

        class Child:
            pid = 4444
            returncode = None
            polls = 0

            def poll(self):
                self.polls += 1
                if self.returncode is not None:
                    return self.returncode
                if self.polls == 1:
                    return None
                self.returncode = 0
                return 0

            def wait(self, timeout=None):
                waits.append(timeout)
                self.returncode = -15
                return self.returncode

        child = Child()

        def launch(*args, **kwargs):
            envs.append(kwargs["env"])
            clock["now"] = startup_end
            return child

        def authorization(*args, **kwargs):
            auth.append(kwargs["deadline"])
            return (
                Outcome.unavailable("L3_AUTHORIZATION_REQUIRED", "literal denied")
                if case == "invalid_primary"
                else Outcome.available(grant)
            )

        def finalize(writer, *args):
            finals.append((writer._final_deadline, writer._final_measurements["wall_elapsed_s"]))
            if case == "finalization_failure":
                raise OSError("literal index write failure")
            return Outcome.unavailable(
                "NO_MANIFEST", "Literal fake child produces no scientific evidence"
            )

        monitored = SimpleNamespace(
            memory_info=lambda: SimpleNamespace(rss=1024),
            num_threads=lambda: 2,
            cpu_times=lambda: SimpleNamespace(user=0.0, system=0.0),
        )
        fake_psutil = SimpleNamespace(
            Process=lambda pid: monitored, Error=ProcessError, NoSuchProcess=ProcessError
        )
        from pathlib import Path

        original_mkdir = Path.mkdir

        def mkdir(path, *args, **kwargs):
            result = original_mkdir(path, *args, **kwargs)
            if case == "expired_during_output_setup" and path == root:
                clock["now"] = 296.0
            return result

        with monkeypatch.context() as patch:
            patch.setattr(Path, "mkdir", mkdir)
            patch.setattr(guards.time, "monotonic", lambda: clock["now"])
            patch.setattr(guards.time, "sleep", lambda duration: None)
            patch.setattr(guards, "check_execution_grant", authorization)
            patch.setattr(guards.subprocess, "Popen", launch)
            patch.setattr(guards.os, "killpg", lambda pid, sig: signals.append(sig))
            patch.setattr(guards.shutil, "disk_usage", lambda p: SimpleNamespace(free=4294967296))
            patch.setattr(evidence, "finalize_run", finalize)
            patch.setitem(sys.modules, "psutil", fake_psutil)
            if case == "invalid_primary":
                with pytest.raises(PermissionError):
                    guards.supervise_worker(
                        command,
                        root,
                        grant,
                        Budget(),
                        deadline=timeline,
                        inputs=inputs,
                        grant_path=tmp_path / "grant.json",
                    )
                assert envs == [] and not root.exists()
                continue
            result = guards.supervise_worker(
                command,
                root,
                grant,
                Budget(),
                deadline=timeline,
                inputs=inputs,
                grant_path=tmp_path / "grant.json",
            )
        if case == "expired_during_output_setup":
            assert (
                envs == []
                and result.worker_exit_code is None
                and result.termination == "RESOURCE_CENSORED"
            )
            failure = json.loads((root / "preworker_failure.json").read_text())
            assert failure["worker_started"] is False and failure["worker_rss_bytes"] is None
            assert failure["deadline_monotonic_s"] == 300.0 and failure["remaining_total_s"] == 4.0
            assert finals == [(300.0, 296.0)]
            marker = json.loads((root / "MEASURED_COMPLETED").read_text())
            assert marker["peak_observed_worker_rss_bytes"] is None
            assert marker["worker_rss_observed"] is False
        elif case == "expired_before_supervisor":
            assert result.worker_exit_code is None and result.termination == "RESOURCE_CENSORED"
            assert envs == [] and not root.exists() and result.elapsed_wall_s == 296.0
        else:
            assert auth == [timeline]
            assert envs[0]["CT1L_DEADLINE_MONOTONIC"] == "300.0"
            assert envs[0]["CT1L_CLI_START_MONOTONIC"] == "0.0"
            assert finals == [(300.0, startup_end)] and result.elapsed_wall_s == startup_end
            assert not result.hard_RSS_enforcement
            if case == "reserve_and_grace":
                assert signal.SIGTERM in signals and waits == [0.5]
                assert result.termination == "RESOURCE_CENSORED"
            else:
                assert result.termination == "MISSING_COVERAGE"  # No fake scientific success.
                if case == "finalization_failure":
                    assert result.worker_exit_code == 0
                    assert any(
                        "supervisor_finalization_incomplete:" in x
                        for x in result.missing_result_ids
                    )
