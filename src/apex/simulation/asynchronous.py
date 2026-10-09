"""Deterministic asynchronous chronology: codriver events continue during planner work."""

from dataclasses import dataclass, replace
from inspect import signature
from time import perf_counter, process_time

import numpy as np

from apex.control.baseline import BaselineController
from apex.control.trajectory.packet import TrajectoryBuffer
from apex.control.trajectory.prediction import CommittedControlPrefix, RollingDelay, UrgentReplan
from apex.coordinates.angles import wrap_angle
from apex.models.errors import ModelValidationError
from apex.simulation.diagnostic_timing import ReplayExhausted
from apex.simulation.prediction_capture import PredictionRelease
from apex.state import STATE_NAMES
from apex.state import StateIndex as S


@dataclass(frozen=True)
class AsyncConfig:
    planner_dt: float = 0.1
    tracker_dt: float = 0.01
    plant_dt: float = 0.005
    duration: float = 80.0
    laps: int = 2
    latency_mode: str = "measured"
    injected_delay: float = 0.0
    spike_plan_id: int = -1
    spike_delay: float = 0.15
    failed_plan_ids: tuple = ()
    disturbance_time: float | None = None
    disturbance_ey: float = 0.08
    disturbance_heading: float = -0.04
    urgent: bool = True
    codriver_delay: float | None = 0.0
    committed_prefix_prediction: bool = False

    def __post_init__(self):
        if type(self.committed_prefix_prediction) is not bool:
            raise ValueError("committed_prefix_prediction must be a boolean")
        if not isinstance(self.laps, int) or self.laps < 1:
            raise ValueError("Positive integer lap count required")
        if self.codriver_delay is not None and (
            not np.isfinite(self.codriver_delay) or self.codriver_delay < 0
        ):
            raise ValueError("Invalid codriver latency")
        if self.latency_mode not in ("measured", "injected", "zero"):
            raise ValueError("Unknown planner latency mode")
        if (
            not np.isfinite(
                [
                    self.planner_dt,
                    self.tracker_dt,
                    self.plant_dt,
                    self.duration,
                    self.injected_delay,
                    self.spike_delay,
                ]
            ).all()
            or min(self.planner_dt, self.tracker_dt, self.plant_dt, self.duration) <= 0
            or min(self.injected_delay, self.spike_delay) < 0
            or self.plant_dt > 0.005
        ):
            raise ValueError("Invalid asynchronous timing")

    def delay(self, plan_id, measured):
        if plan_id == self.spike_plan_id:
            return self.spike_delay
        return (
            measured
            if self.latency_mode == "measured"
            else (self.injected_delay if self.latency_mode == "injected" else 0.0)
        )


class AsyncRunner:
    """One pending solve and one completed future-dated packet, never a solver queue."""

    def __init__(
        self,
        plant,
        planner,
        tracker,
        track,
        config=AsyncConfig(),
        estimator=None,
        *,
        timing=None,
        release_observer=None,
    ):
        self.plant, self.planner, self.tracker, self.track = plant, planner, tracker, track
        self.config = config
        self.timing = timing
        self.release_observer = release_observer
        if config.committed_prefix_prediction:
            try:
                signature(planner.prepare).bind(
                    0, None, 0.0, 0.0, None, None, committed_prefix=None
                )
            except (TypeError, ValueError) as error:
                raise TypeError(
                    "Architecture B requires planner.prepare(..., committed_prefix=...)"
                ) from error
        if not np.isclose(config.tracker_dt, tracker.config.dt, atol=1e-12, rtol=0):
            raise ValueError("Scheduler and tracker periods must match")
        self.estimator = estimator or RollingDelay()
        self.buffer = TrajectoryBuffer()
        self.urgent = UrgentReplan(config.urgent)
        self.fallback = BaselineController(
            replace(plant.parameters, maximum_steering_rate=tracker.config.steering_rate),
            track,
            dt=config.tracker_dt,
        )

    def run(self, initial):
        c, tracker, buffer = self.config, self.tracker, self.buffer
        x, t, command = np.array(initial, copy=True), 0.0, np.zeros(2)
        states, controls, events, packets, triggers, fallbacks = [], [], [], [], [], []
        handoffs, releases, misses, reserves = [], [], [], []
        mode, stop, failure = "trajectory", "duration", None
        plan_id, pending, waiting = 0, None, None
        planner_index, tracker_index = 1, 0
        disturbed = False
        actuator_pending, last_application = None, 0.0
        codriver_misses = []
        lap_times, last_lap_time = [], 0.0
        next_lap = (int(x[S.S_ABS] / self.track.length) + 1) * self.track.length
        startup, startup_event = self.planner.prepare(0, x, 0, 0, buffer, tracker, startup=True)
        startup_event.update(
            completion_time=0.0,
            startup=True,
            prediction_architecture="B" if c.committed_prefix_prediction else "A",
            release_command_pending=False,
            pending_application_time=None,
        )
        if startup is None:
            return dict(
                states=[],
                controls=[],
                plans=[startup_event],
                packets=[],
                triggers=[],
                fallbacks=[],
                handoffs=[],
                releases=[],
                misses=[],
                reserves=[],
                failure="startup_planning_failed",
                stop_reason="startup_failed",
                lap_times=[],
            )
        startup = replace(startup, actual_completion_time=0.0)
        accepted, reason = buffer.insert(startup, 0)
        if not accepted:
            raise ValueError(f"Startup packet rejected: {reason}")
        # Steering/longitudinal command is prepositioned while launch is gated.
        # This takes unmodelled prelaunch time, never a rate jump during vehicle motion.
        command = startup.controls[0].copy()
        tracker.previous = command.copy()
        startup_event["prepositioned_control"] = command.tolist()
        packets.append(startup.as_dict())
        events.append(startup_event)

        def handoff(packet):
            nonlocal waiting
            ref, nominal, _ = packet.sample(t)
            error = x - ref
            error[S.E_PSI] = wrap_angle(error[S.E_PSI])
            # Explicit synthetic continuity envelope; reject rather than hide mismatch.
            limits = np.array([0.5, 0.5, 1.0, 0.20, 0.75, 0.15])
            if np.any(abs(error) > limits):
                ok, why = False, "handoff_mismatch"
            else:
                try:
                    self.plant.diagnostics(ref, nominal)
                    ok, why = buffer.insert(packet, t)
                except ModelValidationError as exception:
                    ok, why = False, str(exception)
            handoffs.append(
                {
                    "time": t,
                    "plan_id": packet.plan_id,
                    "accepted": ok,
                    "reason": why,
                    "reserve": packet.horizon_end_time - t,
                    **{f"error_{k}": float(v) for k, v in zip(STATE_NAMES, error)},
                    "nominal_delta_jump": float(nominal[0] - command[0]),
                    "nominal_acceleration_jump": float(nominal[1] - command[1]),
                }
            )
            waiting = None

        def release(urgent=False):
            nonlocal plan_id, pending
            if pending is not None:
                raise RuntimeError("Overlapping planner solve requested")
            plan_id += 1
            tracker.previous = command.copy()
            estimate = self.estimator.estimate()
            if c.committed_prefix_prediction or self.release_observer is not None:
                # Capture after this timestamp's application/codriver processing. The
                # requested value is still pending, including new zero-latency work.
                prefix = CommittedControlPrefix(
                    release_time=t,
                    applied_control=command,
                    last_application_time=last_application,
                    pending_control=None if actuator_pending is None else actuator_pending[1],
                    pending_application_time=(
                        None if actuator_pending is None else actuator_pending[0]
                    ),
                )
            if self.release_observer is not None:
                # Diagnostic capture only: detached release-known data, before any
                # preparation or future readiness lookup. No new physical event.
                self.release_observer(
                    PredictionRelease.capture(plan_id, x, estimate, prefix, buffer, tracker)
                )
            if c.committed_prefix_prediction:
                packet, event = self.planner.prepare(
                    plan_id, x, t, estimate, buffer, tracker, committed_prefix=prefix
                )
            else:
                packet, event = self.planner.prepare(plan_id, x, t, estimate, buffer, tracker)
            delay = (
                c.delay(plan_id, event["planner_total_time"])
                if self.timing is None
                else self.timing.planner_delay(plan_id)
            )
            if plan_id in c.failed_plan_ids:
                packet = None
                event.update(success=False, status="Injected_planner_failure")
            completion = t + delay
            event.update(
                completion_time=completion,
                physical_delay=delay,
                startup=False,
                urgent=urgent,
                delay_estimation_error=delay - estimate,
                prediction_architecture="B" if c.committed_prefix_prediction else "A",
                release_command_pending=actuator_pending is not None,
                pending_application_time=None if actuator_pending is None else actuator_pending[0],
            )
            if packet is not None:
                packet = replace(packet, actual_completion_time=completion)
                packets.append(packet.as_dict())
            event["completed"] = False
            events.append(event)
            pending = (completion, packet, event)
            releases.append({"time": t, "plan_id": plan_id, "urgent": urgent})
            self.urgent.consume()

        try:
            while t < c.duration - 1e-10:
                # Apply completed codriver work before coincident release events.
                if actuator_pending is not None and actuator_pending[0] <= t + 1e-10:
                    _, requested, row = actuator_pending
                    elapsed = max(0.0, t - last_application)
                    applied = requested.copy()
                    applied[0] = np.clip(
                        applied[0],
                        command[0] - tracker.config.steering_rate * elapsed,
                        command[0] + tracker.config.steering_rate * elapsed,
                    )
                    command = applied
                    tracker.previous = command.copy()
                    row.update(application_time=t, delta=float(command[0]), a_cmd=float(command[1]))
                    controls.append(row)
                    last_application, actuator_pending = t, None
                # Completion precedes coincident codriver/release events.
                if pending is not None and pending[0] <= t + 1e-10:
                    _, packet, event = pending
                    pending = None
                    prediction_error = x - np.asarray(event["predicted_state"])
                    prediction_error[S.E_PSI] = wrap_angle(prediction_error[S.E_PSI])
                    event.update(
                        actual_state=x.tolist(),
                        prediction_error=prediction_error.tolist(),
                        active_reserve_at_completion=buffer.reserve(t),
                        new_reserve_at_completion=(
                            packet.horizon_end_time - t if packet is not None else None
                        ),
                    )
                    event["completed"] = True
                    self.estimator.observe(event["physical_delay"])
                    if packet is not None and mode != "trajectory":
                        handoffs.append(
                            {
                                "time": t,
                                "plan_id": packet.plan_id,
                                "accepted": False,
                                "reason": "fallback_latched",
                            }
                        )
                        packet = None
                    if packet is not None:
                        if packet.horizon_end_time - t < buffer.minimum_handoff_reserve:
                            handoffs.append(
                                {
                                    "time": t,
                                    "plan_id": packet.plan_id,
                                    "accepted": False,
                                    "reason": "insufficient_reserve",
                                }
                            )
                        elif t < packet.timestamps[0] - 1e-10:
                            waiting = packet
                        else:
                            handoff(packet)
                if waiting is not None and t >= waiting.timestamps[0] - 1e-10:
                    handoff(waiting)
                if (
                    c.disturbance_time is not None
                    and not disturbed
                    and t >= c.disturbance_time - 1e-10
                ):
                    x[S.E_Y] += c.disturbance_ey
                    x[S.E_PSI] = wrap_angle(x[S.E_PSI] + c.disturbance_heading)
                    disturbed = True
                    triggers.append({"time": t, "kind": "approved_state_perturbation"})
                if buffer.category(t) == "exhausted" and mode == "trajectory":
                    geometry = self.track.sample(x[S.S_ABS] % self.track.length)
                    valid = (
                        1 <= x[S.VX] <= 3
                        and -geometry.right_width <= x[S.E_Y] <= geometry.left_width
                    )
                    fallbacks.append(
                        {"time": t, "reason": "trajectory_exhausted", "valid_domain": valid}
                    )
                    if not valid:
                        stop = "exhausted_outside_baseline_domain"
                        break
                    mode = "baseline_fallback"
                    self.fallback.previous_delta = float(command[0])
                if t >= tracker_index * c.tracker_dt - 1e-10 and actuator_pending is not None:
                    codriver_misses.append({"time": t, "reason": "codriver_busy"})
                    tracker_index += 1
                if t >= tracker_index * c.tracker_dt - 1e-10:
                    tracker.previous = command.copy()
                    start, cpu = perf_counter(), process_time()
                    if mode == "trajectory":
                        proposed, diagnostics = tracker.update(x, buffer, t)
                        if self.urgent.observe(diagnostics["error"]):
                            triggers.append(
                                {"time": t, "kind": "urgent_replan", "busy": pending is not None}
                            )
                    else:
                        geometry = self.track.sample(x[S.S_ABS] % self.track.length)
                        if not (
                            1 <= x[S.VX] <= 3
                            and -geometry.right_width <= x[S.E_Y] <= geometry.left_width
                        ):
                            stop = "fallback_outside_validity_domain"
                            break
                        requested = self.fallback.compute_control(x, {"dt": c.tracker_dt})
                        proposed = np.clip(requested, tracker.lower, tracker.upper)
                        tracker.previous = proposed.copy()
                        diagnostics = dict(
                            reference=x.copy(),
                            nominal=proposed.copy(),
                            error=np.zeros(6),
                            correction=np.zeros(2),
                            desired=requested,
                            interpolation_time=0.0,
                            feedback_time=perf_counter() - start,
                            cpu_time=process_time() - cpu,
                            total_time=perf_counter() - start,
                        )
                    validation_start = perf_counter()
                    self.plant.diagnostics(x, proposed)
                    diagnostics["command_validation_time"] = perf_counter() - validation_start
                    if mode == "trajectory" and hasattr(tracker, "finalize_update"):
                        finalized = tracker.finalize_update(x, proposed, diagnostics, start)
                        if not np.array_equal(finalized, proposed):
                            self.plant.diagnostics(x, finalized)
                        proposed = finalized
                    diagnostics["kernel_time"] = diagnostics["total_time"]
                    diagnostics["total_time"] = perf_counter() - start
                    diagnostics["cpu_time"] = process_time() - cpu
                    row = {
                        "time": t,
                        "plan_id": buffer.active_plan_id,
                        "mode": mode,
                        "requested_delta": float(proposed[0]),
                        "requested_a_cmd": float(proposed[1]),
                        "reserve": buffer.reserve(t),
                        **{
                            k: diagnostics[k]
                            for k in (
                                "interpolation_time",
                                "feedback_time",
                                "command_validation_time",
                                "kernel_time",
                                "cpu_time",
                                "total_time",
                            )
                        },
                        **{
                            f"error_{k}": float(v)
                            for k, v in zip(STATE_NAMES, diagnostics["error"])
                        },
                        **{
                            f"reference_{k}": float(v)
                            for k, v in zip(STATE_NAMES, diagnostics["reference"])
                        },
                        "nominal_delta": float(diagnostics["nominal"][0]),
                        "nominal_a_cmd": float(diagnostics["nominal"][1]),
                        "delta_correction": float(diagnostics["correction"][0]),
                        "acceleration_correction": float(diagnostics["correction"][1]),
                        "computational_deadline_exceeded": diagnostics["total_time"] > c.tracker_dt,
                    }
                    latency = (
                        diagnostics["total_time"] if c.codriver_delay is None else c.codriver_delay
                    )
                    if self.timing is not None:
                        latency = self.timing.codriver_delay(len(controls))
                    row["physical_latency"] = latency
                    actuator_pending = (t + latency, proposed, row)
                    tracker_index += 1
                nominal_release = t >= planner_index * c.planner_dt - 1e-10
                if nominal_release:
                    if pending is not None:
                        misses.append({"time": t, "reason": "planner_busy"})
                    elif mode == "trajectory":
                        release()
                    planner_index += 1
                elif self.urgent.pending and pending is None and mode == "trajectory":
                    release(urgent=True)
                # A zero-duration solve becomes visible at this same physical timestamp.
                if (pending is not None and pending[0] <= t + 1e-10) or (
                    actuator_pending is not None and actuator_pending[0] <= t + 1e-10
                ):
                    continue
                d = self.plant.diagnostics(x, command)
                geometry = self.track.sample(x[S.S_ABS] % self.track.length)
                states.append(
                    {
                        "time": t,
                        **dict(zip(STATE_NAMES, map(float, x))),
                        "delta": float(command[0]),
                        "a_cmd": float(command[1]),
                        "plan_id": buffer.active_plan_id,
                        "mode": mode,
                        "front_utilization": d.front_combined_utilization,
                        "rear_utilization": d.rear_combined_utilization,
                        "boundary_violation": not -geometry.right_width
                        <= x[S.E_Y]
                        <= geometry.left_width,
                    }
                )
                reserves.append(
                    {
                        "time": t,
                        "reserve": buffer.reserve(t),
                        "category": buffer.category(t),
                        "plan_id": buffer.active_plan_id,
                    }
                )
                candidates = [
                    t + c.plant_dt,
                    tracker_index * c.tracker_dt,
                    planner_index * c.planner_dt,
                    c.duration,
                ]
                if pending is not None:
                    candidates.append(pending[0])
                if actuator_pending is not None:
                    candidates.append(actuator_pending[0])
                if waiting is not None:
                    candidates.append(float(waiting.timestamps[0]))
                if buffer.active is not None and buffer.active.horizon_end_time > t + 1e-10:
                    candidates.append(buffer.active.horizon_end_time)
                if c.disturbance_time is not None and not disturbed:
                    candidates.append(c.disturbance_time)
                next_time = min(v for v in candidates if v > t + 1e-10)
                old_progress = x[S.S_ABS]
                x = self.plant.step(x, command, next_time - t)
                if x[S.S_ABS] >= next_lap:
                    cross = t + (next_time - t) * (next_lap - old_progress) / (
                        x[S.S_ABS] - old_progress
                    )
                    lap_times.append(cross - last_lap_time)
                    last_lap_time = cross
                    next_lap += self.track.length
                    if len(lap_times) >= c.laps:
                        stop, t = "target_laps", next_time
                        break
                t = next_time
        except ReplayExhausted as exception:
            failure, stop = str(exception), "diagnostic_trace_exhausted"
        except (ModelValidationError, ValueError) as exception:
            failure, stop = str(exception), "model_or_control_validity_failure"
        return dict(
            states=states,
            controls=controls,
            plans=events,
            packets=packets,
            triggers=triggers,
            fallbacks=fallbacks,
            handoffs=handoffs,
            releases=releases,
            misses=misses,
            reserves=reserves,
            failure=failure,
            stop_reason=stop,
            lap_times=lap_times,
            end_time=t,
            pending_at_end=pending is not None,
            codriver_misses=codriver_misses,
        )
