"""O00: literal canonical ordering, shapes and immutable contracts. UNEXECUTED in L1."""

from dataclasses import FrozenInstanceError

import pytest


def test_canonical_contracts(point):
    from ct1.contracts import INPUT_NAMES, LATERAL, STATE_NAMES

    assert STATE_NAMES == ("vx", "vy", "r", "e_psi", "s_abs", "e_y")
    assert INPUT_NAMES == ("delta", "a_cmd") and LATERAL == (5, 3, 1, 2)
    with pytest.raises(FrozenInstanceError):
        point.x = (0,) * 6


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
