"""Actual Workbench paths over read-only C0; disposable negative evidence only."""

import shutil

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import c0_archive as c0
from tools.apex_workbench import c0_panels, jobs, run_catalog
from tools.apex_workbench.configuration import ROOT


@pytest.fixture
def disposable(tmp_path, monkeypatch):
    for relative in [c0.RELATIVE, *c0.ANCHORS]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(c0.ROOT / relative, target)
    monkeypatch.setattr(c0, "ROOT", tmp_path)
    return tmp_path


def widget(items, label):
    return next(item for item in items if item.label == label)


def application(monkeypatch, tmp_path):
    monkeypatch.setattr(run_catalog, "OWNED_ROOT", tmp_path / "owned")

    def forbidden(*args, **kwargs):
        raise AssertionError("C0 inspection must never call worker/lifecycle")

    for name in ("start_run", "status_for", "cancel_run"):
        monkeypatch.setattr(jobs, name, forbidden)
    return AppTest.from_file(
        str(ROOT / "tools/apex_workbench/workspace.py"), default_timeout=45
    ).run()


def open_c0(app):
    widget(app.button, "Inspect retained C0 descriptive-only archive").click().run()
    assert not app.exception
    return app


def test_real_c0_navigation_tokens_missingness_and_no_execution(monkeypatch, tmp_path):
    app = open_c0(application(monkeypatch, tmp_path))
    assert any(c0.BANNER in item.value for item in app.warning)
    assert len(app.success) == 0 and len(app.get("plotly_chart")) == 1
    assert any("G1 OPEN" in item.value for item in app.caption)
    assert any("numerical qualification" in item.value for item in app.info)
    widget(app.selectbox, "C0 recorded signal collection").select("controls").run()
    widget(app.selectbox, "C0 recorded field").select("physical_latency").run()
    widget(app.selectbox, "C0 raw collection").select("controls").run()
    raw = app.dataframe[2].value.set_index("pointer")
    assert raw.loc["/controls/0/acceleration_correction", "json_literal"] == "-0.0"
    assert raw.loc["/controls/0/physical_latency", "json_literal"] == "0.0"
    missing = app.dataframe[1].value.set_index("pointer")
    assert missing.loc["/fixed_handoffs/0/first_TVLQR_use", "presence"] == "present-null"
    assert missing.loc["/packets/0/valid_from", "presence"] == "absent"
    widget(app.button, "Prepare C0 descriptive HTML inspection").click().run()
    assert not app.exception and len(app.get("download_button")) == 1
    assert not any(item.label == "Start run" for item in app.button)


def test_c0_never_becomes_execution_or_comparison_candidate(monkeypatch, tmp_path):
    app = open_c0(application(monkeypatch, tmp_path))
    widget(app.radio, "Workspace").set_value("Compare").run()
    assert not app.exception
    assert all("c0_descriptive" not in label for label in app.multiselect[0].options)
    widget(app.radio, "Workspace").set_value("Run").run()
    assert all("C0" not in label for label in widget(app.selectbox, "Execution mode").options)
    assert c0.ADAPTER not in [r.adapter for r in run_catalog.discover(owned_root=tmp_path).runs]


def test_switch_c0_then_home_gp_restores_original_inspector(monkeypatch, tmp_path):
    app = open_c0(application(monkeypatch, tmp_path))
    widget(app.radio, "Workspace").set_value("Home").run()
    widget(app.button, "Inspect retained Performance P GP archive").click().run()
    assert not app.exception
    assert widget(app.radio, "Inspection source").value == "Workbench / P retained runs"
    assert any("Verified retained P/VIS-1R" in item.value for item in app.success)


def test_missing_evidence_is_visible_and_has_no_stale_plot(disposable, monkeypatch, tmp_path):
    (disposable / c0.RELATIVE).unlink()
    app = open_c0(application(monkeypatch, tmp_path))
    assert "descriptive_record_quarantined" in app.error[0].value
    assert not app.get("plotly_chart") and not app.get("download_button")


def test_real_late_render_change_clears_all_scoped_content(disposable, monkeypatch, tmp_path):
    original = c0_panels.st.plotly_chart

    def replacing(*args, **kwargs):
        value = original(*args, **kwargs)
        path = disposable / c0.RELATIVE
        path.write_bytes(path.read_bytes() + b" ")
        return value

    monkeypatch.setattr(c0_panels.st, "plotly_chart", replacing)
    app = open_c0(application(monkeypatch, tmp_path))
    assert "descriptive_record_quarantined" in app.error[0].value
    assert not app.get("plotly_chart") and not app.get("download_button")
    assert not app.dataframe and not app.warning and not app.success


def test_replacement_during_download_preparation_clears_export(disposable, monkeypatch, tmp_path):
    app = open_c0(application(monkeypatch, tmp_path))
    original = c0_panels.st.download_button

    def replacing(*args, **kwargs):
        value = original(*args, **kwargs)
        path = disposable / c0.RELATIVE
        path.write_bytes(path.read_bytes() + b" ")
        return value

    monkeypatch.setattr(c0_panels.st, "download_button", replacing)
    widget(app.button, "Prepare C0 descriptive HTML inspection").click().run()
    assert not app.exception and "descriptive_record_quarantined" in app.error[0].value
    assert not app.get("download_button") and not app.get("plotly_chart")
