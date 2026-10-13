"""Offline evidence conventions: angles, coverage and no fabricated authority timestamps."""

import importlib
import sys
from math import pi
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
analysis = importlib.import_module("task007dc.analysis")


def test_paired_rows_wrap_heading_and_restrict_observed_coverage():
    a = [dict(time=0, angle=pi - 0.01), dict(time=0.01, angle=1.0), dict(time=0.02, angle=3.0)]
    b = [dict(time=0, angle=-pi + 0.01), dict(time=0.01, angle=1.0)]
    result = analysis.paired_rows(a, b, ["angle"], angle_columns=(0,))
    assert result["count"] == 2 and result["end"] == 0.01
    assert result["metrics"]["angle"]["max_abs"] == pytest.approx(0.02, abs=1e-12)
    assert result["first_difference"]["time"] == 0
    assert a[-1]["angle"] == 3.0  # inputs unchanged


def test_common_grid_excludes_off_grid_readiness_sample():
    rows = [dict(time=t, x=t) for t in [0, 0.003, 0.01, 0.015, 0.02]]
    result = analysis.paired_rows(rows, rows, ["x"], grid=True)
    assert result["count"] == 3 and result["bitwise_values_equal"]
    assert result["first_difference"] is None
    assert analysis.paired_rows([], rows, ["x"])["metrics"] is None


def test_readiness_does_not_fabricate_acceptance():
    raw = dict(
        plans=[
            {},
            dict(
                plan_id=1,
                release_time=0.1,
                completion_time=0.14,
                completed=True,
                physical_delay=0.04,
                predicted_completion_time=0.15,
            ),
        ],
        handoffs=[],
        packets=[],
        controls=[],
    )
    row = analysis.cycles(raw)[0]
    assert row["t_ready"] == 0.14
    assert row["t_accept"] is None and row["first_TVLQR_use"] is None
    assert row["valid_from"] is None and row["deadline_margin"] is None
    assert row["status"] == "pending"


def test_heading_variation_wraps_each_step():
    assert analysis.tv([pi - 0.01, -pi + 0.01], True) == pytest.approx(0.02, abs=1e-12)


def test_optional_fixed_metadata_round_trips_without_changing_legacy_records(
    dynamic_vehicle, straight_geometry
):
    from task007d.forensics import packet_from_record
    from test_fixed_handoff_scheduler import simulate

    for offset in [None, 0.07]:
        result = simulate(dynamic_vehicle, straight_geometry, offset=offset, duration=0.2)
        record = result["packets"][1]
        assert ("valid_from" in record) is (offset is not None)
        assert packet_from_record(record).as_dict() == record
