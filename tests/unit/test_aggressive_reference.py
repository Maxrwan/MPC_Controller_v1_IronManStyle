"""Aggressive intent stays unmodified; hard validity is never demoted."""

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "configs/planning/synthetic_grand_prix_v1"
sys.path.insert(0, str(ROOT / "scripts"))
from task007b import references  # noqa: E402
from task007b.metrics import local_tracking_error, planning_deviation  # noqa: E402


@pytest.fixture(scope="module")
def packages(tmp_path_factory):
    output = tmp_path_factory.mktemp("aggression")
    original = references.PACKAGES
    references.PACKAGES = output
    try:
        references.generate([1.0, 1.5, 2.5])
    finally:
        references.PACKAGES = original
    track, _, identity = load_track(BASE / "track_source.json")
    return output, track, identity


def test_scaling_geometry_and_cap(packages):
    output, track, identity = packages
    base = PlanningReference(BASE, track, identity)
    for gamma in [1.0, 1.5, 2.5]:
        folder = output / references.package_name(gamma)
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        ref = PlanningReference(folder, track, identity, feasibility_policy="advisory")
        assert before == {p.name: p.read_bytes() for p in folder.iterdir()}
        for key in ["s_track_m", "e_y_ref_m", "e_psi_ref_rad", "kappa_ref_1pm"]:
            np.testing.assert_allclose(ref.frame[key], base.frame[key], rtol=0, atol=1e-14)
        for s in np.linspace(-track.length, 3 * track.length, 301):
            assert ref(s) == pytest.approx(min(gamma * base(s), 6), abs=1e-10)
            assert 0.5 <= ref(s) <= 6 + 1e-12
        if gamma > 1:
            assert ref.validation["feasibility_warnings"]
            with pytest.raises(ValueError):
                PlanningReference(folder, track, identity)
    assert (output / references.package_name(1.0) / "planning_reference.csv").read_bytes() == (
        BASE / "planning_reference.csv"
    ).read_bytes()


def test_generation_determinism(packages, tmp_path, monkeypatch):
    monkeypatch.setattr(references, "PACKAGES", tmp_path)
    references.generate([2.5])
    folder = packages[0] / references.package_name(2.5)
    for path in folder.iterdir():
        assert path.read_bytes() == (tmp_path / folder.name / path.name).read_bytes()


@pytest.mark.parametrize(
    "field,value",
    [
        ("units", "bad"),
        ("aggression_factor", -1),
        ("aggression_factor", float("nan")),
        ("track_sha256", "bad"),
        ("aggression_policy", "repair"),
    ],
)
def test_advisory_still_rejects_manifest(packages, tmp_path, field, value):
    folder = tmp_path / "reference"
    shutil.copytree(packages[0] / references.package_name(1.5), folder)
    p = folder / "planning_manifest.json"
    m = json.loads(p.read_text())
    m[field] = value
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        PlanningReference(folder, packages[1], packages[2], feasibility_policy="advisory")


@pytest.mark.parametrize(
    "field,value",
    [("v_ref_mps", 7), ("e_y_ref_m", 0.5), ("s_track_m", -1), ("e_psi_ref_rad", np.nan)],
)
def test_advisory_still_rejects_channels(packages, tmp_path, field, value):
    folder = tmp_path / "reference"
    shutil.copytree(packages[0] / references.package_name(1.5), folder)
    p = folder / "planning_reference.csv"
    f = pd.read_csv(p)
    f.loc[10, field] = value
    f.to_csv(p, index=False)
    with pytest.raises(ValueError):
        PlanningReference(folder, packages[1], packages[2], feasibility_policy="advisory")


def test_predicted_progress_deviation_is_not_vehicle_error():
    class Intent:
        def sample(self, s):
            return dict(
                v_ref_mps=2 + s * 0.01, kappa_ref_1pm=0.2, e_psi_ref_rad=0.1, e_y_ref_m=0.02 * s
            )

    x = np.array([[3, 0.1, 0.5, 0.2, 10, 0.3], [4, 0.2, 0.6, 0.3, 20, 0.5]])
    nominal, error = planning_deviation(x, Intent())
    np.testing.assert_allclose(nominal[:, 0], [2.1, 2.2])
    np.testing.assert_allclose(error[:, 5], [0.1, 0.1])
    np.testing.assert_allclose(error[:, 0], [0.9, 1.8])
    vehicle = x + np.array([0.01, 0.001, 0.002, 0.003, 0, 0.004])
    local = local_tracking_error(vehicle, x)
    assert local[0, 5] == pytest.approx(0.004)
    assert error[0, 5] != local[0, 5]


def test_local_heading_wrap():
    x = np.zeros((1, 6))
    nominal = x.copy()
    x[0, 3] = -np.pi + 0.01
    nominal[0, 3] = np.pi - 0.01
    assert local_tracking_error(x, nominal)[0, 3] == pytest.approx(0.02)
