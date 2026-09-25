import numpy as np
import pytest

from apex.state import (
    CONTROL_DIM,
    CONTROL_NAMES,
    CONTROL_UNITS,
    STATE_DIM,
    STATE_NAMES,
    STATE_UNITS,
    ControlIndex,
    StateIndex,
    control_vector,
    state_vector,
)


def test_frozen_state_contract():
    assert [(i.name, i.value) for i in StateIndex] == [
        ("VX", 0),
        ("VY", 1),
        ("YAW_RATE", 2),
        ("E_PSI", 3),
        ("S_ABS", 4),
        ("E_Y", 5),
    ]
    assert STATE_DIM == 6
    assert STATE_NAMES == ("vx", "vy", "r", "e_psi", "s_abs", "e_y")
    assert STATE_UNITS == ("m/s", "m/s", "rad/s", "rad", "m", "m")


def test_frozen_control_contract():
    assert [(i.name, i.value) for i in ControlIndex] == [("DELTA", 0), ("A_CMD", 1)]
    assert CONTROL_DIM == 2
    assert CONTROL_NAMES == ("delta", "a_cmd")
    assert CONTROL_UNITS == ("rad", "m/s^2")


def test_state_copy_dtype_and_unwrapped_progress():
    source = np.array([1, -2, -3, 4, 12345, -6])
    state = state_vector(source)
    source[0] = 99
    assert state.dtype == np.float64
    assert state[StateIndex.VX] == 1
    assert state[StateIndex.S_ABS] == 12345
    np.testing.assert_array_equal(control_vector([0.1, -2]), [0.1, -2])


@pytest.mark.parametrize(
    "values", [[0] * 5, [[0] * 6], [0, 0, 0, 0, -1, 0], [0, 0, float("nan"), 0, 0, 0]]
)
def test_invalid_state(values):
    with pytest.raises(ValueError):
        state_vector(values)


@pytest.mark.parametrize("values", [[0], [[0, 0]], [0, float("inf")]])
def test_invalid_control(values):
    with pytest.raises(ValueError):
        control_vector(values)
