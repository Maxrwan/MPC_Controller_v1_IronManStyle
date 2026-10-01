"""Planner adapter: nominal optimization, time prediction and gain preparation."""

from dataclasses import replace
from time import perf_counter, process_time

import numpy as np

from apex.control.trajectory.packet import TrajectoryPacket
from apex.control.trajectory.prediction import ActuationPredictor
from apex.control.trajectory.tracker import TVLQR


class TrajectoryPlanner:
    def __init__(self, controller, track, tracker_dt=0.01):
        self.controller = controller
        self.predictor = ActuationPredictor(controller.problem.model, track)
        self.gain_builder = TVLQR(controller.problem.model, track, tracker_dt)

    def prepare(self, plan_id, state, time, estimate, buffer, tracker, *, startup=False):
        wall, cpu = perf_counter(), process_time()
        prediction_time, gain_time = 0.0, 0.0
        solver_attempted = False
        packet, reason = None, "planner_failure"
        predicted = np.array(state, copy=True)
        try:
            phase = perf_counter()
            predicted, previous = (
                (predicted, tracker.previous.copy())
                if startup
                else self.predictor.predict(state, time, estimate, buffer, tracker)
            )
            prediction_time = perf_counter() - phase
            solver_attempted = True
            self.controller.compute_control(
                predicted, {"dt": self.controller.config.dt, "previous_control": previous}
            )
            diagnostics = self.controller.diagnostics()
            if diagnostics["success"]:
                x, u, _ = self.controller.solution
                start = time + estimate
                packet = TrajectoryPacket(
                    plan_id,
                    time,
                    time,
                    start,
                    time,
                    start + np.arange(x.shape[1]) * self.controller.config.dt,
                    x.T,
                    u.T,
                    state,
                    predicted,
                    diagnostics["status"],
                    diagnostics["solve_time"],
                    diagnostics["total_compute_time"],
                )
                packet = replace(
                    packet, curvatures=np.asarray(self.controller.last_prediction["preview"])[0]
                )
                phase = perf_counter()
                times, gains = self.gain_builder.compute(packet)
                packet = replace(packet, gain_times=times, gains=gains)
                gain_time = perf_counter() - phase
                reason = "prepared"
        except (ValueError, np.linalg.LinAlgError) as error:
            # A nominal solve alone is insufficient if packet/gain preparation failed.
            packet = None
            diagnostics = {"success": False, "status": str(error), "solve_time": 0.0}
            reason = "prediction_or_gain_validation_failed"
        total = perf_counter() - wall
        cpu_time = process_time() - cpu
        if packet is not None:
            packet = replace(packet, total_computation_duration=total)
        return packet, {
            **diagnostics,
            "solver_attempted": solver_attempted,
            "plan_id": plan_id,
            "release_time": time,
            "estimated_delay": estimate,
            "predicted_completion_time": time + estimate,
            "prediction_time": prediction_time,
            "gain_time": gain_time,
            "planner_total_time": total,
            "planner_cpu_time": cpu_time,
            "preparation": reason,
            "source_state": np.asarray(state).tolist(),
            "predicted_state": predicted.tolist(),
        }
