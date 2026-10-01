"""Constrained lateral QP, unchanged longitudinal P law, per-update TVLQR replacement."""

from dataclasses import dataclass
from time import perf_counter, process_time

import numpy as np

from apex.control.local_mpc.qp import OSQPWorkspace, condense
from apex.control.trajectory.tracker import LATERAL, TrajectoryTracker
from apex.coordinates.angles import wrap_angle
from apex.state import state_vector


@dataclass(frozen=True)
class LocalMPCConfig:
    horizon: int = 5
    rate_weight: float = 0.0
    varying: bool = True
    warm_start: bool = True
    deadline: float = 0.01
    tolerance: float = 1e-6
    residual_limit: float = 1e-5

    def __post_init__(self):
        if not isinstance(self.horizon, int) or not 1 <= self.horizon <= 15:
            raise ValueError("Local horizon must be an integer from 1 to 15")
        if not np.isfinite(
            [self.rate_weight, self.deadline, self.tolerance, self.residual_limit]
        ).all():
            raise ValueError("Nonfinite MPC setting")
        if self.rate_weight < 0 or min(self.deadline, self.tolerance, self.residual_limit) <= 0:
            raise ValueError("Invalid MPC setting")


class LinearMPCTracker(TrajectoryTracker):
    def __init__(
        self, parameters, lower, upper, model, config=LocalMPCConfig(), solver_factory=None
    ):
        super().__init__(parameters, lower, upper)
        self.mpc_config, self.local_model = config, model
        self.solver_factory = solver_factory or (lambda n: OSQPWorkspace(n, config.tolerance))
        self.workspaces = {config.horizon: self.solver_factory(config.horizon)}
        self.solution, self.records = None, []
        self.failure_times = set()
        self._last = None

    def clone(self):
        # The forecast has its own solver workspace and warm state, never the actuator's.
        result = LinearMPCTracker(
            self.parameters,
            self.lower,
            self.upper,
            self.local_model,
            self.mpc_config,
            self.solver_factory,
        )
        result.previous = self.previous.copy()
        result.solution = None if self.solution is None else self.solution.copy()
        return result

    def forecast_command(self, state, buffer, time):
        return self._update(state, buffer, time, record=False)[0]

    def update(self, state, buffer, time):
        return self._update(state, buffer, time, record=True)

    def _update(self, state, buffer, time, record):
        start, cpu = perf_counter(), process_time()
        if buffer.active is None or not len(buffer.active.gains):
            raise ValueError("TVLQR fallback gains unavailable")
        reference, nominal, gain = buffer.sample(time)
        interpolation = perf_counter() - start
        phase = perf_counter()
        error = state_vector(state) - reference
        error[3] = wrap_angle(error[3])
        previous = self.previous.copy()
        # Compute the exact existing TVLQR replacement without committing its private state.
        backup = TrajectoryTracker(self.parameters, self.lower, self.upper, self.config)
        backup.previous = previous.copy()
        replacement = backup.command(state, reference, nominal, gain)
        count = min(
            self.mpc_config.horizon, int(np.floor((buffer.reserve(time) + 1e-9) / self.config.dt))
        )
        info = dict(
            time=time, horizon=count, local_fallback=False, fallback_reason="", status="not_run"
        )
        command, error, correction, desired = replacement
        try:
            if count < 1:
                raise ValueError("insufficient_local_horizon")
            if round(time, 8) in self.failure_times:
                raise ValueError("injected_QP_failure")
            model_start = perf_counter()
            matrices, feedforward, terminal = self.local_model.horizon(
                buffer.active, time, count, self.mpc_config.varying
            )
            h, g, lo, hi = condense(
                matrices,
                error[LATERAL],
                feedforward,
                previous[0],
                self.local_model.q,
                self.local_model.r,
                terminal,
                self.lower[0],
                self.upper[0],
                self.config.steering_rate * self.config.dt,
                self.mpc_config.rate_weight,
            )
            info["model_assembly_time"] = perf_counter() - model_start
            setup_start = perf_counter()
            if count not in self.workspaces:
                self.workspaces[count] = self.solver_factory(count)
            info["workspace_setup_time"] = perf_counter() - setup_start
            warm = None
            if self.mpc_config.warm_start and self.solution is not None:
                shifted = np.r_[self.solution[1:], self.solution[-1]]
                warm = np.pad(shifted, (0, max(0, count - len(shifted))), mode="edge")[:count]
            solution, statistics = self.workspaces[count].solve(h, g, lo, hi, warm)
            info.update(statistics)
            if not statistics["success"]:
                raise ValueError("QP_status:" + statistics["status"])
            if solution is None or not np.isfinite(solution).all():
                raise ValueError("nonfinite_QP_solution")
            constraints = self.workspaces[count].constraints @ solution
            violation = float(max(0.0, np.max(lo - constraints), np.max(constraints - hi)))
            info["constraint_violation"] = violation
            if (
                not np.isfinite([violation, statistics["dual_residual"]]).all()
                or violation > self.mpc_config.residual_limit
                or statistics["dual_residual"] > 1e-3
            ):
                raise ValueError("unacceptable_QP_residual")
            self.solution = solution.copy()
            correction = np.array([solution[0], -self.config.speed_kp * error[0]])
            desired = nominal + correction
            command = np.clip(desired, self.lower, self.upper)
            rate = self.config.steering_rate * self.config.dt
            command[0] = np.clip(command[0], previous[0] - rate, previous[0] + rate)
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as exception:
            info.update(local_fallback=True, fallback_reason=str(exception))
            self.solution = None
            command, error, correction, desired = replacement
        self.previous = command.copy()
        diagnostics = dict(
            reference=reference,
            nominal=nominal,
            error=error,
            correction=correction,
            desired=desired,
            interpolation_time=interpolation,
            feedback_time=perf_counter() - phase,
            total_time=perf_counter() - start,
            cpu_time=process_time() - cpu,
        )
        if record:
            info.update(
                kernel_time=diagnostics["total_time"],
                replacement_delta=float(replacement[0][0]),
                replacement_a_cmd=float(replacement[0][1]),
            )
            self.records.append(info)
            self._last = (replacement, info)
        return command, diagnostics

    def finalize_update(self, state, command, diagnostics, start):
        """Called after physical command validation, before actuator work is scheduled."""
        replacement, info = self._last
        elapsed = perf_counter() - start
        if elapsed > self.mpc_config.deadline:
            info.update(local_fallback=True, fallback_reason="full_update_deadline_exceeded")
            command, error, correction, desired = replacement
            diagnostics.update(error=error, correction=correction, desired=desired)
            self.previous, self.solution = command.copy(), None
        info["validated_elapsed"] = elapsed
        return command
