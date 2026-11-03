"""Stdlib admission followed by lazy composition of the unchanged accepted profile."""

import base64
import hashlib
import importlib.metadata as metadata
import json
import platform
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

SCIENTIFIC = "48adbdf64d492592d15e23c917aca71fa58aa8a5"
PLAN = "63d56fc366de7464e1c71a4f831c87ec03d31a2f"
MANIFEST = "configs/performance/apex_performance_synthetic_v1.json"
MANIFEST_SHA = "5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf"
DOCS = {"docs/CODEX_HANDOFF.md", "docs/DECISIONS.md"}
_runtime_admissions = {}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    """Explicit JSON-compatible projection; never mutate the scientific object."""
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float:
        import math

        if not math.isfinite(value):
            raise ValueError("Nonfinite snapshot")
        return value
    if isinstance(value, dict):
        if any(type(k) is not str for k in value):
            raise ValueError("Snapshot keys must be strings")
        return {k: canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [canonical(v) for v in value]
    raise ValueError("Unsupported snapshot type: " + type(value).__name__)


def match(actual, expected):
    a, b = canonical(actual), canonical(expected)

    def equal(x, y):
        if isinstance(x, dict) and isinstance(y, dict):
            return x.keys() == y.keys() and all(equal(x[k], y[k]) for k in x)
        if isinstance(x, list) and isinstance(y, list):
            return len(x) == len(y) and all(equal(u, v) for u, v in zip(x, y))
        if type(x) is bool or type(y) is bool:
            return type(x) is type(y) and x == y
        return x == y and (
            type(x) is type(y) or type(x) in (int, float) and type(y) in (int, float)
        )

    if not equal(a, b):
        raise ValueError("Resolved configuration mismatch")


def admit_source(root):
    root = Path(root).resolve()
    if git(root, "remote", "get-url", "origin") != (
        "https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle.git"
    ):
        raise ValueError("Wrong repository")
    subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", PLAN, "HEAD"],
        check=True,
        capture_output=True,
    )
    plan_path = "docs/pre_sid/preintegration/PREINTEGRATION_PLAN.md"
    expected_plan = subprocess.check_output(
        ["git", "-C", str(root), "show", PLAN + ":" + plan_path]
    )
    if (root / plan_path).read_bytes() != expected_plan:
        raise ValueError("Approved plan changed")
    import re

    table = expected_plan.decode().split("### 5.2", 1)[1].split("### 5.3", 1)[0]
    allowed = set(re.findall(r"^\| `([^`]+)` \|", table, re.M))
    changed = set(git(root, "diff", "--name-only", PLAN).splitlines())
    changed.update(git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    if changed - allowed:
        raise ValueError("Out-of-allowlist change: " + repr(sorted(changed - allowed)))
    paths = git(root, "ls-tree", "-r", "--name-only", SCIENTIFIC).splitlines()
    # One immutable-object read avoids hundreds of process launches inside the fixed CPU cap.
    from io import BytesIO

    objects = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input="".join(SCIENTIFIC + ":" + p + "\n" for p in paths).encode(),
        capture_output=True,
        check=True,
    )
    stream = BytesIO(objects.stdout)
    hashes = {}
    for p in paths:
        header = stream.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError("Malformed frozen Git object stream")
        frozen = stream.read(int(header[2]))
        if len(frozen) != int(header[2]) or stream.read(1) != b"\n":
            raise ValueError("Incomplete frozen Git object stream")
        hashes[p] = hashlib.sha256(frozen).hexdigest()
        if p not in DOCS and sha(root / p) != hashes[p]:
            raise ValueError("Frozen source changed: " + p)
    if sha(root / MANIFEST) != MANIFEST_SHA:
        raise ValueError("Manifest mismatch")
    profile = json.loads((root / MANIFEST).read_text())
    source = json.loads(
        (root / "docs/task007d/vis/vis1l/evidence/controlled_A/summary.json").read_text()
    )["source_sha256"]
    for p, h in source.items():
        if sha(root / p) != h:
            raise ValueError("Scientific source inventory mismatch: " + p)
    for e in profile["profile"]["planning"]["files"]:
        if sha(root / e["path"]) != e["sha256"]:
            raise ValueError("Planning identity mismatch")
    return {
        "root": str(root),
        "scientific": SCIENTIFIC,
        "plan": PLAN,
        "head": git(root, "rev-parse", "HEAD"),
        "hashes": hashes,
        "source_entries": len(source),
        "profile": profile,
        "dirty": git(root, "status", "--short"),
    }


def admit_environment(root, site):
    """Inspect distributions without executing .pth files or importing numerical packages."""
    root, site = Path(root), Path(site).resolve()
    if not sys.flags.no_site:
        raise ValueError("Launch with -P -S; editable .pth execution is prohibited")
    if sys.version_info[:3] != (3, 12, 14) or platform.system() != "Darwin":
        raise ValueError("Unqualified interpreter/backend")
    versions = {
        p["name"].lower().replace("_", "-"): p["version"]
        for p in tomllib.loads((root / "uv.lock").read_text())["package"]
    }
    inventories = {}
    binaries = {}
    for dist in metadata.distributions(path=[str(site)]):
        name = dist.metadata["Name"].lower().replace("_", "-")
        if name == "defensive-racing-ai":
            continue  # Its editable .pth is never executed; own src is explicit.
        if name in inventories:
            raise ValueError("Duplicate installed distribution: " + name)
        if versions.get(name) != dist.version:
            raise ValueError("Locked distribution mismatch: " + name)
        members = {}
        for entry in dist.files or ():
            if entry.hash is not None and entry.hash.mode == "sha256":
                path = Path(dist.locate_file(entry)).resolve()
                digest = sha(path)
                encoded = base64.urlsafe_b64encode(bytes.fromhex(digest)).rstrip(b"=").decode()
                if encoded != entry.hash.value:
                    raise ValueError("Installed RECORD mismatch: " + str(path))
                members[str(path)] = digest
                if path.suffix in (".so", ".dylib"):
                    binaries[str(path)] = digest
        if not members:
            raise ValueError("Missing installed distribution inventory: " + name)
        inventories[name] = {"version": dist.version, "files": members}
    required = {
        "numpy",
        "scipy",
        "casadi",
        "pandas",
        "pyyaml",
        "psutil",
        "pytest",
        "threadpoolctl",
        "ruff",
    }
    if not required <= inventories.keys():
        raise ValueError("Missing required locked distributions")
    return {
        "python": sys.version,
        "executable": sys.executable,
        "executable_sha256": sha(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "site": str(site),
        "inventories": inventories,
        "native_binaries": binaries,
        "pth_executed": False,
        "historical_solver_binary_equivalence": "UNKNOWN",
    }


def imported_identities(root, environment):
    root = Path(root).resolve()
    members = {p: h for d in environment["inventories"].values() for p, h in d["files"].items()}
    observed = {}
    for name, module in tuple(sys.modules.items()):
        value = getattr(module, "__file__", None)
        if not value:
            continue
        path = Path(value).resolve()
        if name == "apex" or name.startswith("apex."):
            if not path.is_relative_to(root / "src/apex"):
                raise ValueError("Foreign APEX import: " + str(path))
            if environment.get("source_members", {}).get(str(path)) != sha(path):
                raise ValueError("Local module changed after admission: " + name)
            observed[name] = {"path": str(path), "sha256": sha(path)}
        elif name == "preintegration" or name.startswith("preintegration."):
            if not path.is_relative_to(root / "scripts/preintegration"):
                raise ValueError("Foreign execution helper: " + name)
            if environment.get("source_members", {}).get(str(path)) != sha(path):
                raise ValueError("Execution helper changed after admission: " + name)
            observed[name] = {"path": str(path), "sha256": sha(path)}
        elif path.is_relative_to(root / "scripts"):
            if environment.get("source_members", {}).get(str(path)) != sha(path):
                raise ValueError("Foreign or changed native bootstrap helper")
            observed[name] = {"path": str(path), "sha256": sha(path)}
        elif str(path) in members:
            if sha(path) != members[str(path)]:
                raise ValueError("Loaded installed member changed")
            observed[name] = {"path": str(path), "sha256": members[str(path)]}
        elif path.is_relative_to(Path(environment["site"])) and path.suffix != ".pyc":
            raise ValueError("Uninventoried installed import: " + name)
    return observed


@dataclass
class Components:
    controller: object
    planner: object
    tracker: object
    buffer: object
    estimator: object
    urgent: object
    track: object
    validator: object
    parameters: object
    snapshot: dict


def compose(root, solver_factory=None, *, admission):
    """Call only after source/environment/native admission; no plant is owned."""
    if not isinstance(admission, RuntimeAdmission) or Path(root).resolve() != admission.root:
        raise ValueError("Runtime admission required")
    for path, digest in admission.source["hashes"].items():
        if path not in DOCS and sha(Path(root) / path) != digest:
            raise ValueError("Source changed after admission: " + path)
    from apex.config import load_vehicle_parameters
    from apex.control.mpc.controller import MPCController
    from apex.control.mpc.cost import CostScales
    from apex.control.mpc.problem import MPCConfig, MPCProblem
    from apex.control.trajectory.packet import TrajectoryBuffer
    from apex.control.trajectory.planner import TrajectoryPlanner
    from apex.control.trajectory.prediction import RollingDelay, UrgentReplan
    from apex.control.trajectory.tracker import TrackerConfig, TrajectoryTracker
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.optimization.solvers.ipopt import DEFAULT_OPTIONS, IpoptSolver
    from apex.planning_reference.reference import PlanningReference
    from apex.planning_reference.track import load_track

    imported_identities(root, admission.environment)
    root = Path(root)
    manifest = json.loads((root / MANIFEST).read_text())["profile"]
    p = load_vehicle_parameters(root / manifest["vehicle"]["file"]["path"])
    fixture = root / manifest["planning"]["package"]
    track, _, track_id = load_track(fixture / "track_source.json")
    ref = PlanningReference(fixture, track, track_id, feasibility_policy="advisory")
    config = MPCConfig(
        horizon=8,
        dt=0.1,
        substeps=4,
        costs=CostScales(lateral=2),
        tire_physics=RACING_TIRE_PHYSICS,
        tracker_margin=0.08,
        racing_reference=True,
        progress_weight=0,
    )
    options = {**DEFAULT_OPTIONS, "ipopt.warm_start_init_point": "yes"}
    match(asdict(config), manifest["nmpc"]["configuration"])
    match(options, manifest["nmpc"]["solver"]["explicit_effective_options"])
    match(asdict(TrackerConfig()), manifest["tracker"]["configuration"])
    problem = MPCProblem(p, config)
    solver = (solver_factory or (lambda pb, opts: IpoptSolver(pb, opts)))(problem, options)
    controller = MPCController(
        p, track, solver, problem, ref, warm_start=True, racing_reference=ref
    )
    tracker = TrajectoryTracker(
        p, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    )
    snapshot = {
        "mpc": asdict(config),
        "tracker": asdict(tracker.config),
        "solver": options,
        "vehicle": asdict(p),
        "planning": manifest["planning"],
        "architecture": "A",
        "warm_start": True,
        "progress_weight": 0,
    }
    match(tracker.lower.tolist(), manifest["tracker"]["control_lower"])
    match(tracker.upper.tolist(), manifest["tracker"]["control_upper"])
    validation_model = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    return Components(
        controller,
        TrajectoryPlanner(controller, track),
        tracker,
        TrajectoryBuffer(),
        RollingDelay(),
        UrgentReplan(),
        track,
        validation_model.diagnostics,
        p,
        canonical(snapshot),
    )


@dataclass(frozen=True)
class RuntimeAdmission:
    root: Path
    source: dict
    environment: dict
    native: dict


def bootstrap(root, site):
    """Isolated startup: complete stdlib admission before supported native initialization."""
    import os

    root = Path(root).resolve()
    if os.environ.get("PYTHONHASHSEED") != "0" or sys.flags.hash_randomization:
        raise ValueError("Fresh PYTHONHASHSEED=0 process required")
    source = admit_source(root)
    environment = admit_environment(root, site)
    environment["source_members"] = {
        str(p.resolve()): sha(p)
        for folder in (root / "src", root / "scripts")
        for p in folder.rglob("*.py")
    }
    if any(n in sys.modules for n in ("numpy", "scipy", "casadi")):
        raise ValueError("Numerical import preceded admission")
    # -I -S excludes all .pth/editable processing. Preserve only interpreter stdlib paths.
    for path in sys.path:
        if "site-packages" in path and Path(path).resolve() != Path(site).resolve():
            raise ValueError("Conflicting installed package root")
    for path in (root / "src", root / "scripts", Path(site).resolve()):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from threading_study.config import THREAD_VARIABLES, configure_accelerate

    for key in THREAD_VARIABLES:
        os.environ.pop(key, None)
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    native = configure_accelerate(1)
    native["helper_sha256"] = sha(root / "scripts/threading_study/config.py")
    result = RuntimeAdmission(root, source, environment, native)
    _runtime_admissions[root] = result
    return result


def runtime_admission(root):
    """Retrieve this process's completed bootstrap, never silently initialize a backend."""
    try:
        return _runtime_admissions[Path(root).resolve()]
    except KeyError as error:
        raise ValueError("Bootstrap required in fresh process") from error
