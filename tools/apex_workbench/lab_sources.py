"""Versioned scientific dependency inventory. Never fill retained identities from disk."""

import re

VERSION = "apex-dynamic-lab-sources/1"
REQUIRED = (
    "configs/vehicles/synthetic_dynamic_test_vehicle.yaml",
    "scripts/run_dynamic_bicycle_demo.py",
    "scripts/threading_study/config.py",
    *(
        "src/apex/" + name
        for name in (
            "__init__.py",
            "config.py",
            "state.py",
            "control/__init__.py",
            "control/base.py",
            "coordinates/__init__.py",
            "coordinates/angles.py",
            "coordinates/frenet.py",
            "models/__init__.py",
            "models/base.py",
            "models/constants.py",
            "models/errors.py",
            "models/frenet.py",
            "models/integration.py",
            "models/vehicle/__init__.py",
            "models/vehicle/parameters.py",
            "models/vehicle/dynamic_bicycle.py",
            "models/vehicle/load_transfer.py",
            "models/vehicle/force_allocation.py",
            "models/tire/__init__.py",
            "models/tire/base.py",
            "models/tire/config.py",
            "models/tire/linear.py",
            "models/tire/grip.py",
            "simulation/__init__.py",
            "simulation/runner.py",
            "simulation/timing.py",
            "track/__init__.py",
            "track/base.py",
            "track/centerline.py",
            "track/closed_track.py",
            "track/io.py",
            "track/progress.py",
            "track/synthetic.py",
        )
    ),
    *(
        "tools/apex_workbench/" + name
        for name in (
            "__init__.py",
            "configuration.py",
            "jobs.py",
            "worker.py",
            "lifecycle.py",
            "storage.py",
            "lab_configuration.py",
            "lab_sources.py",
            "dynamic_lab.py",
            "lab_reporting.py",
            "lab_evidence.py",
            "lab_comparison.py",
            "comparison.py",
            "plots.py",
            "app.py",
            "qualification_math.py",
            "qualification.py",
            "qualification_campaign.py",
            "qualification_reference.py",
        )
    ),
)


def from_captured(ledger):
    if not isinstance(ledger, dict) or not set(REQUIRED) <= set(ledger):
        raise ValueError("Incomplete versioned laboratory scientific source inventory")
    if any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v) for v in ledger.values()):
        raise ValueError("Invalid captured source digest")
    return {"version": VERSION, "sha256": {name: ledger[name] for name in REQUIRED}}


def validate(request):
    expected = from_captured(request["provenance"]["source_sha256"])
    if request.get("source_inventory") != expected:
        raise ValueError(
            "Missing/conflicting versioned source inventory; historical bytes preserved"
        )
    return expected
