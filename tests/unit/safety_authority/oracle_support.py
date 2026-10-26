"""Independent literal expectations; implementation calls produce ACTUAL values only.

This file and every authored test are unexecuted. Full trace review remains a
separate entry gate. No golden result is derived from a reducer helper.
"""

import json
from decimal import Decimal
from pathlib import Path

from apex.safety_authority import records as r
from apex.safety_authority.codec import decode_configuration, decode_event, decode_snapshot, freeze
from apex.safety_authority.ordering import seal_batch
from apex.safety_authority.reducer import reduce_batch, reject_batch

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures/safety_authority/s1a"


def load(name):
    return json.loads((FIXTURES / (name + ".json")).read_text(), parse_float=Decimal)


def cases():
    return load("cases")["cases"]


def decode_inputs(case):
    cfg_data = load("configurations")[case["configuration_ref"].split("/")[-1]]
    snap_data = load("snapshots")[case["initial_snapshot_ref"].split("/")[-1]]
    cfg = decode_configuration(freeze(cfg_data))
    assert isinstance(cfg, r.DecodeSuccess), cfg
    snap = decode_snapshot(freeze(snap_data), configuration=cfg.value)
    assert isinstance(snap, r.DecodeSuccess), snap
    return cfg.value, snap.value


def run_case(case):
    cfg, snap = decode_inputs(case)
    events, failures = [], []
    for document in case["events"]:
        decoded = decode_event(freeze(document), configuration=cfg)
        if isinstance(decoded, r.DecodeFailure):
            failures.extend(decoded.errors)
        else:
            events.append(decoded.value)
    if case.get("entry_function") == "reject_batch":
        args = case["entry_arguments"]
        errors = tuple(r.InputError(**x) for x in args["errors"])
        return snap, reject_batch(
            cfg,
            snap,
            batch_id=args["batch_id"],
            at_tick=args["at_tick"],
            errors=errors,
            known_critical_events=tuple(events),
        )
    tick = case["events"][0]["at_tick"]
    batch_id = case["trace_reproducibility"]["batch_id"]
    if failures:
        return snap, reject_batch(
            cfg,
            snap,
            batch_id=batch_id,
            at_tick=tick,
            errors=tuple(failures),
            known_critical_events=tuple(events),
        )
    sealed = seal_batch(cfg, snap, batch_id=batch_id, at_tick=tick, events=tuple(events))
    if isinstance(sealed, r.DecodeFailure):
        return snap, reject_batch(
            cfg,
            snap,
            batch_id=batch_id,
            at_tick=tick,
            errors=sealed.errors,
            known_critical_events=tuple(events),
        )
    return snap, reduce_batch(cfg, snap, sealed.value)


def assert_projection(case, initial, result):
    expected = load("expected_traces")["projection_expectations"][case["case_id"]]
    final = result.snapshot
    assert final.state == expected["state"]
    assert final.control_session_id == expected["control_session_id"]
    assert final.desired_epoch == expected["desired_epoch"]
    # Independent lease arithmetic: no implementation eligibility/guard helper.
    live = sorted(
        p.permission_id
        for p in final.permissions
        if p.permission_id not in final.revoked_permission_ids
        and p.session_id == final.control_session_id
        and p.permission_epoch == final.desired_epoch
        and p.valid_from_tick <= final.current_tick < p.valid_until_tick
    )
    assert live == sorted(expected["live_permission_ids"])
    assert [t.transition_id for t in result.transitions] == expected["transition_path"]
    old_ids = {f.fault_id for f in initial.fault_latches}
    assert sorted(f.fault_id for f in final.fault_latches if f.fault_id not in old_ids) == sorted(
        expected["added_fault_ids"]
    )
    prior_uncleared = {f.fault_id for f in initial.fault_latches if f.cleared_tick is None}
    assert sorted(
        f.fault_id
        for f in final.fault_latches
        if f.fault_id in prior_uncleared and f.cleared_tick is not None
    ) == sorted(expected["cleared_fault_ids"])
    assert old_ids <= {f.fault_id for f in final.fault_latches}
    assert result.endpoint_outputs == ()
    assert all(
        t.endpoint_observation is None or t.decision_scope == "SUPPLIED_OBSERVATION"
        for t in result.traces
    )
    assert all(t.physical_actuation_claim == "NOT_OBSERVED_NOT_VALIDATED" for t in result.traces)
    # These are salient trigger expectations, not fabricated full Trace literals.
    # Require an actual trace carrying the declared decision/reasons. Disagreement
    # stays a failure for Engineering Review; do not rewrite approved values.
    assert any(
        t.decision == expected["decision"] and list(t.reason_codes) == expected["reason_codes"]
        for t in result.traces
    ), result.traces
    if "created_permissions" in expected:
        from dataclasses import asdict

        created = [
            asdict(p)
            for p in final.permissions
            if p.permission_id not in {x.permission_id for x in initial.permissions}
        ]

        def json_shape(v):
            if isinstance(v, dict):
                return {k: json_shape(x) for k, x in v.items()}
            if isinstance(v, (tuple, list)):
                return [json_shape(x) for x in v]
            return v

        assert json_shape(created) == expected["created_permissions"]
