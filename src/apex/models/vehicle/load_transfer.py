"""Provisional quasi-static longitudinal axle loads; no suspension/roll/pitch states."""

from dataclasses import dataclass
from math import isfinite
from typing import Protocol

from apex.models.constants import STANDARD_GRAVITY
from apex.models.errors import VehicleModelValidityError
from apex.models.vehicle.parameters import VehicleParameters

MIN_AXLE_LOAD = 1e-9  # N; reject unloaded or numerically indistinguishable-from-zero axles.


@dataclass(frozen=True)
class AxleLoads:
    front: float
    rear: float
    front_static: float
    rear_static: float


class AxleLoadModel(Protocol):
    def evaluate(self, parameters: VehicleParameters, a_cmd: float) -> AxleLoads:
        """Return actual/static front/rear axle loads [N]."""
        ...


@dataclass(frozen=True)
class QuasiStaticLongitudinalLoadTransfer:
    gravity: float = STANDARD_GRAVITY

    def __post_init__(self) -> None:
        if not isfinite(self.gravity) or self.gravity <= 0:
            raise ValueError("gravity must be finite and positive [m/s^2]")

    def evaluate(self, parameters: VehicleParameters, a_cmd: float) -> AxleLoads:
        """Use a_cmd=dvx/dt-r*vy, not body-coordinate dvx/dt."""
        p = parameters
        if any(getattr(p, name) is None for name in ("mass", "lf", "lr", "cg_height")):
            raise ValueError("load transfer requires mass, lf, lr, cg_height")
        if not isfinite(a_cmd):
            raise VehicleModelValidityError("load-transfer a_cmd must be finite")
        assert p.mass is not None and p.lf is not None and p.lr is not None
        assert p.cg_height is not None
        length = p.lf + p.lr
        front_static = p.mass * self.gravity * p.lr / length
        rear_static = p.mass * self.gravity * p.lf / length
        transfer = p.mass * a_cmd * p.cg_height / length
        result = AxleLoads(
            front_static - transfer, rear_static + transfer, front_static, rear_static
        )
        validate_axle_loads(result)
        return result


def validate_axle_loads(loads: AxleLoads) -> None:
    """Reject unloading without clamping, including results of injected load models."""
    values = (loads.front, loads.rear, loads.front_static, loads.rear_static)
    if not all(isfinite(value) and value > MIN_AXLE_LOAD for value in values):
        raise VehicleModelValidityError(
            f"Axle unloading/invalid loads: Fzf={loads.front:g}, Fzr={loads.rear:g}; "
            f"actual and static loads must exceed {MIN_AXLE_LOAD:g} N"
        )
