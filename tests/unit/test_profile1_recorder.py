"""G1-authored, UNEXECUTED G2 protocol cases; no calibration or numerical campaign.

Collection itself is outside G1 authorization. Fake ticks test accounting, never host cost.
Numerical failure counterparts U05-U09 live in test_profile1_parity.py.
"""

import importlib.util
import json
import os
import sys
from pathlib import Path
from threading import Thread

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def api():
    path = ROOT / "scripts/task007f/profile1/recorder.py"
    spec = importlib.util.spec_from_file_location("profile1_protocol_under_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


class Ticks:
    def __init__(self, *, bad=None):
        self.index, self.order, self.bad = 0, [], bad or {}

    def read(self, kind):
        self.order.append(kind)
        self.index += 1
        value = self.bad.get(self.index, self.index * 10)
        if isinstance(value, Exception):
            raise value
        return value

    def wall_ns(self):
        return self.read("wall")

    def cpu_ns(self):
        return self.read("cpu")


def make(api, clock=None, **limits):
    identity = api.WorkerIdentity(
        "protocol", os.getpid(), api.REFERENCE_REVISION, "a" * 40, "b" * 64, api.MANIFEST_SHA256
    )
    return api.create_recorder(
        mode="profile1-v1",
        identity=identity,
        limits=api.RecorderLimits(**limits),
        clock=clock or Ticks(),
    )


def outcome(kind="returned_none"):
    return dict(
        kind=kind, existing_status="negative_fixture", solver_attempted=False, exception_type=None
    )


def start(recorder, *, kind="startup", plan_id=0):
    call = recorder.begin_call(kind=kind, plan_id=plan_id, release_sim_s=0.0, estimate_sim_s=0.0)
    root = recorder.span_begin(call, "prepare_full", expected_parent=None)
    return call, root


def seal(recorder, raw=None):
    recorder.reconcile()  # No invented calibration allowance.
    return recorder.seal(legacy_result=raw, termination="protocol_fixture")


def test_U01_off_and_unsupported_have_no_clock_or_recorder_allocation(api, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("OFF allocated a recorder")

    monkeypatch.setattr(api, "Recorder", forbidden)
    assert api.create_recorder(mode="off", identity=None, limits=None, clock=object()) is None
    with pytest.raises(ValueError):
        api.create_recorder(mode="unknown", identity=None, limits=None)


def test_U02_wall_then_cpu_integer_endpoints(api):
    clock = Ticks()
    recorder = make(api, clock)
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    payload = seal(recorder).payload
    assert clock.order == ["wall", "cpu"] * 4
    assert payload["calls"][0]["wall_start_ns"] == 10
    assert payload["spans"][0]["cpu_end_ns"] == 60
    assert all(
        type(row[k]) is int
        for row in payload["spans"]
        for k in ("wall_start_ns", "cpu_start_ns", "wall_end_ns", "cpu_end_ns")
    )


def test_U03_exact_tree_and_occurrence_accounting(api):
    approved = json.loads((ROOT / "docs/task007f/profile1/g1_recorder_api.json").read_text())
    assert api.PREPARATION_PARENTS == {row["id"]: row["parent"] for row in approved["span_tree"]}
    recorder = make(api)
    call, root = start(recorder)
    controller = recorder.span_begin(call, "controller", expected_parent="prepare_full")
    reference = recorder.span_begin(call, "reference", expected_parent="controller")
    for _ in range(2):
        for name in ("reference_geometry", "reference_values"):
            token = recorder.span_begin(call, name, expected_parent="reference")
            recorder.span_end(token, exit="complete")
    for token in (reference, controller, root):
        recorder.span_end(token, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    report = recorder.reconcile()
    rows = recorder.seal(legacy_result=None, termination="fixture").payload["spans"]
    assert [r["occurrence"] for r in rows if r["span_id"] == "reference_values"] == [1, 2]
    assert report["structural_valid"]
    for phase in report["call_reports"][0]["phases"]:
        assert phase["wall_exclusive_ns"] >= 0
    assert report["allowance_status"] == "unresolved"


def test_U04_no_borrowed_numerical_objects_or_mutation(api):
    recorder = make(api)
    raw = {
        "plans": [{"plan_id": 0, "startup": True, "success": True, "completion_time": 0.0}],
        "controls": [{"plan_id": 0, "application_time": 0.0}],
        "states": [[1.0, 2.0]],
    }
    before = json.dumps(raw, sort_keys=True)
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome("returned_packet"))
    payload = seal(recorder, raw).payload
    assert json.dumps(raw, sort_keys=True) == before
    assert "states" not in payload and "solution" not in payload
    with pytest.raises(TypeError):
        payload["calls"][0]["plan_id"] = 99
    raw["controls"][0]["application_time"] = 9.0
    assert payload["physical_outcomes"][0]["application_times_sim_s"] == (0.0,)


def test_U10_returned_none_complete_root_and_not_reached_children(api):
    recorder = make(api)
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    payload = seal(recorder).payload
    assert payload["calls"][0]["outcome"]["kind"] == "returned_none"
    assert payload["spans"][0]["coverage"] == "complete"
    assert all(
        row["coverage"] == "not_reached"
        for row in payload["reconciliation"]["call_reports"][0]["missing_phases"]
    )


@pytest.mark.parametrize("fault", ["order", "missing", "thread", "parent"])
def test_U11_wrong_or_foreign_tokens_are_invalid(api, fault):
    recorder = make(api)
    call, root = start(recorder)
    if fault == "order":
        recorder.span_begin(call, "controller", expected_parent="prepare_full")
        recorder.span_end(root, exit="complete")
    elif fault == "missing":
        recorder.span_end(None, exit="complete")
    elif fault == "thread":
        thread = Thread(target=lambda: recorder.span_end(root, exit="complete"))
        thread.start()
        thread.join()
    else:
        recorder.span_begin(call, "reference", expected_parent="controller")
    assert recorder.stop_requested()
    assert seal(recorder).payload["observer_validity"] == "invalid"


@pytest.mark.parametrize("bad", [0, 1.5, True, -1, 2**63])
def test_U12_decreasing_and_invalid_clock_values(api, bad):
    recorder = make(api, Ticks(bad={3: bad}))
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    payload = seal(recorder).payload
    assert not payload["reconciliation"]["clock_order_valid"]
    assert payload["observer_validity"] == "invalid"
    if type(bad) is int and bad == 0:
        assert payload["spans"][0]["wall_start_ns"] == 0  # Retain anomalous raw integer.
    else:
        assert payload["spans"][0]["wall_start_ns"] is None


def test_U13_raised_clock_keeps_half_pair_and_original_result(api):
    recorder = make(api, Ticks(bad={3: RuntimeError("observer clock")}))
    call, root = start(recorder)
    original = outcome()
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=original)
    payload = seal(recorder).payload
    assert payload["spans"][0]["wall_start_ns"] is None
    assert payload["spans"][0]["cpu_start_ns"] == 40
    assert dict(payload["calls"][0]["outcome"]) == original
    assert payload["reconciliation"]["call_reports"][0]["phases"][0]["wall_exclusive_ns"] is None


def test_U14_capacity_retains_reserved_endpoints(api):
    recorder = make(api, max_span_records=1)
    call, root = start(recorder)
    assert recorder.span_begin(call, "controller", expected_parent="prepare_full") is None
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    payload = seal(recorder).payload
    assert len(payload["spans"]) == 1
    assert payload["spans"][0]["wall_end_ns"] is not None
    assert payload["first_fault"]["code"] == "span_or_depth_capacity"
    assert payload["observer_validity"] == "invalid"


def test_U15_call_depth_and_sticky_first_fault(api):
    recorder = make(api, max_stack_depth=1, max_fault_records=1)
    call, root = start(recorder)
    recorder.span_begin(call, "controller", expected_parent="prepare_full")
    recorder.span_end(-9, exit="complete")
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    assert (
        recorder.begin_call(kind="recurring", plan_id=1, release_sim_s=0.1, estimate_sim_s=0.0)
        is None
    )
    payload = seal(recorder).payload
    assert payload["first_fault"]["code"] == "span_or_depth_capacity"
    assert payload["diagnostic_overflow_count"] > 0
    other = make(api, max_calls=1)
    call, root = start(other)
    other.span_end(root, exit="complete")
    other.finish_call(call, outcome=outcome())
    assert (
        other.begin_call(kind="recurring", plan_id=1, release_sim_s=0.1, estimate_sim_s=0.0) is None
    )
    assert other.stop_requested()


def test_U16_exception_and_diagnostic_bounds(api):
    recorder = make(api, max_exception_type_utf8_bytes=4, max_status_utf8_bytes=4)
    call, root = start(recorder)
    recorder.span_end(root, exit="exception", exception_type="too.long.Exception")
    recorder.finish_call(call, outcome=outcome())
    payload = seal(recorder).payload
    assert payload["spans"][0]["exception_type"] is None
    assert payload["spans"][0]["coverage"] == "partial"
    assert payload["calls"][0]["outcome"]["existing_status"] is None
    assert payload["observer_validity"] == "invalid"


def test_U17_export_oserror_preserves_original_raw(api, tmp_path, monkeypatch):
    recorder = make(api)
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    original = tmp_path / "original_raw.json"
    original.write_text('{"failure":null}')

    def fail(*args, **kwargs):
        raise OSError("deliberate export failure")

    monkeypatch.setattr(api.os, "link", fail)
    report = api.write_sidecar(seal(recorder), output_dir=tmp_path)
    assert not report["complete"] and report["sha256"] is None
    assert Path(report["partial_path"]).exists()
    assert original.read_text() == '{"failure":null}'


def test_U18_serialized_cap_and_no_overwrite(api, tmp_path):
    recorder = make(api, max_serialized_bytes=64)
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    report = api.write_sidecar(seal(recorder), output_dir=tmp_path)
    assert not report["complete"] and report["sha256"] is None
    partial = Path(report["partial_path"])
    assert partial.stat().st_size <= 64
    before = partial.read_bytes()
    assert not api.write_sidecar(recorder._sealed, output_dir=tmp_path)["complete"]
    assert partial.read_bytes() == before


def test_U19_interrupt_open_span_has_no_invented_endpoint(api):
    recorder = make(api)
    call, root = start(recorder)
    child = recorder.span_begin(call, "prediction", expected_parent="prepare_full")
    recorder.span_end(child, exit="exception", exception_type="builtins.KeyboardInterrupt")
    payload = seal(recorder).payload
    assert payload["spans"][root]["wall_end_ns"] is None
    assert payload["open_span_tokens"] == (root,)
    assert payload["calls"][0]["outcome"] is None
    assert payload["observer_validity"] == "invalid"
    assert payload["physical_outcomes"][0]["wall_observed_lower_bound_ns"] > 0


def test_U20_pending_completion_is_censored_but_full_host_work_retained(api):
    recorder = make(api)
    call, root = start(recorder, kind="recurring", plan_id=1)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome("returned_packet"))
    raw = {
        "plans": [
            {
                "plan_id": 1,
                "completed": False,
                "completion_time": 0.5,
                "planner_total_time": 0.01,
                "planner_cpu_time": 0.01,
            }
        ],
        "controls": [],
        "handoffs": [],
    }
    row = seal(recorder, raw).payload["physical_outcomes"][0]
    assert row["physical_completion_censored"] and row["observed_completion_sim_s"] is None
    assert row["scheduled_legacy_completion_sim_s"] == 0.5
    assert row["full_prepare_cpu_ns"] > 0 and not row["host_call_partial"]
    assert row["accepted_times_sim_s"] == () and row["application_times_sim_s"] == ()
    assert row["hypothetical_measured_full_prepare_completion_sim_s"] != 0.5


def test_missing_root_and_unresolved_allowance_never_validate(api):
    recorder = make(api)
    call = recorder.begin_call(kind="startup", plan_id=0, release_sim_s=0.0, estimate_sim_s=0.0)
    recorder.finish_call(call, outcome=outcome())
    assert seal(recorder).payload["observer_validity"] == "invalid"
    other = make(api)
    call, root = start(other)
    other.span_end(root, exit="complete")
    other.finish_call(call, outcome=outcome())
    assert seal(other).payload["observer_validity"] == "incomplete"


def test_outcome_join_capacity_is_explicit_and_raw_unchanged(api):
    recorder = make(api, max_span_records=1)
    call, root = start(recorder)
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    raw = {"controls": [{"plan_id": 0, "application_time": v} for v in (0.0, 0.01)]}
    payload = seal(recorder, raw).payload
    assert payload["physical_outcomes"][0]["outcome_join_incomplete"]
    assert payload["observer_validity"] == "invalid" and len(raw["controls"]) == 2


def test_signed_negative_residual_is_retained_and_never_clamped(api):
    recorder = make(api, Ticks(bad={7: 200, 9: 110}))
    call, root = start(recorder)
    child = recorder.span_begin(call, "prediction", expected_parent="prepare_full")
    recorder.span_end(child, exit="complete")
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    report = recorder.reconcile()
    phase = report["call_reports"][0]["phases"][0]
    assert phase["wall_inclusive_ns"] == 80
    assert phase["wall_exclusive_ns"] == -70
    assert not report["clock_order_valid"] and not report["structural_valid"]
    assert report["clock_allowance"] is None


def test_partial_child_makes_parent_exclusive_unknown(api):
    recorder = make(api)
    call, root = start(recorder)
    child = recorder.span_begin(call, "prediction", expected_parent="prepare_full")
    recorder.span_end(child, exit="exception", exception_type="builtins.ValueError")
    recorder.span_end(root, exit="complete")
    recorder.finish_call(call, outcome=outcome())
    phase = recorder.reconcile()["call_reports"][0]["phases"][0]
    assert phase["wall_inclusive_ns"] > 0 and phase["wall_exclusive_ns"] is None


def test_auxiliary_populations_never_become_physical_preparations(api):
    recorder = make(api)
    call = recorder.begin_call(
        kind="clock_probe", plan_id=None, release_sim_s=None, estimate_sim_s=None
    )
    for _ in range(2):
        parent = recorder.span_begin(call, "clock_parent", expected_parent=None)
        child = recorder.span_begin(call, "clock_child", expected_parent="clock_parent")
        recorder.span_end(child, exit="complete")
        recorder.span_end(parent, exit="complete")
    recorder.finish_call(
        call,
        outcome=dict(
            kind="not_applicable", existing_status=None, solver_attempted=None, exception_type=None
        ),
    )
    payload = seal(recorder).payload
    assert [row["occurrence"] for row in payload["spans"] if row["span_id"] == "clock_parent"] == [
        1,
        2,
    ]
    assert (
        payload["physical_outcomes"][0]["hypothetical_measured_full_prepare_completion_sim_s"]
        is None
    )
    assert not payload["physical_outcomes"][0]["physical_completion_censored"]
