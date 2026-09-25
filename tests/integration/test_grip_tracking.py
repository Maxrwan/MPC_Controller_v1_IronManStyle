"""Grip-plant/prediction composition and preserved physical-time latency semantics."""

import numpy as np
import pytest

from apex.control.mpc.controller import make_mpc
from apex.control.mpc.problem import MPCConfig
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.simulation.runner import RunConfig, SimulationRunner
from apex.simulation.timing import LatencyConfig


@pytest.mark.parametrize("delay", [0, 0.025, 0.06, 0.1])
def test_grip_physical_time(dynamic_vehicle, circle, delay):
    plant = DynamicBicycle(dynamic_vehicle, circle, tire_physics=RACING_TIRE_PHYSICS)
    controller = make_mpc(dynamic_vehicle, circle, MPCConfig(tire_physics=RACING_TIRE_PHYSICS))
    result = SimulationRunner(
        plant,
        controller,
        circle,
        RunConfig(duration=0.3, dt_control=0.05, latency=LatencyConfig("injected", delay)),
        controller_diagnostics=controller.diagnostics,
        finalize_control=controller.finalize_control,
    ).run(np.array([2, 0.024, 0.4, 0, 0, 0]))
    assert result.failure is None
    assert all(event["success"] for event in result.events)
    completed = [e for e in result.events if e.get("applied")]
    assert completed
    for e in completed:
        assert e["application_time"] - e["release_time"] == pytest.approx(delay)
        assert e["delta_s_abs"] == pytest.approx(e["x_apply_s_abs"] - e["x_sample_s_abs"])
        if delay:
            assert e["delta_s_abs"] > 0 and e["staleness_index"] > 0
    if delay:
        for row in result.states:
            if row["time"] < delay:
                assert row["delta"] == 0 and row["a_cmd"] == 0
    if delay >= 0.05:
        assert result.timing["missed_deadlines"] > 0
    for row in result.states:
        d = plant.diagnostics(
            [row[k] for k in ("vx", "vy", "r", "e_psi", "s_abs", "e_y")],
            [row["delta"], row["a_cmd"]],
        )
        assert max(d.front_combined_utilization, d.rear_combined_utilization) <= 1 + 1e-12
