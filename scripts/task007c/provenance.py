"""Verify unchanged runtime, archived evidence, fixtures and anchor configurations."""

import hashlib
import json
from pathlib import Path

from task007c.anchors import ANCHORS


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(output=Path("results/task007c")):
    previous = Path("results/task007b")
    archive = json.loads((previous / "provenance.json").read_text())
    baseline = json.loads((output / "baseline_preservation.json").read_text())
    runtime = baseline["runtime_source_sha256"]
    assert all(digest(path) == value for path, value in runtime.items())
    assert all(digest(previous / path) == value for path, value in archive["result_sha256"].items())
    records = []
    for letter, old_case in (*ANCHORS, ("e_repeat", "b3_g2.5_w1"), ("f_repeat", "b3_g2.5_w2")):
        folder = output / ("anchor_" + letter)
        old = json.loads((previous / old_case / "summary.json").read_text())
        new = json.loads((folder / "summary.json").read_text())
        checks = {
            key: new[key] == old[key]
            for key in [
                "source_sha256",
                "fixture_sha256",
                "config",
                "planner_config",
                "native_control",
            ]
        }
        checks["runtime_matches_preserved_baseline"] = new["source_sha256"] == runtime
        checks["fixture_bytes_match"] = all(
            digest(folder / "fixture" / path) == value
            for path, value in old["fixture_sha256"].items()
        )
        old_events = json.loads((previous / old_case / "events.json").read_text())
        new_events = json.loads((folder / "events.json").read_text())
        for key in ["source_state", "predicted_state", "prepositioned_control"]:
            checks["startup_" + key] = old_events["plans"][0][key] == new_events["plans"][0][key]
        differences = sorted(
            key
            for key in old["source_sha256"].keys() | new["source_sha256"].keys()
            if old["source_sha256"].get(key) != new["source_sha256"].get(key)
        )
        # The accepted Task007B provenance explicitly records its early B0 loader variant.
        documented_early_loader_variant = letter == "a" and differences == [
            "src/apex/planning_reference/reference.py",
            "src/apex/planning_reference/speed_polynomial.py",
        ]
        assert all(v for k, v in checks.items() if k != "source_sha256"), (folder, checks)
        assert checks["source_sha256"] or documented_early_loader_variant, differences
        records.append(
            dict(
                case=folder.name,
                archived_case=old_case,
                checks=checks,
                source_differences_from_original=differences,
                documented_task007b_loader_variant=documented_early_loader_variant,
            )
        )
    result = dict(
        runtime_files_unchanged=len(runtime),
        task007b_artifacts_unchanged=len(archive["result_sha256"]),
        cases=records,
        note="Measured timing traces differ; equality of configuration is not equality of latency.",
    )
    (output / "anchor_provenance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        "Verified unchanged runtime, archived artifacts and", len(records), "anchor configurations"
    )
    return result


if __name__ == "__main__":
    verify()
