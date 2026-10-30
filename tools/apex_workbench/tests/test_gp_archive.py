"""Pinned retained P evidence; disposable faults, no scientific execution or re-export."""

import csv
import hashlib
import json
import os
import shutil
from contextlib import contextmanager
from dataclasses import replace
from io import StringIO

import pandas as pd
import pytest

from tools.apex_workbench import gp_archive as gp
from tools.apex_workbench import jobs

TABLES = ("states", "controls", "planning", "cycles", "events")


@pytest.fixture(scope="module")
def original():
    # Real production trust chain; no mocked inventory, manifest or accepted source.
    return gp.read(tables=TABLES)


@pytest.fixture(scope="module")
def disposable(tmp_path_factory):
    # One archive copy for all negative cases; mutations below restore exact copied bytes.
    root = tmp_path_factory.mktemp("gp-evidence") / "controlled_A"
    shutil.copytree(gp.DIRECTORY, root)
    return root


@contextmanager
def changed_files(root, changes):
    originals = {name: (root / name).read_bytes() for name in changes}
    try:
        for name, content in changes.items():
            path = root / name
            if content is None:
                path.unlink()
            else:
                path.write_bytes(content)
        yield
    finally:
        for name, content in originals.items():
            path = root / name
            if path.is_symlink():
                path.unlink()
            path.write_bytes(content)


def native_rows(snapshot, table):
    return list(csv.DictReader(StringIO(snapshot.contents[f"scientific/{table}.csv"].decode())))


def test_real_archive_identity_coverage_and_historical_limits(original):
    assert len(original.inventory) == 25
    assert original.manifest["schema"] == "apex-run/0.1.0"
    assert original.manifest["run_id"] == "controlled_A"
    assert original.manifest["architecture"] == "A"
    provenance = original.manifest["provenance"]
    assert provenance["scientific_revision"] == gp.REVISION
    assert provenance["export_revision"] == gp.REVISION
    assert len(provenance["scientific_source_sha256"]) == 294
    assert {name: len(frame) for name, frame in original.frames.items()} == {
        "states": 12448,
        "controls": 6223,
        "planning": 3097,
        "cycles": 622,
        "events": 14310,
    }
    assert original.manifest["field_provenance"]["world_coordinates"] == "reconstructed"
    assert original.manifest["field_provenance"]["reference_sampling"] == "reconstructed"
    assert (
        original.manifest["review_status"] == "candidate_pending_representative_Workbench_ingestion"
    )
    assert original.frames["states"].iloc[-1]["time"] == 62.23500000000001


def test_native_csv_values_and_control_application_clock_are_preserved(original):
    for table, columns in (
        ("states", ("time", *gp.CORE, "x_world", "planning_x", "reference_x")),
        ("controls", ("time", "application_time", "delta", "a_cmd", "reference_r")),
    ):
        rows = native_rows(original, table)
        for index in (0, 1, len(rows) // 2, len(rows) - 1):
            for channel in columns:
                assert original.frames[table].iloc[index][channel] == float(rows[index][channel])
    first = original.frames["controls"].iloc[0]
    assert first["time"] == 0.0 and first["application_time"] == 0.005
    assert first["physical_latency"] == 0.005
    assert first["delta"] == 0.054923548927100344
    assert original.frames["states"].iloc[0]["vx"] == 5.253846582838669


def test_native_events_keep_payload_partial_order_and_solver_meaning(original):
    rows = native_rows(original, "events")
    events = original.frames["events"]
    for index in (0, 29, len(rows) - 1):
        row = rows[index]
        actual = events.iloc[index]
        assert actual["time"] == float(row["time"])
        assert actual["event_kind"] == row["event_kind"]
        assert actual["source_stream"] == row["source_stream"]
        assert actual["source_row"] == int(row["source_row"])
        assert actual["payload"] == row["payload"]
    first = events.iloc[0]
    assert first["event_kind"] == "command_computed"
    assert first["phase"] == 5 and pd.isna(first["within_phase_order"])
    assert first["ordering_status"] == "phase_known_cross_stream_tie_unspecified"
    ready = events.iloc[29]
    assert ready["time"] == 0.135 and ready["event_kind"] == "preparation_ready"
    assert json.loads(ready["payload"])["status"] == "Solve_Succeeded"
    cycle = original.frames["cycles"].iloc[0]
    assert cycle["status"] == "accepted"  # Packet outcome, not the solver status.
    assert pd.isna(cycle["valid_from"])
    assert json.loads(cycle["missing_reasons"])["valid_from"] == "not_applicable"


def test_sector_views_preserve_native_rows_and_full_identity(original):
    before_manifest = json.dumps(original.manifest, sort_keys=True)
    sectors = original.fixture["sectors"]
    assert gp.sector_names(original) == [row["name"] for row in sectors]
    for index, sector in enumerate(sectors):
        start = sector["start_s_m"]
        end = (
            sectors[index + 1]["start_s_m"]
            if index + 1 < len(sectors)
            else original.fixture["closed_track_length_m"]
        )
        states = original.frames["states"]
        progress = states["s_abs"] % original.fixture["closed_track_length_m"]
        expected = states.loc[(progress >= start) & (progress < end)]
        actual = gp.sector_frame(original, "states", sector["name"])
        pd.testing.assert_frame_equal(actual, expected)
        assert actual["run_id"].eq("controlled_A").all()
        assert actual["export_row"].tolist() == expected["export_row"].tolist()
    assert json.dumps(original.manifest, sort_keys=True) == before_manifest
    pd.testing.assert_frame_equal(gp.sector_frame(original, "states"), original.frames["states"])


def test_sector_boundary_rule_is_half_open_without_interpolation(original):
    # Literal row-mapping fixture tests endpoints; it is not scientific telemetry.
    sectors = original.fixture["sectors"]
    boundary = sectors[1]["start_s_m"]
    length = original.fixture["closed_track_length_m"]
    frame = pd.DataFrame({"s_abs": [0.0, boundary, length], "export_row": [7, 8, 9]})
    fixture = replace(original, frames={"states": frame})
    assert gp.sector_frame(fixture, "states", sectors[0]["name"])["export_row"].tolist() == [7, 9]
    assert gp.sector_frame(fixture, "states", sectors[1]["name"])["export_row"].tolist() == [8]
    with pytest.raises(gp.ArchiveError, match="native sector progress"):
        gp.sector_frame(original, "controls", sectors[0]["name"])
    with pytest.raises(gp.ArchiveError, match="Unsupported"):
        gp.read(tables=("invented_telemetry",))


def test_units_do_not_turn_unknown_channels_into_declared_si():
    assert gp.unit("r") == gp.unit("reference_r") == gp.unit("planning_error_r") == "rad/s"
    assert gp.unit("delta") == "rad"
    assert gp.unit("a_cmd") == "m/s²"
    assert gp.unit("time") == gp.unit("application_time") == "s"
    assert gp.unit("made_up_score") == "unit undeclared"


def test_identical_copy_is_same_historical_execution_and_original_is_read_only(
    original, disposable
):
    copied = gp.read(disposable, tables=())
    assert copied.directory != original.directory
    assert copied.manifest == original.manifest
    assert copied.inventory == original.inventory
    assert copied.manifest["run_id"] == original.manifest["run_id"] == "controlled_A"
    assert original.current() is True


@pytest.mark.parametrize("fault", ("missing", "corrupt", "source_resealed", "schedule"))
def test_disposable_missing_corrupt_resealed_source_and_schedule_are_rejected(disposable, fault):
    if fault == "missing":
        changes = {"scientific/events.csv": None}  # Required even when not parsed.
    elif fault == "corrupt":
        content = (disposable / "scientific/states.csv").read_bytes()
        replacement = content.replace(b"5.253846582838669", b"5.353846582838669", 1)
        assert replacement != content and len(replacement) == len(content)
        changes = {"scientific/states.csv": replacement}
    elif fault == "source_resealed":
        manifest = json.loads((disposable / "scientific/manifest.json").read_bytes())
        manifest["provenance"]["scientific_revision"] = "0" * 40
        content = json.dumps(manifest).encode()
        changes = {
            "scientific/manifest.json": content,
            "scientific/manifest.sha256": hashlib.sha256(content).hexdigest().encode() + b"\n",
        }
    else:
        config = json.loads((disposable / "input_configuration.json").read_bytes())
        config["simulation"]["codriver_delay"] = 0.0
        changes = {"input_configuration.json": json.dumps(config).encode()}
    with changed_files(disposable, changes):
        with pytest.raises((gp.ArchiveError, OSError)):
            gp.read(disposable, tables=())


def test_current_rehash_rejects_same_size_and_restored_mtime_replacement(disposable):
    snapshot = gp.read(disposable, tables=())
    path = disposable / "scientific/states.csv"
    stat = path.stat()
    content = path.read_bytes()
    replacement = content.replace(b"5.253846582838669", b"5.353846582838669", 1)
    with changed_files(disposable, {"scientific/states.csv": replacement}):
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        assert path.stat().st_size == stat.st_size
        assert path.stat().st_mtime_ns == stat.st_mtime_ns
        with pytest.raises(gp.ArchiveError, match="checksum"):
            snapshot.current()


def test_linked_artifact_and_linked_archive_are_withheld(disposable, tmp_path):
    original = disposable / "scientific/events.csv"
    target = tmp_path / "outside-events.csv"
    target.write_bytes(original.read_bytes())
    with changed_files(disposable, {"scientific/events.csv": None}):
        original.symlink_to(target)
        with pytest.raises(gp.ArchiveError, match="Linked"):
            gp.read(disposable, tables=())
    linked = tmp_path / "linked-archive"
    linked.symlink_to(disposable, target_is_directory=True)
    with pytest.raises(gp.ArchiveError, match="Unsafe|Linked"):
        gp.read(linked, tables=())


def test_archive_reader_never_calls_worker_lifecycle(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Read-only GP archive inspection invoked worker lifecycle")

    for name in ("start_run", "status_for", "cancel_run"):
        monkeypatch.setattr(jobs, name, forbidden)
    snapshot = gp.read(tables=())
    assert snapshot.current() is True
