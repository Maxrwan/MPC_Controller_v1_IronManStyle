"""Low-slip linear axle tire with provisional linear normal-load scaling.

No saturation or combined slip. Stiffness is axle aggregate, never per wheel.
"""

from math import isfinite

from apex.models.errors import VehicleModelValidityError
from apex.models.tire.base import AxleTireResult


class LinearAxleTire:
    def evaluate(
        self, slip_angle: float, nominal_stiffness: float, normal_load: float, static_load: float
    ) -> AxleTireResult:
        """Educational approximation C_eff=C*(Fz/Fz0), Fy=C_eff*alpha."""
        values = (slip_angle, nominal_stiffness, normal_load, static_load)
        if not all(isfinite(value) for value in values):
            raise VehicleModelValidityError("tire inputs must be finite")
        if min(nominal_stiffness, normal_load, static_load) <= 0:
            raise VehicleModelValidityError("stiffness and axle normal loads must be positive")
        stiffness = nominal_stiffness * (normal_load / static_load)
        force = stiffness * slip_angle
        if not isfinite(stiffness) or not isfinite(force):
            raise VehicleModelValidityError("nonfinite linear tire result")
        return AxleTireResult(force, stiffness)
