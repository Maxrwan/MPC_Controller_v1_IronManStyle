"""Minimal comparison eligibility over verified metadata and selected telemetry."""

import csv
import hashlib
import io

from tools.apex_workbench.configuration import validate
from tools.apex_workbench.storage import (
    IntegrityError,
    artifact_bytes,
    artifact_json,
    check_required_artifacts,
    read_request,
    read_status,
)


def fingerprint(directory):
    request = read_request(directory, verified=True)
    check_required_artifacts(directory, request, read_status(directory))
    provenance = request["provenance"]
    effective = validate(request["adapter"], request["effective"])
    contract = artifact_json(directory, "experiment/telemetry_contract.json")
    if contract["schema"] != "apex-workbench-telemetry/1":
        raise IntegrityError("Unknown telemetry schema")
    required = (
        "state_names",
        "state_units",
        "control_names",
        "control_units",
        "time_unit",
        "xy_unit",
    )
    if any(not contract[key] for key in required):
        raise IntegrityError("Missing telemetry units/order contract")
    source = {
        name: digest
        for name, digest in provenance["source_sha256"].items()
        if name.startswith(("src/", "scripts/", "configs/"))
        or name in {"tools/apex_workbench/worker.py", "tools/apex_workbench/configuration.py"}
    }
    if not source or any(
        not provenance[key] for key in ("model", "tire", "vehicle_yaml", "timing_mode")
    ):
        raise IntegrityError("Missing scientific identity")
    # Verify only the artifacts that will be used, not an entire result archive.
    state_bytes = artifact_bytes(directory, "experiment/states.csv")
    if next(csv.reader(io.StringIO(state_bytes.decode())), None) != contract["state_columns"]:
        raise IntegrityError("CSV schema does not match its telemetry contract")
    numerical = artifact_json(directory, "numerical_environment.json")
    geometry = artifact_bytes(directory, "experiment/geometry.csv")
    return effective, {
        "scientific_source": source,
        "adapter": request["adapter"],
        "model": provenance["model"],
        "tire": provenance["tire"],
        "controller": request["controller"],
        "vehicle": provenance["vehicle_yaml"],
        "track_geometry": hashlib.sha256(geometry).hexdigest(),
        "timing": provenance["timing_mode"],
        "numerical_environment": {
            "packages": {key: provenance["packages"][key] for key in ("numpy", "scipy")},
            "python": provenance["python_version"],
            "platform": numerical["platform"],
            "native_control": numerical.get("native_control"),
            "thread_environment": numerical["thread_environment"],
        },
        "telemetry_contract": contract,
    }


def eligibility(first, second):
    try:
        from tools.apex_workbench.jobs import status_for

        for directory in (first, second):
            status = status_for(directory)
            if status.get("scientific_outcome", status["state"]) != "completed":
                raise IntegrityError(
                    "Only completed scientific executions can be compared; "
                    "retain failures individually"
                )
        a, fa = fingerprint(first)
        b, fb = fingerprint(second)
        varied = {
            key: [a.get(key), b.get(key)] for key in a.keys() | b.keys() if a.get(key) != b.get(key)
        }
        differences = {key: [fa[key], fb[key]] for key in fa if fa[key] != fb[key]}
        if fa["telemetry_contract"] != fb["telemetry_contract"]:
            return {
                "classification": "invalid",
                "reason": "Telemetry schema/units/order differ",
                "differences": differences,
                "varied_inputs": varied,
            }
        return {
            "classification": "illustrative" if differences else "controlled",
            "reason": "Recorded composition/source differences; no causal ranking"
            if differences
            else "Matching scientific identity; explicitly varied inputs shown below",
            "differences": differences,
            "varied_inputs": varied,
        }
    except (IntegrityError, OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        return {
            "classification": "invalid",
            "reason": str(error),
            "differences": {},
            "varied_inputs": {},
        }
