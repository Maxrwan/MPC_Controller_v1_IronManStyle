"""Independent literal expectations, real retained bytes and disposable faults; no producer."""

import ast
import hashlib
import html
import json
import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from tools.apex_workbench import c0_archive as c0
from tools.apex_workbench import c0_panels

TOKENS = {
    "/fixed_handoffs/0/valid_from": "0.17",
    "/fixed_handoffs/1/valid_from": "0.33",
    "/fixed_handoffs/0/t_ready": "0.255",
    "/fixed_handoffs/1/t_ready": "0.41500000000000004",
    "/fixed_handoffs/0/late_discard_time": "0.255",
    "/fixed_handoffs/1/late_discard_time": "0.41500000000000004",
    "/urgent_demands/0/trigger_time": "0.16",
    "/urgent_demands/0/eligible_time": "0.255",
    "/urgent_demands/0/release_time": "0.26",
    "/urgent_demands/0/planner_busy_wait": "0.095",
    "/urgent_demands/0/grid_alignment_wait": "0.0050000000000000044",
    "/misses/0/time": "0.2",
    "/misses/1/time": "0.3",
    "/misses/2/time": "0.4",
    "/fallbacks/0/time": "0.4",
    "/end_time": "0.6",
    "/states/0/time": "0.0",
    "/reserves/0/time": "0.0",
    "/controls/0/time": "0.0",
    "/states/119/time": "0.595",
    "/reserves/119/time": "0.595",
    "/controls/59/time": "0.59",
    "/plans/0/release_time": "0",
    "/controls/0/acceleration_correction": "-0.0",
    "/packets/0/solve_duration": "0.01",
}
NULLS = [
    "/fixed_handoffs/0/t_accept",
    "/fixed_handoffs/1/t_accept",
    "/fixed_handoffs/0/first_TVLQR_use",
    "/fixed_handoffs/1/first_TVLQR_use",
    "/urgent_demands/0/trigger_to_authority",
    "/urgent_demands/0/accepted_time",
    "/urgent_demands/0/accepted_plan_id",
]


@pytest.fixture(scope="module")
def original():
    return c0.read()


@pytest.fixture
def disposable(tmp_path, monkeypatch):
    for relative in [c0.RELATIVE, *c0.ANCHORS]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(c0.ROOT / relative, target)
    monkeypatch.setattr(c0, "ROOT", tmp_path)
    return tmp_path


def at(data, pointer):
    for key in pointer.strip("/").split("/"):
        data = data[int(key)] if isinstance(data, list) else data[key]
    return data


def test_exact_identity_complete_raw_tokens_and_no_new_execution(original):
    assert len(original.raw) == 152600
    assert hashlib.sha256(original.raw).hexdigest() == (
        "2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5"
    )
    # Independent parser checks EVERY numeric token, not the adapter's generated expectations.
    expected = json.loads(original.raw, parse_int=str, parse_float=str)

    def compare(actual, reference):
        if isinstance(actual, c0.Number):
            assert actual.token == reference
        elif isinstance(actual, dict):
            assert list(actual) == list(reference)
            for key in actual:
                compare(actual[key], reference[key])
        elif isinstance(actual, list):
            assert len(actual) == len(reference)
            for a, b in zip(actual, reference):
                compare(a, b)
        else:
            assert type(actual) is type(reference) and actual == reference

    compare(original.data(), expected)
    meta = c0_panels.provenance()
    assert meta["G1"] == "OPEN" and meta["classification"] == "descriptive_only / source_unverified"
    assert "not a new execution" in meta["execution_identity"]


@pytest.mark.parametrize("pointer,token", TOKENS.items())
def test_independently_recorded_literal_examples(original, pointer, token):
    number = at(original.data(), pointer)
    assert isinstance(number, c0.Number) and number.token == token
    assert c0.literal(number) == token


@pytest.mark.parametrize("pointer", NULLS)
def test_present_null_preserves_pointer(original, pointer):
    assert at(original.data(), pointer) is None
    rows = {row["pointer"]: row for row in c0.missingness(original.data())}
    assert rows[pointer] == {"pointer": pointer, "presence": "present-null", "json_literal": "null"}


@pytest.mark.parametrize("pointer", ["/packets/0/valid_from", "/triggers/0/busy"])
def test_absent_is_not_present_null(original, pointer):
    parent, key = pointer.rsplit("/", 1)
    assert key not in at(original.data(), parent)
    rows = {row["pointer"]: row for row in c0.missingness(original.data())}
    assert rows[pointer]["presence"] == "absent"
    assert rows[pointer]["json_literal"] == "[absent — no JSON member]"


def test_original_keys_conditional_shapes_and_coverage(original):
    d = original.data()
    assert [len(d[k]) for k in ["states", "controls", "reserves", "plans", "packets"]] == [
        120,
        60,
        120,
        3,
        3,
    ]
    assert all(
        {"time", "application_time", "physical_latency"} <= row.keys() for row in d["controls"]
    )
    assert all("latency" not in row for row in d["controls"])
    assert "physical_delay" not in d["plans"][0] and "physical_delay" in d["plans"][1]
    assert "valid_from" not in d["packets"][0] and "valid_from" in d["packets"][1]
    for packet in d["packets"]:
        assert len(packet["timestamps"]) == 5 and len(packet["states"]) == 5
        assert all(len(row) == 6 for row in packet["states"])
        assert len(packet["controls"]) == 4 and all(len(row) == 2 for row in packet["controls"])
        assert len(packet["gains"]) == 4 and all(len(row) == 4 for row in packet["gains"])
        assert packet["curvatures"] == []
    assert all(d[k] == [] for k in ["handoffs", "lap_times", "codriver_misses"])
    assert (
        at(d, "/states/0/time").kind == "real" and at(d, "/plans/0/release_time").kind == "integer"
    )


def test_literal_chronology_keeps_stream_identity_and_unknown_ties(original):
    rows = c0.chronology(original.data())
    for collection in c0.CHRONOLOGY_FIELDS:
        indices = [row["source_row"] for row in rows if row["collection"] == collection]
        assert indices == sorted(indices)  # No global time sort or reclassification.
    lookup = {row["pointer"]: row["json_literal"] for row in rows}
    assert lookup["/fixed_handoffs/1/t_ready"] == "0.41500000000000004"
    assert lookup["/misses/2/time"] == lookup["/fallbacks/0/time"] == "0.4"
    assert lookup["/fixed_handoffs/0/t_accept"] == "null"
    assert lookup["/packets/0/valid_from"] == "[absent — no JSON member]"
    assert "unknown" in c0_panels.ORDERING and "no interpolation" in c0_panels.ORDERING


@pytest.mark.parametrize(
    "fault", ["missing", "changed", "malformed", "oversize", "directory", "symlink"]
)
def test_disposable_unsafe_or_altered_evidence_is_not_admitted(disposable, fault):
    p = disposable / c0.RELATIVE
    raw = p.read_bytes()
    p.unlink()
    if fault == "changed":
        p.write_bytes(raw.replace(b"0.41500000000000004", b"0.41500000000000005", 1))
    elif fault == "malformed":
        p.write_bytes(b"{" + b" " * (c0.SIZE - 1))
    elif fault == "oversize":
        p.write_bytes(raw + b" ")
    elif fault == "directory":
        p.mkdir()
    elif fault == "symlink":
        other = disposable / "other.json"
        other.write_bytes(raw)
        p.symlink_to(other)
    with pytest.raises((c0.ArchiveError, OSError)):
        c0.read()


@pytest.mark.parametrize("anchor", list(c0.ANCHORS))
def test_changed_contract_review_or_shape_quarantines(disposable, anchor):
    snapshot = c0.read()
    p = disposable / anchor
    p.write_bytes(p.read_bytes() + b" ")
    with pytest.raises(c0.ArchiveError):
        snapshot.current()
    with pytest.raises(c0.ArchiveError):
        c0.read()


def test_snapshot_and_same_size_mtime_changes_invalidate(disposable):
    snapshot = c0.read()
    p = disposable / c0.RELATIVE
    info = p.stat()
    p.write_bytes(p.read_bytes().replace(b"0.41500000000000004", b"0.41500000000000005", 1))
    os.utime(p, ns=(info.st_atime_ns, info.st_mtime_ns))
    with pytest.raises(c0.ArchiveError):
        snapshot.current()
    with pytest.raises(c0.ArchiveError):
        replace(snapshot, raw=b"{}").data()


def test_linked_root_and_alternate_filename_have_no_admission(disposable, monkeypatch, tmp_path):
    link = tmp_path / "linked-root"
    link.symlink_to(disposable, target_is_directory=True)
    monkeypatch.setattr(c0, "ROOT", link)
    with pytest.raises(c0.ArchiveError):
        c0.read()
    with pytest.raises(c0.ArchiveError):
        c0._path(disposable, "../original155.json")
    with pytest.raises(TypeError):
        c0.read(disposable / "other.json")


@pytest.mark.parametrize(
    "fault",
    [
        "null_absent",
        "bool_numeric",
        "integer_real",
        "extra_key",
        "dimensions",
        "duplicate",
        "nonfinite",
    ],
)
def test_structural_guard_independently_rejects_malformed_payload(original, fault):
    # Unit exercise of the second guard, not a resealed/admissible production archive.
    d = json.loads(original.raw)
    if fault == "null_absent":
        del d["fixed_handoffs"][0]["t_accept"]
    elif fault == "bool_numeric":
        d["controls"][0]["time"] = False
    elif fault == "integer_real":
        d["plans"][0]["release_time"] = 0.0
    elif fault == "extra_key":
        d["packets"][0]["valid_from"] = None
    elif fault == "dimensions":
        d["packets"][0]["gains"][0].append(0.0)
    raw = json.dumps(d).encode()
    if fault == "duplicate":
        raw = b'{"failure":null,' + raw[1:]
    elif fault == "nonfinite":
        raw = raw.replace(b'"vx": 2.0', b'"vx": NaN', 1)
    with pytest.raises(c0.ArchiveError):
        c0._parse(raw, original.shape)


def test_markers_keep_exact_tokens_no_geometry_or_inferred_inputs(original):
    data = original.data()
    plot = c0_panels.figure(data, "controls", "acceleration_correction")
    trace = plot.data[0]
    assert trace.mode == "markers" and len(trace.x) == 60 and trace.x[-1] == 0.59
    assert trace.customdata[0][2:4] == ["/controls/0/acceleration_correction", "-0.0"]
    assert (
        "not declared" in plot.layout.xaxis.title.text
        and "not declared" in plot.layout.yaxis.title.text
    )
    with pytest.raises(c0.ArchiveError):
        c0_panels.figure(data, "packets", "states")
    with pytest.raises(c0.ArchiveError):
        c0_panels.figure(data, "states", "world_X")


def test_standalone_html_retains_original_bytes_tokens_and_limits(original):
    content = c0_panels.report(original, "states", "vx").decode()
    assert html.escape(original.raw.decode()) in content
    assert html.escape(c0.BANNER) in content and "G1 OPEN" in content
    assert c0.SHA256 in content and c0.IDENTIFIER in content
    assert "present-null" in content and "[absent — no JSON member]" in content
    assert "unverified" in content and "not a new execution" in content
    assert "<script src=" not in content


def test_export_rechecks_real_disposable_replacement_after_serialization(disposable, monkeypatch):
    snapshot = c0.read()
    original = c0_panels.go.Figure.to_html

    def replacing(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        p = disposable / c0.RELATIVE
        p.write_bytes(p.read_bytes() + b" ")
        return result

    monkeypatch.setattr(c0_panels.go.Figure, "to_html", replacing)
    with pytest.raises(c0.ArchiveError):
        c0_panels.report(snapshot, "states", "vx")


def test_reader_dependency_boundary_has_no_scientific_or_execution_imports():
    tree = ast.parse(Path(c0.__file__).read_text())
    modules = [
        n.module if isinstance(n, ast.ImportFrom) else a.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for a in (n.names if isinstance(n, ast.Import) else [None])
    ]
    assert set(modules) <= {"hashlib", "json", "math", "stat", "dataclasses", "pathlib"}
