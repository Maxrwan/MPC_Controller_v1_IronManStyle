"""Strict closed-schema scientific evidence with bounded append-only writes."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Mapping

from .contracts import (
    CandidateBinding,
    EvidenceRecord,
    EvidenceWriter,
    FileReceipt,
    JsonValue,
    Outcome,
    RunIndex,
    SchemaIssue,
    StreamKind,
    Termination,
)

STREAMS = {
    "manifest": "run_manifest.json",
    "environment": "source_environment.json",
    "qualification": "panel.jsonl",
    "linearization": "linearizations.jsonl",
    "finite_difference": "finite_differences.jsonl",
    "linear_system": "linear_systems.jsonl",
    "riccati": "riccati.jsonl",
    "closed_loop": "closed_loop.jsonl",
    "product": "products.jsonl",
    "defect": "defects.jsonl",
    "event": "events.jsonl",
    "resource": "resources.jsonl",
    "coverage": "coverage.json",
    "index": "index.json",
}


def _json_equal(a, b):
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


def _schema_check(value, schema, root, path="$"):
    if "$ref" in schema:
        if not schema["$ref"].startswith("#/"):
            raise ValueError("External schemas prohibited")
        target = root
        for part in schema["$ref"][2:].split("/"):
            target = target[part.replace("~1", "/").replace("~0", "~")]
        _schema_check(value, target, root, path)
    if "const" in schema and not _json_equal(value, schema["const"]):
        raise ValueError(path + ":const")
    if "enum" in schema and not any(_json_equal(value, v) for v in schema["enum"]):
        raise ValueError(path + ":enum")
    if "type" in schema:
        allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        kinds = {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "boolean": isinstance(value, bool),
            "null": value is None,
            "integer": isinstance(value, int) and not isinstance(value, bool),
            "number": isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value),
        }
        if not any(kinds[k] for k in allowed):
            raise ValueError(path + ":type")
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        raise ValueError(path + ":pattern")
    if isinstance(value, dict):
        if not set(schema.get("required", ())) <= set(value):
            raise ValueError(path + ":required")
        if schema.get("additionalProperties") is False and not set(value) <= set(
            schema.get("properties", {})
        ):
            raise ValueError(path + ":additionalProperties")
        for k, v in value.items():
            if k in schema.get("properties", {}):
                _schema_check(v, schema["properties"][k], root, path + "/" + k)
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 10**9):
            raise ValueError(path + ":array count")
        for i, v in enumerate(value):
            if "items" in schema:
                _schema_check(v, schema["items"], root, path + "/" + str(i))
    for mode in ("allOf", "anyOf", "oneOf"):
        if mode not in schema:
            continue
        hits = 0
        for child in schema[mode]:
            try:
                _schema_check(value, child, root, path)
                hits += 1
            except ValueError:
                pass
        if not (
            hits == len(schema[mode])
            if mode == "allOf"
            else hits >= 1
            if mode == "anyOf"
            else hits == 1
        ):
            raise ValueError(path + ":" + mode)
    if "if" in schema:
        try:
            _schema_check(value, schema["if"], root, path)
            matched = True
        except ValueError:
            matched = False
        if matched and "then" in schema:
            _schema_check(value, schema["then"], root, path)
        elif not matched and "else" in schema:
            _schema_check(value, schema["else"], root, path)


def _semantic(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("No NaN/Infinity evidence")
    if isinstance(value, dict):
        if {"rows", "cols", "values", "entry_units"} <= set(value):
            r, c = value["rows"], value["cols"]
            if (
                r < 0
                or c < 0
                or len(value["values"]) != r
                or any(len(row) != c for row in value["values"])
            ):
                raise ValueError("Matrix dimensions")
            for field, n in [
                ("row_names", r),
                ("column_names", c),
                ("row_units", r),
                ("column_units", c),
            ]:
                if len(value[field]) != n:
                    raise ValueError("Matrix metadata dimensions")
            if len(value["entry_units"]) != r or any(len(row) != c for row in value["entry_units"]):
                raise ValueError("Matrix entry-unit dimensions")
        if "gain_grid_slots_before_dedup" in value and value["gain_grid_slots_before_dedup"] > 960:
            raise ValueError("Gain slot cap")
        if "per_candidate_status" in value:
            ids = value["candidate_ids"]
            if (
                len(set(ids)) != 12
                or [p["candidate_id"] for p in value["per_candidate_status"]] != ids
            ):
                raise ValueError("Panel membership/denominator")
        if "norm_scope" in value and value["norm_scope"] == "COMPLETED_PREFIX_ONLY":
            if value["endpoint_norm"] is not None or value["Phi_endpoint"] is not None:
                raise ValueError("Censored requested endpoint backfilled")
        if {"start_index_inclusive", "end_index_exclusive"} <= set(value) and value[
            "end_index_exclusive"
        ] < value["start_index_inclusive"]:
            raise ValueError("Reversed coverage interval")
        for child in value.values():
            _semantic(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _semantic(child)


def validate_record(record: Mapping[str, JsonValue], schema_path: Path) -> tuple[SchemaIssue, ...]:
    try:
        _semantic(record)
        schema = json.loads(Path(schema_path).read_text())
        _schema_check(record, schema, schema)
        if not re.fullmatch("[0-9a-f]{64}", record["context"]["source_binding_set_sha256"]):
            raise ValueError("Missing binding set SHA")
        return ()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return (SchemaIssue("$", "schema/semantic", str(exc)),)


def append_record(
    writer: EvidenceWriter, stream: StreamKind, record: EvidenceRecord
) -> Outcome[FileReceipt]:
    try:
        if stream not in STREAMS:
            raise ValueError("Unknown evidence stream")
        seen = getattr(writer, "_record_ids", set())
        if record["record_id"] in seen:
            raise ValueError("Duplicate evidence record ID")
        issues = validate_record(record, writer.schema_path)
        if issues:
            raise ValueError("; ".join(i.detail for i in issues))
        if record["record_type"] != stream or record["run_id"] != writer.run_id:
            raise ValueError("Stream/run identity mismatch")
        payload = (json.dumps(record, allow_nan=False, separators=(",", ":")) + "\n").encode()
        if writer.budget_token is not None:
            writer.budget_token.poll()
        existing = sum(p.stat().st_size for p in writer.root.rglob("*") if p.is_file())
        if existing + len(payload) > 1073741824:
            raise ValueError("Output reservation exhausted")
        path = (writer.root / STREAMS[stream]).resolve()
        if not path.is_relative_to(writer.root.resolve()):
            raise ValueError("Output path escape")
        if path.suffix == ".json" and path.exists():
            raise ValueError("Single-record stream cannot overwrite")
        # Singleton JSON is published atomically; the supervisor never reads a half manifest.
        if path.suffix == ".json":
            temporary = path.with_name("." + path.name + "." + str(os.getpid()) + ".tmp")
            try:
                with temporary.open("xb") as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
                os.link(temporary, path)  # Atomic create; never overwrite another record.
            finally:
                if temporary.exists():
                    temporary.unlink()
        else:
            if path.exists() and path.stat().st_size:
                with path.open("rb") as f:
                    f.seek(-1, 2)
                    if f.read(1) != b"\n":
                        raise ValueError("Refuse append after an incomplete JSONL tail")
            with path.open("ab") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
        # One owner per stream: incremental hashes avoid rereading growing scientific logs.
        hashes = getattr(writer, "_stream_hashes", {})
        prior = next((r for r in writer.receipts if r.path == path.name), None)
        if path.name in hashes:
            digest = hashes[path.name]
            digest.update(payload)
        else:
            digest = hashlib.sha256()
            with path.open("rb") as f:
                for block in iter(lambda: f.read(65536), b""):
                    digest.update(block)
            hashes[path.name] = digest
        writer._stream_hashes = hashes
        receipt = FileReceipt(
            path.name,
            digest.hexdigest(),
            path.stat().st_size,
            (prior.complete_records + 1) if prior else 1,
            0,
        )
        seen.add(record["record_id"])
        writer._record_ids = seen
        writer.bytes_written += len(payload)
        writer.receipts = tuple(r for r in writer.receipts if r.path != receipt.path) + (receipt,)
        return Outcome.available(receipt)
    except (OSError, ValueError, TimeoutError) as exc:
        return Outcome.unavailable("EVIDENCE_WRITE_FAILED", str(exc))


def finalize_run(
    writer: EvidenceWriter, panel: tuple[CandidateBinding, ...], termination: Termination
) -> Outcome[RunIndex]:
    try:
        measurements = getattr(writer, "_final_measurements", None)
        if measurements is None:
            raise ValueError("Actual supervisor wall/RSS observations required")
        receipts = []
        from time import monotonic

        deadline = getattr(writer, "_final_deadline", None)
        for p in sorted(writer.root.rglob("*")):
            if not p.is_file() or p.name == "index.json":
                continue
            digest = hashlib.sha256()
            size = 0
            complete = 0
            tail = 0
            with p.open("rb") as stream:
                for block in iter(lambda: stream.read(65536), b""):
                    if deadline is not None and monotonic() >= deadline:
                        raise ValueError(
                            "Final index resource-censored; completed streams retained"
                        )
                    digest.update(block)
                    size += len(block)
            if p.suffix == ".jsonl":
                valid_end = 0
                with p.open("rb") as stream:
                    for line in stream:
                        if deadline is not None and monotonic() >= deadline:
                            raise ValueError("Final index resource-censored")
                        if not line.endswith(b"\n"):
                            break
                        try:
                            json.loads(line)
                        except ValueError:
                            break
                        complete += 1
                        valid_end += len(line)
                tail = size - valid_end
            elif p.suffix == ".json":
                try:
                    json.loads(p.read_text())
                    complete = 1
                except ValueError:
                    tail = size
            receipts.append(
                {
                    "path": str(p.relative_to(writer.root)),
                    "sha256": digest.hexdigest(),
                    "bytes": size,
                    "complete_JSONL_records": complete,
                    "truncated_tail_bytes": tail,
                }
            )
        return Outcome.available(
            {
                "run_id": writer.run_id,
                "termination": termination,
                "files": receipts,
                "coverage_record_id": writer.run_id + ":coverage",
                "wall_elapsed_s": measurements["wall_elapsed_s"],
                "peak_observed_worker_rss_bytes": measurements["peak_observed_worker_rss_bytes"],
                "full_acceptance_claim": False,
            }
        )
    except (OSError, ValueError, KeyError) as exc:
        return Outcome.unavailable("FINALIZATION_FAILED", str(exc))


def _matrix(
    array,
    row_names=None,
    column_names=None,
    row_units=None,
    column_units=None,
    normalization="DIMENSIONAL",
):
    """Serialization only; caller supplies correct dimensions and units."""
    values = array.tolist() if hasattr(array, "tolist") else array
    r = len(values)
    c = len(values[0]) if r else len(column_names or ())
    rn = list(row_names or [str(i) for i in range(r)])
    cn = list(column_names or [str(i) for i in range(c)])
    ru = list(row_units or ["1"] * r)
    cu = list(column_units or ["1"] * c)
    return {
        "rows": r,
        "cols": c,
        "row_names": rn,
        "column_names": cn,
        "row_units": ru,
        "column_units": cu,
        "entry_units": [[a + "/" + b for b in cu] for a in ru],
        "values": values,
        "normalization": normalization,
        "dtype": "float64",
    }
