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
