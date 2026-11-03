"""New W1 JSON projection and descriptive summaries; never repairs old VIS evidence."""

import hashlib
import json
import math
from dataclasses import fields, is_dataclass
from pathlib import Path


def project(value):
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: project(getattr(value, f.name)) for f in fields(value)}
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("Nonfinite scientific value; retain separate fault representation")
        return value
    if isinstance(value, dict):
        if any(type(k) is not str for k in value):
            raise ValueError("JSON object keys must be strings")
        return {k: project(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [project(v) for v in value]
    if type(value).__module__.startswith("numpy"):
        return project(value.tolist())
    raise TypeError("Unsupported result type " + type(value).__name__)


def write(path, value):
    data = json.dumps(project(value), indent=2, allow_nan=False, sort_keys=True) + "\n"
    Path(path).write_text(data)


class Journal:
    def __init__(self, path):
        self.path = Path(path)

    def __call__(self, event):
        with self.path.open("a") as stream:
            stream.write(json.dumps(project(event), allow_nan=False, sort_keys=True) + "\n")
            stream.flush()


def inventory(root):
    root = Path(root)
    return {
        str(p.relative_to(root)): {
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != "index.json"
    }


def distribution(values):
    raw_values = list(values)
    values = [v for v in raw_values if v is not None]
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Invalid timing observation")
    ordered = sorted(values)
    if not ordered:
        return {
            "count": 0,
            "samples_s": raw_values,
            "missing_count": len(raw_values) - len(values),
            "min": None,
            "median": None,
            "p95": None,
            "max": None,
            "status": "NOT_OBSERVED",
        }
    n = len(values)
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    return {
        "count": n,
        "samples_s": raw_values,
        "missing_count": len(raw_values) - len(values),
        "min": ordered[0],
        "median": median,
        "p95": ordered[math.ceil(0.95 * n) - 1],
        "max": ordered[-1],
        "quantile": "nearest-rank ceil(0.95*n)",
        "status": "OBSERVED",
    }


def assess(raw, boundary):
    plans = raw.get("plans", [])
    recurring = [p for p in plans if not p.get("startup") and p.get("completed")]
    full = distribution(p["planner_total_time"] for p in recurring)
    solve = distribution(p.get("solve_time") for p in recurring)
    tracker = distribution(c["total_time"] for c in raw.get("controls", []))
    valid = (
        raw.get("failure") is None
        and raw.get("stop_reason") == "duration"
        and not raw.get("fallbacks")
    )
    classification = "INSUFFICIENT_EVIDENCE"
    if valid and full["count"] >= 10:
        concern = bool(
            raw.get("misses")
            or raw.get("codriver_misses")
            or full["p95"] > 0.1
            or (tracker["p95"] or 0) > 0.01
        )
        classification = (
            "FEASIBILITY_CONCERN_OBSERVED" if concern else "PRELIMINARY_FEASIBILITY_OBSERVED"
        )
    return {
        "classification": classification,
        "native_preparation": full,
        "native_solve": solve,
        "native_tracker": tracker,
        "startup": [p for p in plans if p.get("startup")],
        "unfinished_preparations": [
            p for p in plans if not p.get("startup") and not p.get("completed")
        ],
        "boundary_envelopes": boundary,
        "planner_busy": raw.get("misses", []),
        "codriver_busy": raw.get("codriver_misses", []),
        "simulated_coverage_s": raw.get("end_time"),
        "comparisons": {
            "preparation_release_opportunity_s": 0.1,
            "tracker_period_s": 0.01,
            "fixed_handoff_deadline": None,
        },
        "limits": [
            "small sample",
            "no observer correction",
            "Mac only, no onboard claim",
            "legacy application observations are not endpoint enforcement",
        ],
    }


def reconcile(exit_code, worker, guard_reason=None):
    return (
        exit_code == 0
        and worker is not None
        and worker.get("complete") is True
        and guard_reason is None
    )
