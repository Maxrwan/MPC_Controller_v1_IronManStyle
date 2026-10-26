"""Reviewed candidate guards over supplied synthetic records; no control policy."""

from __future__ import annotations

from fractions import Fraction

from . import records as r
from .time import map_stamp, validate_interval


def authorized(cfg: r.Configuration, event: r.Event, authorization_id: str | None = None) -> bool:
    return any(
        x.producer_id == event.producer_id
        and event.kind in x.allowed_event_kinds
        and x.valid_interval[0] <= event.at_tick < x.valid_interval[1]
        and (authorization_id is None or authorization_id == x.authorization_id)
        for x in cfg.authorization_registry
    )


def uncleared(s: r.Snapshot) -> bool:
    return any(f.cleared_tick is None for f in s.fault_latches)


def evidence(s: r.Snapshot, identity: str | None) -> r.Evidence | None:
    return next((e for e in s.evidence if e.evidence_id == identity), None)


def evidence_codes(
    s: r.Snapshot, e: r.Evidence | None, tick: int, *, through: int | None = None
) -> tuple[str, ...]:
    if e is None:
        return ("DOMAIN_UNKNOWN",)
    if tick < e.valid_from_tick:
        return ("NOT_YET_VALID",)
    if tick >= e.valid_until_tick or (through is not None and through > e.valid_until_tick):
        return ("EXPIRED",)
    if e.result != "SATISFIED":
        return ("HEALTH_INVALID",) if e.kind == "HEALTH" else ("DOMAIN_UNKNOWN",)
    estimate = s.latest_estimate
    packet = s.active_packet
    if (
        e.estimate_id is not None and (estimate is None or estimate.estimate_id != e.estimate_id)
    ) or (
        e.source_packet_id is not None
        and (packet is None or packet.packet_id != e.source_packet_id)
    ):
        return ("DOMAIN_UNKNOWN",)
    if (
        estimate is not None
        and e.uncertainty_interpretation_ref is not None
        and e.uncertainty_interpretation_ref != estimate.uncertainty.interpretation_ref
    ):
        return ("UNCERTAINTY_UNKNOWN",)
    # Assumption/context strings must agree with current nominal assertions. They
    # are synthetic provenance, never real authentication or a physical domain.
    contexts = {
        x.context_revision
        for x in s.evidence
        if x.kind == "NOMINAL"
        and x.result == "SATISFIED"
        and (packet is None or x.source_packet_id == packet.packet_id)
    }
    if contexts and e.context_revision not in contexts:
        return ("DOMAIN_UNKNOWN",)
    return ()


def estimate_codes(
    cfg: r.Configuration, e: r.Estimate | None, tick: int, *, through: int | None = None
) -> tuple[str, ...]:
    if e is None:
        return ("ESTIMATE_MISSING",)
    codes = []
    if e.quality != "VALID":
        codes.append(
            {
                "INVALID": "ESTIMATE_INVALID",
                "MISSING": "ESTIMATE_MISSING",
                "DEGRADED": "ESTIMATE_DEGRADED",
            }[e.quality]
        )
    if e.state_si is None:
        codes.append("ESTIMATE_MISSING")
    if e.map_id != cfg.expected_map_id:
        codes.append("MAP_MISMATCH")
    if e.frame_id != cfg.expected_frame_id:
        codes.append("FRAME_MISMATCH")
    if cfg.nominal_max_estimate_age_ticks is None:
        codes.append("NO_NOMINAL_FRESHNESS_BOUND")
    if e.capture is None:
        codes.append("CLOCK_UNKNOWN")
    else:
        bound = map_stamp(cfg, e.capture, at_tick=tick)
        if isinstance(bound, r.BoundFailure):
            codes.extend(bound.reason_codes)
        elif bound.upper > tick:
            codes.append("TIME_INVALID")
        elif (
            cfg.nominal_max_estimate_age_ticks is not None
            and max(tick, through if through is not None else tick) - bound.lower
            > cfg.nominal_max_estimate_age_ticks
        ):
            codes.append("STALE_ESTIMATE")
    if e.uncertainty.representation != "BOUNDED_SET" or e.uncertainty.interpretation_ref is None:
        codes.append("UNCERTAINTY_UNKNOWN")
    stamps = (e.capture, e.publication, e.receipt)
    mapped = tuple(
        map_stamp(cfg, stamp, at_tick=tick) if stamp is not None else None for stamp in stamps
    )
    if any(not isinstance(b, r.BoundSuccess) for b in mapped):
        codes.append("CLOCK_UNKNOWN")
    else:
        capture, publication, receipt = mapped
        if (
            capture.upper > publication.lower
            or publication.upper > receipt.lower
            or receipt.upper > tick
        ):
            codes.append("TIME_INVALID")
        latency = (publication.lower - capture.upper, publication.upper - capture.lower)
        if (
            e.publication_latency_tick_bounds is not None
            and e.publication_latency_tick_bounds != latency
        ):
            codes.append("TIME_INVALID")
    return r.reasons(*codes)


def packet_codes(cfg: r.Configuration, packet: r.Packet | r.Proposal) -> tuple[str, ...]:
    mapping = next((x for x in cfg.clock_mappings if x.mapping_id == packet.clock_mapping_id), None)
    if mapping is None:
        return ("CLOCK_UNKNOWN",)
    period = Fraction(cfg.tick_period_s.numerator, cfg.tick_period_s.denominator)
    for timestamp, declared in zip(packet.timestamps_s, packet.timestamp_control_tick_bounds):
        source = Fraction(timestamp) / period
        if not mapping.valid_source_interval[0] <= source < mapping.valid_source_interval[1]:
            return ("CLOCK_UNKNOWN",)
        value = source * Fraction(mapping.scale_numerator, mapping.scale_denominator) + Fraction(
            mapping.offset_numerator, mapping.offset_denominator
        )
        bounds = (
            value.numerator // value.denominator - mapping.lower_error_ticks,
            -(-value.numerator // value.denominator) + mapping.upper_error_ticks,
        )
        if declared != bounds or bounds[0] < 0:
            return ("TIME_INVALID",)
    if (
        isinstance(packet, r.Packet)
        and packet.handoff_mode == "FIXED"
        and packet.accepted_tick != packet.fixed_deadline_tick
    ):
        return ("APPLICATION_DEADLINE_MISSED",)
    if packet.map_id != cfg.expected_map_id:
        return ("MAP_MISMATCH",)
    if packet.frame_id != cfg.expected_frame_id:
        return ("FRAME_MISMATCH",)
    return ()


def barrier(
    s: r.Snapshot,
    tick: int,
    *,
    session: str | None = None,
    barrier_id: str | None = None,
    epoch: int | None = None,
) -> r.BarrierAck | None:
    target = s.control_session_id if session is None else session
    return next(
        (
            a
            for a in reversed(s.barrier_acknowledgement_ledger)
            if a.control_session_id == target
            and a.installed_epoch == (s.desired_epoch if epoch is None else epoch)
            and a.barrier_id in s.prepared_barrier_ids
            and (barrier_id is None or a.barrier_id == barrier_id)
            and a.queue_cleared
            and a.outcome == "INSTALLED"
            and a.installation_tick is not None
            and a.endpoint_delivery_tick <= a.installation_tick <= a.ack_observed_tick <= tick
            and (
                session is not None
                or (
                    a.ack_id == s.epoch_barrier_ack_id
                    and a.endpoint_session_id == s.endpoint_session_id
                    and a.installed_epoch == s.endpoint_installed_epoch
                )
            )
        ),
        None,
    )


def nominal_codes(
    cfg: r.Configuration,
    s: r.Snapshot,
    tick: int,
    *,
    through: int | None = None,
    require_barrier: bool = True,
) -> tuple[str, ...]:
    codes = list(estimate_codes(cfg, s.latest_estimate, tick, through=through))
    if uncleared(s):
        codes.append("FAULT_LATCHED")
    p = s.active_packet
    if p is None or s.active_policy_id is None:
        codes.append("NO_VALID_POLICY")
    else:
        codes.extend(packet_codes(cfg, p))
        if tick >= p.authority_end_tick or (through is not None and through > p.authority_end_tick):
            codes.append("EXPIRED")
        if tick < p.authority_start_tick:
            codes.append("NOT_YET_VALID")
        if p.map_id != cfg.expected_map_id:
            codes.append("MAP_MISMATCH")
        if p.frame_id != cfg.expected_frame_id:
            codes.append("FRAME_MISMATCH")
        e = evidence(s, p.acceptance_evidence_id)
        codes.extend(evidence_codes(s, e, tick, through=through))
        if e is not None and (
            e.kind not in ("NOMINAL", "ACCEPTANCE")
            or not {"D_NOMINAL", "D_PACKET"} <= set(e.domain_ids)
            or e.policy_id != s.active_policy_id
        ):
            codes.append("DOMAIN_UNKNOWN")
    health = evidence(s, s.latest_estimate.health_evidence_id if s.latest_estimate else None)
    codes.extend(evidence_codes(s, health, tick, through=through))
    if health is None or health.kind != "HEALTH":
        codes.append("HEALTH_INVALID")
    if require_barrier and barrier(s, tick) is None:
        codes.append("BARRIER_UNACKNOWLEDGED")
    return r.reasons(*codes)


def rest_codes(
    cfg: r.Configuration, s: r.Snapshot, tick: int, supplied: r.Evidence | None = None
) -> tuple[str, ...]:
    rest = (
        supplied
        if supplied is not None
        else next((e for e in reversed(s.evidence) if e.kind == "REST_HOLD"), None)
    )
    codes = list(evidence_codes(s, rest, tick))
    if rest is not None and rest.kind != "REST_HOLD":
        codes.append("DOMAIN_UNKNOWN")
    e = s.latest_estimate
    codes.extend(estimate_codes(cfg, e, tick))
    if e is None or e.state_si is None or any(v != 0 for v in e.state_si[:3]):
        codes.append("DOMAIN_UNKNOWN")
    return r.reasons(*codes)


def permission_codes(
    cfg: r.Configuration,
    s: r.Snapshot,
    c: r.Command,
    tick: int,
    *,
    start: int,
    end: int,
    bounds: tuple[int, int],
    hold: int,
    reauthorize: bool = False,
) -> tuple[str, ...]:
    # First denying category wins, while fault closure is evaluated separately.
    if c.session_id != s.control_session_id:
        return ("SESSION_MISMATCH",)
    if any(x.command_id == c.command_id for x in s.cancellation_history):
        return ("CANCELLED",)
    if not reauthorize and c.generation_epoch != s.desired_epoch:
        return ("EPOCH_MISMATCH",)
    if s.state not in ("NORMAL", "WARNING"):
        return ("FAULT_LATCHED",) if uncleared(s) else ("NO_VALID_POLICY",)
    codes = nominal_codes(cfg, s, tick, through=max(hold, end))
    if codes:
        return codes
    p = (
        next((x for x in s.accepted_packet_history if x.packet_id == c.source_packet_id), None)
        if reauthorize
        else s.active_packet
    )
    if (
        p is None
        or c.source_packet_id != p.packet_id
        or c.source_controller_id != p.source_controller_id
        or c.source_manifest_sha256 != p.source_manifest_sha256
        or c.mode != "NOMINAL"
        or s.latest_estimate is None
        or (
            not reauthorize
            and (
                c.policy_id != s.active_policy_id or c.estimate_id != s.latest_estimate.estimate_id
            )
        )
    ):
        return ("IDENTITY_CONFLICT",)
    generated = map_stamp(cfg, c.generated, at_tick=tick)
    if isinstance(generated, r.BoundFailure):
        return generated.reason_codes
    capture = (
        map_stamp(cfg, s.latest_estimate.capture, at_tick=tick)
        if s.latest_estimate.capture
        else None
    )
    if (
        not reauthorize
        and (not isinstance(capture, r.BoundSuccess) or capture.upper > generated.lower)
    ) or generated.upper > c.requested_application_tick:
        return ("TIME_INVALID",)
    if generated.upper > tick or tick > c.latest_application_tick:
        return ("APPLICATION_DEADLINE_MISSED",)
    return r.reasons(
        *(
            x.reason_code
            for x in validate_interval(
                start=start,
                end=end,
                application_bounds=bounds,
                latest_application=c.latest_application_tick,
                hold_end=hold,
            )
        ),
        *("EXPIRED",) if end > p.authority_end_tick else (),
    )


def reauthorization_codes(
    s: r.Snapshot, c: r.Command, identities: tuple[str, ...], tick: int, end: int
) -> tuple[str, ...]:
    current = evidence(s, s.active_packet.acceptance_evidence_id if s.active_packet else None)
    assertions = tuple(evidence(s, identity) for identity in identities)
    if current is None or not assertions or any(e is None for e in assertions):
        return ("DOMAIN_UNKNOWN",)
    found = False
    for e in assertions:
        if tick < e.valid_from_tick:
            return ("NOT_YET_VALID",)
        if tick >= e.valid_until_tick or end > e.valid_until_tick:
            return ("EXPIRED",)
        if (
            e.result != "SATISFIED"
            or e.context_revision != current.context_revision
            or s.latest_estimate is None
            or e.estimate_id != s.latest_estimate.estimate_id
        ):
            return ("DOMAIN_UNKNOWN",)
        if e.kind == "REAUTHORIZATION":
            found = True
            if (
                e.source_packet_id != c.source_packet_id
                or e.policy_id != s.active_policy_id
                or e.uncertainty_interpretation_ref
                != s.latest_estimate.uncertainty.interpretation_ref
            ):
                return ("DOMAIN_UNKNOWN",)
    return () if found else ("DOMAIN_UNKNOWN",)
