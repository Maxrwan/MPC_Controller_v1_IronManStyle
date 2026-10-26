"""Literal boundary arithmetic independent of authority guards."""

from dataclasses import replace

import pytest
from apex.safety_authority import records as r
from apex.safety_authority.time import map_stamp, validate_interval
from oracle_support import cases, decode_inputs


@pytest.mark.parametrize(
    "upper,hold,expected", [(39, 40, ()), (40, 40, ("EXPIRED",)), (39, 41, ("EXPIRED",))]
)
def test_half_open_end_and_closed_hold_endpoint(upper, hold, expected):
    actual = validate_interval(
        start=20, end=40, application_bounds=(39, upper), latest_application=39, hold_end=hold
    )
    # Upper40 also exceeds latest39. Preserve both independent denial causes.
    codes = tuple(e.reason_code for e in actual)
    assert ("EXPIRED" in codes) == ("EXPIRED" in expected)
    assert ("APPLICATION_DEADLINE_MISSED" in codes) == (upper == 40)
    assert not codes if not expected else codes


def test_affine_mapping_outward_rounding():
    cfg, snap = decode_inputs(cases()[0])
    mapping = replace(
        cfg.clock_mappings[0],
        scale_numerator=1,
        scale_denominator=2,
        offset_numerator=1,
        offset_denominator=3,
        lower_error_ticks=1,
        upper_error_ticks=2,
    )
    cfg = replace(cfg, clock_mappings=(mapping,))
    stamp = replace(
        snap.latest_estimate.capture,
        source_tick=5,
        control_tick_bounds=None,
        unknown_reason="Conservative mapping supplied separately",
    )
    bound = map_stamp(cfg, stamp, at_tick=20)
    assert isinstance(bound, r.BoundSuccess)
    assert (bound.lower, bound.upper) == (1, 5)  # floor(17/6)-1, ceil(17/6)+2


def test_clock_reset_does_not_reuse_old_mapping():
    cfg, snap = decode_inputs(cases()[0])
    stamp = replace(snap.latest_estimate.capture, clock_session_id="RESET_CLOCK")
    assert isinstance(map_stamp(cfg, stamp, at_tick=20), r.BoundFailure)


def test_crossed_freshness_boundary_latches_before_later_fresh_observation():
    from apex.safety_authority.ordering import seal_batch
    from apex.safety_authority.reducer import reduce_batch

    cfg, snap = decode_inputs(next(c for c in cases() if c["case_id"] == "E05-EXACT-DUPLICATE"))
    stamp = replace(snap.latest_estimate.capture, source_tick=102, control_tick_bounds=(102, 102))
    estimate = replace(
        snap.latest_estimate, estimate_id="E102", capture=stamp, publication=stamp, receipt=stamp
    )
    event = r.Event(
        event_id="fresh-after-boundary",
        producer_id="TOY_INPUT",
        producer_sequence=1,
        at_tick=102,
        causal_parent_ids=(),
        kind="ESTIMATE_OBSERVED",
        payload=estimate,
    )
    sealed = seal_batch(cfg, snap, batch_id="crossed-age", at_tick=102, events=(event,))
    assert isinstance(sealed, r.DecodeSuccess)
    result = reduce_batch(cfg, snap, sealed.value)
    assert result.snapshot.state == "NO_VALID_POLICY"
    assert result.snapshot.desired_epoch == 2
    assert "p1" in result.snapshot.revoked_permission_ids
    assert any(t.at_tick == 101 and "STALE_ESTIMATE" in t.reason_codes for t in result.traces)
    assert not any(t.granted_permission_ids for t in result.traces)
