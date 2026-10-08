"""Preserve accepted baselines, per-case provenance and a portable source snapshot."""

import hashlib
import json
import platform
import sys
import zipfile
from pathlib import Path


def package(output):
    root = Path.cwd()
    output = Path(output)

    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    previous = json.loads((root / "results/task007a/provenance.json").read_text())
    assert all(
        sha(root / "results/task007a" / p) == h for p, h in previous["result_sha256"].items()
    )
    assert all(
        sha(root / p) == h
        for p, h in previous["source_sha256"].items()
        if p.startswith("configs/planning/synthetic_grand_prix_v1/")
    )
    older_root = root / "results/linear_mpc_codriver"
    older = json.loads((older_root / "provenance.json").read_text())
    assert all(sha(older_root / p) == h for p, h in older["result_files_sha256"].items())
    changes = [
        p
        for p, h in previous["source_sha256"].items()
        if p.startswith("src/") and sha(root / p) != h
    ]
    assert set(changes) == {
        "src/apex/control/mpc/cost.py",
        "src/apex/control/mpc/problem.py",
        "src/apex/control/mpc/controller.py",
        "src/apex/planning_reference/reference.py",
    }
    cases = []
    for p in sorted(output.glob("*/summary.json")):
        d = json.loads(p.read_text())
        f = p.parent / "fixture"
        assert all(sha(f / name) == h for name, h in d["fixture_sha256"].items()), p
        cases.append(
            dict(
                case=p.parent.name,
                gamma=d["gamma"],
                progress_weight=d["progress_weight"],
                mode=d["config"]["latency_mode"],
                laps=d["config"]["laps"],
                duration=d["config"]["duration"],
                injected_delay=d["config"]["injected_delay"],
                source_sha256=d["source_sha256"],
                fixture_sha256=d["fixture_sha256"],
            )
        )
    (output / "study_manifest.json").write_text(json.dumps(cases, indent=2) + "\n")
    import casadi
    import numpy
    import scipy

    (output / "environment.json").write_text(
        json.dumps(
            dict(
                platform=platform.platform(),
                python=sys.version,
                numpy=numpy.__version__,
                scipy=scipy.__version__,
                casadi=casadi.__version__,
                native_backend=(
                    "Accelerate SINGLE via supported API; per-case set/get status recorded"
                ),
                chronology=(
                    "serial fresh subprocess benchmarks; no concurrent tests, "
                    "rendering or bulk numerical analysis"
                ),
            ),
            indent=2,
        )
        + "\n"
    )
    files = sorted(
        p
        for folder in ["src", "scripts", "tests", "docs", "configs"]
        for p in (root / folder).rglob("*")
        if p.is_file() and p.suffix in [".py", ".md", ".json", ".yaml", ".yml", ".csv"]
    )
    files += [root / p for p in ["README.md", "AGENTS.md", "pyproject.toml", "uv.lock"]]
    with zipfile.ZipFile(output / "source_snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, p.relative_to(root))
    provenance = dict(
        previous_task007a_artifacts_verified=len(previous["result_sha256"]),
        original_fixture_verified=True,
        previous_task0064_artifacts_verified=len(older["result_files_sha256"]),
        existing_runtime_files_changed=changes,
        source_sha256={str(p.relative_to(root)): sha(p) for p in files},
        case_fixture_hashes_verified=True,
        runtime_source_variants_note=(
            "Early B0 preceded additive capped-polynomial loader support; per-case source hashes "
            "retained. Control/plant mathematics frozen apart from explicit progress weight."
        ),
    )
    provenance["result_sha256"] = {
        str(p.relative_to(output)): sha(p)
        for p in output.rglob("*")
        if p.is_file() and p.name != "provenance.json"
    }
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    with zipfile.ZipFile(output / "source_snapshot.zip") as archive:
        assert archive.testzip() is None
    print(
        "Packaged",
        len(files),
        "source files;",
        len(cases),
        "case fixtures verified; Task007A unchanged",
    )
