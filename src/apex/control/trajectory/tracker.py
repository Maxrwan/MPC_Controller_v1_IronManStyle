"""Finite-horizon trajectory-aware lateral LQR and rate-aware high-rate feedback."""

from dataclasses import dataclass
from sys import exc_info
from time import perf_counter, process_time

import casadi as ca
import numpy as np
from scipy.linalg import solve_discrete_are

from apex.control.baseline.lqr import DesignScales
from apex.coordinates.angles import wrap_angle
from apex.state import StateIndex as S
from apex.state import control_vector, state_vector

LATERAL = [S.E_Y, S.E_PSI, S.VY, S.YAW_RATE]


class TVLQR:
    def __init__(self, model, track, dt=0.01, *, recorder=None):
        self._recorder = recorder
        self.track, self.dt = track, dt
        x, u, k = ca.SX.sym("x", 6), ca.SX.sym("u", 2), ca.SX.sym("k")
        step, _ = model.rk4(dt, 2)(x, u, k)
        self.jacobian = ca.Function(
            "tracker_jacobian", [x, u, k], [ca.jacobian(step, x), ca.jacobian(step, u)]
        )
        self.q, self.r = DesignScales().weights()

    def compute(self, packet):
        recorder = self._recorder
        if recorder is None:
            times = np.arange(packet.timestamps[0], packet.horizon_end_time - 1e-9, self.dt)
            matrices = []
            for time in times:
                x, u, _ = packet.sample(time)
                curvature = (
                    packet.curvature(time)
                    if len(packet.curvatures)
                    else self.track.sample(x[S.S_ABS] % self.track.length).curvature
                )
                full_a, full_b = self.jacobian(x, u, curvature)
                a = np.asarray(full_a)[np.ix_(LATERAL, LATERAL)]
                b = np.asarray(full_b)[LATERAL, :1]
                matrices.append((a, b))
        else:
            _g1_gain_jacobians = recorder.span_begin(
                recorder.active_call, "gain_jacobians", expected_parent="gains"
            )
            _g1_done_gain_jacobians = False
            try:
                times = np.arange(packet.timestamps[0], packet.horizon_end_time - 1e-9, self.dt)
                matrices = []
                for time in times:
                    x, u, _ = packet.sample(time)
                    curvature = (
                        packet.curvature(time)
                        if len(packet.curvatures)
                        else self.track.sample(x[S.S_ABS] % self.track.length).curvature
                    )
                    full_a, full_b = self.jacobian(x, u, curvature)
                    a = np.asarray(full_a)[np.ix_(LATERAL, LATERAL)]
                    b = np.asarray(full_b)[LATERAL, :1]
                    matrices.append((a, b))
                _g1_done_gain_jacobians = True
            finally:
                _g1_error_gain_jacobians = None if _g1_done_gain_jacobians else exc_info()[0]
                recorder.span_end(
                    _g1_gain_jacobians,
                    exit="complete" if _g1_done_gain_jacobians else "exception",
                    exception_type=None
                    if _g1_error_gain_jacobians is None
                    else (
                        _g1_error_gain_jacobians.__module__
                        + "."
                        + _g1_error_gain_jacobians.__qualname__
                    ),
                )
        if recorder is None:
            a, b = matrices[-1]
            p = solve_discrete_are(a, b, self.q, self.r)
        else:
            _g1_gain_terminal_dare = recorder.span_begin(
                recorder.active_call, "gain_terminal_dare", expected_parent="gains"
            )
            _g1_done_gain_terminal_dare = False
            try:
                a, b = matrices[-1]
                p = solve_discrete_are(a, b, self.q, self.r)
                _g1_done_gain_terminal_dare = True
            finally:
                _g1_error_gain_terminal_dare = (
                    None if _g1_done_gain_terminal_dare else exc_info()[0]
                )
                recorder.span_end(
                    _g1_gain_terminal_dare,
                    exit="complete" if _g1_done_gain_terminal_dare else "exception",
                    exception_type=None
                    if _g1_error_gain_terminal_dare is None
                    else (
                        _g1_error_gain_terminal_dare.__module__
                        + "."
                        + _g1_error_gain_terminal_dare.__qualname__
                    ),
                )
        if recorder is None:
            gains = []
            for a, b in reversed(matrices):
                gain = np.linalg.solve(self.r + b.T @ p @ b, b.T @ p @ a)
                p = self.q + a.T @ p @ a - a.T @ p @ b @ gain
                p = (p + p.T) / 2
                gains.append(gain.ravel())
            return times, np.array(gains[::-1])
        else:
            _g1_gain_backward = recorder.span_begin(
                recorder.active_call, "gain_backward", expected_parent="gains"
            )
            _g1_done_gain_backward = False
            try:
                gains = []
                for a, b in reversed(matrices):
                    gain = np.linalg.solve(self.r + b.T @ p @ b, b.T @ p @ a)
                    p = self.q + a.T @ p @ a - a.T @ p @ b @ gain
                    p = (p + p.T) / 2
                    gains.append(gain.ravel())
                _g1_value_gain_backward = times, np.array(gains[::-1])
                _g1_done_gain_backward = True
                return _g1_value_gain_backward
            finally:
                _g1_error_gain_backward = None if _g1_done_gain_backward else exc_info()[0]
                recorder.span_end(
                    _g1_gain_backward,
                    exit="complete" if _g1_done_gain_backward else "exception",
                    exception_type=None
                    if _g1_error_gain_backward is None
                    else (
                        _g1_error_gain_backward.__module__
                        + "."
                        + _g1_error_gain_backward.__qualname__
                    ),
                )


@dataclass(frozen=True)
class TrackerConfig:
    dt: float = 0.01
    steering_rate: float = 1.0
    speed_kp: float = 1.0
    feedback: bool = True

    def __post_init__(self):
        if (
            not np.isfinite([self.dt, self.steering_rate, self.speed_kp]).all()
            or min(self.dt, self.steering_rate) <= 0
            or self.speed_kp < 0
        ):
            raise ValueError("Invalid tracker configuration")


class TrajectoryTracker:
    def __init__(self, parameters, control_lower, control_upper, config=TrackerConfig()):
        self.parameters, self.config = parameters, config
        self.lower, self.upper = control_vector(control_lower), control_vector(control_upper)
        if np.any(self.lower > self.upper):
            raise ValueError("Empty actuator domain")
        self.previous = np.zeros(2)

    def clone(self):
        result = TrajectoryTracker(
            self.parameters, self.lower.copy(), self.upper.copy(), self.config
        )
        result.previous = self.previous.copy()
        return result

    def command(self, state, reference, nominal, gain):
        error = state_vector(state) - state_vector(reference)
        nominal, gain = control_vector(nominal), np.asarray(gain)
        if gain.shape != (4,) or not np.isfinite(gain).all():
            raise ValueError("Finite 1x4 lateral gain required")
        error[S.E_PSI] = wrap_angle(error[S.E_PSI])
        correction = np.zeros(2)
        if self.config.feedback:
            correction = np.array([-gain @ error[LATERAL], -self.config.speed_kp * error[S.VX]])
        desired = nominal + correction
        clipped = np.clip(desired, self.lower, self.upper)
        rate = self.config.steering_rate * self.config.dt
        clipped[0] = np.clip(clipped[0], self.previous[0] - rate, self.previous[0] + rate)
        self.previous = clipped.copy()
        return clipped, error, correction, desired

    def update(self, state, buffer, time):
        start, cpu = perf_counter(), process_time()
        if self.config.feedback and (buffer.active is None or not len(buffer.active.gains)):
            raise ValueError("Feedback gains unavailable")
        reference, nominal, gain = buffer.sample(time)
        interpolation = perf_counter() - start
        phase = perf_counter()
        command, error, correction, desired = self.command(state, reference, nominal, gain)
        feedback = perf_counter() - phase
        return command, {
            "interpolation_time": interpolation,
            "feedback_time": feedback,
            "cpu_time": process_time() - cpu,
            "total_time": perf_counter() - start,
            "reference": reference,
            "nominal": nominal,
            "error": error,
            "correction": correction,
            "desired": desired,
        }
