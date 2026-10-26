"""O01: literal held-versus-nominal identity and immutable archived bindings."""

import pytest


def test_source_identity_and_panel(inputs):
    from ct1.inputs import load_authority_and_command_history, load_candidate_tuples

    assert len(inputs.candidates) == 12
    for c in inputs.candidates:
        actual, nominal = load_candidate_tuples(inputs, c.candidate_id).unwrap()
        history = load_authority_and_command_history(inputs, c.candidate_id).unwrap()
        assert actual.x == tuple(c.original_candidate_json["state"])
        assert actual.u == history.held_control
        assert actual.packet_id == nominal.packet_id == c.packet_id
        assert not history.pending_information_complete


def test_path_escape_rejected(tmp_path):
    from ct1.inputs import _resolve

    with pytest.raises(ValueError):
        _resolve(tmp_path, "../outside")


def test_wrong_revision_rejects_before_numeric_constructor(inputs):
    from dataclasses import replace

    from ct1.inputs import verify_inputs

    assert verify_inputs(replace(inputs.spec, expected_revision="0" * 40)).value is None
