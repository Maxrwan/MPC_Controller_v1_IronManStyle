"""V0.3-C native-time replay/compact UI. No new scenario or qualification execution."""

import csv
import hashlib
import json
import shutil
from dataclasses import replace

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import engineering_views as views
from tools.apex_workbench import jobs, run_catalog, storage, workspace_panels
from tools.apex_workbench import recorded_view as recorded
from tools.apex_workbench.configuration import ADAPTERS, ROOT
from tools.apex_workbench.experiment_catalog import CASES, EXPERIMENTS
from tools.apex_workbench.lab_evidence import read_record
from tools.apex_workbench.lab_reporting import summarize
from tools.apex_workbench.tests.test_corrections import reseal_fixture
from tools.apex_workbench.tests.test_lab_closure import rewrite_csv

Q = run_catalog.QUALIFICATION_ROOT / run_catalog.ACCEPTED_CAMPAIGN / "qualification"
WORKSPACE = ROOT / "tools/apex_workbench/workspace.py"


@pytest.fixture
def runs(tmp_path):
    catalog = run_catalog.discover(owned_root=tmp_path / "empty-owned")
    return [
        next(r for r in catalog.runs if r.case == case and r.profile == "nominal/adapter")
        for case in ("VDL1_BASE", "VDL1_IZ_HIGH", "VDL1_CF_HIGH")
    ]


def app_for(tmp_path, monkeypatch):
    monkeypatch.setattr(run_catalog, "OWNED_ROOT", tmp_path / "owned")
    return AppTest.from_file(str(WORKSPACE), default_timeout=60).run()


def select(app, runs, page="Inspect"):
    app.radio(key="workspace_view").set_value(page).run()
    if page == "Inspect":
        app.selectbox(key="inspect_run").set_value(runs[0].key).run()
    else:
        app.multiselect(key="compare_runs").set_value([r.key for r in runs]).run()
    return app


def sample_table(app):
    return next(item.value for item in app.dataframe if "state_sample" in item.value.columns)


def test_frozen_source_and_presentation_provenance():
    expected = storage.read_json(
        ROOT / "docs/reviews/apex_workbench_v0_3_b/verification_record.json"
    )
    assert len(expected["scientific_source_sha256"]) == 56
    for name, digest in expected["scientific_source_sha256"].items():
        assert storage.sha256(ROOT / name) == digest
    captured = jobs.provenance()["source_sha256"]
    for name in ("recorded_view.py", "workspace_panels.py", "experiment_catalog.py"):
        relative = "tools/apex_workbench/" + name
        assert captured[relative] == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_descriptions_only_describe_actual_adapters_and_cases():
    assert set(EXPERIMENTS) == set(ADAPTERS)
    assert len(CASES) == 5
    for item in EXPERIMENTS.values():
        assert set(item) == {
            "name",
            "mode",
            "purpose",
            "behavior",
            "inputs",
            "measurements",
            "composition",
            "limits",
        }
    assert EXPERIMENTS["lqr_baseline"]["mode"] == "Closed loop"
    assert "qualification" in EXPERIMENTS["dynamic_lab"]["limits"].lower()


def test_exact_0125_state_control_diagnostic_and_stored_xy(runs):
    snapshots = [recorded.load(r) for r in runs[:2]]
    yaw = []
    for snapshot in snapshots:
        assert recorded.times(snapshot)[25] == 0.125
        for source in recorded.TIME_SOURCES:
            value = recorded.sample(snapshot, source, 0.125)
            assert (
                value["available"] and value["timestamp_s"] == 0.125 and value["sample_index"] == 25
            )
            # Independent native CSV lookup, not regenerated model output.
            with (snapshot.run.directory / "experiment" / source).open() as stream:
                row = next(r for r in csv.DictReader(stream) if float(r["time"]) == 0.125)
            for key, actual in value["values"].items():
                if row[key] != "":
                    expected = (
                        row[key] == "True" if row[key] in {"True", "False"} else float(row[key])
                    )
                    assert expected == actual
        yaw.append(recorded.sample(snapshot, "states.csv", 0.125)["values"]["r"])
        assert recorded.sample(snapshot, "controls.csv", 0.125)["values"]["delta"] == 0.02
    assert yaw[0] != yaw[1]


def test_onset_terminal_and_off_grid_have_explicit_meaning(runs):
    snapshot = recorded.load(runs[0])
    assert recorded.sample(snapshot, "controls.csv", 0.095)["values"]["delta"] == 0.0
    assert recorded.sample(snapshot, "states.csv", 0.1)["values"]["r"] == 0.0
    assert recorded.sample(snapshot, "controls.csv", 0.1)["values"]["delta"] == 0.02
    terminal = recorded.sample(snapshot, "controls.csv", 0.5)
    assert not terminal["available"] and "no applied-control interval" in terminal["meaning"]
    assert "informational" in recorded.sample(snapshot, "diagnostics.csv", 0.5)["meaning"]
    assert not recorded.sample(snapshot, "states.csv", 0.126)["available"]
    assert "no interpolation/hold" in recorded.sample(snapshot, "controls.csv", 0.126)["meaning"]
    assert "out of retained coverage" in recorded.sample(snapshot, "states.csv", 0.6)["meaning"]


def test_native_multirate_fixture_never_infers_held_command(runs):
    snapshot = recorded.load(runs[0])
    # A literal row-mapping fixture, not a simulated trajectory or qualification record.
    data = replace(
        snapshot.data,
        request={**snapshot.data.request, "adapter": "lqr_baseline"},
        frames={
            "states.csv": pd.DataFrame({"time": [0.0, 0.005, 0.01]}),
            "controls.csv": pd.DataFrame({"time": [0.0, 0.01], "delta": [0.0, 0.02]}),
        },
    )
    fixture = replace(snapshot, data=data)
    value = recorded.sample(fixture, "controls.csv", 0.005)
    assert not value["available"] and value["values"] == {}
    assert recorded.sample(fixture, "controls.csv", 0.01)["values"]["delta"] == 0.02


def test_viewer_clock_is_bounded_deterministic_and_stops_at_end():
    state = {"index": 19, "playing": True, "last_tick": 0.0}
    assert recorded.tick(state, 101, 0.9)["index"] == 19
    after = recorded.tick(state, 101, 1.0)
    assert after["index"] == 20 and state["index"] == 19
    assert recorded.tick(after, 101, 100.0)["index"] == 21  # No wall-time catch-up.
    assert recorded.tick({**after, "index": 99}, 101, 3.0)["playing"] is False
    assert recorded.step(0, 101, -1) == 0 and recorded.step(100, 101, 10) == 100
    assert recorded.tick({**state, "playing": False}, 101, 100.0)["index"] == 19


def test_three_real_runs_have_pairwise_not_group_qualification(runs):
    snapshots, pairs = recorded.matrix(runs, Q)
    assert len(snapshots) == 3 and len(pairs) == 3
    labels = {(p["left"], p["right"]): p["decision"]["classification"] for p in pairs}
    assert labels == {
        (0, 1): "qualified_synthetic_comparison",
        (0, 2): "qualified_synthetic_comparison",
        (1, 2): "illustrative",
    }
    _, candidates = recorded.matrix(runs)
    assert [p["decision"]["classification"] for p in candidates] == [
        "controlled_candidate",
        "controlled_candidate",
        "illustrative",
    ]
    with pytest.raises(storage.IntegrityError):
        recorded.matrix([runs[0], runs[0]])
    with pytest.raises(storage.IntegrityError):
        recorded.matrix(runs + runs)


def test_snapshot_and_matrix_reject_changed_or_missing_evidence(runs, tmp_path):
    copy = tmp_path / "corrupt"
    shutil.copytree(runs[0].directory, copy)
    run = replace(runs[0], directory=copy, aliases=(copy,))
    snapshot = recorded.load(run)
    with (copy / "experiment/states.csv").open("a") as stream:
        stream.write("\n")
    assert not snapshot.current()
    with pytest.raises(storage.IntegrityError):
        recorded.load(run)
    with pytest.raises(storage.IntegrityError):
        recorded.matrix([run, runs[1]], Q)


def test_partial_replay_stays_partial_and_comparison_invalid(runs, tmp_path):
    copy = tmp_path / "partial"
    shutil.copytree(runs[0].directory, copy)
    for name in (
        "states.csv",
        "controls.csv",
        "diagnostics.csv",
        "track_samples.csv",
        "trajectory_xy.csv",
    ):
        rewrite_csv(copy / "experiment" / name, lambda rows: rows.__delitem__(slice(10, None)))
    original = read_record(runs[0].directory)
    summary = summarize(
        original["states"][:10],
        original["diagnostics"][:10],
        "model_validity_failure",
        "explicit disposable partial fixture",
    )
    for name in ("experiment/summary.json", "worker_result.json"):
        storage.write_json(copy / name, summary)
    for name in ("execution.json", "status.json"):
        value = storage.read_json(copy / name)
        value["scientific_outcome"] = "failed"
        if name == "status.json":
            value["state"] = "failed"
        storage.write_json(copy / name, value)
    reseal_fixture(copy)
    run = replace(runs[0], directory=copy, aliases=(copy,))
    snapshot = recorded.load(run)
    assert recorded.times(snapshot)[-1] == 0.045
    last = recorded.sample(snapshot, "controls.csv", 0.045)
    assert last["available"] and "no completed interval" in last["meaning"]
    assert "partial" in recorded.sample(snapshot, "diagnostics.csv", 0.045)["meaning"]
    assert not recorded.sample(snapshot, "states.csv", 0.125)["available"]
    assert views.compare(run, runs[1])["classification"] == "invalid"


def test_three_run_ui_0125_and_pair_labels(runs, tmp_path, monkeypatch):
    app = select(app_for(tmp_path, monkeypatch), runs, "Compare")
    app.selectbox(key="selected_qualification").set_value(Q).run()
    app.number_input(key="compare_requested_time").set_value(0.125).run()
    app.button(key="compare_seek").click().run()
    assert not app.exception and not app.error
    table = sample_table(app)
    assert table.state_time_s.tolist() == [0.125] * 3
    assert table.control_time_s.tolist() == [0.125] * 3
    assert table["delta [rad]"].tolist() == [0.02] * 3
    assert table["r [rad/s]"].iloc[0] != table["r [rad/s]"].iloc[1]
    pairs = next(i.value for i in app.dataframe if "classification" in i.value.columns)
    assert pairs.classification.tolist() == [
        "qualified_synthetic_comparison",
        "qualified_synthetic_comparison",
        "illustrative",
    ]
    assert not any(i.value == "Qualified Synthetic Comparison" for i in app.subheader)


def test_replay_controls_cross_onset_read_only_and_reset(runs, tmp_path, monkeypatch):
    now = [0.0]
    monkeypatch.setattr(workspace_panels, "viewer_now", lambda: now[0])

    def forbidden(*args, **kwargs):
        pytest.fail("Recorded replay must not execute, cancel or reconcile a job")

    for name in ("start_run", "cancel_run", "status_for", "save_notes"):
        monkeypatch.setattr(jobs, name, forbidden)
    app = select(app_for(tmp_path, monkeypatch), runs)
    app.select_slider(key="inspect_time").set_value(0.095).run()
    app.button(key="inspect_play").click().run()
    assert app.session_state["inspect_playback"]["playing"] is True
    now[0] = 1.0
    app.run()
    assert app.select_slider(key="inspect_time").value == 0.1
    assert sample_table(app)["delta [rad]"].iloc[0] == 0.02
    app.button(key="inspect_pause").click().run()
    assert app.session_state["inspect_playback"]["playing"] is False
    app.button(key="inspect_previous").click().run()
    assert app.select_slider(key="inspect_time").value == 0.095
    app.selectbox(key="inspect_run").set_value(runs[1].key).run()
    assert app.select_slider(key="inspect_time").value == 0.0
    assert app.session_state["inspect_playback"]["playing"] is False
    app.button(key="inspect_play").click().run()
    app.radio(key="workspace_view").set_value("Home").run()
    assert app.session_state["inspect_playback"]["playing"] is False
    app.radio(key="workspace_view").set_value("Inspect").run()
    assert app.session_state["inspect_playback"]["playing"] is False
    assert not app.exception and not app.error


def test_compact_layout_raw_access_source_switch_warning_and_offgrid(
    runs, tmp_path, monkeypatch, caplog
):
    app = select(app_for(tmp_path, monkeypatch), runs)
    assert len(app.tabs) == 3
    assert all(
        not item.proto.expanded
        for item in app.expander
        if item.label == "Configuration and source provenance"
    )
    app.selectbox(key="inspect_source").set_value("controls.csv").run()
    app.multiselect(key="inspect_channels").set_value(["delta"]).run()
    control_plot = json.loads(app.get("plotly_chart")[1].proto.spec)
    assert control_plot["data"][0]["line"]["shape"] == "hv"
    app.selectbox(key="inspect_source").set_value("diagnostics.csv").run()
    app.multiselect(key="inspect_channels").set_value(["alpha_f", "fyf"]).run()
    assert not any(
        "inspect_channels" in rec.message and "default" in rec.message for rec in caplog.records
    )
    app.number_input(key="inspect_requested_time").set_value(0.126).run()
    app.button(key="inspect_seek").click().run()
    assert app.error and app.select_slider(key="inspect_time").value == 0.0
    app.select_slider(key="inspect_time").set_value(0.125).run()
    assert not app.exception and not app.error
    assert app.get("plotly_chart")


def test_unknown_profile_and_inconsistent_stored_xy_are_not_replayed(runs, tmp_path):
    snapshot = recorded.load(runs[0])
    unrecognized = replace(snapshot, data=replace(snapshot.data, contract={}))
    assert not recorded.supports_replay(unrecognized)
    with pytest.raises(storage.IntegrityError, match="unsupported"):
        recorded.times(unrecognized)
    copy = tmp_path / "mismatched-xy"
    shutil.copytree(runs[0].directory, copy)
    rewrite_csv(copy / "experiment/trajectory_xy.csv", lambda rows: rows.pop())
    reseal_fixture(copy)
    with pytest.raises(storage.IntegrityError, match="XY/state"):
        recorded.load(replace(runs[0], directory=copy, aliases=(copy,)))


def test_case_description_and_snapshot_update_before_submission(tmp_path, monkeypatch):
    app = app_for(tmp_path, monkeypatch)
    app.radio(key="workspace_view").set_value("Run").run()
    next(i for i in app.selectbox if i.label == "Execution mode").set_value("dynamic_lab").run()
    case = next(i for i in app.selectbox if i.label == "Synthetic case")
    # The selector is outside the submission form; actual browser changes cause a rerun.
    assert not any(i.label == "Synthetic case" for form in app.get("form") for i in form.selectbox)
    case.set_value("VDL1_IZ_HIGH").run()
    assert any("Yaw-inertia sensitivity" in item.value for item in app.caption)
    assert any("VDL1_IZ_HIGH" in item.value for item in app.json)
    assert not list((tmp_path / "owned").glob("*/request.json"))
    assert not app.exception and not app.error
