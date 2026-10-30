"""O00: literal canonical ordering, shapes and immutable contracts. UNEXECUTED in L1."""

from dataclasses import FrozenInstanceError

import pytest


def test_canonical_contracts(point):
    from ct1.contracts import INPUT_NAMES, LATERAL, STATE_NAMES

    assert STATE_NAMES == ("vx", "vy", "r", "e_psi", "s_abs", "e_y")
    assert INPUT_NAMES == ("delta", "a_cmd") and LATERAL == (5, 3, 1, 2)
    with pytest.raises(FrozenInstanceError):
        point.x = (0,) * 6
    _deadline_contract_literals()


def test_owned_linearization_buffers(pair_factory):
    import numpy as np
    from ct1.contracts import Linearization

    p = pair_factory([[1]], [[1]])
    a = np.array([[1.0]])
    q = Linearization(p.parent_key, a, a.copy(), ("x",), ("u",), ("1",), ("1",))
    a[0, 0] = 9
    assert q.A[0, 0] == 1 and not q.A.flags.writeable


def test_frozen_result_projection_is_deeply_owned():
    import numpy as np
    from ct1.contracts import Outcome

    a = np.array([[1.0]])
    result = Outcome.available({"A": a, "labels": ["literal"]}).unwrap()
    a[0, 0] = 9
    assert result["A"][0, 0] == 1 and not result["A"].flags.writeable
    with pytest.raises(TypeError):
        result["labels"] = ("changed",)


def _deadline_contract_literals():
    from types import SimpleNamespace

    from ct1.contracts import Budget
    from ct1.guards import _AggregateDeadline

    d = _AggregateDeadline(10.0, 310.0)
    assert d.cli_start_monotonic_s == 10.0 and d.deadline_monotonic_s == 310.0
    with pytest.raises(FrozenInstanceError):
        d.deadline_monotonic_s = 610.0
    for start, end in (
        (10.0, 311.0),
        (10.0, 610.0),
        (-1.0, 299.0),
        (float("nan"), 300.0),
        (0.0, float("inf")),
    ):
        with pytest.raises(ValueError):
            _AggregateDeadline(start, end)
    for grant, budget in (
        (SimpleNamespace(host_seconds=301, authorized_stage="L3"), Budget()),
        (SimpleNamespace(host_seconds=300, authorized_stage="L3"), Budget(wall_s=301)),
        (SimpleNamespace(host_seconds=300, authorized_stage="L1"), Budget()),
    ):
        with pytest.raises(PermissionError):
            d.validate_for(grant, budget)
