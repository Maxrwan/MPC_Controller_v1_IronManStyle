"""Canonical SI state and input ordering. Changes require explicit authorization."""

from enum import IntEnum

import numpy as np
from numpy.typing import NDArray

Vector = NDArray[np.float64]


class StateIndex(IntEnum):
    VX = 0
    VY = 1
    YAW_RATE = 2
    E_PSI = 3
    S_ABS = 4
    E_Y = 5


class ControlIndex(IntEnum):
    DELTA = 0
    A_CMD = 1


STATE_DIM = 6
CONTROL_DIM = 2
STATE_NAMES = ("vx", "vy", "r", "e_psi", "s_abs", "e_y")
STATE_UNITS = ("m/s", "m/s", "rad/s", "rad", "m", "m")
CONTROL_NAMES = ("delta", "a_cmd")
CONTROL_UNITS = ("rad", "m/s^2")


def _vector(values: object, size: int, label: str) -> Vector:
    array = np.array(values, dtype=np.float64, copy=True)
    if array.shape != (size,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be a finite vector of shape ({size},)")
    return array


def state_vector(values: object) -> Vector:
    """Copy and validate a canonical state; progress remains unwrapped."""
    state = _vector(values, STATE_DIM, "state")
    if state[StateIndex.S_ABS] < 0:
        raise ValueError("s_abs must be nonnegative")
    return state


def control_vector(values: object) -> Vector:
    """Copy and validate canonical input without inventing actuator limits."""
    return _vector(values, CONTROL_DIM, "control")
