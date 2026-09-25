import numpy as np
import pytest

from apex.simulation.runner import RunConfig, SimulationRunner
from apex.simulation.timing import LatencyConfig, staleness
from apex.state import StateIndex as S


class MovingPlant:
    def __init__(self):
        self.intervals = []
        self.time = 0.0

    def step(self, state, control, dt):
        self.intervals.append((self.time, self.time + dt, control.copy()))
        self.time += dt
        state[S.S_ABS] += state[S.VX] * dt
        state[S.E_Y] += control[0] * dt
        return state


class Controller:
    def __init__(self):
        self.samples = []

    def compute_control(self, state, context):
        self.samples.append((context["time"], state.copy()))
        return np.array([0.2, 0])


def run(track, latency, duration=0.3):
    model, controller = MovingPlant(), Controller()
    result = SimulationRunner(
        model,
        controller,
        track,
        RunConfig(duration=duration, dt_control=0.05, latency=LatencyConfig("injected", latency)),
        initial_control=np.array([0.1, 0]),
    ).run(np.array([2.0, 0, 0, 0, 0, 0]))
    return model, controller, result


@pytest.mark.parametrize("latency", [0.01, 0.025, 0.045, 0.06, 0.1, 0.0137])
def test_motion_hold_and_staleness(circle, latency):
    model, c, result = run(circle, latency)
    first = result.events[0]
    assert first["application_time"] == pytest.approx(latency)
    assert first["delta_s_abs"] == pytest.approx(2 * latency)
    assert first["delta_e_y"] == pytest.approx(0.1 * latency)
    assert first["staleness_index"] == pytest.approx(latency)
    for start, end, u in model.intervals:
        assert end - start <= 0.005 + 1e-12
        if start < latency - 1e-12:
            assert u[0] == 0.1
        elif start < 0.05 + latency:
            assert u[0] == 0.2
    assert np.isclose(sum(b - a for a, b, _ in model.intervals), 0.3)


@pytest.mark.parametrize(
    "latency,missed,frequency",
    [(0.0, 0, 20.0), (0.01, 0, 20.0), (0.045, 0, 20.0), (0.06, 3, 10.0), (0.1, 4, 2 / 0.3)],
)
def test_deadline_policy(circle, latency, missed, frequency):
    _, c, r = run(circle, latency)
    assert r.timing["nominal_releases"] == 6
    assert r.timing["missed_deadlines"] == missed
    assert r.timing["effective_update_hz"] == pytest.approx(frequency)
    assert len(c.samples) + missed == 6


def test_zero_latency_compatibility(circle):
    _, _, timed = run(circle, 0.0)
    regular = SimulationRunner(
        MovingPlant(), Controller(), circle, RunConfig(duration=0.3, dt_control=0.05)
    ).run(np.array([2.0, 0, 0, 0, 0, 0]))
    np.testing.assert_allclose(
        [[r[k] for k in ("time", "s_abs", "e_y", "delta")] for r in timed.states],
        [[r[k] for k in ("time", "s_abs", "e_y", "delta")] for r in regular.states],
        atol=1e-14,
    )
    assert all(e["staleness_index"] == 0 for e in timed.events)


def test_repeatable_injected_timing(circle):
    a = run(circle, 0.06)[2]
    b = run(circle, 0.06)[2]
    assert a.states == b.states and a.controls == b.controls and a.timing == b.timing
    for ea, eb in zip(a.events, b.events):
        for key in ea:
            if key not in ("solve_time", "controller_compute_time"):
                assert ea[key] == eb[key]


def test_staleness_excludes_progress():
    a = np.zeros(6)
    b = np.array([0.5, 0.5, 1, 0.1, 100, 0.1])
    delta, index = staleness(a, b)
    np.testing.assert_array_equal(delta, b)
    assert index == pytest.approx(np.sqrt(5))


def test_measured_timer_is_logged(circle):
    result = SimulationRunner(
        MovingPlant(),
        Controller(),
        circle,
        RunConfig(duration=0.1, dt_control=0.05, latency=LatencyConfig("measured")),
    ).run(np.array([2.0, 0, 0, 0, 0, 0]))
    assert all(e["solve_time"] >= 0 and e["latency"] == e["solve_time"] for e in result.events)


@pytest.mark.parametrize("mode,latency", [("bad", 0), ("injected", -1), ("injected", np.nan)])
def test_invalid_latency(mode, latency):
    with pytest.raises(ValueError):
        LatencyConfig(mode, latency)
