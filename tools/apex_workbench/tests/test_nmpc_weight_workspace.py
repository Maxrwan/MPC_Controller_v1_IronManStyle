"""Actual workspace routes and retained viewers; no experimental execution before the gate."""

import copy
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs, run_catalog, storage
from tools.apex_workbench import nmpc_weight_lab as lab
from tools.apex_workbench import nmpc_weight_panels as panels
from tools.apex_workbench.configuration import ADAPTERS, ROOT
from tools.apex_workbench.tests.test_nmpc_weight_lab import fixture_run, preflights  # noqa: F401


def widget(items, label):
    return next(i for i in items if i.label == label)


def application(monkeypatch, tmp_path):
    monkeypatch.setattr(run_catalog, "OWNED_ROOT", tmp_path / "owned")
    monkeypatch.setattr(lab, "OUTPUT", tmp_path / "m0")
    monkeypatch.setattr(lab, "RUNS", tmp_path / "m0/runs")

    def forbidden(*args, **kwargs):
        raise AssertionError("UI test must not execute a controller")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    return AppTest.from_file(
        str(ROOT / "tools/apex_workbench/workspace.py"), default_timeout=45
    ).run()


def test_m0_configuration_gate_and_no_implicit_execution(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Open experimental NMPC Weight Lab M0").click().run()
    assert not app.exception
    assert widget(app.selectbox, "Execution mode").value == "nmpc_weight_lab"
    assert any("EXPERIMENTAL / UNQUALIFIED" in e.value for e in app.warning)
    assert widget(app.button, "Run one authorized M0 attempt").disabled
    widget(app.selectbox, "M0 preset").select("exploratory").run()
    assert not app.exception and widget(app.button, "Run one authorized M0 attempt").disabled
    assert any("100.0" in e.value for e in app.markdown)


def test_existing_legacy_forms_and_lab_stay_available(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.radio, "Workspace").set_value("Run").run()
    for name in ["dynamic_demo", "lqr_baseline", "dynamic_lab"]:
        widget(app.selectbox, "Execution mode").select(name).run()
        assert not app.exception
        assert widget(app.button, "Start run")
    assert set(ADAPTERS) == {"dynamic_demo", "lqr_baseline", "dynamic_lab", "nmpc_weight_lab"}


def test_original_P_and_C0_viewers_use_readonly_original_evidence(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Inspect retained Performance P GP archive").click().run()
    assert not app.exception and not app.error
    assert any("Verified retained P/VIS-1R" in e.value for e in app.success)
    widget(app.radio, "Workspace").set_value("Home").run()
    widget(app.button, "Inspect retained C0 descriptive-only archive").click().run()
    assert not app.exception and not app.error
    assert any("SOURCE UNVERIFIED" in e.value for e in app.warning)
    assert len(app.table) == 3 and not app.dataframe and not app.json and not app.code


def test_m0_compare_separate_from_qualified_comparison(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.radio, "Workspace").set_value("Compare").run()
    widget(app.radio, "Comparison source").set_value("NMPC Weight Lab M0 (unqualified)").run()
    assert not app.exception
    assert any("EXPERIMENTAL / UNQUALIFIED" in e.value for e in app.warning)
    assert widget(app.multiselect, "M0 retained attempts").options == []
    assert not app.success


def test_comparison_requires_exact_non_treatment_identity(preflights):  # noqa: F811
    a = {
        "request": {
            "run_id": "fixture_nominal",
            "effective": {"preset": "nominal"},
            "nmpc_capture": {"resolved": preflights["nominal"]["resolved"]},
        }
    }
    b = {
        "request": {
            "run_id": "fixture_exploratory",
            "effective": {"preset": "exploratory"},
            "nmpc_capture": {"resolved": preflights["exploratory"]["resolved"]},
        }
    }
    assert "unqualified" in panels.comparison(a, b)
    altered = copy.deepcopy(b)
    altered["request"]["nmpc_capture"]["resolved"]["vehicle"]["mass"] += 1
    with pytest.raises(ValueError):
        panels.comparison(a, altered)
    with pytest.raises(ValueError):
        panels.comparison(a, a)


def test_native_plot_clocks_and_missingness_are_not_reconstructed():
    raw = {
        "states": [{"time": 0.0, "e_y": 0.1}, {"time": 0.005, "e_y": 0.2}],
        "controls": [
            {"time": 0.0, "application_time": 0.005, "requested_delta": 0.1, "delta": 0.2}
        ],
    }
    state = panels.signal(raw, "e_y")
    control = panels.commands(raw)
    assert list(state.data[0].x) == [0.0, 0.005] and state.data[0].mode == "markers"
    assert list(control.data[0].x) == [0.0] and list(control.data[1].x) == [0.005]
    assert list(control.data[0].y) == [0.1] and list(control.data[1].y) == [0.2]
    raw["controls"][0]["application_time"] = None
    assert len(panels.commands(raw).data[1].x) == 0
    assert lab.descriptive_metrics(None) == {"state_samples": 0, "coverage": "unavailable"}


def test_cancel_request_is_owned_marker_and_retains_partial_bytes(tmp_path, monkeypatch):
    directory = tmp_path / "fixture_cancel"
    directory.mkdir()
    (directory / "partial.jsonl").write_text('{"retained":true}\n')
    monkeypatch.setattr(jobs, "status_for", lambda directory: {"state": "running"})
    jobs.cancel_run(directory)
    assert (directory / "cancel.request").exists()
    assert (directory / "partial.jsonl").read_text() == '{"retained":true}\n'


def owned_fixture(tmp_path, monkeypatch, preflights):  # noqa: F811
    directory = fixture_run(tmp_path, preflights)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(lab, "RUNS", tmp_path / "runs")
    catalog = run_catalog.discover(
        owned_root=tmp_path / "legacy", qualification_root=tmp_path / "none", include_nmpc=True
    )
    return directory, catalog.runs[0], catalog


@pytest.mark.parametrize(
    "fault",
    [
        "foreign_root",
        "archive",
        "symlink_directory",
        "symlink_request",
        "alias",
        "conflict",
        "selected_id",
        "selected_adapter",
        "request_adapter",
        "case",
        "claim",
    ],
)
def test_invalid_inspection_never_reaches_lifecycle(
    tmp_path,
    monkeypatch,
    preflights,  # noqa: F811
    fault,
):
    directory, selected, _ = owned_fixture(tmp_path, monkeypatch, preflights)
    if fault == "foreign_root":
        selected = replace(selected, directory=tmp_path / "legacy" / directory.name)
    elif fault == "archive":
        selected = replace(selected, origins=("qualification archive",))
    elif fault == "symlink_directory":
        link = directory.parent / "linked"
        link.symlink_to(directory, target_is_directory=True)
        selected = replace(selected, directory=link)
    elif fault == "symlink_request":
        original = directory / "request.json"
        other = directory / "saved_request.json"
        original.rename(other)
        original.symlink_to(other)
    elif fault == "alias":
        selected = replace(selected, aliases=(directory, tmp_path / "copy"))
    elif fault == "conflict":
        selected = replace(selected, conflict=True)
    elif fault == "selected_id":
        selected = replace(selected, run_id="forged")
    elif fault == "selected_adapter":
        selected = replace(selected, adapter="dynamic_lab")
    elif fault == "request_adapter":
        request = storage.read_json(directory / "request.json")
        storage.write_json(directory / "request.json", dict(request, adapter="dynamic_lab"))
    elif fault == "case":
        selected = replace(selected, case="exploratory")
    elif fault == "claim":
        storage.write_json(tmp_path / "claims/nominal.json", {"run_id": "forged"})
    # Compare every fixture byte and prohibit all potentially mutating entry points.
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid M0 inspection reached a lifecycle mutation path")

    for name in ("status_for", "cancel_run", "_reconcile_locked", "finalize"):
        monkeypatch.setattr(jobs, name, forbidden)
    panels.inspect(selected)
    after = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


def test_actual_workspace_quarantines_forged_archive_route(tmp_path, monkeypatch, preflights):  # noqa: F811
    _, selected, catalog = owned_fixture(tmp_path, monkeypatch, preflights)
    selected = replace(selected, origins=("qualification archive",), state="running")
    monkeypatch.setattr(
        run_catalog, "discover", lambda **kwargs: replace(catalog, runs=(selected,))
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Forged archive reached lifecycle from actual workspace")

    monkeypatch.setattr(jobs, "status_for", forbidden)
    app = AppTest.from_file(
        str(ROOT / "tools/apex_workbench/workspace.py"), default_timeout=45
    ).run()
    widget(app.radio, "Workspace").set_value("Inspect").run()
    assert not app.exception
    assert any("quarantined" in e.value for e in app.error)
    assert not any("Cancel M0" in b.label for b in app.button)


def test_owned_active_refresh_and_cancel_keep_partial_bytes(tmp_path, monkeypatch, preflights):  # noqa: F811
    directory, selected, _ = owned_fixture(tmp_path, monkeypatch, preflights)
    events = []

    def active(path):
        assert path == directory
        events.append("status")
        return {"state": "running", "evidence_state": "pending"}

    monkeypatch.setattr(jobs, "status_for", active)
    monkeypatch.setattr(panels.st, "button", lambda label: label == "Cancel M0 owned run")
    monkeypatch.setattr(panels.st, "rerun", lambda: events.append("rerun"))
    before = (directory / "experiment/plant_segments.jsonl").read_bytes()
    panels.inspect(selected)
    assert (directory / "cancel.request").exists()
    assert (directory / "experiment/plant_segments.jsonl").read_bytes() == before
    assert events == ["status", "status", "rerun"]
