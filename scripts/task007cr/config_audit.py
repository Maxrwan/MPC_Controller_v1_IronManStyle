"""Hashes, frozen settings and behavioral audit of the disclosed historical loader variant."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path


def run(output=Path("results/task007cr")):
    import numpy as np

    from apex.config import load_vehicle_parameters
    from apex.control.mpc.preview import make_preview
    from apex.planning_reference.reference import PlanningReference
    from apex.planning_reference.track import load_track

    previous = json.loads((output / "preservation.json").read_text())["runtime_before"]
    changed = [
        path
        for path, value in previous.items()
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != value
    ]
    assert changed == ["src/apex/simulation/asynchronous.py"], changed
    vehicle_path = Path("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    historical_sources = json.loads(Path("results/task007b/provenance.json").read_text())[
        "source_sha256"
    ]
    vehicle_sha = hashlib.sha256(vehicle_path.read_bytes()).hexdigest()
    assert historical_sources[str(vehicle_path)] == vehicle_sha
    vehicle_parameters = asdict(load_vehicle_parameters(vehicle_path))
    results = []
    mapping = {"e": "b3_g2.5_w1", "f": "b3_g2.5_w2", "c": "b4_g2_w0"}
    for path in sorted(output.glob("r[12347]_*/summary.json")):
        label = path.parent.name.split("_")[1]
        old = json.loads((Path("results/task007b") / mapping[label] / "summary.json").read_text())
        new = json.loads(path.read_text())
        checks = {
            k: old[k] == new[k]
            for k in ["fixture_sha256", "planner_config", "candidate", "native_control"]
        }
        checks["fixture_bytes"] = all(
            hashlib.sha256((path.parent / "fixture" / name).read_bytes()).hexdigest() == digest
            for name, digest in old["fixture_sha256"].items()
        )
        checks["frozen_runtime_hashes"] = all(
            new["source_sha256"].get(k) == v
            for k, v in old["source_sha256"].items()
            if k not in changed
        )
        if label in ["e", "f"]:
            checks["simulation_configuration"] = old["config"] == new["config"]
        model = json.loads((path.parent / "nlp_model.json").read_text())
        checks["captured_configuration"] = model["config"] == new["planner_config"]
        checks["captured_vehicle"] = model["vehicle"] == vehicle_parameters
        assert all(checks.values()), (path, checks)
        results.append(
            dict(
                case=path.parent.name,
                checks=checks,
                original_runtime=old["source_sha256"],
                current_runtime=new["source_sha256"],
                captured_graph_sha256=hashlib.sha256(model["graph"].encode()).hexdigest(),
                captured_solver_options=model["solver_options"],
            )
        )
    anchors = []
    for label in ["e", "f", "e_repeat", "f_repeat"]:
        old = json.loads(
            (Path("results/task007b") / mapping[label[0]] / "summary.json").read_text()
        )
        current = json.loads(
            (Path("results/task007c") / ("anchor_" + label) / "summary.json").read_text()
        )
        checks = {
            k: old[k] == current[k]
            for k in [
                "config",
                "planner_config",
                "native_control",
                "fixture_sha256",
                "source_sha256",
            ]
        }
        assert all(checks.values()), (label, checks)
        anchors.append(dict(case="anchor_" + label, checks=checks))
    folder = Path("results/task007b/b0")
    track, _, identity = load_track(folder / "fixture/track_source.json")
    ref = PlanningReference(folder / "fixture", track, identity, feasibility_policy="advisory")
    vehicle = load_vehicle_parameters(Path("configs/vehicles/synthetic_dynamic_test_vehicle.yaml"))
    records = json.loads((folder / "predictions.json").read_text())
    maximum = 0.0
    count = 0
    for r in records:
        p = r["prediction"]
        if not p:
            continue
        preview = make_preview(
            track, vehicle, ref, p["preview_progress"][0], 4, 0.1, racing_reference=ref
        )
        maximum = max(
            maximum,
            float(np.max(abs(preview.values - np.asarray(p["preview"])))),
            float(np.max(abs(preview.progress - np.asarray(p["preview_progress"])))),
        )
        count += 1
    report = dict(
        runtime_files_changed=changed,
        vehicle_file_sha256=vehicle_sha,
        vehicle_parameters=vehicle_parameters,
        runtime_files_added=["src/apex/simulation/diagnostic_timing.py"],
        cases=results,
        original_task007c_anchor_checks=anchors,
        early_b0_loader=dict(
            exact_old_body_available=False,
            old_hash=json.loads((folder / "summary.json").read_text())["source_sha256"][
                "src/apex/planning_reference/reference.py"
            ],
            current_hash=hashlib.sha256(
                Path("src/apex/planning_reference/reference.py").read_bytes()
            ).hexdigest(),
            interpolation=ref.manifest["interpolation"],
            previews_checked=count,
            maximum_preview_or_progress_difference=maximum,
            conclusion=(
                "Behavioral preview comparison only; does not reconstruct the missing old "
                "source body. Primary E/F/C old sources match frozen hashes."
            ),
        ),
    )
    (output / "configuration_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    run()
