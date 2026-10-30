"""Actual presentation paths over retained evidence; no racing execution."""

from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import gp_archive as gp
from tools.apex_workbench import gp_panels, jobs, run_catalog
from tools.apex_workbench.configuration import ROOT

WORKSPACE = ROOT / "tools/apex_workbench/workspace.py"


def widget(items, label):
    return next(item for item in items if item.label == label)


def application(monkeypatch, tmp_path):
    monkeypatch.setattr(run_catalog, "OWNED_ROOT", tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Inspection/preset must not execute or reconcile")

    for name in ("start_run", "status_for", "cancel_run"):
        monkeypatch.setattr(jobs, name, forbidden)
    return AppTest.from_file(str(WORKSPACE), default_timeout=45).run()


def test_home_gp_navigation_native_events_and_no_execution(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Inspect retained Performance P GP archive").click().run()
    assert not app.exception
    assert any("Verified retained P/VIS-1R" in item.value for item in app.success)
    widget(app.selectbox, "GP sector").select("hairpin").run()
    assert not app.exception
    widget(app.selectbox, "GP signal group").select("Planner and solver events").run()
    widget(app.selectbox, "Recorded event kind").select("preparation_ready").run()
    assert not app.exception
    displayed = app.dataframe[0].value
    assert len(displayed) == 100
    assert set(displayed.event_kind) == {"preparation_ready"}
    assert "Solve_Succeeded" in displayed.iloc[0].payload
    assert displayed.iloc[0].export_row == 29
    assert any("full-run" in item.value.lower() for item in app.caption)


def test_oval_shortcut_prepares_existing_contract_without_execution(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Prepare 2 m/s oval LQR/PI").click().run()
    assert not app.exception
    assert widget(app.selectbox, "Execution mode").value == "lqr_baseline"
    assert widget(app.selectbox, "Track").value == "oval"
    assert widget(app.number_input, "Initial/reference speed [m/s]").value == 2.0
    assert widget(app.number_input, "Duration [s]").value == 12.0
    assert widget(app.number_input, "Initial e_y [m]").value == 0.0
    assert widget(app.number_input, "Initial e_psi [rad]").value == 0.0
    assert widget(app.button, "Start run")


def test_gp_catalog_identity_and_compare_exclusion(monkeypatch, tmp_path):
    plain = run_catalog.discover(owned_root=tmp_path)
    extended = run_catalog.discover(owned_root=tmp_path, include_racing=True)
    assert len(extended.runs) == len(plain.runs) + 1
    run = next(r for r in extended.runs if r.adapter == gp.ADAPTER)
    assert not run.owned and run.key == "gp-" + gp.MANIFEST_SHA256
    assert run.directory == gp.DIRECTORY
    assert replace(run, directory=tmp_path / "copy").key == run.key
    app = application(monkeypatch, tmp_path)
    widget(app.radio, "Workspace").set_value("Compare").run()
    assert not app.exception
    assert all("gp_archive" not in label for label in app.multiselect[0].options)


def test_sector_figures_keep_native_values_and_unconnected_visits():
    data = gp.read()
    sector = "hairpin"
    selected = gp.sector_frame(data, "states", sector)
    plots = gp_panels.figures(data, "Vehicle and reference", "vx", sector)
    assert plots[0].data[0].mode == "lines"  # Whole original context, never sector-stitched.
    assert len(plots[0].data[0].x) == len(data.frames["planning"])
    assert all(trace.mode == "markers" for trace in plots[0].data[1:])
    assert all(trace.mode == "markers" for trace in plots[1].data)
    assert list(plots[1].data[0].x) == selected.time.tolist()
    assert list(plots[1].data[0].y) == selected.vx.tolist()
    controls = gp_panels.figures(data, "Applied/requested controls", "a_cmd", sector)[1]
    assert controls.data[0].x[0] == 0.005 and controls.data[1].x[0] == 0.0
    assert len(controls.data[0].x) == len(data.frames["controls"])
    meta = gp_panels.provenance(data, sector, "Vehicle and reference", "vx")
    content = gp_panels.report(data, plots, meta).decode()
    assert gp.MANIFEST_SHA256 in content and gp.REVISION in content
    assert "derived_read_only_inspection_not_new_execution" in content
    assert '"states_export_rows"' in content.replace("&quot;", '"')


def test_report_rechecks_after_serialization(monkeypatch):
    data = gp.read()
    plots = gp_panels.figures(data, "Vehicle and reference", "vx")

    def changed():
        raise gp.ArchiveError("Disposable late replacement")

    monkeypatch.setattr(data, "current", changed)
    with pytest.raises(gp.ArchiveError, match="late replacement"):
        gp_panels.report(data, plots, {})


def test_late_render_replacement_removes_plots_and_labels(monkeypatch, tmp_path):
    original = gp.Snapshot.current
    calls = []

    def changed(self):
        calls.append(1)
        if len(calls) >= 3:
            raise gp.ArchiveError("Disposable late replacement")
        return original(self)

    monkeypatch.setattr(gp.Snapshot, "current", changed)
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Inspect retained Performance P GP archive").click().run()
    assert not app.exception
    assert len(app.success) == 0 and len(app.get("plotly_chart")) == 0
    assert "quarantined/unavailable" in app.error[0].value
