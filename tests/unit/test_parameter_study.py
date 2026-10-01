"""Study knobs preserve reference costs and exact fractional release clocks."""

from dataclasses import replace

import casadi as ca
import numpy as np
import pytest

from apex.control.mpc.cost import CostScales, stage_cost
from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.simulation.runner import RunConfig, SimulationRunner
from apex.simulation.timing import LatencyConfig


def test_cost_group_multipliers():
    x = ca.DM([2.5, 0.1, 0.2, 0.1, 10, 0.1])
    u = ca.DM([0.1, 0.2])
    previous = ca.DM([0, 0])
    preview = ca.DM([0, 1, 1, 2, 0, 0, 0])
    base = float(stage_cost(x, u, previous, preview))
    changes = {"speed": 1.0, "dynamic": 0.08, "lateral": 2.0, "control": 0.29, "rate": 0.014}
    for field, increase in changes.items():
        got = float(stage_cost(x, u, previous, preview, replace(CostScales(), **{field: 2})))
        assert got - base == pytest.approx(increase)
    with pytest.raises(ValueError):
        CostScales(lateral=0)
    with pytest.raises(ValueError):
        CostScales(terminal=-1)
    assert CostScales(terminal=0).terminal == 0


def test_fifteen_hz_exact_clock(circle):
    class Model:
        def step(self, x, u, dt):
            assert 0 < dt <= 0.005 + 1e-12
            x[4] += x[0] * dt
            return x

    class Controller:
        def compute_control(self, x, context):
            return np.zeros(2)

    result = SimulationRunner(
        Model(),
        Controller(),
        circle,
        RunConfig(duration=0.4, dt_control=1 / 15, latency=LatencyConfig("injected", 0.045)),
    ).run(np.array([2.0, 0, 0, 0, 0, 0]))
    np.testing.assert_allclose(
        [e["release_time"] for e in result.events], np.arange(6) / 15, atol=1e-14
    )
    assert result.timing["missed_deadlines"] == 0
    assert result.states[-1]["s_abs"] == pytest.approx(0.8)


def test_parameterized_dimensions(dynamic_vehicle):
    for n, substeps in [(8, 1), (12, 3), (25, 5)]:
        problem = MPCProblem(
            dynamic_vehicle,
            MPCConfig(horizon=n, substeps=substeps, tire_physics=RACING_TIRE_PHYSICS),
        )
        assert len(problem.lbx) == 10 * n + 8
        assert problem.equality_count == 6 * (n + 1)
        assert problem.inequality_count == n * (9 + 8 * substeps) + 4


def test_timing_and_runtime_graph_reuse(dynamic_vehicle, circle, monkeypatch):
    from apex.control.mpc.controller import MPCController
    from apex.optimization.base import SolverResult

    class FailingSolver:
        def solve(self, request):
            return SolverResult(False, "test_failure")

    problem = MPCProblem(dynamic_vehicle, MPCConfig(horizon=8, substeps=3))
    controller = MPCController(dynamic_vehicle, circle, FailingSolver(), problem)

    def forbidden(*args, **kwargs):
        raise AssertionError("Symbolic graph reconstructed in repeated control call")

    monkeypatch.setattr(MPCProblem, "__init__", forbidden)
    monkeypatch.setattr(ca, "nlpsol", forbidden)
    for _ in range(2):
        controller.compute_control(np.array([2.0, 0, 0, 0, 0, 0]), {})
        timing = controller.diagnostics()
        phases = [
            "preview_time",
            "warm_start_preparation_time",
            "parameter_update_time",
            "solver_adapter_time",
            "postprocessing_time",
        ]
        assert all(timing[key] >= 0 for key in phases)
        assert sum(timing[key] for key in phases) <= timing["total_compute_time"]
        assert (
            timing["preview_geometry_time"] + timing["reference_generation_time"]
            <= timing["preview_time"]
        )
        np.testing.assert_allclose(
            controller.last_prediction["prediction_offsets"], np.arange(9) * 0.05
        )


def test_pareto_preserves_tradeoffs_and_ties(monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from parameter_study.analysis import nondominated
    from parameter_study.common import canonical, semantic_hash

    assert nondominated([[1, 2], [2, 1], [2, 2], [1, 2]]) == [0, 1, 3]
    assert canonical({"b": 2, "a": 1}) == canonical({"a": 1, "b": 2})
    assert canonical({"n": 8}) != canonical({"n": 10})
    assert semantic_hash({"weight": 1}) == semantic_hash({"weight": 1.0})
    assert semantic_hash({"enabled": True}) != semantic_hash({"enabled": 1})


def test_terminal_multiplier_scales_complete_term(dynamic_vehicle, circle):
    from apex.control.mpc.cost import terminal_cost
    from apex.control.mpc.preview import make_preview

    config = MPCConfig(horizon=2, substeps=1, costs=CostScales(terminal=0))
    zero = MPCProblem(dynamic_vehicle, config)
    doubled = MPCProblem(dynamic_vehicle, replace(config, costs=CostScales(terminal=2)))
    state = np.array([2.0, 0.02, 0.3, 0.02, 0, 0.03])
    preview = make_preview(circle, dynamic_vehicle, lambda s: 2, 0, 2, 0.05)
    states, controls, slacks = zero.cold_start(state, np.zeros(2), preview)
    terminal_matrix = np.eye(4)
    parameters = zero.parameter_vector(state, np.zeros(2), preview, terminal_matrix)
    decision = zero.pack(states, controls, slacks)
    expected = 2 * float(terminal_cost(states[:, -1], preview.values[:, -1], terminal_matrix))
    difference = float(
        doubled.evaluate(decision, parameters)[0] - zero.evaluate(decision, parameters)[0]
    )
    assert difference == pytest.approx(expected)
    np.testing.assert_array_equal(
        doubled.evaluate(decision, parameters)[1], zero.evaluate(decision, parameters)[1]
    )
