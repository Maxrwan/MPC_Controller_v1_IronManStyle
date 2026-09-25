"""Smooth engineering friction envelope, not a fitted named tire model."""

from dataclasses import dataclass
from math import hypot, isfinite, sqrt, tanh

from apex.models.errors import VehicleModelValidityError
from apex.models.tire.base import AxleTireResult
from apex.models.tire.linear import LinearAxleTire

# Dimensionless reserve in |Fx|/(mu Fz), shared with the symbolic domain.
LONGITUDINAL_MARGIN = 1e-6


class TireForceValidityError(VehicleModelValidityError):
    """Requested axle force is outside the explicitly admissible grip domain."""


@dataclass(frozen=True)
class CombinedTireResult(AxleTireResult):
    longitudinal_force: float
    friction_capacity: float
    lateral_capacity: float
    combined_utilization: float


class SmoothCombinedGripTire:
    def __init__(self, mu: float):
        if mu is None or not isfinite(mu) or mu <= 0:
            raise ValueError("SmoothCombinedGripTire requires explicit finite mu > 0")
        self.mu = mu

    def evaluate_combined(self, slip_angle, nominal_stiffness, normal_load, static_load, fx):
        linear = LinearAxleTire().evaluate(slip_angle, nominal_stiffness, normal_load, static_load)
        limit = self.mu * normal_load
        if not isfinite(fx) or abs(fx) > (1 - LONGITUDINAL_MARGIN) * limit:
            raise TireForceValidityError(
                "Longitudinal demand must satisfy |Fx| <= (1-1e-6)*mu*Fz; no clipping"
            )
        capacity = sqrt(limit**2 - fx**2)
        fy = capacity * tanh(linear.lateral_force / capacity)
        return CombinedTireResult(
            fy, linear.effective_stiffness, fx, limit, capacity, hypot(fx, fy) / limit
        )
