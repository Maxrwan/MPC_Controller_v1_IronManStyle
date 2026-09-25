"""Generic event-driven computational latency; simulation time never skips plant motion."""

from dataclasses import dataclass
from time import perf_counter

import numpy as np

from apex.models.errors import FrenetGeometryError, ModelValidationError
from apex.state import STATE_NAMES, control_vector, state_vector
from apex.state import StateIndex as S


@dataclass(frozen=True)
class LatencyConfig:
    mode: str = "zero"
    injected: float = 0.0

    def __post_init__(self):
        if self.mode not in ("zero", "injected", "measured"):
            raise ValueError("Latency mode must be zero, injected or measured")
        if not np.isfinite(self.injected) or self.injected < 0:
            raise ValueError("Injected latency must be finite nonnegative")

    def delay(self, measured):
        if not np.isfinite(measured) or measured < 0:
            raise ValueError("Measured solve time must be finite nonnegative")
        return {"zero": 0.0, "injected": self.injected, "measured": measured}[self.mode]


def staleness(sample, application):
    delta = np.asarray(application) - np.asarray(sample)
    # Literal canonical difference requested, including raw e_psi. No branch crossings
    # in the validated tracking domain; at a branch cut interpret this diagnostic carefully.
    index = np.linalg.norm(
        delta[[S.VX, S.VY, S.YAW_RATE, S.E_PSI, S.E_Y]] / [0.5, 0.5, 1, 0.1, 0.1]
    )
    return delta, float(index)


def run_timed(runner, initial_state):
    """Replay measured/injected computation duration as physical evolution.

    A synchronous wall-clock solve supplies a pending result; the simulator then integrates
    all intervening physical intervals with the old input before making that result visible.
    No OS thread/sleep is required. At equal release/completion times, release sees busy,
    so it is skipped; next release is strictly subsequent. Fractional event times split a
    5 ms plant interval, never round latency to a grid or enlarge the plant integration step.
    """
    from apex.simulation.runner import RunResult

    runner.state = state_vector(initial_state)
    if runner.reset_controller is not None:
        runner.reset_controller()
    cfg = runner.config
    action = control_vector(runner.initial_control)
    target = (
        runner.state[S.S_ABS] + cfg.target_laps * runner.track.length
        if cfg.target_laps is not None
        else np.inf
    )
    states, controls, events, predictions = [], [], [], []
    pending = None
    t = 0.0
    release_index, plant_tick = 0, 1
    missed, total = 0, 0
    reason, failure = "duration", None
    tolerance = 1e-12
    while True:
        terminal = t >= cfg.duration - tolerance or runner.state[S.S_ABS] >= target
        if terminal:
            reason = "target_laps" if runner.state[S.S_ABS] >= target else "duration"
            states.append(runner._row(t, action))
            break
        # Fixed release clock, with busy-first ordering for exact deadline ties.
        if abs(t - release_index * cfg.dt_control) <= tolerance:
            total += 1
            if pending is not None:
                missed += 1
                pending["event"]["missed_releases"] += 1
            else:
                sample = runner.state.copy()
                start = perf_counter()
                candidate = control_vector(
                    runner.controller.compute_control(
                        sample.copy(),
                        {"time": t, "dt": cfg.dt_control, "previous_control": action.copy()},
                    )
                )
                total_compute = perf_counter() - start
                diagnostics = (
                    dict(runner.controller_diagnostics()) if runner.controller_diagnostics else {}
                )
                measured = float(diagnostics.get("solve_time", total_compute))
                latency = cfg.latency.delay(measured)
                event = {
                    "release_time": t,
                    "solve_start_time": t,
                    "scheduled_completion_time": t + latency,
                    "application_time": None,
                    "deadline": t + cfg.dt_control,
                    "solve_time": measured,
                    "controller_compute_time": total_compute,
                    "latency": latency,
                    "missed_releases": 0,
                    "completed": False,
                    "applied": False,
                    "fallback": False,
                    "staleness_index": None,
                    **{
                        f"x_sample_{name}": float(value) for name, value in zip(STATE_NAMES, sample)
                    },
                    **{f"x_apply_{name}": None for name in STATE_NAMES},
                    **{f"delta_{name}": None for name in STATE_NAMES},
                    "previous_delta": float(action[0]),
                    "previous_a_cmd": float(action[1]),
                    "candidate_delta": float(candidate[0]),
                    "candidate_a_cmd": float(candidate[1]),
                    "applied_delta": None,
                    "applied_a_cmd": None,
                    **diagnostics,
                }
                events.append(event)
                prediction = (
                    runner.prediction_diagnostics() if runner.prediction_diagnostics else None
                )
                if prediction is not None:
                    predictions.append({"release_time": t, **prediction})
                pending = {
                    "due": t + latency,
                    "sample": sample,
                    "candidate": candidate,
                    "event": event,
                }
            release_index += 1
        if pending is not None and pending["due"] <= t + tolerance:
            event = pending["event"]
            delta, index = staleness(pending["sample"], runner.state)
            event.update(
                completed=True,
                application_time=t,
                staleness_index=index,
                **{
                    f"x_apply_{name}": float(value)
                    for name, value in zip(STATE_NAMES, runner.state)
                },
                **{f"delta_{name}": float(value) for name, value in zip(STATE_NAMES, delta)},
            )
            try:
                candidate = pending["candidate"]
                if runner.finalize_control is not None:
                    candidate = runner.finalize_control(
                        candidate,
                        runner.state.copy(),
                        {"time": t, "dt": cfg.dt_control, "previous_control": action.copy()},
                    )
                action = control_vector(candidate)
            except (ModelValidationError, FrenetGeometryError) as error:
                reason, failure = (
                    "controller_application_failure",
                    f"{type(error).__name__}: {error}",
                )
                states.append(runner._row(t, action))
                break
            diagnostics = (
                dict(runner.controller_diagnostics()) if runner.controller_diagnostics else {}
            )
            event.update(
                applied=True,
                applied_delta=float(action[0]),
                applied_a_cmd=float(action[1]),
                fallback=bool(diagnostics.get("fallback", False)),
            )
            controls.append(
                {**diagnostics, "time": t, "delta": float(action[0]), "a_cmd": float(action[1])}
            )
            pending = None
        row = runner._row(t, action)
        states.append(row)
        if row["boundary_violation"] and cfg.stop_on_boundary:
            reason = "boundary_violation"
            break
        while plant_tick * cfg.dt_plant <= t + tolerance:
            plant_tick += 1
        next_time = min(
            plant_tick * cfg.dt_plant,
            release_index * cfg.dt_control,
            cfg.duration,
            pending["due"] if pending else np.inf,
        )
        try:
            runner.state = state_vector(
                runner.model.step(runner.state.copy(), action.copy(), next_time - t)
            )
        except (ModelValidationError, FrenetGeometryError) as error:
            reason, failure = "model_validity_failure", f"{type(error).__name__}: {error}"
            break
        t = next_time
    completed = sum(bool(e["completed"]) for e in events)
    timing = {
        "nominal_releases": total,
        "launched_solves": len(events),
        "completed_solves": completed,
        "missed_deadlines": missed,
        "missed_deadline_fraction": missed / total if total else 0.0,
        "effective_update_hz": sum(e["applied"] for e in events) / t if t else 0.0,
        "pending_at_end": int(pending is not None and not pending["event"]["completed"]),
        "latency_mode": cfg.latency.mode,
    }
    return RunResult(states, controls, reason, failure, events, predictions, timing)
