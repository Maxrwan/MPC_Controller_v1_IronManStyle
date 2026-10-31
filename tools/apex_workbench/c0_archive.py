"""One pinned descriptive record. No scientific, producer or lifecycle imports."""

import hashlib
import json
import math
import stat
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELATIVE = "results/task007d/c/amended/c0_export/original155.json"
SHA256 = "2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5"
SIZE = 152600
IDENTIFIER = "c0-original155-descriptive-only/1"
PROFILE = "descriptive_only / source_unverified"
ADAPTER = "c0_descriptive_archive"
BANNER = (
    "DESCRIPTIVE ONLY · SOURCE UNVERIFIED — exact retained JSON; capture-time producer, "
    "configuration and environment unknown. Plots show recorded numbers, "
    "not qualified scientific/controller-performance evidence."
)
SHAPE = "tools/apex_workbench/c0_shape.json"
ANCHORS = {
    "docs/apex_workbench_v0_3_d/c0_contract/CONTRACT_DESCRIPTIVE_ONLY_V1.md": (
        "31afeefac753dead492df26f90b5b6aa1d822de705e3a86c97dfba2a0f72fd62"
    ),
    "docs/apex_workbench_v0_3_d/c0_contract/evidence_inventory.json": (
        "2f2aa9f503011e4c8ce4383ef622ef5003472438ab7782b825fb038e5c23b8c4"
    ),
    "docs/reviews/apex_workbench_v0_3_d/c0_descriptive_contract/iteration_2/REVIEW.md": (
        "55b475888733c86a4cf241d996d3f40487e26df226846903b6e8153352e07fa5"
    ),
    "docs/reviews/apex_workbench_v0_3_d/c0_descriptive_contract/iteration_2/review_record.json": (
        "d1e6f1955af10b49ba7a56c2e20793c6a59d9d549f5bcb35786a67877ffbe257"
    ),
    SHAPE: "5acfa2535daeed22bfd3d5033dd74f84d579507136d6088b87caa716b40fe4a6",
}


class ArchiveError(ValueError):
    """Withhold all presentation and export on changed or unsupported evidence."""


@dataclass(frozen=True)
class Number:
    token: str
    kind: str


def _path(root, relative):
    """Reject every symlink component, including ancestors of the configured root."""
    root = Path(root)
    relative = Path(relative)
    if not root.is_absolute() or relative.is_absolute() or ".." in relative.parts:
        raise ArchiveError("Unsafe C0 path")
    path = root / relative
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ArchiveError("Linked C0 path withheld")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ArchiveError("C0 path escapes configured root")
    return path


def _checked(root, relative, digest, size=None):
    path = _path(root, relative)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or (size is not None and info.st_size != size):
        raise ArchiveError("C0 file type/size changed: " + relative)
    # A local I/O ceiling, not a scientific bound. All pinned anchors are smaller.
    limit = size if size is not None else 1024 * 1024
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit or hashlib.sha256(data).hexdigest() != digest:
        raise ArchiveError("C0 checksum/size changed: " + relative)
    # Check paths again after reading; no mtime-only identity or permissive cache.
    _path(root, relative)
    return data


def _anchors(root):
    contents = {name: _checked(root, name, sha) for name, sha in ANCHORS.items()}
    shape = json.loads(contents[SHAPE])
    if shape["identifier"] != IDENTIFIER:
        raise ArchiveError("Unsupported contemporary C0 inspection contract")
    return shape["shape"]


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArchiveError("Duplicate JSON member: " + key)
        result[key] = value
    return result


def _constant(value):
    raise ArchiveError("Nonstandard JSON constant: " + value)


def _validate(value, shape, pointer=""):
    """Check every original key/order, scalar token type, conditional row and dimension."""
    if isinstance(shape, str):
        kind = (
            value.kind
            if isinstance(value, Number)
            else {str: "string", bool: "boolean", type(None): "null"}.get(type(value))
        )
        if kind != shape:
            raise ArchiveError("C0 type mismatch: " + pointer)
        if isinstance(value, Number) and not math.isfinite(float(value.token)):
            raise ArchiveError("Nonfinite C0 number: " + pointer)
    elif "length" in shape and "segments" in shape:
        if not isinstance(value, list) or len(value) != shape["length"]:
            raise ArchiveError("C0 array dimension mismatch: " + pointer)
        next_index = 0
        for segment in shape["segments"]:
            if segment["start"] != next_index or not next_index < segment["stop"] <= len(value):
                raise ArchiveError("Invalid contemporary C0 shape segment")
            for index in range(next_index, segment["stop"]):
                _validate(value[index], segment["item"], f"{pointer}/{index}")
            next_index = segment["stop"]
        if next_index != len(value):
            raise ArchiveError("Incomplete contemporary C0 shape")
    else:
        if not isinstance(value, dict) or list(value) != list(shape):
            raise ArchiveError("C0 field identity/order mismatch: " + pointer)
        for key in shape:
            _validate(value[key], shape[key], pointer + "/" + key)


def _parse(raw, shape):
    # Only called after the immutable byte gate. Never a general archive importer.
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_pairs,
            parse_constant=_constant,
            parse_int=lambda s: Number(s, "integer"),
            parse_float=lambda s: Number(s, "real"),
        )
        _validate(value, shape)
    except (
        KeyError,
        TypeError,
        OverflowError,
        RecursionError,
        UnicodeError,
        json.JSONDecodeError,
    ) as error:
        raise ArchiveError("Malformed C0 record/shape") from error
    return value


def literal(value):
    """JSON value display with original numeric lexemes, never float reserialization."""
    if isinstance(value, Number):
        return value.token
    if isinstance(value, dict):
        return "{" + ", ".join(json.dumps(k) + ": " + literal(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(literal(v) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class Snapshot:
    root: Path
    raw: bytes
    shape: dict

    def current(self):
        """Rehash original and all external contract/review identities at each boundary."""
        if len(self.raw) != SIZE or hashlib.sha256(self.raw).hexdigest() != SHA256:
            raise ArchiveError("C0 operation-local bytes changed")
        if _anchors(self.root) != self.shape:
            raise ArchiveError("C0 inspection authority changed")
        _checked(self.root, RELATIVE, SHA256, SIZE)
        return True

    def data(self):
        # No mutable shared parsed cache; callers derive their view from these verified bytes.
        if len(self.raw) != SIZE or hashlib.sha256(self.raw).hexdigest() != SHA256:
            raise ArchiveError("C0 operation-local bytes changed")
        return _parse(self.raw, self.shape)


def read():
    """Single fixed profile/path. No path, upload, producer, worker or qualification input."""
    root = ROOT
    shape = _anchors(root)
    raw = _checked(root, RELATIVE, SHA256, SIZE)
    _parse(raw, shape)
    snapshot = Snapshot(root, raw, shape)
    snapshot.current()
    return snapshot


def fields(data, collection, index):
    """Retain field order and show absent members from this collection's observed union."""
    row = data[collection][index]
    union = list(dict.fromkeys(key for item in data[collection] for key in item))
    return [
        {
            "pointer": f"/{collection}/{index}/{key}",
            "presence": "absent"
            if key not in row
            else "present-null"
            if row[key] is None
            else "present",
            "json_literal": literal(row[key]) if key in row else "[absent — no JSON member]",
        }
        for key in [*row, *(key for key in union if key not in row)]
    ]


def missingness(data):
    result = []
    for collection, rows in data.items():
        if isinstance(rows, list):
            for index, row in enumerate(rows):
                if isinstance(row, dict):
                    result.extend(
                        f for f in fields(data, collection, index) if f["presence"] != "present"
                    )
        elif rows is None:
            result.append(
                {"pointer": "/" + collection, "presence": "present-null", "json_literal": "null"}
            )
    return result


CHRONOLOGY_FIELDS = {
    "fixed_handoffs": (
        "t_release",
        "valid_from",
        "t_ready",
        "miss_time",
        "late_discard_time",
        "t_accept",
        "first_TVLQR_use",
    ),
    "urgent_demands": (
        "trigger_time",
        "eligible_time",
        "release_time",
        "accepted_time",
        "trigger_to_authority",
    ),
    "plans": ("release_time", "completion_time"),
    "packets": ("planner_release_time", "actual_completion_time", "valid_from"),
    "triggers": ("time",),
    "releases": ("time",),
    "misses": ("time",),
    "fallbacks": ("time",),
}


def chronology(data):
    """Per-collection/source-row index, not a causal interstream total order or new events."""
    return [
        {"collection": collection, "source_row": index, **field}
        for collection in data
        if collection in CHRONOLOGY_FIELDS
        for index in range(len(data[collection]))
        for field in fields(data, collection, index)
        if field["pointer"].rsplit("/", 1)[1] in CHRONOLOGY_FIELDS[collection]
    ]
