"""Offline VIS-1L censoring and evidence checks; never launches a racing worker."""

import copy
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
report = importlib.import_module("task007dvis.long_report")


@pytest.mark.parametrize("kind", ["common_time", "common_progress"])
def test_unequal_coverage_excludes_unmatched_tail_without_interpolation(kind):
    a = pd.DataFrame(dict(time=[0, 1, 2, 3], s_abs=[1, 2, 3, 4]))
    b = pd.DataFrame(dict(time=[0, 0.9, 1.9], s_abs=[1, 2.1, 2.9]))
    wa, wb = report.common_windows(a, b, kind)
    assert not wa["complete"] and not wb["complete"]
    assert wa["end"] == 1 and wb["end"] == 1.9
    assert wa["end_s"] == 2 and wb["end_s"] == 2.9
    assert wa["shared_upper"] == wb["shared_upper"]


def test_no_common_coverage_is_explicit():
    a = pd.DataFrame(dict(time=[0, 1], s_abs=[1, 2]))
    b = pd.DataFrame(dict(time=[2, 3], s_abs=[3, 4]))
    with pytest.raises(ValueError, match="No common"):
        report.common_windows(a, b, "common_time")


def miss_fixture():
    rows = [
        dict(time=0, plan_id=0, reserve=0.17),
        dict(time=0.165, plan_id=0, reserve=0.005),
        dict(time=0.17, plan_id=0, reserve=0.0),
    ]
    cycle = dict(plan_id=1, status="missed", miss_time=0.17, t_accept=None, t_ready=None)
    raw = dict(
        handoffs=[],
        packets=[dict(plan_id=0, timestamps=[0, 0.17])],
        end_time=0.17,
        fixed_handoffs=[cycle],
    )
    return raw, rows


def test_terminal_miss_keeps_completion_and_recovery_unknown():
    raw, rows = miss_fixture()
    before = copy.deepcopy((raw, rows))
    result = report.miss_records(raw, rows)[0]
    assert result["recovery_time"] is None and result["recovery_plan_id"] is None
    assert result["recovery_censored"] and not result["completion_observed"]
    assert result["minimum_native_reserve"] == 0
    assert result["observed_without_replacement"] == 0
    assert (raw, rows) == before


def test_late_discard_is_not_recovery():
    raw, rows = miss_fixture()
    raw["end_time"] = 0.3
    raw["fixed_handoffs"][0].update(t_ready=0.175, late_discard_time=0.175)
    raw["handoffs"] = [
        dict(plan_id=1, time=0.175, accepted=False),
        dict(plan_id=2, time=0.27, accepted=True),
    ]
    result = report.miss_records(raw, rows)[0]
    assert result["completion_observed"]
    assert result["recovery_time"] == 0.27 and result["recovery_plan_id"] == 2
    assert result["old_plan_id"] == 0 and not result["recovery_censored"]


def test_missed_packet_must_not_have_authority():
    raw, rows = miss_fixture()
    raw["handoffs"] = [dict(plan_id=1, time=0.17, accepted=True)]
    with pytest.raises(AssertionError):
        report.miss_records(raw, rows)


def write_trace(folder):
    (folder / "scientific").mkdir()
    state = dict(zip(report.STATE_NAMES, [2, 0, 0, 0, 1, 0]))
    initial = dict(time=0.0, **state, delta=0, a_cmd=0)
    final = dict(initial, time=0.005, s_abs=1.01)
    raw = dict(states=[initial], end_time=0.005)
    segments = [
        dict(
            start=0,
            end=0.005,
            dt=0.005,
            state_before=[initial[k] for k in report.STATE_NAMES],
            state_after=[final[k] for k in report.STATE_NAMES],
            control=[0, 0],
        )
    ]
    for name, v in [("raw", raw), ("segments", segments)]:
        (folder / (name + ".json")).write_text(json.dumps(v))
    path = folder / "scientific/states.csv"
    pd.DataFrame([dict(v, sample_provenance="native") for v in [initial, final]]).to_csv(
        path, index=False
    )
    return path


def test_failed_export_trace_requires_native_endpoint_identity(tmp_path):
    write_trace(tmp_path)
    frame, raw, _ = report.load_trace(tmp_path)
    assert frame.time.iloc[-1] == raw["end_time"]
    assert not (tmp_path / "scientific/manifest.json").exists()
    assert not (tmp_path / "summary.json").exists()


@pytest.mark.parametrize(
    "field,value", [("vx", 2.1), ("time", 0.006), ("sample_provenance", "display_interpolated")]
)
def test_corrupt_or_visual_only_endpoint_rejected(tmp_path, field, value):
    path = write_trace(tmp_path)
    frame = pd.read_csv(path).astype(object)
    frame.loc[1, field] = value
    frame.to_csv(path, index=False)
    with pytest.raises(AssertionError):
        report.load_trace(tmp_path)


def test_retained_nested_numpy_bool_export_defect_is_reproducible(tmp_path):
    # Diagnostic only: NOT a repaired adapter or a successful scientific package.
    from task007dvis.export import csv_rows

    with pytest.raises(TypeError, match="not JSON serializable"):
        csv_rows(tmp_path / "event.csv", [dict(payload=dict(valid_domain=np.bool_(False)))])
