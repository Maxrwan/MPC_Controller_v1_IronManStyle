"""Local no-output and source-bound application tests; no physical endpoint."""

from dataclasses import replace

import pytest
from test_preintegration_session import fb, ready

from apex.preintegration.records import Feedback
from apex.preintegration.validation import BoundaryError, command


@pytest.mark.parametrize(
    "feedback,time,reason",
    [
        (None, 0.01, "FEEDBACK_MISSING"),
        (Feedback(1, 0, (2, 0, 0, 0, 0, 0)), 0.01, "STALE_FEEDBACK"),
        (Feedback(1, 0.02, (2, 0, 0, 0, 0, 0)), 0.01, "FUTURE_FEEDBACK"),
        (Feedback(1, 0.01, (2, 0, 0, 0, 0, 0), "foreign"), 0.01, "CLOCK_MISMATCH"),
        (Feedback(True, 0.01, (2, 0, 0, 0, 0, 0)), 0.01, "SAMPLE_ID_INVALID"),
        (Feedback(1, 0.01, (float("nan"), 0, 0, 0, 0, 0)), 0.01, "BOUNDARY_EXCEPTION"),
        (Feedback(1, 0.01, (2, 0, 0, 0, -1, 0)), 0.01, "BOUNDARY_EXCEPTION"),
        (Feedback(1, 0.01, (2, 0)), 0.01, "BOUNDARY_EXCEPTION"),
    ],
)
def test_invalid_feedback_never_reaches_endpoint(feedback, time, reason):
    session, endpoint = ready(), []
    out = session.propose(feedback, time, [0, 0])
    if out.command is not None:
        endpoint.append(out.command)
    assert not endpoint and out.reasons == (reason,) and session.inhibited
    assert session.propose(fb(0.02, 2), 0.02, [0, 0]).command is None


def test_same_sample_same_instant_then_conflict_and_backward_time():
    session = ready()
    p = session.propose(fb(0.01, 1), 0.01, [0, 0])
    assert session.check_application(p, fb(0.01, 1), 0.01, [0, 0], 0).command is not None
    assert session.propose(fb(0.01, 1, state=(3, 0, 0, 0, 0.02, 0)), 0.01, [0, 0]).reasons == (
        "SAMPLE_CONFLICT",
    )
    other = ready()
    other.propose(fb(0.02, 2), 0.02, [0, 0])
    assert other.propose(fb(0.01, 3), 0.01, [0, 0]).reasons == ("TIME_BACKWARDS",)


@pytest.mark.parametrize(
    "value", [[0.41, 0], [-0.41, 0], [0, -3.1], [0, 2.1], [float("inf"), 0], [0]]
)
def test_invalid_external_command_not_clipped_to_valid(value):
    with pytest.raises((BoundaryError, ValueError)):
        command(value, [-0.4, -3], [0.4, 2])


def test_pending_original_source_survives_handoff_but_not_expiry():
    session = ready()
    p = session.propose(fb(0.01, 1), 0.01, [0, 0])
    prepared, _ = session.prepare(fb(0.02, 2), 0.02, 0, plan_id=1, applied=[0, 0])
    assert session.complete(prepared, fb(0.02, 2), 0.02).status == "ACCEPTED"
    result = session.check_application(p, fb(0.025, 3), 0.025, [0, 0], 0)
    assert result.command is not None and result.plan_id == 0
    assert session.check_application(p, fb(0.03, 4), 0.03, [0, 0], 0).reasons == (
        "DUPLICATE_APPLICATION",
    )
    other = ready()
    p = other.propose(fb(0.01, 1), 0.01, [0, 0])
    assert other.check_application(p, fb(0.4, 2), 0.4, [0, 0], 0).reasons == ("AUTHORITY_EXPIRED",)


def test_proposal_tampering_and_journal_failure_inhibit():
    session = ready()
    p = session.propose(fb(0.01, 1), 0.01, [0, 0])
    assert session.check_application(
        replace(p, command=(0.1, 0)), fb(0.02, 2), 0.02, [0, 0], 0
    ).reasons == ("PROPOSAL_IDENTITY",)
    other = ready()

    def broken(event):
        raise OSError("injected disk failure")

    other.journal = broken
    out = other.propose(fb(0.01, 1), 0.01, [0, 0])
    assert out.command is None and not other.evidence_valid
    assert out.reasons == ("EVIDENCE_WRITE_FAILURE",)


def test_invalid_time_is_fault_evidence_not_invalid_json():
    from preintegration.evidence import project

    session = ready()
    out = session.propose(fb(0.01, 1), float("nan"), [0, 0])
    assert out.command is None and out.time is None and out.reasons == ("TIME_INVALID",)
    assert project(session.events[-1])["time"] is None


def test_current_model_domain_rejection_and_caller_observation_binding():
    session = ready()

    def invalid_state(x, u):
        if x[0] < 0.5:
            raise ValueError("native model speed domain")

    session.components.validator = invalid_state
    assert session.propose(fb(0.01, 1, state=(0.1, 0, 0, 0, 0, 0)), 0.01, [0, 0]).command is None
    other = ready()
    proposed = other.propose(fb(0.01, 1), 0.01, [0, 0])
    checked = other.check_application(proposed, fb(0.02, 2), 0.02, [0, 0], 0)
    assert other.observe_applied(checked, fb(0.02, 2), 0.02).status == "OBSERVED_BY_CALLER"
    assert other.observe_applied(checked, fb(0.03, 3), 0.03).command is None
    assert other.inhibited


def test_independent_simultaneous_feedback_faults_are_retained():
    session = ready()
    result = session.propose(Feedback(True, 0, (2, 0, 0, 0, 0, 0), "foreign"), 0.01, [0, 0])
    assert result.reasons == ("SAMPLE_ID_INVALID", "CLOCK_MISMATCH", "STALE_FEEDBACK")
    assert session.events[-1].reasons == result.reasons and result.command is None
