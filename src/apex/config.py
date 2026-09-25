"""Safe YAML configuration loading; templates are allowed until simulation validation."""

from dataclasses import fields
from pathlib import Path

import yaml

from apex.models.vehicle.parameters import VehicleParameters


def load_vehicle_parameters(
    path: str | Path, *, require_complete: bool = False
) -> VehicleParameters:
    """Load known keys only, optionally requiring simulation-ready parameters."""
    with Path(path).open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError("Vehicle YAML must contain a mapping")
    allowed = {field.name for field in fields(VehicleParameters)}
    unknown = set(data) - allowed
    if unknown:
        raise ValueError(f"Unknown vehicle parameter keys: {sorted(map(str, unknown))}")
    if "name" not in data:
        raise ValueError("Missing vehicle name")
    parameters = VehicleParameters(**data)
    if require_complete:
        parameters.validate_for_simulation()
    return parameters


def load_tire_physics(path: str | Path):
    """Select force physics independently of physical vehicle measurements."""
    from apex.models.tire.config import TirePhysics

    with Path(path).open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError("Tire physics YAML must contain a mapping")
    unknown = set(data) - {"model", "longitudinal_allocation"}
    if unknown:
        raise ValueError(f"Unknown tire physics keys: {sorted(map(str, unknown))}")
    return TirePhysics(**data)
