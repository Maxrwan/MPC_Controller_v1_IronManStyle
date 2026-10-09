"""D5 mathematical record analysis; no solver calls or physical simulations."""

from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
from task007d.forensics import (
    accepted_packets,
    active_at,
    audit_nominals,
    clearance,
    comparisons,
    describe,
    interpolate_progress,
    low_latency_tables,
    paired_row,
)

from apex.control.trajectory.packet import TrajectoryPacket
from apex.state import STATE_NAMES


class Track:
    length = 10.0

    def sample(self, s):
        return SimpleNamespace(track_s=s, left_width=2.0, right_width=1.0, curvature=0.0)


def packet(pid=0, start=0, completion=0):
    x = np.array([[2, 0, 0, 0, 1, 0.1], [2, 0, 0, 0, 3, 0.3]])
    return TrajectoryPacket(
        pid,
        0,
        0,
        start,
        completion,
        np.array([start, start + 2]),
        x,
        np.array([[0.1, 0.2]]),
        x[0],
        x[0],
        "fixture",
        0,
        0,
    )


def rows():
    return [dict(time=0.0, s_abs=1.0, e_y=0.1), dict(time=2.0, s_abs=3.0, e_y=0.3)]


def test_spatial_interpolation_retains_exact_knots_and_brackets_without_mutation():
    data = rows()
    data[0]["plan_id"], data[1]["plan_id"] = 2, 3
    before = deepcopy(data)
    x = interpolate_progress(data, 2.0)
    assert x["time"] == 1.0
    assert x["e_y"] == pytest.approx(0.2, rel=0, abs=1e-12)
    assert x["kind"] == "linear_progress_interpolation"
    assert (x["bracket_start_time"], x["bracket_end_time"]) == (0.0, 2.0)
    assert "plan_id" not in x
    for r in data:
        exact = interpolate_progress(data, r["s_abs"])
        assert exact["e_y"] == r["e_y"] and exact["kind"] == "recorded_knot"
    assert data == before


@pytest.mark.parametrize("progress", [0.99, 3.01, float("nan")])
def test_spatial_extrapolation_rejected(progress):
    with pytest.raises(ValueError, match="coverage"):
        interpolate_progress(rows(), progress)


@pytest.mark.parametrize(
    "key,value", [("s_abs", 1.0), ("s_abs", 0.0), ("time", 0.0), ("e_y", float("nan"))]
)
def test_invalid_spatial_history_rejected(key, value):
    data = rows()
    data[1][key] = value
    with pytest.raises(ValueError):
        interpolate_progress(data, 1.0)


def test_signed_boundary_and_decomposition_even_when_limiting_side_switches():
    p = [(0, packet())]
    a = describe(dict(time=0.0, s_abs=1.0, e_y=1.5), p, Track(), [dict(name="s", start_s_m=0)])
    b = describe(dict(time=0.0, s_abs=1.0, e_y=-0.8), p, Track(), [dict(name="s", start_s_m=0)])
    assert clearance(2.0, 1.0, 1.5)["boundary"] == "left"
    assert b["boundary"] == "right"
    delta = paired_row(a, b)
    assert delta["clearance_B_minus_A"] == pytest.approx(-0.3, rel=0, abs=1e-12)
    assert delta["right_clearance_B_minus_A"] == pytest.approx(-2.3, rel=0, abs=1e-12)
    assert delta["right_tracking_contribution"] == pytest.approx(-2.3, rel=0, abs=1e-12)
    assert delta["right_nominal_contribution"] == 0


def test_active_authority_uses_handoff_not_packet_start_and_trims():
    zero, one = packet(), packet(1, 0.1, 0.5)
    raw = dict(
        states=[dict(time=0, plan_id=0)],
        packets=[zero.as_dict(), one.as_dict()],
        handoffs=[dict(time=0.5, plan_id=1, accepted=True)],
    )
    before = deepcopy(raw)
    timeline = accepted_packets(raw)
    assert active_at(timeline, 0.49).plan_id == 0
    assert active_at(timeline, 0.5).plan_id == 1
    assert timeline[1][1].timestamps[0] == 0.5
    np.testing.assert_array_equal(timeline[1][1].sample(0.5)[0], one.sample(0.5)[0])
    assert raw == before
    with pytest.raises(ValueError):
        active_at(timeline, -0.01)
    raw["handoffs"][0]["time"] = 0.2
    with pytest.raises(ValueError, match="availability"):
        accepted_packets(raw)


def test_spatial_packet_selection_does_not_interpolate_packet_ids():
    timeline = [(0, packet()), (0.5, packet(1).trim(0.5))]
    r = interpolate_progress(rows(), 2.0)
    d = describe(r, timeline, Track(), [dict(name="s", start_s_m=0)])
    assert d["time"] == 1 and d["plan_id"] == 1
    with pytest.raises(ValueError, match="authority"):
        describe({**r, "plan_id": 0}, timeline, Track(), [dict(name="s", start_s_m=0)])


def test_common_coverage_never_extrapolates_or_uses_longer_tail():
    timeline = [(0, packet())]
    sectors = [dict(name="s", start_s_m=0)]
    a = [describe(r, timeline, Track(), sectors) for r in rows()]
    b = [
        describe(r, timeline, Track(), sectors)
        for r in [dict(time=0.0, s_abs=1.0, e_y=0.1), dict(time=1.0, s_abs=2.0, e_y=0.2)]
    ]
    coverage, temporal, spatial = comparisons(
        a, b, {"A": timeline, "B": timeline}, Track(), sectors
    )
    assert coverage["time_end"] == 1 and coverage["progress_end"] == 2
    assert len(temporal) == 1  # Only truly shared recorded event times.
    assert max(r["A_s_abs"] for r in spatial) == 2
    assert spatial[-1]["A_kind"] == "linear_progress_interpolation"
    assert spatial[-1]["B_kind"] == "recorded_knot"


def test_nominal_audit_uses_sample_authority_even_if_application_is_after_handoff():
    zero, one = packet(), packet(1, 0.1, 0.5)
    x, u, _ = zero.sample(0.4)
    command = dict(
        time=0.4, application_time=0.6, plan_id=0, nominal_delta=u[0], nominal_a_cmd=u[1]
    )
    command.update({"reference_" + k: v for k, v in zip(STATE_NAMES, x)})
    command.update({"error_" + k: 0 for k in STATE_NAMES})
    raw = dict(
        states=[dict(time=0.4, **dict(zip(STATE_NAMES, x)))], controls=[command], handoffs=[]
    )
    timeline = [(0, zero), (0.5, one.trim(0.5))]
    assert audit_nominals(raw, timeline)["maximum_absolute_reference_or_error_difference"] == 0
    command["reference_e_y"] += 0.01
    with pytest.raises(ValueError, match="retained references"):
        audit_nominals(raw, timeline)


def scores():
    return [
        dict(
            plan_id=i,
            release_time=i * 0.1,
            target_time=i * 0.1 + 0.017,
            readiness_minus_target=0.018,
            accepted_handoff_minus_target=0.02,
            pending=True,
            pending_application_time=i * 0.1,
            errors={"A": [a] * 6, "B": [b] * 6},
        )
        for i, a, b in [(1, 3.0, 1.0), (2, -4.0, -2.0), (3, 0.0, 1.0), (4, 1.0, 1.0 + 1e-13)]
    ]


def test_phase_squared_error_shares_signs_counts_and_roundoff_ties():
    data = scores()
    before = deepcopy(data)
    details, phases = low_latency_tables(data, "R1", "A")
    assert data == before
    r = [p for p in phases if p["state"] == "r"]
    assert r[0]["A_squared_error_share_percent"] == pytest.approx(900 / 26, rel=0, abs=1e-12)
    assert r[1]["A_rms"] == 4 and r[1]["B_rms"] == 2
    assert r[2]["worse"] == 1 and r[2]["tie"] == 1
    second = next(d for d in details if d["release_number"] == 2 and d["state"] == "r")
    assert second["A_signed"] == -4 and second["A_absolute"] == 4
    assert second["readiness_minus_target"] != second["accepted_handoff_minus_target"]


def test_censored_release_does_not_shift_phase_or_create_zero_error():
    data = scores()
    data[0]["errors"]["B"] = None
    details, phases = low_latency_tables(data, "R2", "B")
    assert phases[0]["excluded"] == 1 and phases[0]["A_rms"] is None
    assert details[0]["outcome"] == "excluded" and details[0]["absolute_increase"] is None
    assert phases[1]["A_rms"] == 4  # Actual release 2, not first comparable release.
    assert low_latency_tables([], "R1", "A")[1][0]["A_rms"] is None
