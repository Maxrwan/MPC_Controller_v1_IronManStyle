"""C0 stop-gate evidence on the unchanged scheduler, not a fixed-mode implementation."""

import numpy as np
import pytest
from test_async_chronology import run


def off_grid_case(parameters, track):
    """Existing isolated straight planner, real NumPy plant and unmodified urgent policy."""
    return run(parameters, track, injected_delay=0.155, disturbance_time=0.15)


def urgent_release(result):
    return next(p for p in result["plans"] if p.get("urgent"))


def test_busy_urgent_request_releases_at_off_grid_completion(dynamic_vehicle, straight_geometry):
    result = off_grid_case(dynamic_vehicle, straight_geometry)
    assert result["failure"] is None and not result["fallbacks"]
    trigger = next(t for t in result["triggers"] if t["kind"] == "urgent_replan")
    assert trigger["busy"] and trigger["time"] == pytest.approx(0.16, abs=1e-12)
    first, urgent = result["plans"][1:3]
    assert first["release_time"] == 0.1
    assert first["completion_time"] == urgent["release_time"] == 0.255
    assert urgent["urgent"] and urgent["plan_id"] == 2
    assert any(m["time"] == 0.2 and m["reason"] == "planner_busy" for m in result["misses"])
    assert all(
        a["completion_time"] <= b["release_time"] + 1e-10
        for a, b in zip(result["plans"][1:], result["plans"][2:])
    )
    during = [s for s in result["states"] if 0.1 <= s["time"] < 0.255]
    assert during[-1]["s_abs"] > during[0]["s_abs"]
    assert {s["plan_id"] for s in during} == {0}
    updates = [c for c in result["controls"] if 0.1 <= c["time"] < 0.255]
    assert len(updates) >= 15
    np.testing.assert_allclose(np.diff([c["time"] for c in updates]), 0.01, rtol=0, atol=1e-12)
    assert result["plans"][0]["startup"]
    assert result["plans"][0]["completion_time"] == 0


def test_every_eligible_offset_preserves_the_off_grid_phase(dynamic_vehicle, straight_geometry):
    release = urgent_release(off_grid_case(dynamic_vehicle, straight_geometry))["release_time"]
    for ticks in range(1, 11):
        offset = ticks * 0.01
        target = release + offset
        nearest_grid = round(target / 0.01) * 0.01
        assert abs(target - nearest_grid) == pytest.approx(0.005, rel=0, abs=1e-12)
        assert abs(target - nearest_grid) > 1e-10  # Existing scheduler event tolerance.
    assert release + 0.07 == 0.325
    # Rounding takeover or delaying release to the next grid changes the prescribed contract.
    assert (0.33 - release) != pytest.approx(0.07, rel=0, abs=1e-12)
    assert (0.26 + 0.07) != pytest.approx(release + 0.07, rel=0, abs=1e-12)


def test_unblocked_urgent_release_can_be_on_grid(dynamic_vehicle, straight_geometry):
    result = run(
        dynamic_vehicle,
        straight_geometry,
        injected_delay=0.025,
        disturbance_time=0.035,
    )
    assert result["failure"] is None
    release = urgent_release(result)["release_time"]
    assert release == pytest.approx(0.05, rel=0, abs=1e-12)
    assert release + 0.07 == pytest.approx(0.12, rel=0, abs=1e-12)


def test_counterexample_has_deterministic_physical_chronology(dynamic_vehicle, straight_geometry):
    first = off_grid_case(dynamic_vehicle, straight_geometry)
    second = off_grid_case(dynamic_vehicle, straight_geometry)
    for channel in ("states", "handoffs", "releases", "misses", "triggers", "reserves"):
        assert first[channel] == second[channel]
    physical = (
        "time",
        "application_time",
        "plan_id",
        "requested_delta",
        "requested_a_cmd",
        "delta",
        "a_cmd",
    )
    assert [[c[k] for k in physical] for c in first["controls"]] == [
        [c[k] for k in physical] for c in second["controls"]
    ]
