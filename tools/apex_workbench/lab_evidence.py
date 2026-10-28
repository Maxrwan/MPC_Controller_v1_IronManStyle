"""Consume verified lab records without running a model or accepting qualification claims."""

import csv
import io
import re
from math import isfinite

from tools.apex_workbench import storage
from tools.apex_workbench.lab_configuration import canonical_json, validate_resolved
from tools.apex_workbench.lab_reporting import (
    DIAGNOSTIC_UNITS,
    OPTIONAL_DIAGNOSTIC_UNITS,
    summarize,
)

STATE_NAMES = ["vx", "vy", "r", "e_psi", "s_abs", "e_y"]
STATE_COLUMNS = [
    "time",
    *STATE_NAMES,
    "lap_index",
    "track_s",
    "curvature",
    "left_width",
    "right_width",
    "boundary_violation",
    "delta",
    "a_cmd",
]
CONTROL_COLUMNS = ["time", "delta", "a_cmd"]


def _rows(contents, columns, *, optional=()):
    reader = csv.DictReader(io.StringIO(contents.decode()))
    if reader.fieldnames != columns:
        raise ValueError("Laboratory CSV columns differ from the telemetry contract")
    rows = []
    for raw in reader:
        if set(raw) != set(columns) or any(v is None for v in raw.values()):
            raise ValueError("Malformed laboratory CSV row")
        row = {}
        for key, value in raw.items():
            if key == "boundary_violation":
                if value not in {"True", "False"}:
                    raise ValueError("Invalid corridor flag")
                row[key] = value == "True"
            elif value == "" and key in optional:
                row[key] = None
            else:
                row[key] = float(value)
                if not isfinite(row[key]):
                    raise ValueError("Nonfinite retained laboratory telemetry: " + key)
        rows.append(row)
    if not rows:
        raise ValueError("Empty laboratory telemetry")
    return rows


def read_record(directory):
    try:
        request = storage.read_request(directory, verified=True)
        status = storage.read_status(directory)
        if request["adapter"] != "dynamic_lab":
            raise ValueError("Not a laboratory record")
        storage.check_required_artifacts(directory, request, status)
        # All required lab contents are checked, even when a state-only graph is selected.
        for name in storage.required_artifacts(request, status):
            storage.artifact_bytes(directory, name)
        resolved = storage.artifact_json(directory, "experiment/resolved_lab.json")
        provenance = request["provenance"]
        numerical = storage.artifact_json(directory, "numerical_environment.json")
        if (
            request.get("record_version") != 2
            or request.get("adapter_version") != "0.2.0"
            or request.get("entry_point") != "tools/apex_workbench/dynamic_lab.py:execute"
            or request.get("controller") != "none (prescribed integer-tick ZOH input)"
            or provenance["model"] != resolved["composition"]["model"]
            or provenance["tire"] != "LinearAxleTire (unsaturated; mu diagnostic only)"
            or not all(
                isinstance(provenance[key], str) and provenance[key]
                for key in ("python_version", "timing_mode")
            )
            or not all(
                isinstance(provenance["packages"][key], str) and provenance["packages"][key]
                for key in (
                    "numpy",
                    "scipy",
                    "pandas",
                    "matplotlib",
                    "streamlit",
                    "plotly",
                    "psutil",
                    "threadpoolctl",
                )
            )
            or not isinstance(numerical, dict)
            or not all(
                key in numerical
                for key in ("python", "platform", "threadpools", "thread_environment")
            )
            or numerical["python"] != provenance["python_version"]
            or not isinstance(numerical["threadpools"], list)
            or not isinstance(numerical["thread_environment"], dict)
            or not numerical["platform"]
            or (numerical["platform"] == "darwin" and not numerical.get("native_control"))
        ):
            raise ValueError("Incomplete or inconsistent laboratory composition/numerical identity")
        sources = request["provenance"]["source_sha256"]
        required_sources = {
            "src/apex/models/vehicle/dynamic_bicycle.py",
            "src/apex/models/integration.py",
            "src/apex/models/tire/linear.py",
            "src/apex/models/vehicle/load_transfer.py",
            "src/apex/models/vehicle/parameters.py",
            "scripts/run_dynamic_bicycle_demo.py",
            "configs/vehicles/synthetic_dynamic_test_vehicle.yaml",
            *(
                "tools/apex_workbench/" + name
                for name in (
                    "lab_configuration.py",
                    "dynamic_lab.py",
                    "lab_reporting.py",
                    "lab_evidence.py",
                    "lab_comparison.py",
                    "configuration.py",
                    "worker.py",
                )
            ),
        }
        if not required_sources <= set(sources) or any(
            not isinstance(h, str) or not re.fullmatch("[0-9a-f]{64}", h) for h in sources.values()
        ):
            raise ValueError("Incomplete laboratory scientific source identity")
        validate_resolved(
            request["effective"], resolved, vehicle_yaml=request["provenance"]["vehicle_yaml"]
        )
        if canonical_json(resolved) != canonical_json(request["lab_resolved"]):
            raise ValueError("Request/export laboratory composition mismatch")
        contract = storage.artifact_json(directory, "experiment/telemetry_contract.json")
        units = {"time": "s", **DIAGNOSTIC_UNITS, **OPTIONAL_DIAGNOSTIC_UNITS}
        if (
            contract["schema"] != "apex-workbench-telemetry/1"
            or contract["lab_schema"] != "apex-vdl-telemetry/1"
            or contract["state_names"] != STATE_NAMES
            or contract["state_units"] != ["m/s", "m/s", "rad/s", "rad", "m", "m"]
            or contract["control_names"] != ["delta", "a_cmd"]
            or contract["control_units"] != ["rad", "m/s^2"]
            or contract["time_unit"] != "s"
            or contract["xy_unit"] != "m"
            or contract["state_columns"] != STATE_COLUMNS
            or contract["control_columns"] != CONTROL_COLUMNS
            or contract["diagnostic_units"] != units
            or len(contract["diagnostic_columns"]) != len(units)
            or set(contract["diagnostic_columns"]) != set(units)
            or contract["diagnostic_origin"]
            != "canonical diagnostics recomputed at retained samples"
            or contract["row_semantics"]
            != ("state at tick k; input held over next interval; terminal informational")
            or contract["terminal_input"] != resolved["runner"]["terminal_input"]
        ):
            raise ValueError("Unknown or inconsistent laboratory telemetry schema/units")
        states = _rows(storage.artifact_bytes(directory, "experiment/states.csv"), STATE_COLUMNS)
        controls = _rows(
            storage.artifact_bytes(directory, "experiment/controls.csv"), CONTROL_COLUMNS
        )
        diagnostics = _rows(
            storage.artifact_bytes(directory, "experiment/diagnostics.csv"),
            contract["diagnostic_columns"],
            optional=OPTIONAL_DIAGNOSTIC_UNITS,
        )
        summary = storage.artifact_json(directory, "experiment/summary.json")
        if storage.artifact_json(directory, "worker_result.json") != summary:
            raise ValueError("Worker and runner summaries disagree")
        receipt = storage.artifact_json(directory, "execution.json")
        if receipt["scientific_outcome"] != status["scientific_outcome"]:
            raise ValueError("Execution receipt and status disagree")
        complete = status["scientific_outcome"] == "completed"
        if len(states) > 101 or (complete and (len(states), len(controls)) != (101, 100)):
            raise ValueError("Laboratory horizon/row count mismatch")
        if len(diagnostics) != len(states) or len(controls) not in {len(states), len(states) - 1}:
            raise ValueError("Laboratory diagnostic/control coverage mismatch")
        if [states[0][name] for name in STATE_NAMES] != resolved["initial_state"]:
            raise ValueError("Laboratory initial state mismatch")
        for k, row in enumerate(states):
            if row["time"] != k * 0.005 or diagnostics[k]["time"] != row["time"]:
                raise ValueError("Retained laboratory tick mismatch")
            if row["boundary_violation"] != (
                not -row["right_width"] <= row["e_y"] <= row["left_width"]
            ):
                raise ValueError("Retained corridor flag disagrees with state/widths")
            delta = 0.0 if k < 20 else resolved["schedule"]["segments"][1]["delta_rad"]
            if (row["delta"], row["a_cmd"]) != (delta, 0.0):
                raise ValueError("State-row laboratory input mismatch")
            if k < len(controls) and controls[k] != {
                "time": k * 0.005,
                "delta": delta,
                "a_cmd": 0.0,
            }:
                raise ValueError("Actual applied laboratory input mismatch")
        expected = summarize(states, diagnostics, summary["runner_stop_reason"], summary["failure"])
        if (
            canonical_json(summary) != canonical_json(expected)
            or complete != summary["horizon_reached"]
        ):
            raise ValueError("Laboratory summary/qualification conflicts with retained telemetry")
        return {
            "request": request,
            "status": status,
            "resolved": resolved,
            "states": states,
            "controls": controls,
            "diagnostics": diagnostics,
            "summary": summary,
        }
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeError) as error:
        raise storage.IntegrityError("Laboratory record quarantined: " + str(error)) from error
