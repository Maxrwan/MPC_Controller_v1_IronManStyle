"""Nonlinear CG bicycle using replaceable axle tires and normal-load components.

All six canonical channels are dynamic. a_cmd=Fx/m=dvx/dt-r*vy, unlike Task 003.
The prescribed body balances omit front-force steering rotation. Tire physics is selectable.
"""

from dataclasses import dataclass
from math import atan2, hypot, isfinite, sqrt

import numpy as np

from apex.coordinates.angles import wrap_angle
from apex.models.errors import (
    LowSpeedValidityError,
    ModelValidationError,
    VehicleModelValidityError,
)
from apex.models.frenet import frenet_rates, validated_denominator
from apex.models.integration import rk4_step
from apex.models.tire.base import AxleTireModel, CombinedAxleTireModel
from apex.models.tire.config import TirePhysics
from apex.models.tire.grip import SmoothCombinedGripTire
from apex.models.tire.linear import LinearAxleTire
from apex.models.vehicle.force_allocation import NormalLoadProportionalAllocation
from apex.models.vehicle.load_transfer import (
    AxleLoadModel,
    QuasiStaticLongitudinalLoadTransfer,
    validate_axle_loads,
)
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import ControlIndex as U
from apex.state import StateIndex as I
from apex.state import Vector, control_vector, state_vector
from apex.track.base import Track
from apex.track.progress import wrap_progress

DEFAULT_DYNAMIC_TIMESTEP = 0.005
DEFAULT_DYNAMIC_MIN_SPEED = 0.5
DYNAMIC_SPEED_TOLERANCE = 1e-10  # m/s; accept roundoff only, never regularize vx.


@dataclass(frozen=True)
class DynamicDiagnostics:
    alpha_f: float
    alpha_r: float
    fyf: float
    fyr: float
    fzf: float
    fzr: float
    fzf_static: float
    fzr_static: float
    cf: float
    cr: float
    cf_eff: float
    cr_eff: float
    track_s: float
    curvature: float
    frenet_denominator: float
    fx_total: float
    a_cmd: float
    mu: float | None
    front_lateral_utilization: float | None
    rear_lateral_utilization: float | None
    fx_front: float | None = None
    fx_rear: float | None = None
    front_friction_capacity: float | None = None
    rear_friction_capacity: float | None = None
    front_lateral_capacity: float | None = None
    rear_lateral_capacity: float | None = None
    front_combined_utilization: float | None = None
    rear_combined_utilization: float | None = None


class DynamicBicycle:
    """NumPy-first derivative and held-input RK4; explicit racing-speed validity."""

    def __init__(
        self,
        parameters: VehicleParameters,
        track: Track,
        *,
        default_dt: float = DEFAULT_DYNAMIC_TIMESTEP,
        v_dynamic_min: float = DEFAULT_DYNAMIC_MIN_SPEED,
        tire_model: AxleTireModel | CombinedAxleTireModel | None = None,
        load_model: AxleLoadModel | None = None,
        tire_physics: TirePhysics = TirePhysics(),
        force_allocation=None,
    ) -> None:
        parameters.validate_for_dynamic()
        if not isfinite(default_dt) or default_dt <= 0:
            raise ModelValidationError("default_dt must be finite and positive")
        if not isfinite(v_dynamic_min) or v_dynamic_min <= DYNAMIC_SPEED_TOLERANCE:
            raise ModelValidationError("v_dynamic_min must exceed the speed numerical tolerance")
        if parameters.maximum_speed is not None and parameters.maximum_speed < v_dynamic_min:
            raise ModelValidationError("maximum_speed is below v_dynamic_min")
        wrap_progress(0, track.length)
        self.parameters = parameters
        self.track = track
        self.default_dt = default_dt
        self.v_dynamic_min = v_dynamic_min
        if tire_model is not None and tire_physics.model != "linear":
            raise ValueError("Select tire_physics or inject tire_model, not both")
        self.tire_physics = tire_physics
        self.tire_model = (
            tire_model
            if tire_model is not None
            else (
                SmoothCombinedGripTire(parameters.tire_road_friction_coefficient)
                if tire_physics.model == "smooth_combined_grip"
                else LinearAxleTire()
            )
        )
        if (
            isinstance(self.tire_model, SmoothCombinedGripTire)
            and self.tire_model.mu != parameters.tire_road_friction_coefficient
        ):
            raise ValueError("Injected tire mu must match configured vehicle friction")
        self.force_allocation = force_allocation
        if self.force_allocation is None and tire_physics.longitudinal_allocation is not None:
            self.force_allocation = NormalLoadProportionalAllocation()
        if hasattr(self.tire_model, "evaluate_combined") and self.force_allocation is None:
            raise ValueError("Combined tire requires explicit force allocation")
        self.load_model = (
            QuasiStaticLongitudinalLoadTransfer() if load_model is None else load_model
        )

    def _inputs(self, state: Vector, control: Vector) -> tuple[Vector, Vector]:
        x, u = state_vector(state), control_vector(control)
        vx = float(x[I.VX])
        if vx < self.v_dynamic_min - DYNAMIC_SPEED_TOLERANCE:
            raise LowSpeedValidityError(
                f"vx={vx:g} m/s is below dynamic-model minimum {self.v_dynamic_min:g} m/s; "
                "no low-speed regularization or automatic model switch is implemented"
            )
        p = self.parameters
        if p.maximum_speed is not None and vx > p.maximum_speed + DYNAMIC_SPEED_TOLERANCE:
            raise ModelValidationError("vx exceeds maximum_speed")
        if p.maximum_steering_angle is not None and abs(u[U.DELTA]) > p.maximum_steering_angle:
            raise ModelValidationError("delta exceeds maximum_steering_angle")
        if p.maximum_acceleration is not None and u[U.A_CMD] > p.maximum_acceleration:
            raise ModelValidationError("a_cmd exceeds maximum_acceleration")
        if (
            p.maximum_braking_deceleration is not None
            and -u[U.A_CMD] > p.maximum_braking_deceleration
        ):
            raise ModelValidationError("a_cmd exceeds maximum_braking_deceleration")
        return x, u

    def _evaluate(self, x: Vector, u: Vector) -> DynamicDiagnostics:
        p = self.parameters
        assert p.mass is not None and p.lf is not None and p.lr is not None
        assert p.front_cornering_stiffness is not None and p.rear_cornering_stiffness is not None
        delta, acceleration = float(u[U.DELTA]), float(u[U.A_CMD])
        alpha_f = delta - atan2(x[I.VY] + p.lf * x[I.YAW_RATE], x[I.VX])
        alpha_r = -atan2(x[I.VY] - p.lr * x[I.YAW_RATE], x[I.VX])
        loads = self.load_model.evaluate(p, acceleration)
        validate_axle_loads(loads)
        fx_front, fx_rear = (
            (None, None)
            if self.force_allocation is None
            else (self.force_allocation.allocate(p.mass * acceleration, loads.front, loads.rear))
        )
        if fx_front is not None and (
            not all(isfinite(v) for v in (fx_front, fx_rear))
            or not np.isclose(fx_front + fx_rear, p.mass * acceleration, atol=1e-10, rtol=1e-12)
        ):
            raise VehicleModelValidityError("Allocation must preserve total longitudinal force")

        def tire(alpha, stiffness, load, static, fx):
            if hasattr(self.tire_model, "evaluate_combined"):
                return self.tire_model.evaluate_combined(alpha, stiffness, load, static, fx)
            return self.tire_model.evaluate(alpha, stiffness, load, static)

        front = tire(
            alpha_f, p.front_cornering_stiffness, loads.front, loads.front_static, fx_front
        )
        rear = tire(alpha_r, p.rear_cornering_stiffness, loads.rear, loads.rear_static, fx_rear)
        if not all(
            isfinite(v)
            for v in (
                front.lateral_force,
                rear.lateral_force,
                front.effective_stiffness,
                rear.effective_stiffness,
            )
        ):
            raise VehicleModelValidityError("tire component returned nonfinite force/stiffness")
        track_s = wrap_progress(float(x[I.S_ABS]), self.track.length)
        curvature = self.track.sample(track_s).curvature
        denominator = validated_denominator(curvature, x[I.E_Y], x[I.S_ABS])
        mu = p.tire_road_friction_coefficient
        uf = None if mu is None else abs(front.lateral_force) / (mu * loads.front)
        ur = None if mu is None else abs(rear.lateral_force) / (mu * loads.rear)
        return DynamicDiagnostics(
            alpha_f,
            alpha_r,
            front.lateral_force,
            rear.lateral_force,
            loads.front,
            loads.rear,
            loads.front_static,
            loads.rear_static,
            p.front_cornering_stiffness,
            p.rear_cornering_stiffness,
            front.effective_stiffness,
            rear.effective_stiffness,
            track_s,
            curvature,
            denominator,
            p.mass * acceleration,
            acceleration,
            mu,
            uf,
            ur,
            fx_front,
            fx_rear,
            None if mu is None else mu * loads.front,
            None if mu is None else mu * loads.rear,
            None
            if mu is None or fx_front is None or abs(fx_front) >= mu * loads.front
            else sqrt((mu * loads.front) ** 2 - fx_front**2),
            None
            if mu is None or fx_rear is None or abs(fx_rear) >= mu * loads.rear
            else sqrt((mu * loads.rear) ** 2 - fx_rear**2),
            None
            if mu is None or fx_front is None
            else hypot(fx_front, front.lateral_force) / (mu * loads.front),
            None
            if mu is None or fx_rear is None
            else hypot(fx_rear, rear.lateral_force) / (mu * loads.rear),
        )

    def diagnostics(self, state: Vector, control: Vector) -> DynamicDiagnostics:
        """Evaluate all stage quantities without mutation or time advancement."""
        return self._evaluate(*self._inputs(state, control))

    def derivative(self, state: Vector, control: Vector) -> Vector:
        """Continuous f(x,u) in fixed canonical order, independent of integration."""
        x, u = self._inputs(state, control)
        d = self._evaluate(x, u)
        p = self.parameters
        assert p.mass is not None and p.yaw_inertia is not None
        assert p.lf is not None and p.lr is not None
        de_psi, ds, de_y = frenet_rates(
            x[I.VX], x[I.VY], x[I.YAW_RATE], x[I.E_PSI], d.curvature, d.frenet_denominator
        )
        result = np.array(
            [
                d.fx_total / p.mass + x[I.YAW_RATE] * x[I.VY],
                (d.fyf + d.fyr) / p.mass - x[I.YAW_RATE] * x[I.VX],
                (p.lf * d.fyf - p.lr * d.fyr) / p.yaw_inertia,
                de_psi,
                ds,
                de_y,
            ]
        )
        if not np.all(np.isfinite(result)):
            raise VehicleModelValidityError("nonfinite dynamic derivative")
        return result

    def step(self, state: Vector, control: Vector, dt: float | None = None) -> Vector:
        """RK4 of all six states; every stage and final state must remain valid."""
        x, u = self._inputs(state, control)
        timestep = self.default_dt if dt is None else dt
        result = rk4_step(lambda stage: self.derivative(stage, u), x, timestep)
        self.diagnostics(result, u)  # Reject invalid final state, not only RK4 stages.
        result[I.E_PSI] = wrap_angle(float(result[I.E_PSI]))
        return result
