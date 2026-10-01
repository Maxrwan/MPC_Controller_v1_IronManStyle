"""Archive study source and hash retained evidence without touching earlier results."""

import hashlib
import json
import random
import zipfile
from datetime import datetime, timezone

from threading_study.config import OUT, ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write():
    previous = json.loads(
        (ROOT / "results/mpc_parameter_study/provenance_manifest.json").read_text()
    )
    production = {
        k: digest(ROOT / k) == v
        for k, v in previous["source_files_sha256"].items()
        if k.startswith("src/")
    }
    assert production and all(production.values()), "Production code changed since Task006.2"
    assert (OUT / "frozen_candidates.json").read_bytes() == (
        ROOT / "results/mpc_parameter_study/selected_candidates.json"
    ).read_bytes()
    sources = [ROOT / "AGENTS.md", ROOT / "pyproject.toml", ROOT / "uv.lock"]
    for directory, suffix in [
        ("src", ".py"),
        ("scripts", ".py"),
        ("tests", ".py"),
        ("docs", ".md"),
        ("configs", ".yaml"),
    ]:
        sources.extend(sorted((ROOT / directory).rglob("*" + suffix)))
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    archive = OUT / "reproduction_sources.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sources:
            z.write(p, p.relative_to(ROOT))
    order = []
    for replicate in range(3):
        conditions = [(w, n) for w in ["C", "D"] for n in [1, 2, 4, 8]]
        random.Random(6220 + replicate).shuffle(conditions)
        order.append(dict(replicate=replicate, seed=6220 + replicate, conditions=conditions))
    result_hashes = {
        str(p.relative_to(OUT)): digest(p)
        for p in sorted(OUT.rglob("*"))
        if p.is_file() and p.name not in ["provenance_manifest.json", "reproduction_sources.zip"]
    }
    report = dict(
        packaged_utc=datetime.now(timezone.utc).isoformat(),
        source_files_sha256=source_hashes,
        result_files_sha256=result_hashes,
        archive_sha256=digest(archive),
        primary_order=order,
        closed_loop_order=[4, 1, 8, 2],
        production_unchanged_vs_task0062=production,
        frozen_candidates_byte_identical=True,
        tests=(OUT / "validation_tests.txt").read_text(),
        lint=(OUT / "validation_lint.txt").read_text(),
        timing_policy="Primary, closed-loop and component experiments serialized. "
        "Tests began after timing collection. Lightweight inspection/editing "
        "and ordinary OS activity were not excluded.",
        date_note="Primary and closed-loop data retained from the original study session; "
        "supplementary component probes and final validation completed on resume. "
        "Packaging date is not a benchmark timestamp.",
    )
    (OUT / "provenance_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Archived {len(sources)} source files; verified {len(production)} production files")


if __name__ == "__main__":
    write()
