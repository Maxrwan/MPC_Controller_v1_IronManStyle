"""Pure sealed admission; producer sequencing is independent of phase execution."""

from __future__ import annotations

from . import records as r
from .codec import digest, snapshot_errors
from .policy import estimate_codes

EXCLUDED = (
    "COMMAND_DELIVER",
    "PERMISSION_DELIVER",
    "ENDPOINT_ESTIMATE_DELIVER",
    "ENDPOINT_EVIDENCE_DELIVER",
    "CANCEL_DELIVER",
    "ENDPOINT_COMMIT",
)


def phase(cfg: r.Configuration, e: r.Event) -> int:
    if e.kind not in r.PAYLOAD_TYPES or not isinstance(e.payload, r.PAYLOAD_TYPES[e.kind]):
        return 0
    if e.kind in EXCLUDED:
        return 5
    if e.kind in ("ADVANCE", "EMERGENCY", "REVOKE_REQUEST", "EPOCH_INSTALL", "RESTART"):
        return 0
    if e.kind == "ESTIMATE_OBSERVED":
        return 0 if estimate_codes(cfg, e.payload, e.at_tick) else 2
    if (
        e.kind == "EVIDENCE_OBSERVED"
        and (e.payload.result != "SATISFIED" or e.at_tick >= e.payload.valid_until_tick)
        and e.payload.kind in ("NOMINAL", "CONTINUATION", "REST_HOLD", "HEALTH")
    ):
        return 0
    if e.kind in ("ENDPOINT_OBSERVATION", "BARRIER_ACK_OBSERVED"):
        return 1
    if e.kind in ("ESTIMATE_OBSERVED", "EVIDENCE_OBSERVED", "PROPOSAL_READY", "AUTHORITY_ACCEPT"):
        return 2
    if e.kind in (
        "ARM_REQUEST",
        "RENEWAL_WARNING",
        "WARNING_CLEAR",
        "REENTRY_REQUEST",
        "RESET_REQUEST",
        "POLICY_SELECT",
        "CANCEL_REQUEST",
    ):
        return 3
    return 4


def event_key(cfg: r.Configuration, e: r.Event):
    return (
        e.at_tick,
        phase(cfg, e),
        e.producer_id.encode("utf-8"),
        e.producer_sequence,
        e.event_id.encode("utf-8"),
    )


def seal_batch(
    configuration: r.Configuration,
    snapshot: r.Snapshot,
    *,
    batch_id: str,
    at_tick: r.Tick,
    events: tuple[r.Event, ...],
) -> r.DecodeSuccess[r.SealedBatch] | r.DecodeFailure:
    errors = list(snapshot_errors(snapshot, configuration))

    def err(path, code, message):
        errors.append(r.InputError(path=path, reason_code=code, message=message))

    if (
        type(at_tick) is not int
        or at_tick < snapshot.current_tick
        or not batch_id
        or type(events) is not tuple
    ):
        return r.DecodeFailure(
            errors=(
                r.InputError(
                    path="batch",
                    reason_code="BATCH_INVALID",
                    message="monotonic tick, identity and immutable events required",
                ),
            )
        )
    prior = {x.event_id: x for x in snapshot.event_ledger}
    floors = {x.producer_id: x.sequence for x in snapshot.event_high_watermarks}
    seen_ids, sequences = set(), set()
    ordered = tuple(sorted(events, key=lambda e: event_key(configuration, e)))
    keys = {e.event_id: event_key(configuration, e) for e in ordered}
    for e in ordered:
        if e.at_tick != at_tick:
            err(e.event_id, "BATCH_INVALID", "batch tick mismatch")
        if e.event_id in seen_ids:
            err(e.event_id, "IDENTITY_CONFLICT", "duplicate batch event ID")
        seen_ids.add(e.event_id)
        if e.kind not in r.PAYLOAD_TYPES or not isinstance(
            e.payload, r.PAYLOAD_TYPES.get(e.kind, r.InputError)
        ):
            err(e.event_id, "SCHEMA_INVALID", "event/payload mismatch")
        previous = prior.get(e.event_id)
        if previous is not None:
            if (previous.producer_id, previous.producer_sequence, previous.payload_sha256) != (
                e.producer_id,
                e.producer_sequence,
                digest(e),
            ):
                err(e.event_id, "IDENTITY_CONFLICT", "persisted event identity differs")
            continue
        seq = (e.producer_id, e.producer_sequence)
        if seq in sequences or e.producer_sequence <= floors.get(e.producer_id, -1):
            err(e.event_id, "SEQUENCE_REORDERED", "sequence not new against initial snapshot")
        sequences.add(seq)
        for parent in e.causal_parent_ids:
            if parent in keys:
                if keys[parent] >= keys[e.event_id]:
                    err(
                        e.event_id,
                        "CAUSALITY_INVALID",
                        "parent must precede child under declared key",
                    )
            elif parent not in prior:
                err(e.event_id, "CAUSALITY_INVALID", "unknown parent")
    batch_history = next(
        (x for x in snapshot.operation_ledger if x.operation_key == ("SEALED_BATCH", batch_id)),
        None,
    )
    if batch_history is not None and batch_history.content_sha256 != digest(ordered):
        err("batch_id", "IDENTITY_CONFLICT", "batch identity already binds different input")
    if errors:
        return r.DecodeFailure(
            errors=tuple(sorted(errors, key=lambda e: (e.path.encode("utf-8"), e.reason_code)))
        )
    return r.DecodeSuccess(
        value=r.SealedBatch(
            batch_id=batch_id,
            at_tick=at_tick,
            events=ordered,
            configuration_sha256=digest(configuration),
            initial_snapshot_sha256=digest(snapshot),
            canonical_input_sha256=digest(ordered),
        )
    )
