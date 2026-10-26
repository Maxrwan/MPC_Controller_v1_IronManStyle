"""O00/O19 strict schemas, numeric nulls and honest censored coverage."""

import json
from pathlib import Path


def test_evidence_rejects_nonfinite_and_backfilled_prefix():
    import pytest
    from ct1.evidence import _semantic

    with pytest.raises(ValueError):
        _semantic({"value": float("nan")})
    with pytest.raises(ValueError):
        _semantic(
            {"norm_scope": "COMPLETED_PREFIX_ONLY", "endpoint_norm": 1.0, "Phi_endpoint": None}
        )
    with pytest.raises(ValueError):
        _semantic(
            {
                "total_candidates": 12,
                "candidate_ids": ["same"] * 12,
                "per_candidate_status": [{"candidate_id": "same"}] * 12,
            }
        )


def test_closed_schema_and_complex_representation():
    import pytest
    from ct1.evidence import _schema_check

    schema = json.loads(
        (
            Path(__file__).resolve().parents[2] / "docs/ct1/ct1l/scientific_evidence.schema.json"
        ).read_text()
    )
    _schema_check({"re": 1.0, "im": 0.0}, schema["$defs"]["complex"], schema)
    with pytest.raises(ValueError):
        _schema_check({"re": 1.0, "im": 0.0, "extra": 1}, schema["$defs"]["complex"], schema)


def test_truncated_record_tail_retained(tmp_path):
    from ct1.contracts import EvidenceWriter
    from ct1.evidence import finalize_run

    writer = EvidenceWriter(tmp_path, Path("unused"), "TEST")
    (tmp_path / "events.jsonl").write_bytes(b'{"a":1}\n{"partial":')
    writer._final_measurements = {"wall_elapsed_s": 0.1, "peak_observed_worker_rss_bytes": 1024}
    result = finalize_run(writer, (), "RESOURCE_CENSORED").unwrap()
    row = result["files"][0]
    assert row["complete_JSONL_records"] == 1 and row["truncated_tail_bytes"] > 0
