"""Compose the canonical plant/runner; numerical imports occur only after worker setup."""

import csv
from dataclasses import asdict, replace
from math import isfinite

from tools.apex_workbench import lab_configuration as config
from tools.apex_workbench.lab_reporting import (
    DIAGNOSTIC_UNITS,
    OPTIONAL_DIAGNOSTIC_UNITS,
    summarize,
)
from tools.apex_workbench.storage import write_json


class PrescribedInputs:
    """Integer-call ZOH provider. The runner, not this class, propagates physics."""

    def __init__(self, schedule):
        if not isinstance(schedule, dict) or set(schedule) != {
            "dt_plant_s",
            "duration_ticks",
            "dt_input_ticks",
            "segments",
        }:
            raise ValueError("Unsupported input schedule schema")
        self.h = schedule["dt_plant_s"]
        self.steps = schedule["duration_ticks"]
        self.segments = tuple(dict(segment) for segment in schedule["segments"])
        if (
            isinstance(self.h, bool)
            or not isinstance(self.h, (int, float))
            or not isfinite(self.h)
            or self.h <= 0
            or type(self.steps) is not int
            or self.steps <= 0
            or schedule["dt_input_ticks"] != 1
            or type(schedule["dt_input_ticks"]) is not int
        ):
            raise ValueError("Invalid integer-grid input schedule")
        previous = -1
        for segment in self.segments:
            if set(segment) != {"start_tick", "delta_rad", "a_cmd_m_per_s2"}:
                raise ValueError("Unsupported schedule segment")
            tick = segment["start_tick"]
            if type(tick) is not int or not previous < tick < self.steps:
                raise ValueError("Input ticks must be strictly ordered and nonterminal")
            previous = tick
            for key, low, high in (("delta_rad", -0.4, 0.4), ("a_cmd_m_per_s2", -3.0, 2.0)):
                v = segment[key]
                if type(v) not in (float, int) or not isfinite(v) or not low <= v <= high:
                    raise ValueError("Invalid configured command: " + key)
        if not self.segments or self.segments[0]["start_tick"] != 0:
            raise ValueError("Input schedule must begin at tick zero")
        self.reset()

    def reset(self):
        self.tick = 0
        self.segment = 0

    def compute_control(self, state, context):
        if (
            self.tick >= self.steps
            or context["time"] != self.tick * self.h
            or context["dt"] != self.h
        ):
            raise ValueError("Runner input clock differs from the declared integer ticks")
        if (
            self.segment + 1 < len(self.segments)
            and self.segments[self.segment + 1]["start_tick"] == self.tick
        ):
            self.segment += 1
        segment = self.segments[self.segment]
        self.tick += 1
        return [segment["delta_rad"], segment["a_cmd_m_per_s2"]]


def construct(resolved):
    from run_dynamic_bicycle_demo import synthetic_track

    from apex.models.tire.linear import LinearAxleTire
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer
    from apex.models.vehicle.parameters import VehicleParameters

    base = VehicleParameters(**resolved["base_parameters"])
    parameters = replace(base, **resolved["parameter_overrides"])
    parameters.validate_for_dynamic()
    if asdict(parameters) != resolved["effective_parameters"]:
        raise ValueError("Constructed canonical parameters differ from the captured snapshot")
    return DynamicBicycle(
        parameters,
        synthetic_track(),
        default_dt=resolved["schedule"]["dt_plant_s"],
        v_dynamic_min=0.5,
        tire_model=LinearAxleTire(),
        load_model=QuasiStaticLongitudinalLoadTransfer(),
    )


def execute(values, output, *, resolved=None, qualification=False):
    from apex.simulation.runner import RunConfig, SimulationRunner
    from apex.state import state_vector

    config.execution_context(values, qualification=qualification)

    resolved = (
        config.resolve(values)
        if resolved is None
        else config.validate_resolved(
            values, resolved, vehicle_yaml=resolved["base_source"]["yaml"]
        )
    )
    output.mkdir(exist_ok=False)
    write_json(output / "resolved_lab.json", resolved, exclusive=True)
    model = construct(resolved)
    initial = state_vector(resolved["initial_state"])
    model.diagnostics(initial, [0.0, 0.0])
    provider = PrescribedInputs(resolved["schedule"])
    result = SimulationRunner(
        model,
        provider,
        model.track,
        RunConfig(
            duration=0.5,
            dt_plant=resolved["schedule"]["dt_plant_s"],
            dt_control=resolved["schedule"]["dt_plant_s"],
            latency=None,
            target_laps=None,
            stop_on_boundary=False,
        ),
        reset_controller=provider.reset,
    ).run(initial)
    return export_result(model, result, resolved, output)


def export_result(model, result, resolved, output):
    """Canonical sampled export shared by adapter/reference, never expected dynamics."""
    from apex.state import CONTROL_NAMES, STATE_NAMES
    from tools.apex_workbench.worker import export_geometry

    result.write_csv(output)  # Retain actual partials before diagnostic/geometry export.
    raw = {
        "runner_stop_reason": result.stop_reason,
        "failure": result.failure,
        "horizon_reached": bool(
            result.states
            and result.states[-1]["time"] == 0.5
            and result.stop_reason == "duration"
            and not result.failure
        ),
    }
    write_json(output / "summary.json", raw, exclusive=True)
    diagnostics = []
    for row in result.states:
        d = asdict(
            model.diagnostics([row[k] for k in STATE_NAMES], [row[k] for k in CONTROL_NAMES])
        )
        diagnostics.append({"time": row["time"], **d})
    with (output / "diagnostics.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(diagnostics[0]))
        writer.writeheader()
        writer.writerows(diagnostics)
    track_rows = []
    for row in result.states:
        sample = model.track.sample(row["track_s"])
        track_rows.append({"time": row["time"], **asdict(sample)})
    with (output / "track_samples.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(track_rows[0]))
        writer.writeheader()
        writer.writerows(track_rows)
    summary = summarize(result.states, diagnostics, result.stop_reason, result.failure)
    if not summary["horizon_reached"] and not summary["failure"]:
        summary["failure"] = "Canonical runner ended before the declared laboratory horizon"
    write_json(output / "summary.json", summary)
    export_geometry(
        "dynamic_lab",
        resolved["configuration"],
        output,
        track=model.track,
        telemetry_extra={
            "lab_schema": "apex-vdl-telemetry/2",
            "diagnostic_columns": list(diagnostics[0]),
            "diagnostic_units": {"time": "s", **DIAGNOSTIC_UNITS, **OPTIONAL_DIAGNOSTIC_UNITS},
            "diagnostic_origin": "canonical diagnostics recomputed at retained samples",
            "terminal_input": resolved["runner"]["terminal_input"],
            "row_semantics": (
                "state at tick k; input held over next interval; terminal informational"
            ),
            "track_columns": list(track_rows[0]),
            "track_units": {
                "time": "s",
                "track_s": "m",
                "x": "m",
                "y": "m",
                "heading": "rad",
                "curvature": "1/m",
                "left_width": "m",
                "right_width": "m",
            },
            "alias_equality": (
                "exact finite float64 values from the same canonical sampled state/input"
            ),
        },
    )
    return summary
