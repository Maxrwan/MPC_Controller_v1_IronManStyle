"""Portable evidence helpers; no numerical imports during launcher bootstrap."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THREAD_ENV = {
    "OPENBLAS_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_DYNAMIC": "FALSE",
    "PYTHONHASHSEED": "0",
    "PYTHONDONTWRITEBYTECODE": "1",
}


def clean(value):
    """Strict JSON; nonfinite observations remain explicit rather than invalid JSON."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": str(value)}
    if hasattr(value, "tolist"):
        return clean(value.tolist())
    return value


def write(path, value):
    Path(path).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + "\n")


def verify_sources():
    manifest = json.loads((ROOT / "source_manifest.json").read_text())
    for name, entry in manifest["files"].items():
        data = (ROOT / name).read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Frozen source/configuration mismatch: " + name)
    return manifest


def distribution(values, period):
    """Linear interpolated empirical percentiles; never a WCET estimate."""
    values = sorted(float(x) for x in values if x is not None and math.isfinite(x))
    if not values:
        return {
            "count": 0,
            "mean_s": None,
            "median_s": None,
            "p95_s": None,
            "p99_s": None,
            "maximum_s": None,
            "period_s": period,
            "exceeding_period_count": 0,
            "exceeding_period_proportion": None,
        }

    def percentile(q):
        index = (len(values) - 1) * q
        low = int(index)
        high = min(low + 1, len(values) - 1)
        return values[low] + (values[high] - values[low]) * (index - low)

    exceeds = sum(x > period for x in values)
    return {
        "count": len(values),
        "mean_s": sum(values) / len(values),
        "median_s": percentile(0.5),
        "p95_s": percentile(0.95),
        "p99_s": percentile(0.99),
        "maximum_s": values[-1],
        "period_s": period,
        "exceeding_period_count": exceeds,
        "exceeding_period_proportion": exceeds / len(values),
    }
