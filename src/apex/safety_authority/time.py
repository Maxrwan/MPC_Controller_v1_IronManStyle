"""Pure exact rational clock bounds and integer authority boundaries."""

from __future__ import annotations

from fractions import Fraction

from . import records as r


def map_stamp(
    configuration: r.Configuration, stamp: r.ClockStamp, *, at_tick: r.Tick
) -> r.BoundSuccess | r.BoundFailure:
    r._check(at_tick, int, "at_tick")
    if at_tick < 0:
        raise ValueError("nonnegative at_tick required")
    mappings = tuple(
        m
        for m in configuration.clock_mappings
        if m.mapping_id == stamp.mapping_id
        and m.source_clock_id == stamp.clock_id
        and m.source_session_id == stamp.clock_session_id
        and m.control_clock_id == configuration.control_clock_id
    )
    if len(mappings) != 1:
        return r.BoundFailure(
            reason_codes=("CLOCK_UNKNOWN",),
            unknowns=(
                r.UnknownField(field="clock_mapping", reason="absent or reset/session mismatch"),
            ),
        )
    m = mappings[0]
    if not m.valid_source_interval[0] <= stamp.source_tick < m.valid_source_interval[1]:
        return r.BoundFailure(
            reason_codes=("CLOCK_UNKNOWN",),
            unknowns=(
                r.UnknownField(field="clock_mapping", reason="outside declared source interval"),
            ),
        )
    v = Fraction(stamp.source_tick * m.scale_numerator, m.scale_denominator) + Fraction(
        m.offset_numerator, m.offset_denominator
    )
    lo = v.numerator // v.denominator - m.lower_error_ticks
    hi = -(-v.numerator // v.denominator) + m.upper_error_ticks
    if lo < 0 or (stamp.control_tick_bounds is not None and stamp.control_tick_bounds != (lo, hi)):
        return r.BoundFailure(
            reason_codes=("TIME_INVALID",),
            unknowns=(
                r.UnknownField(
                    field="control_tick_bounds", reason="negative or inconsistent supplied bounds"
                ),
            ),
        )
    return r.BoundSuccess(lower=lo, upper=hi, mapping_id=m.mapping_id)


def validate_interval(
    *,
    start: r.Tick,
    end: r.Tick,
    application_bounds: tuple[r.Tick, r.Tick],
    latest_application: r.Tick,
    hold_end: r.Tick,
) -> tuple[r.InputError, ...]:
    vals = (start, end, *application_bounds, latest_application, hold_end)
    if any(type(x) is not int or x < 0 for x in vals) or len(application_bounds) != 2:
        return (
            r.InputError(
                path="interval",
                reason_code="TIME_INVALID",
                message="nonnegative integer bounds required",
            ),
        )
    lo, hi = application_bounds
    codes = []
    if start >= end or lo > hi or hold_end < hi or latest_application < lo:
        codes.append("TIME_INVALID")
    if lo < start:
        codes.append("NOT_YET_VALID")
    if hi >= end or latest_application >= end or hold_end > end:
        codes.append("EXPIRED")
    if hi > latest_application:
        codes.append("APPLICATION_DEADLINE_MISSED")
    return tuple(
        r.InputError(path="interval", reason_code=c, message="half-open interval check: " + c)
        for c in r.reasons(*codes)
    )


def boundaries(
    configuration: r.Configuration, snapshot: r.Snapshot, target: r.Tick
) -> tuple[r.Tick, ...]:
    ticks = {
        p.valid_until_tick
        for p in snapshot.permissions
        if p.permission_id not in snapshot.revoked_permission_ids
    }
    ticks.update(e.valid_until_tick for e in snapshot.evidence)
    if snapshot.active_packet is not None:
        ticks.add(snapshot.active_packet.authority_end_tick)
    e = snapshot.latest_estimate
    if (
        e is not None
        and e.capture is not None
        and configuration.nominal_max_estimate_age_ticks is not None
    ):
        b = map_stamp(configuration, e.capture, at_tick=snapshot.current_tick)
        if isinstance(b, r.BoundSuccess):
            ticks.add(b.lower + configuration.nominal_max_estimate_age_ticks + 1)
    return tuple(sorted(t for t in ticks if snapshot.current_tick < t <= target))
