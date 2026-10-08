"""Verify untouched historical evidence and archive final diagnostic sources and hashes."""

import hashlib
import json
import zipfile
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path("results/task007cr")
    preserved = {}
    for study in ["task007b", "task007c"]:
        manifest = Path("results") / study / "provenance.json"
        original = json.loads(manifest.read_text())
        entries = original["result_sha256"]
        missing = [
            p
            for p, digest in entries.items()
            if not (manifest.parent / p).exists() or sha(manifest.parent / p) != digest
        ]
        if missing:
            raise RuntimeError(f"Historical artifacts changed: {missing}")
        preserved[study] = dict(artifacts_verified=len(entries), provenance_sha256=sha(manifest))
    sources = sorted(
        p
        for folder in ["src", "scripts", "tests", "docs", "configs"]
        for p in Path(folder).rglob("*")
        if p.is_file() and p.suffix in [".py", ".md", ".json", ".yaml", ".yml", ".csv"]
    )
    sources += [Path(p) for p in ["README.md", "AGENTS.md", "pyproject.toml", "uv.lock"]]
    with zipfile.ZipFile(root / "source_snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sources:
            archive.write(path, str(path))
    report = dict(
        status="Task007C-R complete; C1-C4 not executed",
        historical_preservation=preserved,
        source_sha256={str(p): sha(p) for p in sources},
        result_sha256={
            str(p): sha(p)
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.name != "provenance.json"
        },
    )
    (root / "provenance.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Historical preservation verified", preserved)
    print("Archived", len(sources), "source files and", len(report["result_sha256"]), "results")


if __name__ == "__main__":
    main()
