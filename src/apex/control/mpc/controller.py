"""Tracking NMPC orchestration; no physical plant object is owned or called."""

from dataclasses import replace
from sys import exc_info
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
        racing_reference=None,
        recorder=None,
    ):
        self._recorder = recorder
        self.parameters, self.track = parameters, track
        self.problem, self.solver, self.config = problem, solver, problem.config
        self.speed_reference = speed_reference
        self.racing_reference = racing_reference
        if problem.config.racing_reference != (racing_reference is not None):
            raise ValueError("Racing preview configuration/reference mismatch")
        if recorder is None:
            self.terminal = TerminalSchedule(
                parameters, alpha_vy=self.config.costs.alpha_vy, alpha_r=self.config.costs.alpha_r
            )
        else:
            _g1_terminal_construction = recorder.span_begin(
                recorder.active_call,
                "terminal_construction",
                expected_parent="controller_construction",
            )
            _g1_done_terminal_construction = False
            try:
                self.terminal = TerminalSchedule(
                    parameters,
                    alpha_vy=self.config.costs.alpha_vy,
                    alpha_r=self.config.costs.alpha_r,
                )
                _g1_done_terminal_construction = True
            finally:
                _g1_error_terminal_construction = (
                    None if _g1_done_terminal_construction else exc_info()[0]
                )
                recorder.span_end(
                    _g1_terminal_construction,
                    exit="complete" if _g1_done_terminal_construction else "exception",
                    exception_type=None
                    if _g1_error_terminal_construction is None
                    else (
                        _g1_error_terminal_construction.__module__
                        + "."
                        + _g1_error_terminal_construction.__qualname__
                    ),
                )
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
        recorder = self._recorder
        compute_start = perf_counter()
        x = state_vector(state)
        if not np.isclose(context.get("dt", self.config.dt), self.config.dt):
            raise ValueError("Controller period differs from prediction interval")
        previous = control_vector(context.get("previous_control", self.previous_control))
        timing = {}
        if recorder is None:
            phase = perf_counter()
            preview = make_preview(
                self.track,
                self.parameters,
                self.speed_reference,
                x[S.S_ABS],
                self.config.horizon,
                self.config.dt,
                timing=timing,
                racing_reference=self.racing_reference,
            )
            timing["preview_time"] = perf_counter() - phase
        else:
            _g1_reference = recorder.span_begin(
                recorder.active_call, "reference", expected_parent="controller"
            )
            _g1_done_reference = False
            try:
                phase = perf_counter()
                preview = make_preview(
                    self.track,
                    self.parameters,
                    self.speed_reference,
                    x[S.S_ABS],
                    self.config.horizon,
                    self.config.dt,
                    timing=timing,
                    racing_reference=self.racing_reference,
                    recorder=recorder,
                )
                timing["preview_time"] = perf_counter() - phase
                _g1_done_reference = True
            finally:
                _g1_error_reference = None if _g1_done_reference else exc_info()[0]
                recorder.span_end(
                    _g1_reference,
                    exit="complete" if _g1_done_reference else "exception",
                    exception_type=None
                    if _g1_error_reference is None
                    else (_g1_error_reference.__module__ + "." + _g1_error_reference.__qualname__),
                )
        if recorder is None:
            phase = perf_counter()
            p_terminal = self.terminal.matrix(preview.values[3, -1])
            warm = self.use_warm_start and self.solution is not None
            guess = (
                shift_solution(*self.solution, x)
                if warm
                else self.problem.cold_start(x, previous, preview)
            )
            timing["warm_start_preparation_time"] = perf_counter() - phase
        else:
            _g1_warm = recorder.span_begin(
                recorder.active_call, "warm", expected_parent="controller"
            )
            _g1_done_warm = False
            try:
                phase = perf_counter()
                _g1_terminal_lookup = recorder.span_begin(
                    recorder.active_call, "terminal_lookup", expected_parent="warm"
                )
                _g1_done_terminal_lookup = False
                try:
                    p_terminal = self.terminal.matrix(preview.values[3, -1])
                    _g1_done_terminal_lookup = True
                finally:
                    _g1_error_terminal_lookup = None if _g1_done_terminal_lookup else exc_info()[0]
                    recorder.span_end(
                        _g1_terminal_lookup,
                        exit="complete" if _g1_done_terminal_lookup else "exception",
                        exception_type=None
                        if _g1_error_terminal_lookup is None
                        else (
                            _g1_error_terminal_lookup.__module__
                            + "."
                            + _g1_error_terminal_lookup.__qualname__
                        ),
                    )
                _g1_guess = recorder.span_begin(
                    recorder.active_call, "guess", expected_parent="warm"
                )
                _g1_done_guess = False
                try:
                    warm = self.use_warm_start and self.solution is not None
                    guess = (
                        shift_solution(*self.solution, x)
                        if warm
                        else self.problem.cold_start(x, previous, preview)
                    )
                    _g1_done_guess = True
                finally:
                    _g1_error_guess = None if _g1_done_guess else exc_info()[0]
                    recorder.span_end(
                        _g1_guess,
                        exit="complete" if _g1_done_guess else "exception",
                        exception_type=None
                        if _g1_error_guess is None
                        else (_g1_error_guess.__module__ + "." + _g1_error_guess.__qualname__),
                    )
                timing["warm_start_preparation_time"] = perf_counter() - phase
                _g1_done_warm = True
            finally:
                _g1_error_warm = None if _g1_done_warm else exc_info()[0]
                recorder.span_end(
                    _g1_warm,
                    exit="complete" if _g1_done_warm else "exception",
                    exception_type=None
                    if _g1_error_warm is None
                    else (_g1_error_warm.__module__ + "." + _g1_error_warm.__qualname__),
                )
        if recorder is None:
            phase = perf_counter()
            request = NLPRequest(
                self.problem.pack(*guess),
                self.problem.parameter_vector(x, previous, preview, p_terminal),
            )
            timing["parameter_update_time"] = perf_counter() - phase
        else:
            _g1_parameter_pack = recorder.span_begin(
                recorder.active_call, "parameter_pack", expected_parent="controller"
            )
            _g1_done_parameter_pack = False
            try:
                phase = perf_counter()
                request = NLPRequest(
                    self.problem.pack(*guess),
                    self.problem.parameter_vector(x, previous, preview, p_terminal),
                )
                timing["parameter_update_time"] = perf_counter() - phase
                _g1_done_parameter_pack = True
            finally:
                _g1_error_parameter_pack = None if _g1_done_parameter_pack else exc_info()[0]
                recorder.span_end(
                    _g1_parameter_pack,
                    exit="complete" if _g1_done_parameter_pack else "exception",
                    exception_type=None
                    if _g1_error_parameter_pack is None
                    else (
                        _g1_error_parameter_pack.__module__
                        + "."
                        + _g1_error_parameter_pack.__qualname__
                    ),
                )
        if recorder is None:
            phase = perf_counter()
            result = self.solver.solve(request)
            timing["solver_adapter_time"] = perf_counter() - phase
        else:
            _g1_solver_adapter = recorder.span_begin(
                recorder.active_call, "solver_adapter", expected_parent="controller"
            )
            _g1_done_solver_adapter = False
            try:
                phase = perf_counter()
                result = self.solver.solve(request)
                timing["solver_adapter_time"] = perf_counter() - phase
                _g1_done_solver_adapter = True
            finally:
                _g1_error_solver_adapter = None if _g1_done_solver_adapter else exc_info()[0]
                recorder.span_end(
                    _g1_solver_adapter,
                    exit="complete" if _g1_done_solver_adapter else "exception",
                    exception_type=None
                    if _g1_error_solver_adapter is None
                    else (
                        _g1_error_solver_adapter.__module__
                        + "."
                        + _g1_error_solver_adapter.__qualname__
                    ),
                )
        if recorder is None:
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
                "prediction_offsets": (
                    np.arange(self.config.horizon + 1) * self.config.dt
                ).tolist(),
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
                            states=states.tolist(),
                            controls=controls.tolist(),
                            slacks=slacks.tolist(),
                        )
                        self.last_diagnostics.update(
                            objective_components=dict(
                                zip(
                                    self.problem.component_names,
                                    np.asarray(
                                        self.problem.evaluate_components(z, request.parameters)
                                    )
                                    .ravel()
                                    .tolist(),
                                )
                            ),
                            max_slack=float(slacks.max()),
                            slack_sum=float(slacks.sum()),
                            nonzero_slack=bool(np.any(slacks > 0)),
                        )
                        self._finish_timing(compute_start, post_start)
                        return controls[:, 0].copy()
            if result.success:
                self.last_diagnostics.update(
                    success=False, status="Rejected_invalid_optimizer_result"
                )
            self.solution = None
            # This placeholder is NEVER directly applied by the timing runner. Fallback
            # must use the current application state, not the stale optimization sample.
            self._finish_timing(compute_start, post_start)
            return previous.copy()
        else:
            _g1_controller_validation = recorder.span_begin(
                recorder.active_call, "controller_validation", expected_parent="controller"
            )
            _g1_done_controller_validation = False
            try:
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
                    "prediction_offsets": (
                        np.arange(self.config.horizon + 1) * self.config.dt
                    ).tolist(),
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
                                states=states.tolist(),
                                controls=controls.tolist(),
                                slacks=slacks.tolist(),
                            )
                            self.last_diagnostics.update(
                                objective_components=dict(
                                    zip(
                                        self.problem.component_names,
                                        np.asarray(
                                            self.problem.evaluate_components(z, request.parameters)
                                        )
                                        .ravel()
                                        .tolist(),
                                    )
                                ),
                                max_slack=float(slacks.max()),
                                slack_sum=float(slacks.sum()),
                                nonzero_slack=bool(np.any(slacks > 0)),
                            )
                            self._finish_timing(compute_start, post_start)
                            _g1_value_controller_validation = controls[:, 0].copy()
                            _g1_done_controller_validation = True
                            return _g1_value_controller_validation
                if result.success:
                    self.last_diagnostics.update(
                        success=False, status="Rejected_invalid_optimizer_result"
                    )
                self.solution = None
                # This placeholder is NEVER directly applied by the timing runner. Fallback
                # must use the current application state, not the stale optimization sample.
                self._finish_timing(compute_start, post_start)
                _g1_value_controller_validation = previous.copy()
                _g1_done_controller_validation = True
                return _g1_value_controller_validation
            finally:
                _g1_error_controller_validation = (
                    None if _g1_done_controller_validation else exc_info()[0]
                )
                recorder.span_end(
                    _g1_controller_validation,
                    exit="complete" if _g1_done_controller_validation else "exception",
                    exception_type=None
                    if _g1_error_controller_validation is None
                    else (
                        _g1_error_controller_validation.__module__
                        + "."
                        + _g1_error_controller_validation.__qualname__
                    ),
                )

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
    *,
    recorder=None,
    **kwargs,
):
    """Composition root; controller itself depends only on the injected solver contract."""
    from apex.optimization.solvers.ipopt import IpoptSolver

    if recorder is None:
        problem = MPCProblem(parameters, config)
        return MPCController(
            parameters,
            track,
            IpoptSolver(problem, solver_options),
            problem,
            speed_reference,
            **kwargs,
        )
    else:
        _g1_nlp_graph = recorder.span_begin(
            recorder.active_call, "nlp_graph", expected_parent="construction_full"
        )
        _g1_done_nlp_graph = False
        try:
            problem = MPCProblem(parameters, config)
            _g1_done_nlp_graph = True
        finally:
            _g1_error_nlp_graph = None if _g1_done_nlp_graph else exc_info()[0]
            recorder.span_end(
                _g1_nlp_graph,
                exit="complete" if _g1_done_nlp_graph else "exception",
                exception_type=None
                if _g1_error_nlp_graph is None
                else (_g1_error_nlp_graph.__module__ + "." + _g1_error_nlp_graph.__qualname__),
            )
        _g1_solver_construction = recorder.span_begin(
            recorder.active_call, "solver_construction", expected_parent="construction_full"
        )
        _g1_done_solver_construction = False
        try:
            solver = IpoptSolver(problem, solver_options, recorder=recorder)
            _g1_done_solver_construction = True
        finally:
            _g1_error_solver_construction = None if _g1_done_solver_construction else exc_info()[0]
            recorder.span_end(
                _g1_solver_construction,
                exit="complete" if _g1_done_solver_construction else "exception",
                exception_type=None
                if _g1_error_solver_construction is None
                else (
                    _g1_error_solver_construction.__module__
                    + "."
                    + _g1_error_solver_construction.__qualname__
                ),
            )
        _g1_controller_construction = recorder.span_begin(
            recorder.active_call, "controller_construction", expected_parent="construction_full"
        )
        _g1_done_controller_construction = False
        try:
            _g1_value_controller_construction = MPCController(
                parameters, track, solver, problem, speed_reference, recorder=recorder, **kwargs
            )
            _g1_done_controller_construction = True
            return _g1_value_controller_construction
        finally:
            _g1_error_controller_construction = (
                None if _g1_done_controller_construction else exc_info()[0]
            )
            recorder.span_end(
                _g1_controller_construction,
                exit="complete" if _g1_done_controller_construction else "exception",
                exception_type=None
                if _g1_error_controller_construction is None
                else (
                    _g1_error_controller_construction.__module__
                    + "."
                    + _g1_error_controller_construction.__qualname__
                ),
            )
