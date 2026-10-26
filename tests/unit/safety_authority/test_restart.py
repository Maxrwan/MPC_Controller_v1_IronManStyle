"""Logical persistence and controlled reentry; no durability claim."""

from dataclasses import replace

from apex.safety_authority import records as r
from apex.safety_authority.codec import digest
from apex.safety_authority.reducer import restore_snapshot
from oracle_support import cases, decode_inputs


def test_missing_persistence_boot_latches_without_grants():
    cfg, _ = decode_inputs(cases()[0])
    restart = r.RestartInput(
        event_id="boot",
        at_tick=0,
        boot_control_session_id="NEW_SESSION",
        endpoint_session_id="ENDPOINT_UNKNOWN",
        saved_snapshot_sha256=None,
    )
    result = restore_snapshot(cfg, saved=None, integrity=None, restart=restart)
    assert result.snapshot.state == "NO_VALID_POLICY"
    assert [t.transition_id for t in result.transitions] == ["T09"]
    assert result.snapshot.permissions == ()
    assert result.snapshot.held_observation is None
    assert result.endpoint_outputs == ()


def test_intact_restore_preserves_all_histories_and_uncleared_latch():
    case = next(c for c in cases() if c["case_id"] == "T11-NO_VALID_POLICY-POSITIVE")
    cfg, snap = decode_inputs(case)
    integrity = replace(snap.evidence[0], evidence_id="INTEGRITY", kind="REENTRY", policy_id=None)
    restart = r.RestartInput(
        event_id="restore",
        at_tick=snap.current_tick,
        boot_control_session_id=snap.control_session_id,
        endpoint_session_id=snap.endpoint_session_id,
        saved_snapshot_sha256=digest(snap),
    )
    result = restore_snapshot(cfg, saved=snap, integrity=integrity, restart=restart)
    assert result.snapshot.fault_latches == snap.fault_latches
    assert result.snapshot.command_ledger == snap.command_ledger
    assert result.snapshot.event_ledger == snap.event_ledger
    assert result.snapshot.operation_ledger == snap.operation_ledger
    assert result.snapshot.trace_ledger[: len(snap.trace_ledger)] == snap.trace_ledger
    assert result.snapshot.state == snap.state
    assert result.endpoint_outputs == ()
