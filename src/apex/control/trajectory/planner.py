"""Planner adapter: nominal optimization, time prediction and gain preparation."""

from dataclasses import replace
from sys import exc_info
from time import perf_counter, process_time

import numpy as np

from apex.control.trajectory.packet import TrajectoryPacket
from apex.control.trajectory.prediction import ActuationPredictor
from apex.control.trajectory.tracker import TVLQR


class TrajectoryPlanner:
    def __init__(self, controller, track, tracker_dt=0.01, *, recorder=None):
        self._recorder = recorder
        self.controller = controller
        self.predictor = ActuationPredictor(controller.problem.model, track)
        if recorder is None:
            self.gain_builder = TVLQR(controller.problem.model, track, tracker_dt)
        else:
            _g1_gain_builder_construction = recorder.span_begin(
                recorder.active_call,
                "gain_builder_construction",
                expected_parent="planner_construction",
            )
            _g1_done_gain_builder_construction = False
            try:
                self.gain_builder = TVLQR(
                    controller.problem.model, track, tracker_dt, recorder=recorder
                )
                _g1_done_gain_builder_construction = True
            finally:
                _g1_error_gain_builder_construction = (
                    None if _g1_done_gain_builder_construction else exc_info()[0]
                )
                recorder.span_end(
                    _g1_gain_builder_construction,
                    exit="complete" if _g1_done_gain_builder_construction else "exception",
                    exception_type=None
                    if _g1_error_gain_builder_construction is None
                    else (
                        _g1_error_gain_builder_construction.__module__
                        + "."
                        + _g1_error_gain_builder_construction.__qualname__
                    ),
                )

    def prepare(
        self,
        plan_id,
        state,
        time,
        estimate,
        buffer,
        tracker,
        *,
        startup=False,
        committed_prefix=None,
    ):
        recorder = self._recorder
        wall, cpu = perf_counter(), process_time()
        prediction_time, gain_time = 0.0, 0.0
        solver_attempted = False
        packet, reason = None, "planner_failure"
        predicted = np.array(state, copy=True)
        previous = None
        try:
            if recorder is None:
                phase = perf_counter()
                if startup:
                    previous = tracker.previous.copy()
                elif committed_prefix is None:
                    predicted, previous = self.predictor.predict(
                        state, time, estimate, buffer, tracker
                    )
                else:
                    predicted, previous = self.predictor.predict(
                        state, time, estimate, buffer, tracker, committed_prefix=committed_prefix
                    )
                prediction_time = perf_counter() - phase
            else:
                _g1_prediction = recorder.span_begin(
                    recorder.active_call, "prediction", expected_parent="prepare_full"
                )
                _g1_done_prediction = False
                try:
                    phase = perf_counter()
                    if startup:
                        previous = tracker.previous.copy()
                    elif committed_prefix is None:
                        predicted, previous = self.predictor.predict(
                            state, time, estimate, buffer, tracker
                        )
                    else:
                        predicted, previous = self.predictor.predict(
                            state,
                            time,
                            estimate,
                            buffer,
                            tracker,
                            committed_prefix=committed_prefix,
                        )
                    prediction_time = perf_counter() - phase
                    _g1_done_prediction = True
                finally:
                    _g1_error_prediction = None if _g1_done_prediction else exc_info()[0]
                    recorder.span_end(
                        _g1_prediction,
                        exit="complete" if _g1_done_prediction else "exception",
                        exception_type=None
                        if _g1_error_prediction is None
                        else (
                            _g1_error_prediction.__module__
                            + "."
                            + _g1_error_prediction.__qualname__
                        ),
                    )
            solver_attempted = True
            if recorder is None:
                self.controller.compute_control(
                    predicted, {"dt": self.controller.config.dt, "previous_control": previous}
                )
            else:
                _g1_controller = recorder.span_begin(
                    recorder.active_call, "controller", expected_parent="prepare_full"
                )
                _g1_done_controller = False
                try:
                    self.controller.compute_control(
                        predicted, {"dt": self.controller.config.dt, "previous_control": previous}
                    )
                    _g1_done_controller = True
                finally:
                    _g1_error_controller = None if _g1_done_controller else exc_info()[0]
                    recorder.span_end(
                        _g1_controller,
                        exit="complete" if _g1_done_controller else "exception",
                        exception_type=None
                        if _g1_error_controller is None
                        else (
                            _g1_error_controller.__module__
                            + "."
                            + _g1_error_controller.__qualname__
                        ),
                    )
            diagnostics = self.controller.diagnostics()
            if diagnostics["success"]:
                if recorder is None:
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
                else:
                    _g1_packet_initial = recorder.span_begin(
                        recorder.active_call, "packet_initial", expected_parent="prepare_full"
                    )
                    _g1_done_packet_initial = False
                    try:
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
                            packet,
                            curvatures=np.asarray(self.controller.last_prediction["preview"])[0],
                        )
                        _g1_done_packet_initial = True
                    finally:
                        _g1_error_packet_initial = (
                            None if _g1_done_packet_initial else exc_info()[0]
                        )
                        recorder.span_end(
                            _g1_packet_initial,
                            exit="complete" if _g1_done_packet_initial else "exception",
                            exception_type=None
                            if _g1_error_packet_initial is None
                            else (
                                _g1_error_packet_initial.__module__
                                + "."
                                + _g1_error_packet_initial.__qualname__
                            ),
                        )
                phase = perf_counter()
                if recorder is None:
                    times, gains = self.gain_builder.compute(packet)
                else:
                    _g1_gains = recorder.span_begin(
                        recorder.active_call, "gains", expected_parent="prepare_full"
                    )
                    _g1_done_gains = False
                    try:
                        times, gains = self.gain_builder.compute(packet)
                        _g1_done_gains = True
                    finally:
                        _g1_error_gains = None if _g1_done_gains else exc_info()[0]
                        recorder.span_end(
                            _g1_gains,
                            exit="complete" if _g1_done_gains else "exception",
                            exception_type=None
                            if _g1_error_gains is None
                            else (_g1_error_gains.__module__ + "." + _g1_error_gains.__qualname__),
                        )
                if recorder is None:
                    packet = replace(packet, gain_times=times, gains=gains)
                else:
                    _g1_packet_gain_attach = recorder.span_begin(
                        recorder.active_call, "packet_gain_attach", expected_parent="prepare_full"
                    )
                    _g1_done_packet_gain_attach = False
                    try:
                        packet = replace(packet, gain_times=times, gains=gains)
                        _g1_done_packet_gain_attach = True
                    finally:
                        _g1_error_packet_gain_attach = (
                            None if _g1_done_packet_gain_attach else exc_info()[0]
                        )
                        recorder.span_end(
                            _g1_packet_gain_attach,
                            exit="complete" if _g1_done_packet_gain_attach else "exception",
                            exception_type=None
                            if _g1_error_packet_gain_attach is None
                            else (
                                _g1_error_packet_gain_attach.__module__
                                + "."
                                + _g1_error_packet_gain_attach.__qualname__
                            ),
                        )
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
            if recorder is None:
                packet = replace(packet, total_computation_duration=total)
            else:
                _g1_packet_final = recorder.span_begin(
                    recorder.active_call, "packet_final", expected_parent="prepare_full"
                )
                _g1_done_packet_final = False
                try:
                    packet = replace(packet, total_computation_duration=total)
                    _g1_done_packet_final = True
                finally:
                    _g1_error_packet_final = None if _g1_done_packet_final else exc_info()[0]
                    recorder.span_end(
                        _g1_packet_final,
                        exit="complete" if _g1_done_packet_final else "exception",
                        exception_type=None
                        if _g1_error_packet_final is None
                        else (
                            _g1_error_packet_final.__module__
                            + "."
                            + _g1_error_packet_final.__qualname__
                        ),
                    )
        if recorder is None:
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
                "predicted_previous_control": None if previous is None else previous.tolist(),
                "prediction_mode": (
                    "startup"
                    if startup
                    else "legacy"
                    if committed_prefix is None
                    else "committed_prefix"
                ),
            }
        else:
            _g1_return_assembly = recorder.span_begin(
                recorder.active_call, "return_assembly", expected_parent="prepare_full"
            )
            _g1_done_return_assembly = False
            try:
                _g1_value_return_assembly = (
                    packet,
                    {
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
                        "predicted_previous_control": None
                        if previous is None
                        else previous.tolist(),
                        "prediction_mode": (
                            "startup"
                            if startup
                            else "legacy"
                            if committed_prefix is None
                            else "committed_prefix"
                        ),
                    },
                )
                _g1_done_return_assembly = True
                return _g1_value_return_assembly
            finally:
                _g1_error_return_assembly = None if _g1_done_return_assembly else exc_info()[0]
                recorder.span_end(
                    _g1_return_assembly,
                    exit="complete" if _g1_done_return_assembly else "exception",
                    exception_type=None
                    if _g1_error_return_assembly is None
                    else (
                        _g1_error_return_assembly.__module__
                        + "."
                        + _g1_error_return_assembly.__qualname__
                    ),
                )
