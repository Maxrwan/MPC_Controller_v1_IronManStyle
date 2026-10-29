"""Focused presentation tests. Accepted qualification is read-only, never regenerated."""

import hashlib
import io
import shutil
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import engineering_views as views
from tools.apex_workbench import jobs, run_catalog, storage
from tools.apex_workbench.configuration import ROOT
from tools.apex_workbench.tests.test_corrections import finished, reseal_fixture

WORKSPACE = ROOT / "tools/apex_workbench/workspace.py"
QUALIFICATION = run_catalog.QUALIFICATION_ROOT / run_catalog.ACCEPTED_CAMPAIGN / "qualification"


@pytest.fixture
def accepted(tmp_path):
    catalog = run_catalog.discover(owned_root=tmp_path / "owned")
    document = storage.read_json(QUALIFICATION / "qualification.json")
    paths = [
        Path(document["references"][case + "/nominal"]["directory"])
        for case in ("VDL1_BASE", "VDL1_IZ_HIGH")
    ]
    runs = [next(run for run in catalog.runs if run.directory == path) for path in paths]
    return catalog, runs[0], runs[1]


def application(monkeypatch, tmp_path):
    monkeypatch.setattr(run_catalog, "OWNED_ROOT", tmp_path)
    return AppTest.from_file(str(WORKSPACE), default_timeout=45).run()


def test_accepted_source_and_new_presentation_provenance():
    expected = storage.read_json(
        ROOT / "docs/reviews/apex_workbench_v0_2_e/verification_record.json"
    )
    assert len(expected["source_sha256"]) == 56
    for name, digest in expected["source_sha256"].items():
        assert storage.sha256(ROOT / name) == digest
    ledger = jobs.provenance()["source_sha256"]
    for name in ("workspace.py", "run_catalog.py", "engineering_views.py"):
        relative = "tools/apex_workbench/" + name
        assert ledger[relative] == storage.sha256(ROOT / relative)


def test_actual_archive_discovery_and_unique_profiles(accepted):
    catalog, base, treatment = accepted
    assert len(catalog.runs) == 17 and catalog.qualifications == (QUALIFICATION,)
    assert base.case == "VDL1_BASE" and treatment.case == "VDL1_IZ_HIGH"
    assert base.profile == "nominal/adapter" and not base.owned
    assert len({run.key for run in catalog.runs}) == 17
    assert len({run.label for run in catalog.runs}) == 17
    assert all(not run.owned for run in catalog.runs)


def test_duplicate_canonical_paths_are_not_new_executions():
    runs = QUALIFICATION.parent / "runs"
    catalog = run_catalog.discover(owned_root=runs)
    assert len(catalog.runs) == 17
    assert all(len(run.aliases) == 1 and not run.owned for run in catalog.runs)


def test_copied_execution_prefers_original_archive(accepted, tmp_path):
    _, base, _ = accepted
    owned = tmp_path / "owned"
    shutil.copytree(base.directory, owned / "copy")
    catalog = run_catalog.discover(owned_root=owned)
    selected = next(run for run in catalog.runs if run.run_id == base.run_id)
    assert len(catalog.runs) == 17 and len(selected.aliases) == 2
    assert selected.directory == base.directory and not selected.owned
    assert selected.key == base.key and views.inspect(selected).valid


def test_conflicting_alias_does_not_invalidate_verified_original(accepted, tmp_path):
    _, base, _ = accepted
    owned = tmp_path / "owned"
    copy = owned / "conflicting-copy"
    shutil.copytree(base.directory, copy)
    request = storage.read_json(copy / "request.json")
    request["prediction"] = "Explicit disposable alias conflict"
    storage.write_json(copy / "request.json", request)
    reseal_fixture(copy)
    catalog = run_catalog.discover(owned_root=owned)
    run = next(r for r in catalog.runs if r.run_id == base.run_id)
    assert run.conflict and not run.owned and run.directory == base.directory
    assert (
        views.qualification(run, QUALIFICATION)["numerical_qualification"] == "grid_qualified_case"
    )


def test_corrupt_discovery_and_outside_paths_stay_untrusted(tmp_path, monkeypatch):
    owned = tmp_path / "owned"
    broken = owned / "broken"
    broken.mkdir(parents=True)
    (broken / "request.json").write_text("not json")
    (broken / "status.json").write_text("[]")
    (owned / "outside-link").symlink_to(tmp_path, target_is_directory=True)
    catalog = run_catalog.discover(owned_root=owned, qualification_root=tmp_path / "no-archives")
    assert len(catalog.runs) == 1 and catalog.issues
    run = catalog.runs[0]
    assert run.issues and not views.inspect(run).valid
    assert views.raw_records(run)["request.json"] == "not json"
    original = run_catalog.metadata

    def outside(directory, name):
        value = original(directory, name)
        if name == "qualification.json":
            value["references"] = {"invalid": {"directory": str(tmp_path)}}
        return value

    monkeypatch.setattr(run_catalog, "metadata", outside)
    assert run_catalog.discover(owned_root=owned).issues


def test_archive_inspection_comparison_never_reconcile(accepted, monkeypatch):
    _, base, treatment = accepted

    def forbidden(*args, **kwargs):
        raise AssertionError("Archive must never call execution lifecycle")

    monkeypatch.setattr(jobs, "status_for", forbidden)
    monkeypatch.setattr(jobs, "cancel_run", forbidden)
    data = views.inspect(base)
    assert data.valid and len(data.frames["states.csv"]) == 101
    assert len(data.frames["controls.csv"]) == 100
    assert "reference_speed" not in data.frames["controls.csv"]
    assert views.compare(base, treatment)["classification"] == "controlled_candidate"
    assert (
        views.compare(base, treatment, qualification_record=QUALIFICATION)["classification"]
        == "qualified_synthetic_comparison"
    )


def test_nonterminal_archive_is_read_only_and_ineligible(accepted, tmp_path, monkeypatch):
    _, base, treatment = accepted
    copy = tmp_path / "nonterminal"
    shutil.copytree(base.directory, copy)
    status = storage.read_json(copy / "status.json")
    status["state"] = "running"
    storage.write_json(copy / "status.json", status)
    run = replace(base, directory=copy, aliases=(copy,))
    monkeypatch.setattr(jobs, "status_for", lambda *args: pytest.fail("Archive reconciliation"))
    assert "Nonterminal archive" in views.inspect(run).error
    assert views.compare(run, treatment)["classification"] == "invalid"
    assert not (copy / "cancel.request").exists()


def test_raw_forensics_and_verified_bundle(accepted, tmp_path):
    _, base, _ = accepted
    archive = zipfile.ZipFile(io.BytesIO(views.bundle(base)))
    assert (
        archive.read("experiment/states.csv")
        == (base.directory / "experiment/states.csv").read_bytes()
    )
    assert archive.read("artifacts.json") == (base.directory / "artifacts.json").read_bytes()
    copy = tmp_path / "corrupt"
    shutil.copytree(base.directory, copy)
    (copy / "experiment/states.csv").unlink()
    run = replace(base, directory=copy, aliases=(copy,))
    assert not views.inspect(run).valid and views.inspect(run).frames == {}
    assert "request.json" in views.raw_records(run)
    with pytest.raises(storage.IntegrityError):
        views.bundle(run)


def test_bundle_epoch_change_is_rejected(accepted, monkeypatch):
    _, base, _ = accepted
    real = views.inspect
    read_bytes = Path.read_bytes

    def changed(run):
        result = real(run)
        # No original file mutation: simulate a moving anchor returned after validation.
        monkeypatch.setattr(
            Path,
            "read_bytes",
            lambda path: (
                b"changed anchor" if path == run.directory / "status.json" else read_bytes(path)
            ),
        )
        return result

    monkeypatch.setattr(views, "inspect", changed)
    with pytest.raises(storage.IntegrityError):
        views.bundle(base)


def test_notes_remain_append_only_in_owned_copy(accepted, tmp_path):
    _, base, _ = accepted
    copy = tmp_path / "owned-copy"
    shutil.copytree(base.directory, copy)
    run = replace(base, directory=copy, origins=("owned",), aliases=(copy,))
    first = jobs.save_notes(copy, "first observation", "first interpretation")
    original = first.read_bytes()
    jobs.save_notes(copy, "second", "second")
    assert views.notes(run)[0]["observation"] == "second"
    assert first.read_bytes() == original


def test_home_and_actual_inspect_view(accepted, tmp_path, monkeypatch):
    _, base, _ = accepted
    app = application(monkeypatch, tmp_path)
    assert not app.exception and not app.error and app.dataframe
    assert any("NMPC/TVLQR/async execution" in item.value for item in app.info)
    app.radio(key="workspace_view").set_value("Inspect").run()
    app.selectbox(key="inspect_run").set_value(base.key).run()
    assert not app.exception and not app.error and app.get("plotly_chart")
    assert any("reference channel unavailable" in item.value for item in app.caption)
    app.selectbox(key="inspect_source").set_value("controls.csv").run()
    app.multiselect(key="inspect_channels").set_value(["delta"]).run()
    app.selectbox(key="inspect_source").set_value("diagnostics.csv").run()
    app.multiselect(key="inspect_channels").set_value(["alpha_f", "fyf"]).run()
    assert not app.exception and not app.error and len(app.get("plotly_chart")) == 3
    assert not any(
        button.label in {"Cancel owned run", "Append engineering note"} for button in app.button
    )


def test_actual_compare_ui_candidate_then_qualified(accepted, tmp_path, monkeypatch):
    _, base, treatment = accepted
    app = application(monkeypatch, tmp_path)
    app.radio(key="workspace_view").set_value("Compare").run()
    next(item for item in app.multiselect if item.label == "Runs").set_value(
        [base.key, treatment.key]
    ).run()
    assert any(item.value == "Controlled Candidate" for item in app.subheader)
    app.selectbox(key="selected_qualification").set_value(QUALIFICATION).run()
    assert not app.exception and not app.error
    assert any(item.value == "Qualified Synthetic Comparison" for item in app.subheader)
    assert app.get("plotly_chart")
    app.selectbox(key="compare_source").set_value("diagnostics.csv").run()
    app.multiselect(key="compare_channels").set_value(["alpha_f", "fyf"]).run()
    assert not app.exception and not app.error and len(app.get("plotly_chart")) == 2


def test_invalid_evidence_ui_has_raw_records_no_scientific_plots(accepted, tmp_path, monkeypatch):
    _, base, _ = accepted
    copy = tmp_path / "corrupt"
    shutil.copytree(base.directory, copy)
    (copy / "experiment/states.csv").unlink()
    monkeypatch.setattr(run_catalog, "QUALIFICATION_ROOT", tmp_path / "no-archives")
    app = application(monkeypatch, tmp_path)
    app.radio(key="workspace_view").set_value("Inspect").run()
    assert not app.exception and app.error and not app.get("plotly_chart")
    assert any("request.json" in item.value for item in app.markdown)


def test_real_nominal_run_through_workspace_and_reopen(tmp_path, monkeypatch):
    app = application(monkeypatch, tmp_path)
    app.radio(key="workspace_view").set_value("Run").run()
    next(item for item in app.selectbox if item.label == "Execution mode").set_value(
        "dynamic_lab"
    ).run()
    next(item for item in app.button if item.label == "Start run").click().run()
    runs = list(tmp_path.glob("*/request.json"))
    assert len(runs) == 1 and finished(runs[0].parent)["scientific_outcome"] == "completed"
    app.run()
    assert not app.exception and not app.error and app.get("plotly_chart")
    request = storage.read_json(runs[0])
    assert request["execution_context"]["purpose"] == "interactive"
    for name in ("workspace.py", "engineering_views.py", "run_catalog.py"):
        relative = "tools/apex_workbench/" + name
        assert (
            request["provenance"]["source_sha256"][relative]
            == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        )


def test_legacy_mode_forms_use_accepted_defaults(tmp_path, monkeypatch):
    from tools.apex_workbench.configuration import DEFAULTS

    app = application(monkeypatch, tmp_path)
    app.radio(key="workspace_view").set_value("Run").run()
    mode = next(item for item in app.selectbox if item.label == "Execution mode")
    for adapter in ("dynamic_demo", "lqr_baseline"):
        mode.set_value(adapter).run()
        assert not app.exception and not app.error
        for name, expected in DEFAULTS[adapter].items():
            if name == "track":
                assert (
                    next(item for item in app.selectbox if item.label == "Track").value == expected
                )
            else:
                assert app.number_input(key=adapter + "_" + name).value == expected
        mode = next(item for item in app.selectbox if item.label == "Execution mode")


def test_ui_withholds_overlay_if_evidence_changes_after_classification(
    accepted, tmp_path, monkeypatch
):
    _, base, treatment = accepted
    app = application(monkeypatch, tmp_path)
    app.radio(key="workspace_view").set_value("Compare").run()
    inspect = views.inspect
    calls = 0

    def changed(run):
        nonlocal calls
        calls += 1
        # Classification verifies two records; simulate the next presentation read failing.
        return inspect(run) if calls <= 2 else views.Inspection(error="Changed evidence")

    monkeypatch.setattr(views, "inspect", changed)
    next(item for item in app.multiselect if item.label == "Runs").set_value(
        [base.key, treatment.key]
    ).run()
    assert not app.exception and app.error and not app.get("plotly_chart")
