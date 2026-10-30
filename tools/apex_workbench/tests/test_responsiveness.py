"""Presentation reuse preserves native payloads, integrity and original UI deadlines."""

import json
import shutil

import pytest

from tools.apex_workbench import plots, recorded_view, run_catalog, workspace_panels
from tools.apex_workbench.tests.test_recorded_view import Q, app_for, sample_table, select


@pytest.fixture
def nominal(tmp_path):
    catalog = run_catalog.discover(owned_root=tmp_path / "empty")
    return [
        next(r for r in catalog.runs if r.case == case and r.profile == "nominal/adapter")
        for case in ("VDL1_BASE", "VDL1_IZ_HIGH", "VDL1_CF_HIGH")
    ]


def test_snapshot_plot_payloads_match_original_verified_plotter(nominal):
    snapshots = [recorded_view.load(run) for run in nominal[:2]]
    for source, channel in (
        ("states.csv", "r"),
        ("controls.csv", "delta"),
        ("diagnostics.csv", "alpha_f"),
    ):
        old = plots.series(
            [(s.run.run_id, s.run.directory) for s in snapshots],
            [channel],
            "native units",
            source=source,
        )
        new = workspace_panels._series(snapshots, channel, "native units", source=source)
        assert json.loads(new.to_json()) == json.loads(old.to_json())
    assert json.loads(workspace_panels._trajectory(snapshots[0]).to_json()) == json.loads(
        plots.trajectory(snapshots[0].run.directory).to_json()
    )


def test_snapshot_figures_use_verified_frames_without_new_file_reads(nominal, monkeypatch):
    snapshot = recorded_view.load(nominal[0])

    def forbidden(*args, **kwargs):
        pytest.fail("Figure construction must reuse this operation's already verified frames")

    monkeypatch.setattr(plots, "read_frame", forbidden)
    assert workspace_panels._series([snapshot], "r", "r [rad/s]").data
    assert workspace_panels._trajectory(snapshot).data
    assert snapshot.current()  # Reuse never removes source-currentness checks.


def test_seek_runs_one_comparison_operation_with_original_deadline(nominal, tmp_path, monkeypatch):
    app = select(app_for(tmp_path, monkeypatch), nominal, "Compare")
    app.selectbox(key="selected_qualification").set_value(Q).run()
    app.number_input(key="compare_requested_time").set_value(0.125).run()
    matrix = recorded_view.matrix
    calls = []

    def counted(*args, **kwargs):
        calls.append(True)
        return matrix(*args, **kwargs)

    monkeypatch.setattr(recorded_view, "matrix", counted)
    app.button(key="compare_seek").click().run()  # Original 60 s default unchanged.
    assert calls == [True]
    assert not app.exception and not app.error
    table = sample_table(app)
    assert table.state_time_s.tolist() == [0.125] * 3
    assert table.control_time_s.tolist() == [0.125] * 3
    assert table["delta [rad]"].tolist() == [0.02] * 3


def test_selected_configuration_details_load_on_demand(nominal, tmp_path, monkeypatch):
    app = select(app_for(tmp_path, monkeypatch), nominal[:2], "Compare")
    assert not any('"original_path"' in item.value for item in app.json)
    app.toggle(key="compare_details").set_value(True).run()
    details = [json.loads(item.value) for item in app.json if '"original_path"' in item.value]
    assert [item["run_id"] for item in details] == [run.run_id for run in nominal[:2]]
    assert [item["original_path"] for item in details] == [
        str(run.directory) for run in nominal[:2]
    ]
    assert not app.exception and not app.error


@pytest.mark.parametrize("fault", ["changed_bytes", "missing_file"])
def test_reused_plot_frames_still_quarantine_late_artifact_changes(
    nominal, tmp_path, monkeypatch, fault
):
    owned = tmp_path / "owned"
    copy = owned / "copy"
    shutil.copytree(nominal[0].directory, copy)
    shutil.copytree(nominal[1].directory, owned / "second")
    monkeypatch.setattr(run_catalog, "QUALIFICATION_ROOT", tmp_path / "no-archives")
    catalog = run_catalog.discover(owned_root=owned)
    runs = [next(r for r in catalog.runs if r.case == original.case) for original in nominal[:2]]
    app = app_for(tmp_path, monkeypatch)
    app.radio(key="workspace_view").set_value("Compare").run()
    series = workspace_panels._series

    def changed(*args, **kwargs):
        figure = series(*args, **kwargs)
        path = copy / "experiment/controls.csv"
        if fault == "missing_file":
            path.unlink(missing_ok=True)
        else:
            with path.open("a") as stream:
                stream.write("\n")
        return figure

    monkeypatch.setattr(workspace_panels, "_series", changed)
    app.multiselect(key="compare_runs").set_value([run.key for run in runs]).run()
    assert not app.exception and app.error and not app.get("plotly_chart")
    assert not any(
        s.value in {"Qualified Synthetic Comparison", "Controlled Candidate"} for s in app.subheader
    )
