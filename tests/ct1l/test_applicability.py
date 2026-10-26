"""O01/O18 literal box, slew, memory, pending and authority cases; no hybrid map."""

from dataclasses import replace

import pytest


def test_original_pending_evidence_is_not_assumed_complete(inputs):
    from ct1.inputs import (
        load_authority_and_command_history,
        load_candidate_tuples,
        load_original_packet,
    )
    from ct1.qualification import classify_feedback_applicability

    c = inputs.candidates[0]
    p = load_candidate_tuples(inputs, c.candidate_id).unwrap()[0]
    packet = load_original_packet(inputs, p.packet_id).unwrap()
    h = load_authority_and_command_history(inputs, p.candidate_id).unwrap()
    app = classify_feedback_applicability(p, h, packet)
    assert not app.hybrid_event_map_available and not app.pending_information_complete
    assert "PENDING_OR_DELAYED_COMMAND" in app.flags


@pytest.mark.parametrize(
    "ey,previous,complete,expiry,end,flag",
    [
        (-0.5, 0.0, True, 2.0, 2.0, "SATURATED_BOX"),
        (-0.4, 0.0, True, 2.0, 2.0, "CLIP_TIE_NONDIFFERENTIABLE"),
        (-0.1, 0.0, True, 2.0, 2.0, "SLEW_ACTIVE"),
        (-0.01, 0.0, True, 2.0, 2.0, "CLIP_TIE_NONDIFFERENTIABLE"),
        (0.0, 0.0, False, 2.0, 2.0, "PENDING_OR_DELAYED_COMMAND"),
        (0.0, 0.0, True, 1.0, 1.0, "AUTHORITY_EXPIRED"),
        (0.0, 0.0, True, 2.0, 1.0, "AUTHORITY_SUPERSEDED"),
    ],
)
def test_literal_actuator_and_authority_branches(point, ey, previous, complete, expiry, end, flag):
    from ct1.contracts import ArchivedPacket, AuthorityInterval, CausalHistory, FileBinding
    from ct1.qualification import classify_feedback_applicability

    a = AuthorityInterval(
        0.0, end, expiry, 1.0 if end == 1.0 else None, 0, "SYNTHETIC_NOT_PERFORMANCE"
    )
    packet = ArchivedPacket(
        {"plan_id": 0},
        (0.0, 2.0),
        (point.x, point.x),
        ((0.0, 0.0),),
        (0.0,),
        ((1.0, 0.0, 0.0, 0.0),),
        (0.0, 0.0),
        FileBinding("literal", "a" * 64),
        (a,),
    )
    p = replace(point, x=point.x[:5] + (ey,))
    h = CausalHistory(p.x, 1.0, (0.0, 0.0), 0, 0.99, previous, None, complete, a, (), ())
    app = classify_feedback_applicability(p, h, packet)
    assert flag in app.flags and not app.hybrid_event_map_available
