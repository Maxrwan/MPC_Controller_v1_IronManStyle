"""C1–C3 regressions on new genuine records and deliberately rebound disposable copies."""

import ast
import csv
import shutil
from copy import deepcopy

import pytest

from tools.apex_workbench import comparison, configuration, jobs, storage
from tools.apex_workbench import lab_configuration as config
from tools.apex_workbench.lab_evidence import read_record
from tools.apex_workbench.lab_reporting import summarize
from tools.apex_workbench.lab_sources import REQUIRED, from_captured, validate
from tools.apex_workbench.tests.test_corrections import finished, reseal_fixture


def copy_run(source, target):
    shutil.copytree(source, target)
    return target


def rewrite_csv(path, transform):
    with path.open() as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    transform(rows)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize("name", REQUIRED)
def test_every_inventory_identity_is_mandatory(lab_runs, name):
    request = deepcopy(read_record(lab_runs[0])["request"])
    del request["provenance"]["source_sha256"][name]
    request["source_inventory"]["sha256"].pop(name)
    with pytest.raises(ValueError, match="Incomplete"):
        validate(request)
    with pytest.raises(ValueError):
        config.verify_captured_sources(request)


def test_inventory_covers_actual_canonical_import_closure():
    required = set(REQUIRED)
    for name in REQUIRED:
        assert (configuration.ROOT / name).is_file(), name
        if not name.startswith("src/") or not name.endswith(".py"):
            continue
        for node in ast.walk(ast.parse((configuration.ROOT / name).read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("apex"):
                relative = "src/" + node.module.replace(".", "/")
                candidates = [relative + ".py", relative + "/__init__.py"]
                present = next((p for p in candidates if (configuration.ROOT / p).is_file()), None)
                assert present in required, (name, node.module)


def test_c1_missing_runner_invalidates_both_read_and_comparison(lab_runs, tmp_path):
    paths = []
    for i, original in enumerate(lab_runs):
        target = copy_run(original, tmp_path / str(i))
        request = storage.read_json(target / "request.json")
        request["provenance"]["source_sha256"].pop("src/apex/simulation/runner.py")
        request["source_inventory"]["sha256"].pop("src/apex/simulation/runner.py")
        storage.write_json(target / "request.json", request)
        reseal_fixture(target)
        paths.append(target)
        with pytest.raises(storage.IntegrityError):
            read_record(target)
    assert comparison.eligibility(*paths)["classification"] == "invalid"


def test_no_current_checkout_inference_and_inventory_consistency(lab_runs):
    request = deepcopy(read_record(lab_runs[0])["request"])
    request.pop("source_inventory")
    with pytest.raises(ValueError, match="Missing/conflicting"):
        validate(request)
    ledger = deepcopy(read_record(lab_runs[0])["request"]["provenance"]["source_sha256"])
    ledger["src/apex/state.py"] = "invalid"
    with pytest.raises(ValueError):
        from_captured(ledger)


@pytest.mark.parametrize(
    "file,key,value",
    [
        ("diagnostics.csv", "a_cmd", "1.0"),
        ("diagnostics.csv", "track_s", "0.123"),
        ("diagnostics.csv", "curvature", "0.3"),
        ("diagnostics.csv", "cf", "540.0"),
        ("track_samples.csv", "curvature", "0.3"),
        ("track_samples.csv", "left_width", "0.8"),
    ],
)
def test_c2_rebound_alias_contradictions_are_rejected(lab_runs, tmp_path, file, key, value):
    target = copy_run(lab_runs[0], tmp_path / "contradiction")
    rewrite_csv(target / "experiment" / file, lambda rows: rows[25].__setitem__(key, value))
    if file == "diagnostics.csv":
        record = read_record(lab_runs[0])
        diagnostics = deepcopy(record["diagnostics"])
        diagnostics[25][key] = float(value)
        summary = summarize(record["states"], diagnostics, "duration", None)
        storage.write_json(target / "experiment/summary.json", summary)
        storage.write_json(target / "worker_result.json", summary)
    reseal_fixture(target)
    with pytest.raises(storage.IntegrityError, match="contradict"):
        read_record(target)


@pytest.mark.parametrize("outcome", ["cancelled", "interrupted", "failed"])
def test_c3_complete_integration_with_unsuccessful_process_is_inspectable(
    lab_runs, tmp_path, outcome
):
    target = copy_run(lab_runs[0], tmp_path / outcome)
    for name in ("execution.json", "status.json"):
        value = storage.read_json(target / name)
        value["scientific_outcome"] = outcome
        if name == "status.json":
            value["state"] = outcome
        storage.write_json(target / name, value)
    reseal_fixture(target)
    record = read_record(target)
    assert record["summary"]["horizon_reached"] is True
    assert record["status"]["scientific_outcome"] == outcome
    assert record["summary"]["qualification_record"] is None
    assert comparison.eligibility(target, lab_runs[1])["classification"] == "invalid"


def test_c3_partial_coverage_and_fabricated_coverage(lab_runs, tmp_path):
    target = copy_run(lab_runs[0], tmp_path / "partial")
    for name in ("states.csv", "controls.csv", "diagnostics.csv", "track_samples.csv"):
        rewrite_csv(target / "experiment" / name, lambda rows: rows.__delitem__(slice(10, None)))
    original = read_record(lab_runs[0])
    summary = summarize(
        original["states"][:10],
        original["diagnostics"][:10],
        "model_validity_failure",
        "software fixture failure",
    )
    for name in ("experiment/summary.json", "worker_result.json"):
        storage.write_json(target / name, summary)
    for name in ("execution.json", "status.json"):
        value = storage.read_json(target / name)
        value["scientific_outcome"] = "failed"
        if name == "status.json":
            value["state"] = "failed"
        storage.write_json(target / name, value)
    reseal_fixture(target)
    assert read_record(target)["summary"]["last_retained_time_s"] == 0.045
    summary["horizon_reached"] = True
    for name in ("experiment/summary.json", "worker_result.json"):
        storage.write_json(target / name, summary)
    reseal_fixture(target)
    with pytest.raises(storage.IntegrityError):
        read_record(target)


def test_c3_ui_keeps_verified_full_cancelled_data_and_logs_inspectable(
    lab_runs, tmp_path, monkeypatch
):
    from streamlit.testing.v1 import AppTest

    target = copy_run(lab_runs[0], tmp_path / "cancelled")
    for name in ("execution.json", "status.json"):
        value = storage.read_json(target / name)
        value["scientific_outcome"] = "cancelled"
        if name == "status.json":
            value["state"] = "cancelled"
        storage.write_json(target / name, value)
    reseal_fixture(target)
    monkeypatch.setattr(configuration, "RUNS", tmp_path)
    app = AppTest.from_file(
        str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=30
    ).run()
    assert not app.exception and not app.error and app.get("plotly_chart")
    assert any("unsuccessful process" in w.value for w in app.warning)
    assert app.get("download_button")


@pytest.mark.parametrize("grid", ["half", "quarter"])
def test_refinements_require_explicit_admission_without_launch(tmp_path, grid):
    values = config.request_for(grid_id=grid)
    with pytest.raises(ValueError, match="Refinement admission"):
        jobs.start_run("dynamic_lab", values, runs=tmp_path)
    assert not list(tmp_path.iterdir())
    context = config.execution_context(values, qualification=True)
    assert config.validate_context(values, context) == context
    for bad in ({**context, "protocol": "other"}, {**context, "role": "unknown"}):
        with pytest.raises(ValueError):
            config.validate_context(values, bad)


def test_one_refinement_software_smoke_cannot_become_qualification(tmp_path):
    # One BASE/half execution tests runner/export rates, not scientific convergence.
    from tools.apex_workbench.qualification import require_protocol_run

    directory = jobs.start_run(
        "dynamic_lab",
        config.request_for(grid_id="half"),
        "WORK software rate smoke only; explicitly excluded from scientific qualification",
        runs=tmp_path,
        qualification=True,
        test_only=True,
    )
    assert finished(directory)["state"] == "completed"
    record = read_record(directory)
    assert len(record["states"]) == len(record["diagnostics"]) == 201
    assert len(record["controls"]) == 200
    assert record["controls"][39]["delta"] == 0 and record["controls"][40]["delta"] == 0.020
    assert record["states"][-1]["time"] == 0.5
    assert record["summary"]["qualification_record"] is None
    with pytest.raises(storage.IntegrityError, match="Test/interactive"):
        require_protocol_run(record, "VDL1_BASE/half")
