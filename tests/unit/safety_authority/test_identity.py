"""No authority resurrection from duplicate identity or stale sealing."""

from dataclasses import replace

import pytest
from apex.safety_authority import records as r
from apex.safety_authority.codec import decode_event, freeze
from apex.safety_authority.ordering import seal_batch
from apex.safety_authority.reducer import reduce_batch
from oracle_support import cases, decode_inputs, run_case


def test_exact_receipt_duplicate_does_not_create_permission():
    case = next(c for c in cases() if c["case_id"] == "E05-EXACT-DUPLICATE")
    initial, result = run_case(case)
    assert result.snapshot.permissions == initial.permissions
    assert all(not t.granted_permission_ids for t in result.traces)


def test_stale_snapshot_fingerprint_cannot_grant():
    case = next(c for c in cases() if c["case_id"] == "E13-LOGICAL-GRANT")
    cfg, snap = decode_inputs(case)
    decoded = decode_event(freeze(case["events"][0]), configuration=cfg)
    assert isinstance(decoded, r.DecodeSuccess)
    sealed = seal_batch(cfg, snap, batch_id="forged", at_tick=20, events=(decoded.value,))
    assert isinstance(sealed, r.DecodeSuccess)
    changed = replace(snap, desired_epoch=snap.desired_epoch + 1)
    result = reduce_batch(cfg, changed, sealed.value)
    assert not any(t.granted_permission_ids for t in result.traces)
    assert result.endpoint_outputs == ()


def test_same_command_different_exact_payload_latches_and_revokes():
    case = next(c for c in cases() if c["case_id"] == "E04-CONFLICT-ID")
    initial, result = run_case(case)
    assert result.snapshot.state == "NO_VALID_POLICY"
    assert result.snapshot.desired_epoch == initial.desired_epoch + 1
    assert any(f.reason == "IDENTITY_CONFLICT" for f in result.snapshot.fault_latches)
    assert all(not t.granted_permission_ids for t in result.traces)


@pytest.mark.parametrize(
    "transition_id", ["HANDOFF_RECORD", "T04", "T05", "T07", "T08", "T10", "T12"]
)
def test_explicit_reauthorization_preserves_command_and_generation(transition_id):
    case = next(c for c in cases() if c["case_id"] == "E05-EXACT-DUPLICATE")
    cfg, snap = decode_inputs(case)
    # Complete independent barrier input; the approved seed has no ack ledger.
    ack = r.BarrierAck(
        ack_id="ACK2",
        barrier_id="BARRIER2",
        endpoint_session_id="ENDPOINT_A",
        control_session_id="SESSION_A",
        installed_epoch=2,
        endpoint_delivery_tick=10,
        installation_tick=10,
        ack_observed_tick=10,
        queue_cleared=True,
        outcome="INSTALLED",
        unknown_reason=None,
    )
    evidence = replace(
        snap.evidence[0],
        evidence_id="REAUTH_ORIGINAL",
        kind="REAUTHORIZATION",
        valid_from_tick=20,
        valid_until_tick=80,
    )
    original = snap.commands[0]
    snap = replace(
        snap,
        desired_epoch=2,
        endpoint_installed_epoch=2,
        epoch_barrier_ack_id="ACK2",
        prepared_barrier_ids=snap.prepared_barrier_ids + ("BARRIER2",),
        barrier_acknowledgement_ledger=(ack,),
        revoked_permission_ids=("p1",),
        evidence=snap.evidence + (evidence,),
    )
    event = r.Event(
        event_id="explicit-reauthorization",
        producer_id="TOY_INPUT",
        producer_sequence=5,
        at_tick=23,
        causal_parent_ids=(),
        kind="REAUTHORIZE",
        payload=r.ReauthorizePayload(
            command_id="c1",
            prior_permission_id="p1",
            new_permission_id="p-renewed",
            transition_id=transition_id,
            evidence_ids=("REAUTH_ORIGINAL",),
            requested_permission_interval_ticks=(24, 80),
        ),
    )
    sealed = seal_batch(cfg, snap, batch_id="reauthorization-batch", at_tick=23, events=(event,))
    assert isinstance(sealed, r.DecodeSuccess)
    result = reduce_batch(cfg, snap, sealed.value)
    if transition_id != "HANDOFF_RECORD":
        assert not any(p.permission_id == "p-renewed" for p in result.snapshot.permissions)
        assert any("TRANSITION_DISABLED" in t.reason_codes for t in result.traces)
        return
    granted = next(p for p in result.snapshot.permissions if p.permission_id == "p-renewed")
    assert (granted.valid_from_tick, granted.valid_until_tick) == (24, 80)
    assert (granted.generation_epoch, granted.permission_epoch) == (1, 2)
    assert granted.source_packet_id == "P1"
    assert result.snapshot.commands[0] == original
    assert result.endpoint_outputs == ()
