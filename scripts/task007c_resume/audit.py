"""Verify frozen runtime, archived evidence, and explicit experimental configuration changes."""

import hashlib
import json
from pathlib import Path

ROOT = Path("results/task007c_resume")
ALLOWED = {"src/apex/control/mpc/cost.py", "src/apex/control/mpc/controller.py"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not run bulk audits during measured repetitions")
    before = json.loads((ROOT / "preservation.json").read_text())["runtime_before"]
    changed = {p for p, digest in before.items() if sha(p) != digest}
    assert changed == ALLOWED, changed
    historical = {}
    for task in ["task007b", "task007c", "task007cr"]:
        root = Path("results") / task
        provenance = json.loads((root / "provenance.json").read_text())
        for name, digest in provenance["result_sha256"].items():
            path = Path(name) if name.startswith("results/") else root / name
            assert sha(path) == digest, path
        historical[task] = len(provenance["result_sha256"])
    baseline = json.loads((ROOT / "g2_w0_vy1_r1_n4_fixed_l1/summary.json").read_text())
    for name, digest in baseline["source_sha256"].items():
        assert sha(name) == digest, f"Current runtime differs from retained case: {name}"
    histories = json.loads((ROOT / "histories.json").read_text())
    cases = []
    for path in sorted(ROOT.glob("g*/summary.json")):
        summary = json.loads(path.read_text())
        cell = json.loads((path.parent / "cell.json").read_text())
        expected = json.loads(json.dumps(baseline["planner_config"]))
        expected["costs"].update(alpha_vy=cell["alpha_vy"], alpha_r=cell["alpha_r"])
        expected.update(horizon=cell["horizon"], progress_weight=cell["progress_weight"])
        assert summary["planner_config"] == expected, path
        assert summary["native_control"]["mode_name"] == "single", path
        assert summary["candidate"] == baseline["candidate"], path
        assert summary["source_sha256"] == baseline["source_sha256"], path
        for name, digest in summary["fixture_sha256"].items():
            assert sha(path.parent / "fixture" / name) == digest, path
        timing = summary["diagnostic_timing"]
        history = cell["history"]
        if history == "fixed":
            assert timing["mode"] == "fixed", path
            assert timing["planner"] == [0.035] and timing["codriver"] == [0.001], path
        elif history == "measured":
            assert timing is None, path
            assert summary["config"]["latency_mode"] == "measured", path
            assert summary["config"]["codriver_delay"] is None, path
        else:
            trace = json.loads(Path(histories[history]["path"]).read_text())
            assert timing["mode"] == "replay", path
            for channel in ["planner", "codriver"]:
                assert timing[channel] == trace[channel], path
        cases.append(
            dict(
                case=path.parent.name,
                configuration_verified=True,
                runtime_verified=True,
                fixture_verified=True,
                timing_verified=True,
            )
        )
    report = dict(
        runtime_changes=sorted(changed),
        historical_artifacts_verified=historical,
        cases=cases,
        note=(
            "Only approved cost multipliers and compatible terminal construction change runtime "
            "mathematics. Effective diagnostic_timing overrides the fallback latency_mode field "
            "in imposed-history cases."
        ),
    )
    (ROOT / "configuration_preservation_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Configuration and preservation audit:", len(cases), "cases;", historical)


if __name__ == "__main__":
    run()
