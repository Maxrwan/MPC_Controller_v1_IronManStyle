"""Approved terminal-progress mathematics and unchanged physical constraints."""

from dataclasses import replace

import numpy as np
import pytest

from apex.control.mpc.cost import TerminalSchedule
from apex.control.mpc.preview import make_preview
from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.models.tire.config import RACING_TIRE_PHYSICS, TirePhysics
from apex.optimization.base import NLPRequest
from apex.optimization.solvers.ipopt import IpoptSolver


def request(problem, track):
    x = np.array([2.0, 0, 0, 0, 100.0, 0])
    preview = make_preview(track, problem.parameters, lambda s: 2, 100, 4, 0.1)
    guess = problem.cold_start(x, np.zeros(2), preview)
    p = problem.parameter_vector(
        x, np.zeros(2), preview, TerminalSchedule(problem.parameters).matrix(2)
    )
    return problem.pack(*guess), p


def test_progress_cost_and_dimensions(dynamic_vehicle, straight_geometry):
    cfg = MPCConfig(horizon=4, dt=0.1, substeps=4)
    old = MPCProblem(dynamic_vehicle, cfg)
    new = MPCProblem(dynamic_vehicle, replace(cfg, progress_weight=8))
    z, p = request(old, straight_geometry)
    x, u, e = old.unpack(z)
    before = float(old.evaluate(z, p)[0])
    after = float(new.evaluate(z, p)[0])
    assert after - before == pytest.approx(
        -8 * (x[4, -1] - x[4, 0]) / (dynamic_vehicle.maximum_speed * 0.4)
    )
    for name in ["lbx", "ubx", "lbg", "ubg"]:
        np.testing.assert_array_equal(getattr(old, name), getattr(new, name))
    np.testing.assert_array_equal(old.evaluate(z, p)[1], new.evaluate(z, p)[1])
    components = np.asarray(new.evaluate_components(z, p)).ravel()
    assert sum(components[:-1]) == pytest.approx(components[-1])
    x[4, :] += 12345
    shifted = new.pack(x, u, e)
    assert float(new.evaluate(shifted, p)[0]) == pytest.approx(after)
    x[4, -1] += 1
    assert float(new.evaluate(new.pack(x, u, e), p)[0]) < after
    assert float(old.evaluate(new.pack(x, u, e), p)[0]) == before


@pytest.mark.parametrize("tires", [TirePhysics(), RACING_TIRE_PHYSICS])
def test_progress_solver_pushes_straight(dynamic_vehicle, straight_geometry, tires):
    problem = MPCProblem(
        dynamic_vehicle,
        MPCConfig(horizon=4, dt=0.1, substeps=4, progress_weight=8, tire_physics=tires),
    )
    z, p = request(problem, straight_geometry)
    solved = IpoptSolver(problem).solve(NLPRequest(z, p))
    assert solved.success
    x, u, _ = problem.unpack(solved.solution)
    assert x[4, -1] - x[4, 0] > 0.8
    assert u[1, 0] > 0
    _, g = problem.evaluate(solved.solution, p)
    assert np.all(np.asarray(g).ravel() >= problem.lbg - 1e-6)
    assert np.all(np.asarray(g).ravel() <= problem.ubg + 1e-6)


@pytest.mark.parametrize("weight", [-1, np.nan, np.inf])
def test_invalid_progress_weight(weight):
    with pytest.raises(ValueError):
        MPCConfig(progress_weight=weight)


def test_nonzero_objective_groups_accounted(dynamic_vehicle, straight_geometry):
    problem = MPCProblem(
        dynamic_vehicle, MPCConfig(horizon=4, dt=0.1, substeps=4, progress_weight=8)
    )
    z, p = request(problem, straight_geometry)
    x, u, slack = problem.unpack(z)
    x[[0, 1, 2, 3, 5], :] += np.array([0.2, 0.05, 0.1, 0.1, 0.05])[:, None]
    u[:] = np.array([0.1, 0.2])[:, None]
    slack[:] = 1e-4
    values = np.asarray(problem.evaluate_components(problem.pack(x, u, slack), p)).ravel()
    groups = dict(zip(problem.component_names, values))
    assert groups["state_tracking"] == pytest.approx(
        4 * (4 * 0.2**2 + 4 * 0.05**2 + 0.1**2 + 100 * 0.1**2 + 100 * 0.05**2)
    )
    assert groups["input_reference"] == pytest.approx(4 * (25 * 0.1**2 + 0.2**2))
    assert groups["input_increment"] == pytest.approx(0.1**2 + 0.1 * 0.2**2)
    lateral = np.array([0.05, 0.1, 0.05, 0.1])
    terminal = TerminalSchedule(dynamic_vehicle).matrix(2)
    assert groups["terminal_tracking"] == pytest.approx(lateral @ terminal @ lateral + 4 * 0.2**2)
    assert groups["slack_linear"] == pytest.approx(10)
    assert groups["slack_quadratic"] == pytest.approx(0.01)
    assert sum(values[:-1]) == pytest.approx(values[-1])
