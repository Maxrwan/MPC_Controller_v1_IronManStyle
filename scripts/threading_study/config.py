"""Startup-only threading configuration; no numerical imports in this module."""

import ctypes
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/mpc_threading_study"
THREAD_VARIABLES = (
    "VECLIB_MAXIMUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def thread_count(value, maximum=None):
    maximum = maximum or os.cpu_count() or 1
    try:
        count = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Thread count must be an integer") from error
    if isinstance(value, bool) or str(count) != str(value) or not 1 <= count <= maximum:
        raise ValueError(f"Thread count must be an integer in [1, {maximum}]")
    return count


def environment(count):
    count = thread_count(count)
    env = {k: v for k, v in os.environ.items() if k not in THREAD_VARIABLES}
    env.update(
        VECLIB_MAXIMUM_THREADS=str(count),
        MPLCONFIGDIR="/private/tmp/apex-matplotlib",
        XDG_CACHE_HOME="/private/tmp/apex-cache",
        PYTHONHASHSEED="0",
    )
    return env


def configure_accelerate(count):
    count = thread_count(count)
    if os.environ.get("VECLIB_MAXIMUM_THREADS") != str(count):
        raise RuntimeError("Thread ceiling must be set by a fresh parent subprocess")
    library = ctypes.CDLL("/System/Library/Frameworks/Accelerate.framework/Accelerate")
    library.BLASSetThreading.argtypes = [ctypes.c_uint]
    library.BLASSetThreading.restype = ctypes.c_int
    library.BLASGetThreading.restype = ctypes.c_uint
    mode = 1 if count == 1 else 0  # SDK thread_api.h: SINGLE=1, MULTI=0.
    status = library.BLASSetThreading(mode)
    actual = library.BLASGetThreading()
    if status != 0 or actual != mode:
        raise RuntimeError("Accelerate did not accept requested threading mode")
    return {
        "requested_ceiling": count,
        "set_status": status,
        "blas_threading_mode": actual,
        "mode_name": "single" if actual == 1 else "automatic_multi",
        "exact_active_thread_count_available": False,
    }
