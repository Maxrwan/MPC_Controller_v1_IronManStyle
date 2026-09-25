from dataclasses import fields
from pathlib import Path

import pytest
import yaml

from apex.config import load_vehicle_parameters
from apex.models.vehicle.parameters import VehicleParameters

TEMPLATE = Path(__file__).resolve().parents[2] / "configs/vehicles/generic_1_10_racecar.yaml"


def test_unknown_template_loads_but_cannot_simulate():
    parameters = load_vehicle_parameters(TEMPLATE)
    assert parameters.name == "generic_1_10_racecar"
    assert all(getattr(parameters, f.name) is None for f in fields(parameters) if f.name != "name")
    with pytest.raises(ValueError, match="Undefined vehicle parameters: mass"):
        parameters.validate_for_simulation()
    with pytest.raises(ValueError, match="Undefined"):
        load_vehicle_parameters(TEMPLATE, require_complete=True)


def test_complete_synthetic_configuration(tmp_path):
    # Synthetic parser/validation fixture only, never a physical vehicle recommendation.
    data = {f.name: 1.0 for f in fields(VehicleParameters) if f.name != "name"}
    data.update(name="synthetic_test_fixture", wheelbase=2.0, cg_height=0.0)
    path = tmp_path / "vehicle.yaml"
    path.write_text(yaml.safe_dump(data))
    assert load_vehicle_parameters(path, require_complete=True).wheelbase == 2.0


@pytest.mark.parametrize(
    "text",
    [
        "",
        "[]",
        "mass: 1",
        "name: test\nunknown: 1",
        "name: test\nmass: TBD",
        "name: test\nmass: true",
    ],
)
def test_bad_yaml_configuration(tmp_path, text):
    path = tmp_path / "bad.yaml"
    path.write_text(text)
    with pytest.raises(ValueError):
        load_vehicle_parameters(path)


@pytest.mark.parametrize("value", [-1, 0, float("inf"), float("nan"), True, "1"])
def test_invalid_mass(value):
    with pytest.raises(ValueError, match="mass"):
        VehicleParameters(name="test", mass=value)


def test_missing_fields_remain_unknown():
    parameters = VehicleParameters(name="test", mass=1)
    assert parameters.yaw_inertia is None
    with pytest.raises(ValueError, match="yaw_inertia"):
        parameters.validate_for_simulation()


def test_geometry_consistency():
    with pytest.raises(ValueError, match="wheelbase"):
        VehicleParameters(name="test", wheelbase=1, lf=1, lr=1)


@pytest.mark.parametrize("name", ["", "  ", None, 1])
def test_invalid_name(name):
    with pytest.raises(ValueError, match="name"):
        VehicleParameters(name=name)
