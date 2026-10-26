"""Strict constructors, versions, immutable encoding and exact payload bytes."""

from dataclasses import FrozenInstanceError, replace

import pytest
from apex.safety_authority import records as r
from apex.safety_authority.codec import (
    command_errors,
    decode_configuration,
    decode_snapshot,
    encode_snapshot,
    freeze,
    parse_json,
)
from oracle_support import cases, decode_inputs, load


@pytest.mark.parametrize("value", [True, -1, 1.0])
def test_tick_rejects_noninteger_or_negative(value):
    with pytest.raises((TypeError, ValueError)):
        r.AdvancePayload(target_tick=value)


def test_kw_only_and_frozen_records():
    with pytest.raises(TypeError):
        r.AdvancePayload(1)
    value = r.AdvancePayload(target_tick=1)
    with pytest.raises(FrozenInstanceError):
        value.target_tick = 2


def test_version_selection_and_unknown_fields():
    original = load("configurations")["S1A_TOY_CONFIG"]
    assert isinstance(
        decode_configuration(freeze(dict(original, contract_version="apex-s1-authority/0.1.0"))),
        r.DecodeFailure,
    )
    assert isinstance(
        decode_configuration(freeze(dict(original, undocumented=True))), r.DecodeFailure
    )


def test_snapshot_round_trip_preserves_immutable_records():
    cfg, snap = decode_inputs(cases()[0])
    decoded = decode_snapshot(encode_snapshot(snap), configuration=cfg)
    assert isinstance(decoded, r.DecodeSuccess)
    assert decoded.value == snap


@pytest.mark.parametrize("document", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'])
def test_duplicate_and_nonfinite_json_rejected(document):
    with pytest.raises(ValueError):
        parse_json(document)


def test_command_hash_is_original_utf8_not_reserialized():
    _, snap = decode_inputs(cases()[0])
    command = snap.commands[0]
    assert command_errors(command) == ()
    altered = replace(command, payload_utf8=command.payload_utf8 + " ")
    assert command_errors(altered)[0].reason_code == "IDENTITY_CONFLICT"


def test_mutable_tuple_substitution_rejected():
    with pytest.raises((TypeError, ValueError)):
        r.ArmRequestPayload(operator_authorization_id="OPERATOR_TOY", evidence_ids=["NOMINAL_OK"])
