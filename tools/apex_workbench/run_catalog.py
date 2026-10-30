"""Read-only discovery, not scientific validation or process ownership."""

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from tools.apex_workbench.configuration import ROOT, RUNS

OWNED_ROOT = RUNS
QUALIFICATION_ROOT = ROOT / "results/apex_workbench_qualifications"
ACCEPTED_CAMPAIGN = "v0_2_reviewed_20261029"
METADATA_BYTES = 16 * 1024**2  # Existing worker single-file ceiling; an I/O safeguard only.


def metadata(directory, name):
    path = Path(directory) / name
    if not path.resolve().is_relative_to(Path(directory).resolve()):
        raise ValueError("Metadata path escapes its record")
    if path.stat().st_size > METADATA_BYTES:
        raise ValueError("Metadata exceeds the local file-size safeguard")
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("Expected a metadata object")
    return value


@dataclass(frozen=True)
class Run:
    key: str
    directory: Path
    origins: tuple[str, ...]
    aliases: tuple[Path, ...]
    run_id: str
    adapter: str
    case: str
    state: str
    outcome: str
    evidence: str
    issues: tuple[str, ...]
    conflict: bool = False
    profile: str = ""

    @property
    def owned(self):
        return self.origins == ("owned",) and not self.conflict

    @property
    def label(self):
        return (
            f"{self.adapter} · {self.case or 'original'} · {self.profile} · {self.state} · "
            f"{','.join(self.origins)} · {self.run_id}"
        )


@dataclass(frozen=True)
class Catalog:
    runs: tuple[Run, ...]
    qualifications: tuple[Path, ...]
    issues: tuple[str, ...]
    owned_root: Path


def _candidate(directory, origin):
    values, problems = {}, []
    for name in ("request", "status", "worker"):
        try:
            values[name] = metadata(directory, name + ".json")
        except (OSError, ValueError, RuntimeError) as error:
            values[name] = {}
            problems.append(f"{name}.json: {error}")
    request, worker = values["request"], values["worker"]
    run_id = request.get("run_id")
    run_id = run_id if isinstance(run_id, str) and run_id.strip() else None
    birth = worker.get("created")
    worker_id = None
    if (
        worker.get("role") == "worker"
        and type(worker.get("pid")) is int
        and worker["pid"] > 0
        and type(birth) in (float, int)
        and isfinite(birth)
        and birth > 0
    ):
        worker_id = f"{worker['pid']}:{birth!r}"
    digest = None
    try:
        path = directory / "artifacts.json"
        if not path.resolve().is_relative_to(directory) or path.stat().st_size > METADATA_BYTES:
            raise ValueError("Unsafe manifest path/size")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError, RuntimeError) as error:
        problems.append(f"artifacts.json: {error}")
    tokens = {"path:" + str(directory)}
    tokens.update(
        prefix + value
        for prefix, value in (("run:", run_id), ("worker:", worker_id), ("manifest:", digest))
        if value
    )
    return dict(
        directory=directory,
        origin=origin,
        values=values,
        issues=problems,
        identity=(run_id, worker_id, digest),
        tokens=tokens,
    )


def discover(*, owned_root=None, qualification_root=None, include_racing=False):
    """Only configured owned runs and the accepted qualification's original run directories."""
    owned = Path(OWNED_ROOT if owned_root is None else owned_root).resolve()
    qualified = Path(
        QUALIFICATION_ROOT if qualification_root is None else qualification_root
    ).resolve()
    candidates, issues, qualifications = [], [], []
    if owned.is_dir():
        for path in sorted(owned.iterdir(), reverse=True):
            if path.is_dir() and not path.name.startswith("."):
                if path.is_symlink() or path.resolve().parent != owned:
                    issues.append("Excluded linked/outside owned directory: " + str(path))
                else:
                    candidates.append(_candidate(path.resolve(), "owned"))
    campaign = qualified / ACCEPTED_CAMPAIGN
    record = campaign / "qualification"
    if (record / "commit.json").is_file():
        qualifications.append(record)
        try:
            document = metadata(record, "qualification.json")
            if document.get("schema") != "apex-vdl-qualification/1":
                raise ValueError("Unsupported qualification schema")
            references = document["references"]
            if not isinstance(references, dict):
                raise ValueError("Invalid qualification reference index")
            for reference in references.values():
                path = Path(reference["directory"])
                if path.is_symlink() or path.resolve().parent != (campaign / "runs").resolve():
                    raise ValueError("Qualification reference outside its approved run root")
                candidates.append(_candidate(path.resolve(), "qualification archive"))
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
            issues.append("Qualification discovery is incomplete/unverified: " + str(error))
    # Original archives anchor groups before untrusted owned aliases. A candidate may attach
    # to ONE anchor; conflicting metadata must never union two distinct original executions.
    groups = []
    for candidate in sorted(candidates, key=lambda row: row["origin"] == "owned"):
        # Canonical path, then run ID, then worker identity, then manifest. Only anchor
        # identifiers participate: an alias cannot propagate contradictory weak hints.
        priorities = ("path:", "run:", "worker:", "manifest:")
        matches = []
        for group in groups:
            shared = group["tokens"] & candidate["tokens"]
            if shared:
                if (
                    candidate["origin"] == "qualification archive"
                    and "path:" + str(candidate["directory"]) not in shared
                    and candidate["identity"] != group["rows"][0]["identity"]
                ):
                    candidate["issues"].append(
                        "Conflicting archive identity; distinct source path kept separately"
                    )
                    continue
                rank = min(
                    i
                    for i, prefix in enumerate(priorities)
                    if any(token.startswith(prefix) for token in shared)
                )
                matches.append((rank, group))
        if matches:
            group = min(matches, key=lambda match: match[0])[1]
            group["rows"].append(candidate)
            group["tokens"].add("path:" + str(candidate["directory"]))
            if len(matches) > 1:
                candidate["issues"].append(
                    "Alias hints match distinct anchors; attached once without merging originals"
                )
        else:
            groups.append({"rows": [candidate], "tokens": set(candidate["tokens"])})
    runs = []
    for group in groups:
        rows = sorted(group["rows"], key=lambda r: (r["origin"] == "owned", str(r["directory"])))
        primary = rows[0]
        request, status = primary["values"]["request"], primary["values"]["status"]
        conflict = len({row["identity"] for row in rows}) > 1
        problems = sorted({p for row in rows for p in row["issues"]})
        if conflict:
            problems.append(
                "Conflicting alias identities; only the selected original source can be verified"
            )
        run_id = primary["identity"][0] or primary["directory"].name
        key_material = "path:" + str(primary["directory"])
        if primary["identity"][0] and primary["origin"] == "owned":
            key_material = "id:" + run_id
        effective = request.get("effective")
        effective = effective if isinstance(effective, dict) else {}
        context = request.get("execution_context")
        context = context if isinstance(context, dict) else {}

        def text(value):
            return value if isinstance(value, str) else "unknown"

        runs.append(
            Run(
                "run-" + hashlib.sha256(key_material.encode()).hexdigest()[:20],
                primary["directory"],
                tuple(sorted({r["origin"] for r in rows})),
                tuple(sorted({r["directory"] for r in rows})),
                run_id,
                text(request.get("adapter")),
                text(effective.get("case_id", "")),
                text(status.get("state")),
                text(status.get("scientific_outcome")),
                text(status.get("evidence_state")),
                tuple(problems),
                conflict,
                text(effective.get("grid_id", "original"))
                + "/"
                + text(context.get("role", "adapter")),
            )
        )
    if include_racing:
        from tools.apex_workbench import gp_archive

        # One declared historical identity, no recursive import or copies counted as executions.
        runs.append(
            Run(
                "gp-" + gp_archive.MANIFEST_SHA256,
                gp_archive.DIRECTORY,
                ("P historical archive",),
                (gp_archive.DIRECTORY,),
                "controlled_A",
                gp_archive.ADAPTER,
                "controlled_A",
                "historical",
                "unverified discovery",
                "inspect to verify",
                (),
                profile=gp_archive.PROFILE,
            )
        )
    return Catalog(
        tuple(sorted(runs, key=lambda r: (r.adapter != "gp_archive", r.run_id), reverse=True)),
        tuple(qualifications),
        tuple(issues),
        owned,
    )
