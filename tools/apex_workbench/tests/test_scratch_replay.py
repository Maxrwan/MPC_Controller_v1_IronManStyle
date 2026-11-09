"""Read-only replay boundaries over retained data and disposable malformed copies."""

import copy
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs
from tools.apex_workbench import nmpc_scratch as scratch
from tools.apex_workbench import scratch_replay as replay


@pytest.fixture
def native_view():
    path = next(
        p
        for p in scratch.RUNS.iterdir()
        if scratch.read_run(p)["request"]["effective"]["configuration_id"] == "baseline"
    )
    return scratch.read_run(path)


def test_payload_preserves_native_clocks_channels_and_n8_associations(native_view):
    before = copy.deepcopy(native_view)
    value = replay.payload(native_view)
    assert len(value["states"]) == 400
    assert len(value["controls"]) == 200
    assert len(value["packets"]) == 20
    for a, b in zip(value["states"], native_view["raw"]["states"], strict=True):
        for key in ("time", "vx", "vy", "r", "e_psi", "e_y", "plan_id", "mode"):
            assert a[key] == b[key]
    for a, b in zip(value["packets"], native_view["packets"], strict=True):
        assert a["states"] == b["packet"]["states"]
        assert a["controls"] == b["packet"]["controls"]
        assert len(a["states"]) == 9 and len(a["controls"]) == 8
        scheduled = next(r for r in native_view["raw"]["packets"] if r["plan_id"] == a["id"])
        assert a["completion"] == scheduled["actual_completion_time"]
        assert a["valid"] == scheduled["valid"]
    assert native_view == before
    assert len(json.dumps(value)) < 350_000


@pytest.mark.parametrize("fault", ["time", "coverage", "position", "packet", "geometry", "clock"])
def test_payload_rejects_inconsistent_or_unusable_records(native_view, fault):
    view = copy.deepcopy(native_view)
    if fault == "time":
        view["presentation"]["states"][1]["time"] = 0.0
    if fault == "coverage":
        view["presentation"]["states"].pop()
    if fault == "position":
        view["presentation"]["states"][0]["x"] = float("nan")
    if fault == "packet":
        view["packets"][0]["packet"]["controls"].pop()
    if fault == "geometry":
        view["presentation"]["geometry"] = []
    if fault == "clock":
        view["raw"]["controls"][0]["application_time"] = None
    with pytest.raises(ValueError):
        replay.payload(view)


def test_partial_record_stays_unavailable(native_view):
    view = copy.deepcopy(native_view)
    view["raw"] = None
    with pytest.raises(ValueError, match="partial journals"):
        replay.payload(view)


def test_acknowledged_payload_is_not_resent_on_each_presentation(native_view, monkeypatch):
    calls = []

    def component(**kwargs):
        calls.append(kwargs)
        return {"epoch": kwargs["epoch"], "loaded": True}

    monkeypatch.setattr(replay, "component", lambda: component)
    # Use a real Streamlit context; bare-mode fragments intentionally do not execute.
    app = AppTest.from_string(
        "from tools.apex_workbench import scratch_replay,nmpc_scratch\n"
        "from pathlib import Path\nscratch_replay.replay(nmpc_scratch.read_run(Path("
        + repr(str(native_view["directory"]))
        + ")))"
    ).run()
    app.run()
    assert not app.exception
    assert calls[0]["payload"] is not None and calls[1]["payload"] is None
    assert calls[0]["epoch"] == calls[1]["epoch"]
    assert calls[0]["heartbeat"] != calls[1]["heartbeat"]


def test_post_render_replacement_withdraws_the_component(native_view, monkeypatch):
    original = scratch.current

    def current(view):
        if changed[0]:
            changed[0] = False  # Restored bytes cannot silently clear the quarantine latch.
            raise ValueError("disposable replacement during mounting")
        original(view)

    changed = [False]

    def component(**kwargs):
        changed[0] = True
        return None

    monkeypatch.setattr(scratch, "current", current)
    monkeypatch.setattr(replay, "component", lambda: component)
    app = AppTest.from_string(
        "from tools.apex_workbench import scratch_replay,nmpc_scratch\n"
        "from pathlib import Path\nscratch_replay.replay(nmpc_scratch.read_run(Path("
        + repr(str(native_view["directory"]))
        + ")))"
    ).run()
    assert not app.exception
    assert any("replacement during mounting" in x.value for x in app.error)


def test_small_editor_analysis_and_gate_are_preserved(monkeypatch):
    def unaccepted_fixture(*a, **kw):
        raise ValueError("Unaccepted policy fixture")

    monkeypatch.setattr(scratch, "access", unaccepted_fixture)

    def forbidden(*a, **kw):
        raise AssertionError("No controller execution or probe")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    monkeypatch.setattr(scratch, "probe", forbidden)
    path = Path(__file__).parents[1] / "workspace.py"
    app = AppTest.from_file(str(path), default_timeout=45).run()
    next(b for b in app.button if b.label == "Open NMPC Scratch / Control Analysis").click().run()
    assert not app.exception and not app.warning
    assert next(b for b in app.button if b.label == "Run Scratch experiment").disabled
    assert len([x for x in app.number_input if x.label in scratch.FIELDS]) == 8
    next(x for x in app.radio if x.label == "Workspace").set_value("Analyze").run()
    assert not app.exception and not app.error and not app.warning
