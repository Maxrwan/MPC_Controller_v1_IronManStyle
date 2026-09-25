"""Explicit model selection, separate from unknown physical vehicle parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TirePhysics:
    model: str = "linear"
    longitudinal_allocation: str | None = None

    def __post_init__(self):
        if self.model not in ("linear", "smooth_combined_grip"):
            raise ValueError("Unknown tire model")
        if self.longitudinal_allocation not in (None, "normal_load_proportional"):
            raise ValueError("Unsupported longitudinal force allocation")
        if self.model == "smooth_combined_grip" and self.longitudinal_allocation is None:
            raise ValueError("Grip model requires explicit longitudinal force allocation")


RACING_TIRE_PHYSICS = TirePhysics("smooth_combined_grip", "normal_load_proportional")
