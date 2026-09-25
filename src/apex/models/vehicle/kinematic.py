"""CG kinematic bicycle: four propagated channels, two algebraic channels.

vy and r are reconstructed from vx and ideal instantaneous steering, never integrated.
This model contains no tire forces, inertia, load transfer, or actuator dynamics.
"""

from dataclasses import dataclass
from math import atan, cos, isfinite, pi, sin, tan

import numpy as np

from apex.coordinates.angles import wrap_angle
from apex.models.errors import ModelValidationError
from apex.models.frenet import FRENET_DENOMINATOR_MIN as FRENET_DENOMINATOR_MIN
from apex.models.frenet import validated_denominator
from apex.models.vehicle.parameters import VehicleParameters
from apex.state import ControlIndex, StateIndex, Vector, control_vector, state_vector
from apex.track.base import Track
from apex.track.progress import wrap_progress

DEFAULT_TIMESTEP = 0.01  # seconds; configuration default, not an integration constant.
SPEED_TOLERANCE = 1e-10  # m/s; floating-point boundary correction only.
STEERING_COSINE_MIN = 1e-8  # numerical guard near tan(delta)'s singularity.
_REDUCED_INDICES = [StateIndex.VX, StateIndex.E_PSI, StateIndex.S_ABS, StateIndex.E_Y]


@dataclass(frozen=True)
class KinematicDiagnostics:
    beta: float
    vy: float
    yaw_rate: float
    track_s: float
    curvature: float
    frenet_denominator: float


class KinematicBicycle:
    """Inject parameters and Track once; satisfy DynamicsModel.step(state, control, dt)."""

    def __init__(
        self, parameters: VehicleParameters, track: Track, *, default_dt: float = DEFAULT_TIMESTEP
    ) -> None:
        parameters.validate_for_kinematic()
        self._validate_dt(default_dt)
        wrap_progress(0.0, track.length)
        self.parameters = parameters
        self.track = track
        self.default_dt = float(default_dt)
        # Validation establishes these values; L follows the explicitly specified lf+lr.
        assert parameters.lf is not None and parameters.lr is not None
        self._lr = parameters.lr
        self._wheelbase = parameters.lf + parameters.lr

    @staticmethod
    def _validate_dt(dt: float) -> None:
        if not isfinite(dt) or dt <= 0:
            raise ModelValidationError("dt must be finite and positive [s]")

    def _speed(self, vx: float) -> float:
        if not isfinite(vx) or vx < -SPEED_TOLERANCE:
            raise ModelValidationError("forward-only vx must be finite and nonnegative [m/s]")
        vx = max(0.0, vx)
        limit = self.parameters.maximum_speed
        if limit is not None and vx > limit:
            if vx - limit > SPEED_TOLERANCE:
                raise ModelValidationError(f"vx={vx:g} exceeds maximum_speed={limit:g} m/s")
            vx = limit
        return vx

    def _control(self, control: Vector) -> tuple[float, float]:
        u = control_vector(control)
        delta, acceleration = float(u[ControlIndex.DELTA]), float(u[ControlIndex.A_CMD])
        # Principal front-wheel steering branch, not an invented physical actuator limit.
        if abs(delta) >= pi / 2 or abs(cos(delta)) <= STEERING_COSINE_MIN:
            raise ModelValidationError("delta is outside the regular steering domain (-pi/2, pi/2)")
        p = self.parameters
        if p.maximum_steering_angle is not None and abs(delta) > p.maximum_steering_angle:
            raise ModelValidationError("delta exceeds maximum_steering_angle")
        if p.maximum_acceleration is not None and acceleration > p.maximum_acceleration:
            raise ModelValidationError("a_cmd exceeds maximum_acceleration")
        if (
            p.maximum_braking_deceleration is not None
            and -acceleration > p.maximum_braking_deceleration
        ):
            raise ModelValidationError("a_cmd exceeds maximum_braking_deceleration magnitude")
        return delta, acceleration

    def _diagnostics(self, z: Vector, delta: float) -> KinematicDiagnostics:
        if not np.all(np.isfinite(z)) or z[2] < 0:
            raise ModelValidationError("reduced state must be finite with nonnegative s_abs")
        vx = self._speed(float(z[0]))
        beta = atan((self._lr / self._wheelbase) * tan(delta))
        vy = vx * tan(beta)
        yaw_rate = (vx / self._lr) * tan(beta)
        track_s = wrap_progress(float(z[2]), self.track.length)
        curvature = self.track.sample(track_s).curvature
        denominator = validated_denominator(curvature, z[3], z[2])
        if not all(isfinite(value) for value in (beta, vy, yaw_rate)):
            raise ModelValidationError("nonfinite kinematic algebraic quantities")
        return KinematicDiagnostics(beta, vy, yaw_rate, track_s, curvature, float(denominator))

    def diagnostics(self, state: Vector, control: Vector) -> KinematicDiagnostics:
        """Evaluate derived channels and geometry without advancing or mutating state."""
        x = state_vector(state)
        delta, _ = self._control(control)
        return self._diagnostics(x[_REDUCED_INDICES], delta)

    def consistent_state(self, state: Vector, control: Vector) -> Vector:
        """Copy a state onto the steering-dependent kinematic manifold."""
        x = state_vector(state)
        x[StateIndex.VX] = self._speed(float(x[StateIndex.VX]))
        d = self.diagnostics(x, control)
        x[StateIndex.VY], x[StateIndex.YAW_RATE] = d.vy, d.yaw_rate
        x[StateIndex.E_PSI] = wrap_angle(float(x[StateIndex.E_PSI]))
        return x

    def _rhs(self, z: Vector, delta: float, acceleration: float) -> Vector:
        d = self._diagnostics(z, delta)
        vx = self._speed(float(z[0]))
        e_psi = float(z[1])
        ds = (vx * cos(e_psi) - d.vy * sin(e_psi)) / d.frenet_denominator
        de_y = vx * sin(e_psi) + d.vy * cos(e_psi)
        return np.array([acceleration, d.yaw_rate - d.curvature * ds, ds, de_y])

    def step(self, state: Vector, control: Vector, dt: float | None = None) -> Vector:
        """RK4 under held input; split at the exact zero-speed event and hold at rest.

        Incoming finite vy/r are deliberately ignored and reconstructed. No race
        completion logic, physical input clipping, or independent vy/r derivatives.
        """
        timestep = self.default_dt if dt is None else dt
        self._validate_dt(timestep)
        delta, acceleration = self._control(control)
        x = state_vector(state)
        x[StateIndex.VX] = self._speed(float(x[StateIndex.VX]))
        z = x[_REDUCED_INDICES].copy()
        self._diagnostics(z, delta)  # Validate even if already stopped under braking.
        h = timestep
        stopping = acceleration < 0 and -acceleration * timestep >= z[0]
        if stopping:
            h = float(z[0] / -acceleration)
        final_vx = 0.0 if stopping else self._speed(float(z[0] + acceleration * timestep))
        if h > 0:
            k1 = self._rhs(z, delta, acceleration)
            k2 = self._rhs(z + h * k1 / 2, delta, acceleration)
            k3 = self._rhs(z + h * k2 / 2, delta, acceleration)
            k4 = self._rhs(z + h * k3, delta, acceleration)
            z = z + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        z[0] = final_vx  # Exact scalar solution, including the stopping event.
        x[_REDUCED_INDICES] = z
        # Also validates final geometry, which need not equal the k4 stage geometry.
        return self.consistent_state(x, control)
