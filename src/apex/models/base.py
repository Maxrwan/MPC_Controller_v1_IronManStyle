"""Structural model interface; plant and prediction instances are independent."""

from typing import Protocol

from apex.state import Vector


class DynamicsModel(Protocol):
    def step(self, state: Vector, control: Vector, dt: float) -> Vector:
        """Return next canonical state for positive dt [s], without mutating inputs.

        No integration scheme is prescribed. Plant and prediction implementations
        may use different equations, parameters, and discretizations.
        """
        ...
