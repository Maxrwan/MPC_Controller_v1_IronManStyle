"""Small axle lateral-force interface; independent of body dynamics and solvers."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AxleTireResult:
    lateral_force: float
    effective_stiffness: float


class AxleTireModel(Protocol):
    def evaluate(
        self, slip_angle: float, nominal_stiffness: float, normal_load: float, static_load: float
    ) -> AxleTireResult:
        """Return axle aggregate force [N] and effective stiffness [N/rad]."""
        ...


class CombinedAxleTireModel(Protocol):
    def evaluate_combined(
        self,
        slip_angle: float,
        nominal_stiffness: float,
        normal_load: float,
        static_load: float,
        longitudinal_force: float,
    ) -> AxleTireResult:
        """Return bounded axle lateral force for an explicit longitudinal demand."""
        ...
