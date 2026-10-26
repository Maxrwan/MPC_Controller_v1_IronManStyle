"""Admission, causal parent order, replay identity and input permutations."""

from dataclasses import replace

from apex.safety_authority import records as r
from apex.safety_authority.codec import decode_event, freeze
from apex.safety_authority.ordering import seal_batch
from apex.safety_authority.reducer import reduce_batch
from oracle_support import cases, decode_inputs


def inputs(identity):
    case = next(c for c in cases() if c["case_id"] == identity)
    cfg, snap = decode_inputs(case)
    decoded = [decode_event(freeze(e), configuration=cfg) for e in case["events"]]
    assert all(isinstance(x, r.DecodeSuccess) for x in decoded)
    return cfg, snap, tuple(x.value for x in decoded)


def test_sequence_admission_precedes_phase_sort_and_is_permutation_invariant():
    cfg, snap, events = inputs("E11-SEALED-SEQUENCE")
    a = seal_batch(cfg, snap, batch_id="independent-order", at_tick=20, events=events)
    b = seal_batch(
        cfg, snap, batch_id="independent-order", at_tick=20, events=tuple(reversed(events))
    )
    assert isinstance(a, r.DecodeSuccess) and a == b
    assert tuple(e.producer_sequence for e in a.value.events) == (2, 1)
    result = reduce_batch(cfg, snap, a.value)
    assert [t.transition_id for t in result.transitions] == ["T06", "T09"]
    assert not any("SEQUENCE_REORDERED" in t.reason_codes for t in result.traces)
    assert result == reduce_batch(cfg, snap, b.value)


def test_future_parent_and_duplicate_id_reject_sealing():
    cfg, snap, events = inputs("E11-SEALED-SEQUENCE")
    bad = replace(events[1], causal_parent_ids=(events[0].event_id,))
    result = seal_batch(cfg, snap, batch_id="bad-parent", at_tick=20, events=(events[0], bad))
    assert isinstance(result, r.DecodeFailure)
    assert "CAUSALITY_INVALID" in {x.reason_code for x in result.errors}
    duplicate = seal_batch(
        cfg, snap, batch_id="duplicate", at_tick=20, events=(events[0], events[0])
    )
    assert isinstance(duplicate, r.DecodeFailure)
    assert "IDENTITY_CONFLICT" in {x.reason_code for x in duplicate.errors}


def test_simultaneous_causes_retained_epoch_once():
    cfg, snap, events = inputs("E12-SIMULTANEOUS-FAULTS")
    batch = seal_batch(cfg, snap, batch_id="both-causes", at_tick=20, events=events)
    assert isinstance(batch, r.DecodeSuccess)
    result = reduce_batch(cfg, snap, batch.value)
    assert result.snapshot.desired_epoch == snap.desired_epoch + 1
    assert {"F_EMERGENCY", "F_MAP_MISMATCH"} <= {f.fault_id for f in result.snapshot.fault_latches}
    assert [t.transition_id for t in result.transitions] == ["T06", "T09"]
