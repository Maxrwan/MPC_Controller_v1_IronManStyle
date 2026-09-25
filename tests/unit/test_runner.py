import numpy as np
import pytest

from apex.models.errors import FrenetGeometryError
from apex.simulation.metrics import tracking_metrics
from apex.simulation.runner import RunConfig, SimulationRunner
from apex.state import StateIndex as S


class CountingController:
    def __init__(self):
        self.times = []

    def compute_control(self, state, context):
        self.times.append(context["time"])
        return np.array([0.01 * len(self.times), 0])


class RecordingModel:
    def __init__(self):
        self.actions = []

    def step(self, state, action, dt):
        self.actions.append(action.copy())
        state[S.S_ABS] += state[S.VX] * dt
        return state


def test_rates_hold_and_input_immutability(circle, tmp_path):
    model, controller = RecordingModel(), CountingController()
    initial = np.array([2.0, 0, 0, 0, 0, 0])
    result = SimulationRunner(model, controller, circle, RunConfig(duration=0.04)).run(initial)
    assert controller.times == [0, 0.01, 0.02, 0.03]
    np.testing.assert_allclose(
        np.array(model.actions)[:, 0], np.repeat([0.01, 0.02, 0.03, 0.04], 2)
    )
    assert len(result.states) == 9
    assert initial[S.S_ABS] == 0
    result.write_csv(tmp_path)
    assert (tmp_path / "states.csv").read_text().count("\n") == 10


@pytest.mark.parametrize(
    "config",
    [
        dict(dt_control=0.007),
        dict(duration=0.003),
        dict(target_laps=0),
        dict(target_laps=1.5),
        dict(dt_plant=0),
    ],
)
def test_invalid_config(config):
    with pytest.raises(ValueError):
        RunConfig(**config)


def test_target_laps_and_metrics(circle):
    result = SimulationRunner(
        RecordingModel(), CountingController(), circle, RunConfig(duration=40, target_laps=2)
    ).run(np.array([2.0, 0, 0, 0, 0, 0]))
    assert result.stop_reason == "target_laps"
    m = tracking_metrics(result, circle.length, lambda s: 2)
    assert m["distance_laps"] >= 2
    np.testing.assert_allclose(m["lap_times"], [circle.length / 2] * 2, atol=1e-10)
    assert m["nominal_criteria_pass"]


@pytest.mark.parametrize("stop", [False, True])
def test_boundary_monitoring(circle, stop):
    result = SimulationRunner(
        RecordingModel(),
        CountingController(),
        circle,
        RunConfig(duration=0.02, stop_on_boundary=stop),
    ).run(np.array([2.0, 0, 0, 0, 0, 1]))
    assert all(row["boundary_violation"] for row in result.states)
    assert result.stop_reason == ("boundary_violation" if stop else "duration")


def test_failure_logged(circle):
    class InvalidModel:
        def step(self, state, action, dt):
            raise FrenetGeometryError("synthetic explicit failure")

    result = SimulationRunner(
        InvalidModel(), CountingController(), circle, RunConfig(duration=0.01)
    ).run(np.array([2.0, 0, 0, 0, 0, 0]))
    assert result.stop_reason == "model_validity_failure"
    assert "FrenetGeometryError" in result.failure
    assert tracking_metrics(result, circle.length, lambda s: 2)["validity_failures"] == 1
