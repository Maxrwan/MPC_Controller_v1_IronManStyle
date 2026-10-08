"""Final preservation/configuration/physical chronology checks and artifact inventory."""

import hashlib
import json
from pathlib import Path

from threading_study.config import configure_accelerate

ROOT = Path("results/task007c_resume")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not audit during measured repetitions")
    configure_accelerate(1)
    from async_study.analysis import audit as chronology
    from task007c_resume.audit import run as configurations

    configurations()
    chronology(ROOT)
    baseline = json.loads((ROOT / "g2_w0_vy1_r1_n4_fixed_l1/summary.json").read_text())
    diagnostic_cases = []
    for folder in sorted(ROOT.glob("latency_n*")):
        s = json.loads((folder / "summary.json").read_text())
        assert s["source_sha256"] == baseline["source_sha256"]
        assert s["native_control"]["mode_name"] == "single"
        expected = json.loads(json.dumps(baseline["planner_config"]))
        expected["horizon"] = int(folder.name.split("_")[1][1:])
        assert s["planner_config"] == expected
        diagnostic_cases.append(folder.name)
    inventory = dict(
        status="Evidence inventory; acceptance is documented separately in the scientific report.",
        diagnostic_cases_verified=diagnostic_cases,
        source_sha256={str(p): sha(p) for base in ["src", "scripts/task007c_resume"]
                       for p in sorted(Path(base).rglob("*.py"))},
        document_sha256={str(p): sha(p) for p in sorted(Path("docs").glob("TASK007C*.md"))},
        result_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(ROOT.rglob("*"))
                       if p.is_file() and p.name != "provenance.json"},
    )
    (ROOT / "provenance.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print("Final inventory:", len(inventory["result_sha256"]), "result files", flush=True)


if __name__ == "__main__":
    main()
