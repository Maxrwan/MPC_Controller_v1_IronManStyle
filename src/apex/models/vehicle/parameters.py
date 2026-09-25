"""Vehicle configuration with explicitly unknown physical parameters."""

from dataclasses import dataclass, fields
from math import isclose, isfinite


@dataclass(frozen=True)
class VehicleParameters:
    """SI parameters; cornering stiffness is axle-aggregate [N/rad].

    Braking deceleration is a positive magnitude. No per-tire stiffness is implied.
    """

    name: str
    mass: float | None = None
    yaw_inertia: float | None = None
    wheelbase: float | None = None
    lf: float | None = None
    lr: float | None = None
    cg_height: float | None = None
    vehicle_width: float | None = None
    vehicle_length: float | None = None
    front_cornering_stiffness: float | None = None
    rear_cornering_stiffness: float | None = None
    tire_road_friction_coefficient: float | None = None
    maximum_steering_angle: float | None = None
    maximum_steering_rate: float | None = None
    maximum_acceleration: float | None = None
    maximum_braking_deceleration: float | None = None
    maximum_speed: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a nonempty string")
        for field in fields(self):
            if field.name == "name":
                continue
            value = getattr(self, field.name)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field.name} must be a number or null")
            minimum_ok = value >= 0 if field.name == "cg_height" else value > 0
            if not isfinite(value) or not minimum_ok:
                raise ValueError(f"{field.name} has an invalid SI value")
        if self.wheelbase is not None and self.lf is not None and self.lr is not None:
            if not isclose(self.wheelbase, self.lf + self.lr, rel_tol=1e-6, abs_tol=1e-9):
                raise ValueError("wheelbase must equal lf + lr")

    def validate_for_simulation(self) -> None:
        """Reject incomplete templates before use in a future simulator."""
        missing = [field.name for field in fields(self) if getattr(self, field.name) is None]
        if missing:
            raise ValueError("Undefined vehicle parameters: " + ", ".join(missing))

    def validate_for_kinematic(self) -> None:
        """Require only CG bicycle geometry; preserve the full simulation gate."""
        missing = [name for name in ("wheelbase", "lf", "lr") if getattr(self, name) is None]
        if missing:
            raise ValueError("Undefined kinematic geometry: " + ", ".join(missing))
        # Positivity and wheelbase consistency are enforced on construction.

    def validate_for_dynamic(self) -> None:
        """Require force-model parameters; mu remains optional diagnostic metadata."""
        required = (
            "mass",
            "yaw_inertia",
            "wheelbase",
            "lf",
            "lr",
            "cg_height",
            "front_cornering_stiffness",
            "rear_cornering_stiffness",
        )
        missing = [name for name in required if getattr(self, name) is None]
        if missing:
            raise ValueError("Undefined dynamic parameters: " + ", ".join(missing))
