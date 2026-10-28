"""Finite baseline/treatment candidates; no numerical qualification promotion."""

import hashlib

from tools.apex_workbench import storage
from tools.apex_workbench.lab_configuration import CRITERIA
from tools.apex_workbench.lab_evidence import read_record


def identity(record):
    request = record["request"]
    provenance = request["provenance"]
    numerical = storage.artifact_json(record["directory"], "numerical_environment.json")
    return {
        "scientific_source": request["source_inventory"],
        "grid": request["effective"]["grid_id"],
        "execution_context": request["execution_context"],
        "python": provenance["python_version"],
        "packages": provenance["packages"],
        "numerical_environment": numerical,
        "model": provenance["model"],
        "tire": provenance["tire"],
        "timing": provenance["timing_mode"],
        "controller": request["controller"],
        "geometry_sha256": hashlib.sha256(
            storage.artifact_bytes(record["directory"], "experiment/geometry.csv")
        ).hexdigest(),
        "telemetry": storage.artifact_json(
            record["directory"], "experiment/telemetry_contract.json"
        ),
    }


def eligibility(first, second, *, qualification_record=None):
    records = [read_record(path) for path in (first, second)]
    for record, path in zip(records, (first, second)):
        record["directory"] = path
    if any(r["status"]["scientific_outcome"] != "completed" for r in records):
        raise storage.IntegrityError("Only complete verified lab runs can form a candidate")
    a, b = records
    ia, ib = identity(a), identity(b)
    ia.pop("execution_context")
    ib.pop("execution_context")
    differences = {key: [ia[key], ib[key]] for key in ia if ia[key] != ib[key]}
    varied = {
        key: [a["request"]["effective"][key], b["request"]["effective"][key]]
        for key in a["request"]["effective"]
        if a["request"]["effective"][key] != b["request"]["effective"][key]
    }
    cases = [r["request"]["effective"]["case_id"] for r in records]
    permitted = cases.count("VDL1_BASE") == 1 and cases[0] != cases[1]
    permitted = permitted and all(
        r["request"]["effective"]["grid_id"] == "nominal"
        and r["request"]["execution_context"]["role"] == "adapter"
        and not r["request"]["execution_context"]["test_only"]
        for r in records
    )
    result = {
        "classification": "illustrative",
        "differences": differences,
        "varied_inputs": varied,
        "reason": "Not one of the four same-source baseline/treatment pairs; no causal ranking",
        "numerical_qualification": "not_qualified",
        "sampled_model_windows": [r["summary"]["sampled_model_window"] for r in records],
        "excitation": {"status": "unavailable for an incompatible pair"},
    }
    if permitted and not differences:
        # Each full snapshot, fixed field, state and applied schedule was validated independently.
        treatment = records[0 if cases[1] == "VDL1_BASE" else 1]["resolved"]["treatment"]
        peak = max(abs(x["r"] - y["r"]) for x, y in zip(a["states"][20:], b["states"][20:]))
        floor = CRITERIA["yaw_signal_margin"] * CRITERIA["state_tolerance_per_channel_SI"]
        result.update(
            classification="controlled_candidate",
            reason="Permitted single-factor pair; numerical qualification remains separately gated",
            declared_treatment=treatment,
            excitation={
                "observed_peak_yaw_difference_rad_per_s": peak,
                "minimum_provisional_signal_rad_per_s": floor,
                "status": "insufficient_excitation"
                if peak < floor
                else "unqualified; convergence discrepancies unavailable",
            },
        )
        if qualification_record is not None:
            from tools.apex_workbench.qualification import applicability

            applied = [applicability(qualification_record, path) for path in (first, second)]
            result["qualification_evidence"] = applied
            treatment_case = cases[1] if cases[0] == "VDL1_BASE" else cases[0]
            result["excitation"] = applied[0]["pair_results"][treatment_case]
            if (
                all(r["numerical_qualification"] == "grid_qualified_case" for r in applied)
                and applied[0]["comparison_pair_requirements"][treatment_case]
            ):
                result.update(
                    classification="qualified_synthetic_comparison",
                    reason=(
                        "Verified accepted provisional numerical protocol; no physical validation"
                    ),
                    numerical_qualification="qualified_synthetic_comparison",
                )
    return result
