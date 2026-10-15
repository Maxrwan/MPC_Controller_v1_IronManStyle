"""Scientific export checks independent of any Workbench UI/importer."""

import csv
import hashlib
import json
import math
from pathlib import Path

from apex.state import STATE_NAMES
from task007dvis.interface import REQUEST_COVERAGE, SCHEMA

REQUIRED = (
    "states",
    "segments",
    "controls",
    "planning",
    "cycles",
    "events",
    "boundaries",
    "metrics",
)


def validate(folder):
    folder = Path(folder)
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["schema"] == SCHEMA
    assert manifest["canonical_state"] == list(STATE_NAMES)
    assert manifest["controls"] == ["delta", "a_cmd"]
    assert manifest["request_coverage"] == REQUEST_COVERAGE
    assert (
        hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest()
        == (folder / "manifest.sha256").read_text().split()[0]
    )
    tables = {}
    for name in REQUIRED:
        with (folder / (name + ".csv")).open(newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames, name + " header missing"
            tables[name] = list(reader)
    for name, item in manifest["artifacts"].items():
        p = folder / name
        assert p.stat().st_size == item["bytes"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == item["sha256"]
        if item["rows"] is not None:
            with p.open(newline="") as f:
                assert sum(1 for _ in csv.DictReader(f)) == item["rows"]
    packets = json.loads((folder / "packets.json").read_text())
    ids = {p["plan_id"] for p in packets}
    intervals = manifest["accepted_authority_intervals"]
    previous = -math.inf
    for r in tables["states"]:
        t = float(r["time"])
        assert t >= previous
        previous = t
        assert r["sample_provenance"] == "native"
        assert all(math.isfinite(float(r[k])) for k in [*STATE_NAMES, "delta", "a_cmd"])
        assert int(r["plan_id"]) in ids
        candidates = [v for v in intervals if v["start"] <= t + 1e-10 and v["end"] >= t - 1e-10]
        if r.get("mode") == "trajectory":
            assert candidates and candidates[-1]["plan_id"] == int(r["plan_id"])
    for r in tables["controls"]:
        assert float(r["application_time"]) >= float(r["time"]) - 1e-10
        assert int(r["plan_id"]) in ids
        candidates = [v for v in intervals if v["start"] <= float(r["time"]) + 1e-10]
        assert candidates[-1]["plan_id"] == int(r["plan_id"])
    for r in tables["segments"]:
        assert float(r["dt"]) > 0
        assert abs(float(r["end"]) - float(r["start"]) - float(r["dt"])) < 1e-10
        assert len(json.loads(r["state_before"])) == len(json.loads(r["state_after"])) == 6
        assert len(json.loads(r["control"])) == 2
    for r in tables["events"]:
        assert int(r["phase"]) in range(1, 7)
        assert r["within_phase_order"] == ""
        assert json.loads(r["missing_reasons"])["within_phase_order"] == "ordering_not_recorded"
    for r in tables["metrics"]:
        assert r["metric_definition_id"] in manifest["metric_definitions"]
        assert r["aggregation_scope"] in ("run", "lap", "sector", "common_time", "common_progress")
        assert r["sample_provenance"] != "display_interpolated"
    for r in tables["cycles"]:
        if r["status"] == "missed":
            assert r["t_accept"] == ""
            assert not any(v["plan_id"] == int(r["plan_id"]) for v in intervals)
        if manifest["architecture"] == "A":
            assert r["valid_from"] == ""
    return dict(
        passed=True,
        rows={n: len(v) for n, v in tables.items()},
        artifacts=len(manifest["artifacts"]),
        acceptance="adapter_checks_only; Workbench_ingestion_pending",
    )
