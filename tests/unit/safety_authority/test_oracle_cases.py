"""Protocol cases plus an explicit unresolved full-trace readiness gate."""

import pytest
from oracle_support import assert_projection, cases, load, run_case

PROTOCOL_CASES = [c for c in cases() if c["case_id"].startswith("E")]


@pytest.mark.parametrize("case", PROTOCOL_CASES, ids=[c["case_id"] for c in PROTOCOL_CASES])
def test_reviewed_protocol_projection(case):
    initial, result = run_case(case)
    assert_projection(case, initial, result)


def test_independent_full_trace_materialization_entry_gate():
    data = load("expected_traces")
    assert data["full_trace_status"] == "INDEPENDENTLY_REVIEWED", data["unresolved_findings"]
    assert set(data["full_trace_cases"]) == {c["case_id"] for c in cases()}


def test_original_map_scenario_literal_materialization():
    from apex.safety_authority import records as r
    from apex.safety_authority.codec import (
        decode_configuration,
        decode_event,
        decode_snapshot,
        freeze,
    )
    from apex.safety_authority.ordering import seal_batch
    from apex.safety_authority.reducer import reduce_batch

    material = load("cases")["original_materializations"][0]
    cfg = decode_configuration(freeze(load("configurations")[material["configuration_key"]]))
    assert isinstance(cfg, r.DecodeSuccess)
    saved = decode_snapshot(
        freeze(load("snapshots")[material["initial_snapshot_key"]]), configuration=cfg.value
    )
    assert isinstance(saved, r.DecodeSuccess)
    snapshot = saved.value
    projections = load("expected_traces")["original_materialization_projections"][
        material["case_id"]
    ]
    for index, (step, expected) in enumerate(zip(material["steps"], projections)):
        decoded = [decode_event(freeze(e), configuration=cfg.value) for e in step["events"]]
        assert all(isinstance(e, r.DecodeSuccess) for e in decoded)
        sealed = seal_batch(
            cfg.value,
            snapshot,
            batch_id="original-map-" + str(index),
            at_tick=step["at_tick"],
            events=tuple(e.value for e in decoded),
        )
        assert isinstance(sealed, r.DecodeSuccess)
        result = reduce_batch(cfg.value, snapshot, sealed.value)
        assert result.snapshot.state == expected["state"]
        assert result.snapshot.desired_epoch == expected["desired_epoch"]
        assert [t.transition_id for t in result.transitions] == expected["transition_path"]
        assert any(
            t.decision == expected["decision"] and list(t.reason_codes) == expected["reason_codes"]
            for t in result.traces
        )
        assert not any(t.granted_permission_ids for t in result.traces)
        assert result.endpoint_outputs == ()
        snapshot = result.snapshot
