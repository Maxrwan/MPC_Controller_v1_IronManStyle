"""Identity and representation checks; no genuine optimizer calls."""

import json
import sys
from dataclasses import asdict
from pathlib import Path
from types import ModuleType

import pytest

from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.preintegration import profile

ROOT = Path(__file__).resolve().parents[2]


def test_effective_frozen_configuration_and_roundtrip():
    expected = json.loads((ROOT / profile.MANIFEST).read_text())["profile"]["nmpc"]["configuration"]
    actual = asdict(
        MPCConfig(
            horizon=8,
            dt=0.1,
            substeps=4,
            costs=CostScales(lateral=2),
            tire_physics=RACING_TIRE_PHYSICS,
            tracker_margin=0.08,
            racing_reference=True,
            progress_weight=0,
        )
    )
    profile.match(actual, expected)
    captured = {"configuration": actual, "failed_plan_ids": (), "missing": None, "enabled": True}
    profile.match(captured, json.loads(json.dumps(profile.canonical(captured))))
    assert captured["failed_plan_ids"] == ()
    with pytest.raises(ValueError):
        profile.match(asdict(MPCConfig()), expected)
    with pytest.raises(ValueError):
        profile.match({**captured, "enabled": 1}, captured)
    with pytest.raises(ValueError):
        profile.match({**captured, "unknown": 1}, captured)
    with pytest.raises(ValueError):
        profile.canonical(float("nan"))


def test_frozen_source_change_rejects_without_touching_source(monkeypatch):
    original = profile.sha

    def altered(path):
        return "0" * 64 if str(path).endswith("src/apex/state.py") else original(path)

    monkeypatch.setattr(profile, "sha", altered)
    with pytest.raises(ValueError, match="Frozen source changed"):
        profile.admit_source(ROOT)


def test_foreign_actual_import_is_rejected(monkeypatch):
    module = ModuleType("apex.untrusted")
    module.__file__ = str(ROOT / "tests/unit/test_preintegration_profile.py")
    monkeypatch.setitem(sys.modules, "apex.untrusted", module)
    with pytest.raises(ValueError, match="Foreign APEX"):
        profile.imported_identities(ROOT, profile.runtime_admission(ROOT).environment)


def test_factory_requires_real_runtime_admission():
    with pytest.raises(ValueError, match="Runtime admission"):
        profile.compose(ROOT, admission={})


def test_genuine_profile_composition_with_injected_no_solve_backend():
    """Real configuration/problem/TVLQR construction, explicitly zero optimizer calls."""
    calls = []

    class NoSolve:
        def solve(self, request):
            calls.append(request)
            raise AssertionError("No solve authorized in this composition check")

    admitted = profile.runtime_admission(ROOT)
    comp = profile.compose(ROOT, lambda problem, options: NoSolve(), admission=admitted)
    expected = json.loads((ROOT / profile.MANIFEST).read_text())["profile"]
    profile.match(comp.snapshot["mpc"], expected["nmpc"]["configuration"])
    profile.match(comp.snapshot["solver"], expected["nmpc"]["solver"]["explicit_effective_options"])
    assert comp.controller.solution is None and not calls
    assert (
        comp.buffer.active is None and comp.validator.__self__ is not comp.controller.problem.model
    )
