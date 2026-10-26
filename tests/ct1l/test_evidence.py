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


def test_broken_common_evidence_stops_candidate_dispatch(monkeypatch):
    from types import SimpleNamespace

    import ct1.worker as worker
    import pytest
    from ct1.contracts import Outcome

    writer = SimpleNamespace(budget_token=None)
    monkeypatch.setattr(
        worker,
        "append_record",
        lambda *a: Outcome.unavailable("EVIDENCE_WRITE_FAILED", "literal closed-schema mismatch"),
    )
    visits = []
    local = []

    class Token:
        def poll(self):
            pass

    def run(candidate):
        visits.append(candidate)
        worker._append_or_stop(writer, "event", {"literal": "not accepted by fake producer"})

    with pytest.raises(worker._EvidenceIntegrityFailure):
        worker._run_independent(
            ("first", "must_not_run"),
            run,
            lambda *a: local.append(a),
            scope="CANDIDATE",
            budget=Token(),
        )
    assert visits == ["first"] and local == [] and writer._integrity_failed


def test_partial_selected_coverage_counts_omissions_separately():
    from types import SimpleNamespace

    from ct1.closed_loop import _product_selection
    from ct1.worker import _missing_selected_products

    seq = tuple(
        SimpleNamespace(
            time_s=i / 100,
            next_time_s=(i + 1) / 100,
            original_gain_index=i,
            authority_scope="DESIGN_CONDITIONAL",
        )
        for i in range(3)
    )
    design = _product_selection(seq, "TOY", "DESIGN_CONDITIONAL")
    observed = _product_selection((), "TOY", "OBSERVED_AUTHORITY")
    # Four selected intervals * three subsystems * four normalizations = 48.
    # One completed original endpoint leaves 47 missing, not the two deliberately omitted windows.
    completed = {("DESIGN_CONDITIONAL", "full", "nominal_scaled", 0)}
    missing = _missing_selected_products(
        {"DESIGN_CONDITIONAL": design, "OBSERVED_AUTHORITY": observed}, completed
    )
    assert len(missing) == 47
    assert design["omitted_interval_count"] == 2
    assert all(row["population"] == "DESIGN_CONDITIONAL" for row in missing)
    assert not any(
        (row["population"], row["subsystem"], row["normalization"], row["selected_interval_index"])
        in completed
        for row in missing
    )
    assert len(completed) == 1  # Failed/missing endpoints never replace completed evidence.
