"""Symbolic equations, transcription, constraints, warm starts and solver rejection."""

import runpy
from pathlib import Path

import casadi as ca
import numpy as np
import pytest
from scipy.integrate import solve_ivp

from apex.config import load_vehicle_parameters
from apex.control.mpc.controller import ControllerApplicationError, MPCController
from apex.control.mpc.cost import TerminalSchedule, stage_cost, terminal_cost
from apex.control.mpc.preview import make_preview
from apex.control.mpc.problem import MPCProblem
from apex.control.mpc.warm_start import shift_solution
from apex.optimization.base import NLPRequest, SolverResult
from apex.optimization.solvers.ipopt import IpoptSolver

_parity = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/check_mpc_parity.py"))
ConstantCurvatureChart = _parity["ConstantCurvatureChart"]
check_parity = _parity["check_parity"]


@pytest.fixture(scope="module")
def problem():
    p = load_vehicle_parameters(
        Path(__file__).resolve().parents[2] / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml"
    )
    return MPCProblem(p)


def test_symbolic_parity():
    report = check_parity(200)
    assert max(report["derivative_max_abs"].values()) < 1e-11
    assert max(report["rk4_50ms_max_abs"].values()) < 1e-11


def test_prediction_convergence(problem):
    model = problem.model
    x = np.array([2.0, 0.07, 0.25, 0.03, 1.0, 0.04])
    u = np.array([0.06, 0.1])
    curvature = 0.2
    exact = solve_ivp(
        lambda t, z: np.asarray(model.derivative(z, u, curvature)).ravel(),
        [0, 0.05],
        x,
        method="DOP853",
        rtol=1e-12,
        atol=1e-13,
    ).y[:, -1]
    errors = [
        np.max(abs(np.asarray(model.rk4(0.05, n)(x, u, curvature)[0]).ravel() - exact))
        for n in (5, 10, 20)
    ]
    assert errors[0] / errors[1] > 12 and errors[1] / errors[2] > 12
    assert errors[0] < 2e-5  # absolute mixed-channel numerical check; refinement >12x above


def test_dimensions(problem):
    assert len(problem.lbx) == 208
    assert problem.equality_count == 126
    assert problem.inequality_count == 944
    assert len(problem.lbg) == 1070


def straight_request(problem, ey=0):
    state = np.array([2.0, 0, 0, 0, 0, ey])
    previous = np.zeros(2)
    track = ConstantCurvatureChart(0)
    preview = make_preview(track, problem.parameters, lambda s: 2, 0)
    states, controls, slacks = problem.cold_start(state, previous, preview)
    p = problem.parameter_vector(
        state, previous, preview, TerminalSchedule(problem.parameters).matrix(2)
    )
    return state, preview, p, states, controls, slacks


def test_known_zero_cost_trajectory(problem):
    _, _, p, x, u, e = straight_request(problem)
    cost, g = problem.evaluate(problem.pack(x, u, e), p)
    g = np.asarray(g).ravel()
    assert float(cost) == pytest.approx(0, abs=1e-12)
    np.testing.assert_allclose(g[:126], 0, atol=1e-12)
    assert np.all(g >= problem.lbg) and np.all(g <= problem.ubg)
    x[4] += 1234  # cost independent of absolute progress (initial equality changes only)
    assert float(problem.evaluate(problem.pack(x, u, e), p)[0]) == 0


def test_cost_reference_and_positive_errors(problem):
    x = ca.SX.sym("x", 6)
    u = ca.SX.sym("u", 2)
    prev = ca.SX.sym("prev", 2)
    v = ca.SX.sym("preview", 7)
    f = ca.Function("cost_test", [x, u, prev, v], [stage_cost(x, u, prev, v)])
    reference = np.array([0.2, 0.6, 0.9, 2, 0.024, 0.4, 0.06])
    state = np.array([2, 0.024, 0.4, 0, 100, 0])
    control = np.array([0.06, 0])
    assert float(f(state, control, control, reference)) == pytest.approx(0)
    for i in (0, 1, 2, 3, 5):
        changed = state.copy()
        changed[i] += 0.1
        assert float(f(changed, control, control, reference)) > 0
    assert float(f(state, control, np.zeros(2), reference)) > 0


def test_terminal_mapping_positive(problem):
    schedule = TerminalSchedule(problem.parameters)
    for speed in (1, 1.5, 2, 2.5, 3):
        p = schedule.matrix(speed)
        assert p.shape == (4, 4)
        assert np.linalg.eigvalsh(p).min() > 0
    x = ca.SX.sym("x", 6)
    v = ca.SX.sym("v", 7)
    p = schedule.matrix(2)
    fun = ca.Function("terminal_test", [x, v], [terminal_cost(x, v, p)])
    state = np.array([2.0, 0.02, 0.4, 0.03, 999.0, 0.04])
    ref = np.array([0.2, 0.6, 0.9, 2, 0.01, 0.3, 0.06])
    z = np.array([0.04, 0.03, 0.01, 0.1])
    assert float(fun(state, ref)) == pytest.approx(z @ p @ z)


def test_track_slack_required(problem):
    _, _, p, x, u, e = straight_request(problem, 1.1)  # test chart width=1m
    assert e[0, 0] == pytest.approx(0.1)
    assert np.all(e[0] > 0) and np.all(e[1] == 0)
    g = np.asarray(problem.evaluate(problem.pack(x, u, e), p)[1]).ravel()
    assert np.all(g <= problem.ubg + 1e-12)
    e[:] = 0
    g = np.asarray(problem.evaluate(problem.pack(x, u, e), p)[1]).ravel()
    assert np.max(g - problem.ubg) > 0.09


@pytest.mark.parametrize("index,value", [(0, 0.41), (0, -0.41), (1, 2.1), (1, -3.1)])
def test_hard_input_bounds(problem, index, value):
    _, _, _, x, u, e = straight_request(problem)
    u[index, 0] = value
    z = problem.pack(x, u, e)
    assert np.any(z < problem.lbx) or np.any(z > problem.ubx)


@pytest.mark.parametrize("stage", [0, 1, 19])
def test_steering_rate_constraints(problem, stage):
    _, _, p, x, u, e = straight_request(problem)
    u[0, stage] = 0.06
    g = np.asarray(problem.evaluate(problem.pack(x, u, e), p)[1]).ravel()
    # Each nonterminal stage has 47 inequalities: track2,domain2,rate1,load2,RK4domain40.
    assert g[126 + stage * 47 + 4] > 0.05


def test_domain_constraints(problem):
    _, _, p, x, u, e = straight_request(problem)
    x[0, 1] = 0.4
    z = problem.pack(x, u, e)
    assert np.any(z < problem.lbx)
    p[8] = 2.0  # curvature first node
    x[5, 0] = 0.5
    # Node denominator at first stage must meet positive margin.
    g = np.asarray(problem.evaluate(problem.pack(x, u, e), p)[1]).ravel()
    assert g[126 + 3] < problem.lbg[126 + 3]


def test_periodic_preview(problem, circle):
    a = make_preview(circle, problem.parameters, lambda s: 2, 0.2)
    b = make_preview(circle, problem.parameters, lambda s: 2, 0.2 + circle.length)
    np.testing.assert_allclose(a.values, b.values, atol=1e-12)
    np.testing.assert_allclose(b.progress - a.progress, circle.length)


def test_shift():
    x = np.arange(126).reshape(6, 21)
    u = np.arange(40).reshape(2, 20)
    e = np.arange(42).reshape(2, 21)
    shifted = shift_solution(x, u, e, np.zeros(6))
    np.testing.assert_array_equal(shifted[0][:, 0], 0)
    np.testing.assert_array_equal(shifted[0][:, 1:-1], x[:, 2:])
    np.testing.assert_array_equal(shifted[1][:, :-1], u[:, 1:])
    np.testing.assert_array_equal(shifted[1][:, -1], u[:, -1])
    np.testing.assert_array_equal(shifted[2][:, :-1], e[:, 1:])
    assert x[0, 0] == 0 and x[1, 0] == 21


class FailingSolver:
    last_statistics = {"solve_time": 0.01, "iterations": 3}

    def solve(self, request):
        return SolverResult(False, "forced_failure")


def test_failure_fallback_and_reset(problem, circle):
    c = MPCController(problem.parameters, circle, FailingSolver(), problem)
    x = np.array([2.0, 0.024, 0.4, 0, 0, 0.02])
    prev = np.array([0.06, 0])
    candidate = c.compute_control(x, {"previous_control": prev})
    assert not c.diagnostics()["success"] and c.solution is None
    applied = c.finalize_control(candidate, x, {"previous_control": prev})
    assert c.diagnostics()["fallback"] and np.isfinite(applied).all()
    assert abs(applied[0] - prev[0]) <= 0.05 + 1e-12
    c.reset()
    assert c.solution is None and c.fallback.speed.integral == 0


@pytest.mark.parametrize("speed", [0.6, 3.1])
def test_fallback_rejects_outside_domain(problem, circle, speed):
    c = MPCController(problem.parameters, circle, FailingSolver(), problem)
    x = np.array([speed, 0, 0, 0, 0, 0])
    c.compute_control(x, {})
    with pytest.raises(ControllerApplicationError):
        c.finalize_control(np.zeros(2), x, {"previous_control": np.zeros(2)})


def test_invalid_optimizer_success_rejected(problem, circle):
    for invalid in (None, np.full(208, np.nan), np.zeros(208), ["bad"]):

        class InvalidSolver:
            def solve(self, request):
                return SolverResult(True, "fake_success", invalid)

        c = MPCController(problem.parameters, circle, InvalidSolver(), problem)
        x = np.array([2.0, 0, 0, 0, 0, 0])
        candidate = c.compute_control(x, {})
        assert c.diagnostics()["status"] == "Rejected_invalid_optimizer_result"
        command = c.finalize_control(candidate, x, {"previous_control": np.zeros(2)})
        assert np.isfinite(command).all() and c.diagnostics()["fallback"]


def test_actual_optimizer_known_solution_and_warm_start(problem, circle):
    solver = IpoptSolver(problem)
    _, _, p, x, u, e = straight_request(problem)
    result = solver.solve(NLPRequest(problem.pack(x, u, e), p))
    assert result.success
    assert solver.last_statistics["primal_infeasibility"] < 1e-6
    assert solver.last_statistics["solve_time"] > 0
    _, controls, _ = problem.unpack(result.solution)
    np.testing.assert_allclose(controls, 0, atol=1e-5)
    c = MPCController(problem.parameters, circle, solver, problem)
    state = np.array([2.0, 0.024, 0.4, 0, 0, 0])
    c.compute_control(state, {})
    assert not c.diagnostics()["warm_start"] and c.diagnostics()["success"]
    c.compute_control(state, {})
    assert c.diagnostics()["warm_start"] and c.diagnostics()["success"]
    limited = IpoptSolver(problem, {"ipopt.max_iter": 0})
    failure = limited.solve(NLPRequest(problem.pack(x, u, e), p))
    assert not failure.success and failure.solution is None
    assert failure.status == "Maximum_Iterations_Exceeded"
    assert failure.statistics["solve_time"] >= 0
    c.solver = limited
    c.compute_control(state, {})
    assert not c.diagnostics()["success"] and c.solution is None
    c.compute_control(state, {})
    assert not c.diagnostics()["warm_start"]


def test_delayed_failure_checks_application_state(problem, circle):
    from apex.simulation.runner import RunConfig, SimulationRunner
    from apex.simulation.timing import LatencyConfig

    class GrowingSpeed:
        def step(self, state, control, dt):
            state[0] += 2 * dt
            state[4] += state[0] * dt
            return state

    c = MPCController(problem.parameters, circle, FailingSolver(), problem)
    result = SimulationRunner(
        GrowingSpeed(),
        c,
        circle,
        RunConfig(duration=0.1, dt_control=0.05, latency=LatencyConfig("injected", 0.025)),
        controller_diagnostics=c.diagnostics,
        finalize_control=c.finalize_control,
    ).run(np.array([2.99, 0, 0, 0, 0, 0]))
    assert result.stop_reason == "controller_application_failure"
    assert result.events[0]["x_sample_vx"] < 3 and result.events[0]["x_apply_vx"] > 3
    assert not result.events[0]["applied"] and not result.controls
