"""Small, explicit input contract for existing experiment entry points."""

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "results/apex_workbench"
ADAPTERS = {"dynamic_demo": "Dynamic bicycle · open loop", "lqr_baseline": "LQR/PI · tracking"}
DEFAULTS = {
    "dynamic_demo": {"duration": 10.0, "dt": 0.005},
    "lqr_baseline": {
        "duration": 12.0,
        "speed": 2.0,
        "track": "circle",
        "ey": 0.0,
        "epsi": 0.0,
    },
}
# These are conservative UI/resource safeguards, NOT validated physical ranges.
BOUNDS = {
    "duration": (0.01, 20.0),
    "dt": (0.001, 0.01),
    "speed": (1.0, 3.0),
    "ey": (-0.1, 0.1),
    "epsi": (-0.05, 0.05),
}


def validate(adapter: str, values: dict) -> dict:
    if adapter not in DEFAULTS:
        raise ValueError("Unsupported experiment adapter")
    if not isinstance(values, dict) or set(values) != set(DEFAULTS[adapter]):
        raise ValueError("Configuration must contain exactly the supported parameter keys")
    effective = {}
    for key, value in values.items():
        if key == "track":
            if value not in ("circle", "oval"):
                raise ValueError("track must be circle or oval")
            effective[key] = value
            continue
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise ValueError(f"{key} must be a finite number")
        low, high = BOUNDS[key]
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{key} must be finite and in [{low}, {high}]")
        effective[key] = float(value)
    if adapter == "lqr_baseline":
        ticks = effective["duration"] / 0.005
        if not math.isclose(ticks, round(ticks), rel_tol=0, abs_tol=1e-9):
            raise ValueError("LQR duration must be an integer multiple of 0.005 s")
    return effective


def validate_note(value: str) -> str:
    if not isinstance(value, str) or len(value) > 8000:
        raise ValueError("Each learning note must be text of at most 8000 characters")
    return value
