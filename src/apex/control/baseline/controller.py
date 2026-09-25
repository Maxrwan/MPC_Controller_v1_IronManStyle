"""Feedforward + scheduled LQR + PI, using perfect canonical state feedback."""

from collections.abc import Callable, Mapping
from dataclasses import asdict

import numpy as np

from apex.control.baseline.lqr import DesignScales, ScheduledLQR
from apex.control.baseline.references import (
    ConstantSpeed,
    cornering_reference,
    validate_reference_speed,
)
from apex.control.baseline.speed import SpeedPI
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import StateIndex as S
from apex.state import Vector, control_vector, state_vector
from apex.track.base import Track
from apex.track.progress import wrap_progress


class BaselineController:
    def __init__(
        self,
        parameters: VehicleParameters,
        track: Track,
        speed_reference: Callable[[float], float] = ConstantSpeed(),
        *,
        dt: float = 0.01,
        scales: DesignScales = DesignScales(),
        kp: float = 1.0,
        ki: float = 0.5,
    ):
        parameters.validate_for_dynamic()
        for name in (
            "maximum_steering_angle",
            "maximum_acceleration",
            "maximum_braking_deceleration",
        ):
            if getattr(parameters, name) is None:
                raise ValueError(f"Baseline requires configured {name}")
        self.parameters, self.track, self.speed_reference, self.dt = (
            parameters,
            track,
            speed_reference,
            dt,
        )
        self.lqr = ScheduledLQR(parameters, dt, scales)
        self.speed = SpeedPI(
            parameters.maximum_acceleration, parameters.maximum_braking_deceleration, kp, ki
        )
        self.reset()

    def reset(self):
        self.speed.reset()
        self.previous_delta = 0.0
        self.last_diagnostics = {}

    def compute_control(self, state: Vector, context: Mapping[str, object]) -> Vector:
        if "dt" in context and not np.isclose(float(context["dt"]), self.dt, rtol=0, atol=1e-12):
            raise ValueError("Controller context dt must match LQR discretization")
        x = state_vector(state)
        geometry = self.track.sample(wrap_progress(x[S.S_ABS], self.track.length))
        target = validate_reference_speed(self.speed_reference(geometry.track_s))
        gain, scheduled, clamped = self.lqr.gain(x[S.VX])
        reference = cornering_reference(self.parameters, x[S.VX], geometry.curvature)
        error = np.array(
            [x[S.E_Y], x[S.E_PSI], x[S.VY] - reference.vy, x[S.YAW_RATE] - reference.yaw_rate]
        )
        feedback = float(-gain @ error)
        unsaturated = reference.delta_dynamic + feedback
        limit = self.parameters.maximum_steering_angle
        angle_limited = float(np.clip(unsaturated, -limit, limit))
        delta = angle_limited
        rate_limit = self.parameters.maximum_steering_rate
        if rate_limit is not None:
            delta = float(
                np.clip(
                    delta,
                    self.previous_delta - rate_limit * self.dt,
                    self.previous_delta + rate_limit * self.dt,
                )
            )
        rate = (delta - self.previous_delta) / self.dt
        longitudinal = self.speed.update(x[S.VX], target, self.dt)
        self.previous_delta = delta
        self.last_diagnostics = {
            "curvature": geometry.curvature,
            "reference_speed": target,
            "vy_ref": reference.vy,
            "r_ref": reference.yaw_rate,
            "delta_feedforward": reference.delta_dynamic,
            "delta_kinematic": reference.delta_kinematic,
            "delta_feedback": feedback,
            "delta_unsaturated": unsaturated,
            "delta": delta,
            "steering_saturated": angle_limited != unsaturated,
            "steering_rate_limited": delta != angle_limited,
            "steering_rate": rate,
            "scheduling_speed": scheduled,
            "scheduling_clamped": clamped,
            **dict(zip(("gain_e_y", "gain_e_psi", "gain_vy", "gain_r"), map(float, gain))),
            **asdict(longitudinal),
        }
        return control_vector([delta, longitudinal.acceleration])

    def diagnostics(self):
        """Independent snapshot for the runner's optional diagnostics callback."""
        return dict(self.last_diagnostics)
