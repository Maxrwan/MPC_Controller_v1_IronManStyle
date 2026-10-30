"""Read-only, externally pinned P/VIS-1R evidence. No scientific/runtime imports."""

import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tools.apex_workbench.configuration import ROOT

ADAPTER = "gp_archive"
PROFILE = "P/VIS-1R controlled_A · historical synthetic"
DIRECTORY = ROOT / "results/task007d/vis/vis1r_c699057/controlled_A"
REVISION = "8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae"
MANIFEST_SHA256 = "5375580236b5e4b9305babe5d25e6459f91f80e31bb3fdb937e3e4c054d85a10"
ANCHORS = {
    "configs/performance/apex_performance_synthetic_v1.json": (
        "5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf"
    ),
    "docs/task007e/e2/evidence_links.json": (
        "5e788c428bd706f20792b1852b3400bf0eeb7fe11d93285bbc5bc7accec8fced"
    ),
    "docs/task007d/vis/vis1l/verification.json": (
        "8055a017dbbbf19b0d0143311a8299d97c0c860583f233685270a4980a9d9a67"
    ),
}
CORE = ("vx", "vy", "r", "e_psi", "s_abs", "e_y")
UNITS = dict(zip(CORE, ("m/s", "m/s", "rad/s", "rad", "m", "m")))
UNITS.update(
    delta="rad",
    a_cmd="m/s²",
    time="s",
    application_time="s",
    front_utilization="1",
    rear_utilization="1",
    packet_age="s",
    reserve="s",
    clearance="m",
    measured_solver_duration="s",
    t_release="s",
    t_accept="s",
)


class ArchiveError(ValueError):
    """Withhold a view when any part of its pinned evidence is unavailable."""


def _path(root, name):
    root = Path(root).absolute()
    relative = Path(name)
    if root.is_symlink() or relative.is_absolute() or ".." in relative.parts:
        raise ArchiveError("Unsafe archive path")
    path = root / relative
    if any(
        (root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)
    ):
        raise ArchiveError("Linked archive path withheld")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ArchiveError("Archive path escapes its root")
    return path


def _checked(root, name, expected, *, retain=False):
    path = _path(root, name)
    if path.stat().st_size != expected["bytes"]:
        raise ArchiveError("Archive size changed: " + name)
    digest, blocks = hashlib.sha256(), []
    with path.open("rb") as stream:
        while block := stream.read(1024**2):
            digest.update(block)
            if retain:
                blocks.append(block)
    if digest.hexdigest() != expected["sha256"]:
        raise ArchiveError("Archive checksum changed: " + name)
    return b"".join(blocks) if retain else None


def _anchors():
    documents = {}
    for name, digest in ANCHORS.items():
        path = _path(ROOT, name)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ArchiveError("Historical authority record changed: " + name)
        documents[name] = json.loads(content)
    return documents["docs/task007d/vis/vis1l/verification.json"]["current_run_inventory"][
        "controlled_A"
    ]


@dataclass
class Snapshot:
    directory: Path
    manifest: dict
    fixture: dict
    inventory: dict
    contents: dict
    frames: dict

    def current(self):
        """Rehash original bytes before publishing; no metadata-only cache epoch."""
        if _anchors() != self.inventory:
            raise ArchiveError("Archive authority changed during presentation")
        for name, expected in self.inventory.items():
            _checked(self.directory, name, expected)
        return True


def read(directory=None, tables=("states", "controls", "planning")):
    """Verify all25 original files, parse only requested tables from verified bytes."""
    directory = Path(DIRECTORY if directory is None else directory)
    inventory = _anchors()
    names = {"scientific/" + table + ".csv" for table in tables}
    if any(name not in inventory for name in names):
        raise ArchiveError("Unsupported archive table")
    names.update(
        (
            "scientific/manifest.json",
            "scientific/manifest.sha256",
            "scientific/fixture/planning_manifest.json",
            "summary.json",
        )
    )
    contents = {}
    for name, expected in inventory.items():
        data = _checked(directory, name, expected, retain=name in names)
        if data is not None:
            contents[name] = data
    manifest_bytes = contents["scientific/manifest.json"]
    manifest = json.loads(manifest_bytes)
    if (
        hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256
        or contents["scientific/manifest.sha256"].decode().split()[0] != MANIFEST_SHA256
        or manifest["schema"] != "apex-run/0.1.0"
        or manifest["run_id"] != "controlled_A"
        or manifest["architecture"] != "A"
        or manifest["provenance"]["scientific_revision"] != REVISION
        or manifest["provenance"]["export_revision"] != REVISION
    ):
        raise ArchiveError("Unsupported source/schema/identity")
    for name, expected in manifest["artifacts"].items():
        if inventory.get("scientific/" + name) != {
            "bytes": expected["bytes"],
            "sha256": expected["sha256"],
        }:
            raise ArchiveError("Artifact manifest disagrees with external inventory")
    frames = {}
    for table in tables:
        name = table + ".csv"
        frame = pd.read_csv(
            io.BytesIO(contents["scientific/" + name]), float_precision="round_trip"
        )
        if len(frame) != manifest["artifacts"][name]["rows"]:
            raise ArchiveError("CSV coverage changed: " + name)
        frames[table] = frame
    result = Snapshot(
        directory,
        manifest,
        json.loads(contents["scientific/fixture/planning_manifest.json"]),
        inventory,
        contents,
        frames,
    )
    result.current()
    return result


def sector_names(snapshot):
    return [row["name"] for row in snapshot.fixture["sectors"]]


def sector_frame(snapshot, table, sector=None):
    """Filter each stream only by its own native progress; no asynchronous joins."""
    frame = snapshot.frames[table]
    if sector is None:
        return frame.copy()
    if table not in ("states", "planning"):
        raise ArchiveError("No native sector progress for this stream; use full-run view")
    sectors = snapshot.fixture["sectors"]
    index = sector_names(snapshot).index(sector)
    start = sectors[index]["start_s_m"]
    length = snapshot.fixture["closed_track_length_m"]
    end = sectors[index + 1]["start_s_m"] if index + 1 < len(sectors) else length
    progress = frame["s_abs"] % length if table == "states" else frame["s_track_m"]
    return frame.loc[(progress >= start) & (progress < end)].copy()


def unit(channel):
    for prefix in (
        "planning_error_",
        "reference_",
        "planning_",
        "error_",
        "nominal_",
        "requested_",
    ):
        if channel.startswith(prefix):
            return UNITS.get(channel[len(prefix) :], "unit undeclared")
    return UNITS.get(channel, "unit undeclared")
