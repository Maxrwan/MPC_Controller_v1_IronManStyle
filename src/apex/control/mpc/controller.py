"""Tracking NMPC orchestration; no physical plant object is owned or called."""

from dataclasses import replace
from time import perf_counter

import numpy as np

from apex.control.baseline import BaselineController, ConstantSpeed
from apex.control.mpc.cost import TerminalSchedule
from apex.control.mpc.preview import make_preview
from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.control.mpc.warm_start import shift_solution
from apex.models.errors import ModelValidationError
from apex.models.tire.grip import LONGITUDINAL_MARGIN
from apex.optimization.base import NLPRequest
from apex.state import StateIndex as S
from apex.state import control_vector, state_vector
from apex.track.progress import wrap_progress


class ControllerApplicationError(ModelValidationError):
    """No valid optimizer/fallback command is available at application time."""


class MPCController:
    def __init__(
        self,
        parameters,
        track,
        solver,
        problem: MPCProblem,
        speed_reference=ConstantSpeed(),
        *,
        warm_start=True,
    ):
        self.parameters, self.track = parameters, track
        self.problem, self.solver, self.config = problem, solver, problem.config
        self.speed_reference = speed_reference
        self.terminal = TerminalSchedule(parameters)
        self.use_warm_start = warm_start
        self.fallback = BaselineController(
            replace(parameters, maximum_steering_rate=self.config.steering_rate),
            track,
            speed_reference,
            dt=self.config.dt,
        )
        self.reset()

    def reset(self):
        self.solution = None
        self.last_diagnostics = {}
        self.last_prediction = None
        self.fallback.reset()
        self.previous_control = np.zeros(2)

    def compute_control(self, state, context):
        compute_start = perf_counter()
        x = state_vector(state)
        if not np.isclose(context.get("dt", self.config.dt), self.config.dt):
            raise ValueError("Controller period differs from prediction interval")
        previous = control_vector(context.get("previous_control", self.previous_control))
        timing = {}
        phase = perf_counter()
        preview = make_preview(
            self.track,
            self.parameters,
            self.speed_reference,
            x[S.S_ABS],
            self.config.horizon,
            self.config.dt,
            timing=timing,
        )
        timing["preview_time"] = perf_counter() - phase
        phase = perf_counter()
        p_terminal = self.terminal.matrix(preview.values[3, -1])
        warm = self.use_warm_start and self.solution is not None
        guess = (
            shift_solution(*self.solution, x)
            if warm
            else self.problem.cold_start(x, previous, preview)
        )
        timing["warm_start_preparation_time"] = perf_counter() - phase
        phase = perf_counter()
        request = NLPRequest(
            self.problem.pack(*guess),
            self.problem.parameter_vector(x, previous, preview, p_terminal),
        )
        timing["parameter_update_time"] = perf_counter() - phase
        phase = perf_counter()
        result = self.solver.solve(request)
        timing["solver_adapter_time"] = perf_counter() - phase
        post_start = perf_counter()
        stats = dict(result.statistics)
        self.last_diagnostics = {
            **timing,
            "success": bool(result.success),
            "status": result.status,
            "warm_start": bool(warm),
            "solve_time": float(stats.get("solve_time", 0)),
            "iterations": int(stats.get("iterations", 0)),
            "objective": stats.get("objective"),
            "primal_infeasibility": stats.get("primal_infeasibility"),
            "reference_speed": float(preview.values[3, 0]),
            "vy_ref": float(preview.values[4, 0]),
            "r_ref": float(preview.values[5, 0]),
            "delta_feedforward": float(preview.values[6, 0]),
            "curvature": float(preview.values[0, 0]),
            "fallback": False,
            "max_slack": None,
            "slack_sum": None,
            "nonzero_slack": False,
        }
        self.last_prediction = {
            "prediction_dt": self.config.dt,
            "prediction_offsets": (np.arange(self.config.horizon + 1) * self.config.dt).tolist(),
            "preview": preview.values.tolist(),
            "preview_progress": preview.progress.tolist(),
            "solver_statistics": stats,
        }
        if result.success and result.solution is not None:
            try:
                z = np.asarray(result.solution, dtype=float).ravel()
            except (TypeError, ValueError):
                z = np.array([])
            # Independently validate injected solver output; don't trust success alone.
            if z.shape == self.problem.lbx.shape and np.isfinite(z).all():
                _, g = self.problem.evaluate(z, request.parameters)
                g = np.asarray(g).ravel()
                valid = (
                    np.isfinite(g).all()
                    and np.all(g >= self.problem.lbg - 1e-6)
                    and np.all(g <= self.problem.ubg + 1e-6)
                    and np.all(z >= self.problem.lbx - 1e-8)
                    and np.all(z <= self.problem.ubx + 1e-8)
                )
                if valid:
                    self.solution = tuple(a.copy() for a in self.problem.unpack(z))
                    states, controls, slacks = self.solution
                    self.last_prediction.update(
                        states=states.tolist(), controls=controls.tolist(), slacks=slacks.tolist()
                    )
                    self.last_diagnostics.update(
                        max_slack=float(slacks.max()),
                        slack_sum=float(slacks.sum()),
                        nonzero_slack=bool(np.any(slacks > 0)),
                    )
                    self._finish_timing(compute_start, post_start)
                    return controls[:, 0].copy()
        if result.success:
            self.last_diagnostics.update(success=False, status="Rejected_invalid_optimizer_result")
        self.solution = None
        # This placeholder is NEVER directly applied by the timing runner. Fallback
        # must use the current application state, not the stale optimization sample.
        self._finish_timing(compute_start, post_start)
        return previous.copy()

    def _finish_timing(self, compute_start, post_start):
        self.last_diagnostics["postprocessing_time"] = perf_counter() - post_start
        self.last_diagnostics["total_compute_time"] = perf_counter() - compute_start

    def finalize_control(self, candidate, state, context):
        x = state_vector(state)
        previous = control_vector(context["previous_control"])
        geometry = self.track.sample(wrap_progress(x[S.S_ABS], self.track.length))
        if x[S.VX] < self.config.minimum_speed or 1 - geometry.curvature * x[S.E_Y] <= 0.001:
            raise ControllerApplicationError(
                "Current state outside dynamic validity at application"
            )
        if self.last_diagnostics["success"]:
            command = control_vector(candidate)
        else:
            if (
                not 1 <= x[S.VX] <= 3
                or not -geometry.right_width <= x[S.E_Y] <= geometry.left_width
            ):
                raise ControllerApplicationError(
                    "MPC failed and current state outside baseline fallback domain"
                )
            self.fallback.previous_delta = float(previous[0])
            command = self.fallback.compute_control(x, {"dt": self.config.dt})
            self.last_diagnostics["fallback"] = True
        p = self.parameters
        if (
            abs(command[0]) > p.maximum_steering_angle
            or not -p.maximum_braking_deceleration <= command[1] <= p.maximum_acceleration
            or abs(command[0] - previous[0]) > self.config.steering_rate * self.config.dt + 1e-6
            or np.min(np.asarray(self.problem.model.loads(command))) <= 1e-9
            or x[S.VX] > p.maximum_speed
        ):
            raise ControllerApplicationError("Application command/state violates configured limits")
        if self.problem.model.longitudinal_domain is not None:
            utilization = np.asarray(self.problem.model.longitudinal_domain(command))
            if not np.isfinite(utilization).all() or np.any(
                abs(utilization) > 1 - LONGITUDINAL_MARGIN
            ):
                raise ControllerApplicationError(
                    "Application longitudinal force violates grip domain"
                )
        self.previous_control = command.copy()
        return command

    def diagnostics(self):
        return dict(self.last_diagnostics)


def make_mpc(
    parameters,
    track,
    config=MPCConfig(),
    speed_reference=ConstantSpeed(),
    solver_options=None,
    **kwargs,
):
    """Composition root; controller itself depends only on the injected solver contract."""
    from apex.optimization.solvers.ipopt import IpoptSolver

    problem = MPCProblem(parameters, config)
    return MPCController(
        parameters, track, IpoptSolver(problem, solver_options), problem, speed_reference, **kwargs
    )
