"""Versioned qualification evidence bound to verified real source-run manifests."""

import hashlib
import json
from pathlib import Path

from tools.apex_workbench import storage
from tools.apex_workbench.configuration import ROOT
from tools.apex_workbench.lab_comparison import identity
from tools.apex_workbench.lab_configuration import CASES, CRITERIA, GRIDS, canonical_json
from tools.apex_workbench.lab_evidence import read_record
from tools.apex_workbench.lab_sources import REQUIRED, VERSION
from tools.apex_workbench.qualification_math import calculate

SCHEMA = "apex-vdl-qualification/1"
SLOTS = tuple(f"{case}/{grid}" for case in CASES for grid in GRIDS) + ("repeat", "reference")
PARITY_FILES = ("experiment/states.csv", "experiment/controls.csv", "experiment/diagnostics.csv")


def exact_export_comparison(baseline, other):
    """Byte comparison only; literal fixtures here cannot create qualification evidence."""
    if set(baseline) != set(PARITY_FILES) or set(other) != set(PARITY_FILES):
        raise ValueError("Incomplete repeat/reference export set")
    if any(type(v) is not bytes for v in (*baseline.values(), *other.values())):
        raise ValueError("Expected retained export bytes")
    return {name: baseline[name] == other[name] for name in PARITY_FILES}


def bind_run(directory):
    directory = Path(directory).resolve()
    initial_status = storage.read_status(directory)
    initial_manifest = storage.sha256(directory / "artifacts.json")
    if initial_status.get("manifest_sha256") != initial_manifest:
        raise storage.IntegrityError("Qualification source manifest is not committed")
    record = read_record(directory)
    # Binding the entire manifest requires every listed byte, including nonplotted artifacts.
    manifest = storage.artifact_manifest(directory)
    for name in manifest:
        storage.artifact_bytes(directory, name)
    if (
        storage.sha256(directory / "artifacts.json") != initial_manifest
        or storage.read_status(directory) != initial_status
    ):
        raise storage.IntegrityError("Qualification source changed while consumed")
    return {
        "directory": str(directory),
        "manifest_sha256": initial_manifest,
    }, record


def bound_run(reference):
    if not isinstance(reference, dict) or set(reference) != {"directory", "manifest_sha256"}:
        raise storage.IntegrityError("Invalid qualification source-run reference")
    actual, record = bind_run(reference["directory"])
    if actual != reference:
        raise storage.IntegrityError("Qualification source-run manifest identity changed")
    return record


def scientific_identity(record):
    result = identity(record)
    # These are deliberately varied by the accepted finite protocol, not omitted unknown fields.
    result.pop("grid")
    result.pop("execution_context")
    return result


def require_protocol_run(record, slot):
    request = record["request"]
    context = request["execution_context"]
    if (
        request.get("test_fixture_only")
        or context["test_only"]
        or context["purpose"] != "numerical_qualification"
        or context["protocol"] != CRITERIA["version"]
    ):
        raise storage.IntegrityError(
            "Test/interactive data cannot become scientific qualification evidence"
        )
    if record["status"]["scientific_outcome"] != "completed":
        raise storage.IntegrityError("Qualification requires successful source executions")
    expected_role = "canonical_reference" if slot == "reference" else "adapter"
    if context["role"] != expected_role:
        raise storage.IntegrityError("Qualification source role mismatch")
    case, grid = ("VDL1_BASE", "nominal") if slot in {"repeat", "reference"} else slot.split("/")
    if request["effective"]["case_id"] != case or request["effective"]["grid_id"] != grid:
        raise storage.IntegrityError("Qualification case/grid identity mismatch")


def evaluate_references(references):
    if not isinstance(references, dict) or set(references) != set(SLOTS):
        raise storage.IntegrityError(
            "Qualification requires exactly 15 grid runs, one repeat, one reference"
        )
    if len({str(Path(r["directory"]).resolve()) for r in references.values()}) != 17:
        raise storage.IntegrityError("Qualification slots must refer to 17 distinct executions")
    records = {slot: bound_run(references[slot]) for slot in SLOTS}
    for slot, record in records.items():
        require_protocol_run(record, slot)
    common = scientific_identity(records[SLOTS[0]])
    if any(scientific_identity(r) != common for r in records.values()):
        raise storage.IntegrityError(
            "Qualification source/composition/schema/environment identity differs"
        )
    family = {case: {grid: records[f"{case}/{grid}"] for grid in GRIDS} for case in CASES}
    calculation = calculate(family)
    baseline = records["VDL1_BASE/nominal"]
    parity = {}
    for role in ("repeat", "reference"):
        parity[role] = exact_export_comparison(
            {name: storage.artifact_bytes(baseline["directory"], name) for name in PARITY_FILES},
            {
                name: storage.artifact_bytes(records[role]["directory"], name)
                for name in PARITY_FILES
            },
        )
    satisfied = calculation["all_criteria_satisfied"] and all(
        all(values.values()) for values in parity.values()
    )
    parity_ok = all(all(values.values()) for values in parity.values())
    return {
        "schema": SCHEMA,
        "protocol": dict(CRITERIA),
        "references": references,
        "scientific_identity": common,
        "calculation": calculation,
        "exact_parity": parity,
        "numerical_cases": {
            case: calculation["cases"][case]["numerical_satisfied"] and parity_ok for case in CASES
        },
        "comparison_pairs": {
            case: result["satisfied"] and parity_ok for case, result in calculation["pairs"].items()
        },
        "decision": "qualified_synthetic_comparisons" if satisfied else "not_qualified",
        "physical_validity": "not_established",
        "test_fixture_only": False,
    }


def publish(references, directory):
    """Called only by the explicitly authorized future campaign, never by fixture tests."""
    document = evaluate_references(references)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    storage.write_json(directory / "qualification.json", document, exclusive=True)
    storage.write_json(
        directory / "commit.json",
        {
            "schema": SCHEMA,
            "qualification_sha256": storage.sha256(directory / "qualification.json"),
        },
        exclusive=True,
    )
    return document


def _read_qualification(directory, *, require_current_source=True):
    directory = Path(directory)
    commit_bytes = (directory / "commit.json").read_bytes()
    commit = json.loads(commit_bytes)
    if set(commit) != {"schema", "qualification_sha256"}:
        raise storage.IntegrityError("Unknown qualification commit schema")
    raw = (directory / "qualification.json").read_bytes()
    if commit.get("schema") != SCHEMA or hashlib.sha256(raw).hexdigest() != commit.get(
        "qualification_sha256"
    ):
        raise storage.IntegrityError("Qualification commit missing or changed")
    document = json.loads(raw)
    if document.get("schema") != SCHEMA or document.get("test_fixture_only") is not False:
        raise storage.IntegrityError("Unknown/test-only qualification evidence")
    actual = evaluate_references(document["references"])
    if canonical_json(document) != canonical_json(actual):
        raise storage.IntegrityError(
            "Qualification record no longer matches referenced evidence/criteria"
        )
    if require_current_source:
        check_current_source(document["scientific_identity"]["scientific_source"])
    if (directory / "commit.json").read_bytes() != commit_bytes or (
        directory / "qualification.json"
    ).read_bytes() != raw:
        raise storage.IntegrityError("Qualification document changed while consumed")
    return document


def read_qualification(directory, *, require_current_source=True):
    try:
        return _read_qualification(directory, require_current_source=require_current_source)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        raise storage.IntegrityError("Qualification evidence quarantined: " + str(error)) from error


def check_current_source(inventory):
    if inventory.get("version") != VERSION or set(inventory["sha256"]) != set(REQUIRED):
        raise storage.IntegrityError("Unknown/incomplete qualification source inventory")
    for name, digest in inventory["sha256"].items():
        if not (ROOT / name).is_file() or storage.sha256(ROOT / name) != digest:
            raise storage.IntegrityError("Qualification is inapplicable to changed source: " + name)


def applicability(directory, run_directory):
    """Revalidates all source evidence and the selected run on every consumption."""
    document = read_qualification(directory)
    run = read_record(run_directory)
    if run["status"]["scientific_outcome"] != "completed":
        raise storage.IntegrityError("Noncompleted runs cannot inherit qualification")
    if run["request"]["execution_context"]["test_only"]:
        raise storage.IntegrityError("Test-only runs cannot inherit qualification")
    if run["request"]["effective"]["grid_id"] != "nominal":
        raise storage.IntegrityError("Teaching qualification applies to nominal profiles only")
    if scientific_identity(run) != document["scientific_identity"]:
        raise storage.IntegrityError("Qualification source/environment/composition is inapplicable")
    case = run["request"]["effective"]["case_id"]
    slot = case + "/nominal"
    qualified_case = bound_run(document["references"][slot])
    for name in (*PARITY_FILES, "experiment/track_samples.csv", "experiment/trajectory_xy.csv"):
        if storage.artifact_bytes(run_directory, name) != storage.artifact_bytes(
            qualified_case["directory"], name
        ):
            raise storage.IntegrityError("Selected run data differ from the qualified finite case")
    return {
        "numerical_qualification": "grid_qualified_case"
        if document["numerical_cases"][case]
        else "not_qualified",
        "comparison_pair_requirements": document["comparison_pairs"],
        "pair_results": document["calculation"]["pairs"],
        "sampled_model_window": run["summary"]["sampled_model_window"],
        "physical_validity": "not_established",
        "qualification_directory": str(directory),
        "record_sha256": storage.sha256(Path(directory) / "qualification.json"),
    }
