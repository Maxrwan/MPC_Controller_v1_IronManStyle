"""Accepted finite synthetic cases. Standard library only; safe before native setup."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import MappingProxyType

CONTRACT = "apex-vdl-linear-cases-v1"
PROFILE = "apex-vdl-rk4-zoh-v1"
ACCEPTED_REVISION = "0cc7e4f626311aec05977bd3beda40c346fa4214"
VEHICLE_SOURCE = "configs/vehicles/synthetic_dynamic_test_vehicle.yaml"
VEHICLE_SHA256 = "df1b853d21a1d3efaf858f7e58401151f2c5237793c40e16bb4189ed651f9cf3"
BASE = MappingProxyType(
    dict(
        name="synthetic_dynamic_test_vehicle",
        mass=2.0,
        yaw_inertia=0.025,
        wheelbase=0.30,
        lf=0.15,
        lr=0.15,
        cg_height=0.04,
        vehicle_width=None,
        vehicle_length=None,
        front_cornering_stiffness=45.0,
        rear_cornering_stiffness=45.0,
        tire_road_friction_coefficient=1.0,
        maximum_steering_angle=0.4,
        maximum_steering_rate=None,
        maximum_acceleration=2.0,
        maximum_braking_deceleration=3.0,
        maximum_speed=6.0,
    )
)
TREATMENTS = MappingProxyType(
    {
        "VDL1_BASE": ("baseline", None),
        "VDL1_IZ_HIGH": ("yaw_inertia", 0.030),
        "VDL1_STEER_HIGH": ("post_step_delta", 0.025),
        "VDL1_CF_HIGH": ("front_cornering_stiffness", 54.0),
        "VDL1_CR_HIGH": ("rear_cornering_stiffness", 54.0),
    }
)
CASES = tuple(TREATMENTS)
CRITERIA = MappingProxyType(
    {
        "version": "apex-vdl-provisional-qualification/1",
        "status": "provisional teaching criteria; no physical validation or error guarantee",
        "state_tolerance_per_channel_SI": 1e-5,
        "refinement_roundoff_floor_per_channel_SI": 1e-12,
        "refinement_contraction": 0.5,
        "yaw_signal_margin": 10.0,
        "maximum_absolute_slip_rad": 0.050,
        "maximum_lateral_utilization": 1.0,
        "maximum_sampled_corridor_violations": 0,
        "analytical_oracle_absolute_tolerance_per_quantity_SI": 1e-12,
        "refinement_timesteps_s": (0.005, 0.0025, 0.00125),
    }
)


def request_for(case_id="VDL1_BASE"):
    if not isinstance(case_id, str) or case_id not in TREATMENTS:
        raise ValueError("Unsupported finite laboratory case")
    return dict(
        contract_id=CONTRACT,
        runner_profile=PROFILE,
        case_id=case_id,
        grid_id="nominal",
        treatment=TREATMENTS[case_id][0],
    )


def validate(values):
    if not isinstance(values, dict) or set(values) != set(request_for()):
        raise ValueError("Lab configuration must contain exactly the versioned case keys")
    if any(type(value) is not str for value in values.values()):
        raise ValueError(
            "Lab configuration fields must be strings from the accepted finite registry"
        )
    expected = request_for(values["case_id"])
    if values != expected:
        raise ValueError("Unsupported lab contract/profile/grid/treatment; qualification is gated")
    return expected


def canonical_json(value):
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


def resolve(values, *, vehicle_yaml=None):
    config = validate(values)
    if vehicle_yaml is None:
        vehicle_yaml = (Path(__file__).resolve().parents[2] / VEHICLE_SOURCE).read_text()
    if not isinstance(vehicle_yaml, str):
        raise ValueError("Missing captured base vehicle YAML")
    if hashlib.sha256(vehicle_yaml.encode()).hexdigest() != VEHICLE_SHA256:
        raise ValueError("Base vehicle YAML differs from the accepted scientific contract")
    key, value = TREATMENTS[config["case_id"]]
    parameters = dict(BASE)
    overrides = {}
    if key not in {"baseline", "post_step_delta"}:
        overrides[key] = value
        parameters[key] = value
    amplitude = value if key == "post_step_delta" else 0.020
    return {
        "configuration": config,
        "accepted_contract_revision": ACCEPTED_REVISION,
        "base_source": {
            "path": VEHICLE_SOURCE,
            "sha256": VEHICLE_SHA256,
            "yaml": vehicle_yaml,
            "classification": "unmeasured synthetic fixture",
        },
        "base_parameters": dict(BASE),
        "effective_parameters": parameters,
        "parameter_overrides": overrides,
        "parameter_origins": {
            name: "accepted independent synthetic counterfactual"
            if name in overrides
            else "inherited synthetic YAML/default null"
            for name in BASE
        },
        "treatment": {
            "key": key,
            "old": 0.020 if key == "post_step_delta" else BASE.get(key),
            "new": value,
        },
        "initial_state": [2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "initial_state_origin": "accepted common synthetic seed; no equilibrium reconstruction",
        "schedule": {
            "duration_ticks": 100,
            "dt_plant_s": 0.005,
            "dt_input_ticks": 1,
            "segments": [
                {"start_tick": 0, "delta_rad": 0.0, "a_cmd_m_per_s2": 0.0},
                {"start_tick": 20, "delta_rad": amplitude, "a_cmd_m_per_s2": 0.0},
            ],
        },
        "composition": {
            "model": "apex.models.vehicle.dynamic_bicycle.DynamicBicycle",
            "tire": "apex.models.tire.linear.LinearAxleTire",
            "loads": "apex.models.vehicle.load_transfer.QuasiStaticLongitudinalLoadTransfer",
            "allocation": None,
            "gravity_m_per_s2": 9.81,
            "v_dynamic_min_m_per_s": 0.5,
            "speed_roundoff_m_per_s": 1e-10,
            "minimum_axle_load_N": 1e-9,
            "frenet_denominator_min": 1e-3,
        },
        "track": {
            "factory": "run_dynamic_bicycle_demo.synthetic_track",
            "radius_m": 5.0,
            "waypoint_count": 128,
            "left_width_m": 0.6,
            "right_width_m": 0.9,
        },
        "runner": {
            "class": "apex.simulation.runner.SimulationRunner",
            "integrator": "RK4",
            "latency": None,
            "target_laps": None,
            "stop_on_boundary": False,
            "duration_s": 0.5,
            "dt_control_s": 0.005,
            "terminal_input": "last held command; informational, no terminal interval",
        },
        "qualification_criteria": json.loads(canonical_json(dict(CRITERIA))),
    }


def validate_resolved(values, snapshot, *, vehicle_yaml=None):
    expected = resolve(values, vehicle_yaml=vehicle_yaml)
    if canonical_json(snapshot) != canonical_json(expected):
        raise ValueError("Resolved laboratory snapshot conflicts with the accepted case")
    return deepcopy(expected)


def verify_captured_sources(request):
    """Fail a lab worker if its captured composition/source has changed since admission."""
    root = Path(__file__).resolve().parents[2]
    validate_resolved(
        request["effective"],
        request["lab_resolved"],
        vehicle_yaml=request["provenance"]["vehicle_yaml"],
    )
    sources = request["provenance"]["source_sha256"]
    if not all(
        "tools/apex_workbench/" + name in sources
        for name in ("lab_configuration.py", "dynamic_lab.py", "lab_reporting.py", "worker.py")
    ):
        raise ValueError("Missing laboratory scientific source identity")
    for name, expected in sources.items():
        path = (root / name).resolve()
        if (
            not path.is_relative_to(root)
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Captured scientific source changed: " + name)
