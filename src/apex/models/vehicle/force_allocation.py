"""Replaceable idealized longitudinal allocation; no drivetrain claim."""

from math import isfinite
from typing import Protocol

from apex.models.errors import VehicleModelValidityError


class LongitudinalForceAllocation(Protocol):
    def allocate(
        self, total: float, front_load: float, rear_load: float
    ) -> tuple[float, float]: ...


class NormalLoadProportionalAllocation:
    def allocate(self, total, front_load, rear_load):
        if (
            not all(isfinite(v) for v in (total, front_load, rear_load))
            or min(front_load, rear_load) <= 0
        ):
            raise VehicleModelValidityError("Force allocation requires finite positive axle loads")
        load = front_load + rear_load
        return total * front_load / load, total * rear_load / load
