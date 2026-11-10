"""UI-only checks. Retained scientific evidence is read-only; no native runtime execution."""

import copy
import hashlib
import json

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs, scratch_replay
from tools.apex_workbench.lap import config, execution, ui_data, ui_replay, ui_views


@pytest.fixture
def pilot():
    return ui_data.read(ui_data.recordings("V2")[0])


@pytest.mark.parametrize("family", ["V2", "Transient"])
def test_genuine_payload_preserves_state_applied_nominal_packet_and_reference(family):
    view = ui_data.read(ui_data.recordings(family)[0])
    original = copy.deepcopy(view)
    data = ui_data.payload(ui_data.window(view, ui_data.windows(view)[0]))
    for a, b in zip(data["states"], view["raw"]["states"], strict=True):
        for key in (
            "time",
            "delta",
            "a_cmd",
            "vx",
            "s_abs",
            "plan_id",
            "mode",
            "front_utilization",
        ):
            assert a[key] == b[key]
    for a, b in zip(data["controls"], view["raw"]["controls"], strict=True):
        for key in ("time", "application_time", "delta", "nominal_delta"):
            assert a[key] == b[key]
    assert all(len(p["states"]) == 9 and len(p["controls"]) == 8 for p in data["packets"])
    assert len(data["planning_reference"]) == 3097
    assert data["meta"]["lap_crossings"] == []
    assert view == original
    assert len(json.dumps(data).encode()) < ui_data.MAX_PAYLOAD_BYTES


def test_long_native_windows_cover_all_samples_without_resampling():
    # Explicit transport fixture; these scalar clocks are not scientific observations.
    native = [{"time": i * 0.005} for i in range(16000)]
    view = {"raw": {"states": native}, "presentation": {"states": native}}
    windows = ui_data.windows(view)
    assert len(windows) == 8
    covered = set()
    for start, end in windows:
        assert 1 < end - start <= ui_data.MAX_SAMPLES
        assert native[end - 1]["time"] - native[start]["time"] <= 10
        part = ui_data.window(view, (start, end))
        assert part["raw"]["states"] == native[start:end]
        covered.update(range(start, end))
    assert covered == set(range(16000))


@pytest.mark.parametrize("times", [[0], [0, 0], [1, 0], [0, float("nan")], [0, 11]])
def test_invalid_native_windows_reject(times):
    with pytest.raises(ValueError):
        ui_data.windows({"raw": {"states": [{"time": t} for t in times]}})


@pytest.mark.parametrize("fault", ["steering", "track_length", "reference_hash"])
def test_display_metadata_rejects_missing_or_inconsistent_sources(pilot, fault):
    if fault == "steering":
        pilot["raw"]["states"][0]["delta"] = None
    elif fault == "track_length":
        pilot["request"]["capture"]["resolved"]["track_length_m"] += 1
    else:
        pilot["request"]["capture"]["source_sha256"][ui_data.REFERENCE] = "wrong"
    with pytest.raises(ValueError):
        ui_data.payload(ui_data.window(pilot, ui_data.windows(pilot)[0]))


def test_clock_is_byte_identical_and_all_new_assets_are_bound():
    assert (ui_replay.ASSETS / "clock.mjs").read_bytes() == (
        scratch_replay.ASSETS / "clock.mjs"
    ).read_bytes()
    inventory = config.producers()
    for asset in ui_replay.ASSETS.iterdir():
        assert (
            inventory[str(asset.relative_to(config.ROOT))]
            == hashlib.sha256(asset.read_bytes()).hexdigest()
        )
    # The existing access record is preserved and rejects the changed UI inventory.
    with pytest.raises(ValueError, match="stale"):
        config.access(config.defaults())


def test_post_render_replacement_clears_and_latches_replay(pilot, monkeypatch):
    original = ui_data.current
    changed = [False]

    def check(view):
        if changed[0]:
            changed[0] = False
            raise ValueError("disposable changed epoch after mounting")
        original(view)

    def component(**kwargs):
        changed[0] = True
        return {"epoch": kwargs["epoch"], "loaded": True}

    monkeypatch.setattr(ui_data, "current", check)
    monkeypatch.setattr(ui_replay, "component", lambda: component)
    app = AppTest.from_string(
        (
            "from tools.apex_workbench.lap import ui_data,ui_replay\n"
            "v=ui_data.read(ui_data.recordings('V2')[0])\n"
            "ui_replay.replay(ui_data.window(v,ui_data.windows(v)[0]))"
        )
    ).run(timeout=20)
    assert not app.exception
    assert any("changed epoch after mounting" in e.value for e in app.error)
    assert not app.get("component_instance")


def test_full_navigation_validation_drafts_analysis_and_comparison_without_execution(
    tmp_path, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("No simulation, controller execution or probe permitted")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    monkeypatch.setattr(execution, "start", forbidden)
    monkeypatch.setattr(config.v1, "probe", forbidden)
    app = AppTest.from_file(str(config.HERE / "app.py")).run(timeout=20)
    assert app.radio[0].options == ui_views.PAGES and not app.exception and not app.error
    app.radio[0].set_value("Configure").run()
    assert len([n for n in app.number_input if n.label not in {"Configuration version"}]) == 8
    next(n for n in app.number_input if n.label == "Lateral").set_value(0).run()
    assert any("positivity" in e.value for e in app.error)
    next(n for n in app.number_input if n.label == "Lateral").set_value(1).run()
    # Draft storage is disposable; retained roots remain byte-for-byte unchanged.
    original_output = config.OUTPUT
    monkeypatch.setattr(config, "OUTPUT", tmp_path)
    next(b for b in app.button if b.label == "Save configuration draft").click().run()
    assert len(list((tmp_path / "configurations").glob("*.json"))) == 1
    next(b for b in app.button if b.label == "Save configuration draft").click().run()
    assert any("not saved" in e.value for e in app.error)
    monkeypatch.setattr(config, "OUTPUT", original_output)
    app.radio[0].set_value("Run").run()
    assert next(b for b in app.button if b.label == "Run experiment").disabled
    app.radio[0].set_value("Analyze").run(timeout=20)
    for group in ["Actuation & grip", "Solver & events", "Prediction inspection"]:
        next(s for s in app.selectbox if s.label == "Analysis view").select(group).run(timeout=20)
        assert not app.exception and not app.error
    app.radio[0].set_value("Compare").run()
    assert any("Only one V2" in e.value for e in app.info)
    app.selectbox[0].select("Transient").run()
    app.multiselect[0].set_value(ui_data.recordings("Transient")[:2]).run(timeout=20)
    assert not app.exception and not app.error
    assert any("comparison" in e.value for e in app.info)


def test_missing_incomplete_and_replaced_evidence_are_contained(tmp_path, monkeypatch):
    from tools.apex_workbench.tests.test_lap_v2 import archive_fixture

    directory = archive_fixture(tmp_path, monkeypatch)
    record = {"family": "V2", "directory": directory}
    view = ui_data.read(record)
    # Real production hash check on disposable archive bytes.
    (directory / "native/states-00000.jsonl").write_text("changed")
    with pytest.raises(ValueError):
        ui_data.current(view)
    with pytest.raises(ValueError):
        ui_data.read(record)
    (directory / "presentation.json").unlink()
    errors = []
    monkeypatch.setattr(ui_views.st, "error", errors.append)
    ui_views.guarded([record], lambda _: pytest.fail("Corrupt evidence rendered"))
    assert errors and errors[0].startswith("Evidence quarantined")
    monkeypatch.setattr(ui_data, "read", lambda _: {"raw": None, "presentation": None})
    ui_views.guarded([record], lambda _: pytest.fail("Incomplete evidence rendered"))


def test_missing_status_is_contained(tmp_path, monkeypatch):
    errors = []
    monkeypatch.setattr(ui_views.st, "error", errors.append)
    assert ui_views.active({"directory": tmp_path, "family": "V2"}) is True
    assert errors and errors[0].startswith("Evidence quarantined")


def test_draft_survives_navigation_and_invalid_editor_blocks_stale_run(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("UI test must not execute or probe")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    monkeypatch.setattr(execution, "start", forbidden)
    monkeypatch.setattr(config.v1, "probe", forbidden)
    app = AppTest.from_file(str(config.HERE / "app.py")).run(timeout=20)
    app.radio[0].set_value("Configure").run()
    next(n for n in app.number_input if n.label == "Lateral").set_value(1.5).run()
    next(s for s in app.selectbox if s.label == "Recording duration [simulated s]").select(20).run()
    app.text_input[0].set_value("explicit_draft").run()
    app.radio[0].set_value("Run").run()
    assert app.session_state["ui_configuration"]["maximum_simulation_s"] == 20
    app.radio[0].set_value("Configure").run()
    assert next(n for n in app.number_input if n.label == "Lateral").value == 1.5
    assert app.text_input[0].value == "explicit_draft"
    next(n for n in app.number_input if n.label == "Lateral").set_value(0).run()
    app.radio[0].set_value("Run").run()
    assert any("requires correction" in e.value for e in app.error)
    assert not any(b.label == "Run experiment" for b in app.button)


@pytest.mark.parametrize("missing", [None, float("nan"), float("inf")])
def test_optional_plot_missing_values_break_actual_plotly_lines(monkeypatch, missing):
    figures = []
    monkeypatch.setattr(ui_views.theme, "chart", figures.append)
    ui_views.plot(
        [{"time": 0, "v": 1}, {"time": 1, "v": missing}, {"time": 2, "v": 3}],
        [("v", "Optional diagnostic")],
        "Diagnostic [1]",
    )
    trace = figures[0].data[0]
    assert list(trace.x) == [0, 1, 2] and list(trace.y) == [1, None, 3]
    assert trace.connectgaps is False


def test_reduction_preserves_unsampled_missingness_without_mutating_source():
    rows = [{"time": i, "v": i} for i in range(16000)]
    rows[4]["v"] = None  # Not one of the uniformly selected display points.
    rows[10001]["time"] = None
    before = copy.deepcopy(rows)
    xs, ys = ui_data.trace(rows, "time", "v")
    assert len([v for v in ys if v is not None]) <= 2000
    assert ys[xs.index(4)] is None and None in xs
    assert xs[0] == 0 and xs[-1] == 15999
    assert rows == before
    assert all(
        (x, y) in [(r["time"], r["v"]) for r in rows] for x, y in zip(xs, ys) if y is not None
    )
