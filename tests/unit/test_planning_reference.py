"""Serialized offline interface, geometry semantics and backward-compatible preview."""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from apex.planning_reference.reference import PlanningReference, intersection_count
from apex.planning_reference.track import load_track

FIXTURE = Path(__file__).resolve().parents[2] / "configs/planning/synthetic_grand_prix_v1"


@pytest.fixture(scope="module")
def loaded():
    track, source, identity = load_track(FIXTURE / "track_source.json")
    return track, source, identity, PlanningReference(FIXTURE, track, identity)


def test_geometry_and_generation_source_deterministic(loaded):
    track, _, identity, _ = loaded
    other, _, same = load_track(FIXTURE / "track_source.json")
    assert identity == same and track.length == other.length
    for s in np.linspace(0, track.length, 20):
        np.testing.assert_array_equal(track.centerline.geometry(s), other.centerline.geometry(s))
        g = track.sample(s)
        projected = track.project_point(g.x, g.y)
        distance = (projected - s + track.length / 2) % track.length - track.length / 2
        assert abs(distance) < 1e-7
    a, b = track.sample(0), track.sample(track.length - 1e-7)
    assert abs(a.curvature - b.curvature) < 1e-6
    assert abs(a.heading - b.heading) < 1e-6


def test_reference_gates_and_nontrivial_racing_line(loaded):
    track, _, _, ref = loaded
    v = ref.validation
    assert v["accepted"] and v["sampled_self_intersections"] == 0
    assert v["minimum_boundary_clearance_m"] >= 0.08
    assert 0.5 < v["speed_min"] < v["speed_max"] <= 6
    assert v["maximum_lateral_demand_mps2"] < 2
    assert v["maximum_steering_rad"] < 0.4 and v["maximum_steering_rate_rad_s"] < 1
    assert v["acceleration_max"] < 0.65 and v["braking_min"] > -0.85
    assert np.ptp(ref.frame.e_y_ref_m) > 0.3
    assert (
        max(abs(ref.frame.kappa_ref_1pm - np.array([track.sample(s).curvature for s in ref.s])))
        > 0.05
    )


@pytest.mark.parametrize("laps", [-2, 0, 1, 7])
def test_periodic_lookup(loaded, laps):
    track, _, _, ref = loaded
    for s in [0, 0.01, 23.45, track.length - 0.001]:
        a, b = ref.sample(s), ref.sample(s + laps * track.length)
        np.testing.assert_allclose(list(a.values()), list(b.values()), atol=1e-10)
    with pytest.raises(ValueError):
        ref.sample(np.nan)


@pytest.mark.parametrize(
    "key,value",
    [
        ("schema_version", 2),
        ("units", "imperial"),
        ("track_sha256", "bad"),
        ("tracker_margin_m", 0),
        ("progress", "racing_arc_length"),
    ],
)
def test_manifest_rejection(tmp_path, loaded, key, value):
    shutil.copytree(FIXTURE, tmp_path / "ref")
    p = tmp_path / "ref/planning_manifest.json"
    m = json.loads(p.read_text())
    m[key] = value
    p.write_text(json.dumps(m))
    with pytest.raises(ValueError):
        PlanningReference(tmp_path / "ref", loaded[0], loaded[2])


@pytest.mark.parametrize(
    "bad", ["nan", "progress", "seam", "heading", "speed", "margin", "curvature"]
)
def test_invalid_channels_rejected(tmp_path, loaded, bad):
    shutil.copytree(FIXTURE, tmp_path / "ref")
    p = tmp_path / "ref/planning_reference.csv"
    f = pd.read_csv(p)
    if bad == "nan":
        f.loc[3, "e_y_ref_m"] = np.nan
    if bad == "progress":
        f.loc[3, "s_track_m"] = f.loc[2, "s_track_m"]
    if bad == "seam":
        f.loc[len(f) - 1, "v_ref_mps"] += 0.1
    if bad == "heading":
        f.loc[3, "e_psi_ref_rad"] = 4
    if bad == "speed":
        f.loc[3, "v_ref_mps"] = 0
    if bad == "margin":
        f.loc[100, "e_y_ref_m"] = 0.5
    if bad == "curvature":
        f.loc[100, "kappa_ref_1pm"] = 3
    f.to_csv(p, index=False)
    with pytest.raises(ValueError):
        PlanningReference(tmp_path / "ref", loaded[0], loaded[2])


def test_heading_wrap_at_world_seam(loaded):
    ref = loaded[3]
    assert np.ptp(ref.frame.psi_ref_rad) > np.pi
    a, b = ref.sample(1e-7), ref.sample(ref.length - 1e-7)
    assert abs(a["e_psi_ref_rad"] - b["e_psi_ref_rad"]) < 1e-6


def test_intersection_detector():
    assert intersection_count(np.array([[0, 0], [1, 1], [0, 1], [1, 0], [0, 0]])) == 1


def test_preview_uses_distinct_curvatures_and_offsets(loaded, dynamic_vehicle):
    from apex.control.mpc.cost import tracking_error
    from apex.control.mpc.preview import make_preview

    track, _, _, ref = loaded
    preview = make_preview(track, dynamic_vehicle, ref, 24, 4, 0.1, racing_reference=ref)
    assert preview.values.shape == (11, 5)
    for i, s in enumerate(preview.progress):
        nominal = ref.sample(s)
        assert preview.values[0, i] == pytest.approx(track.sample(s).curvature)
        assert preview.values[9, i] == nominal["kappa_ref_1pm"]
        assert preview.values[7, i] == nominal["e_y_ref_m"]
        x = np.array(
            [
                preview.values[3, i],
                0,
                preview.values[5, i],
                preview.values[8, i],
                s,
                preview.values[7, i],
            ]
        )
        np.testing.assert_allclose(np.array(tracking_error(x, preview.values[:, i])).ravel(), 0)
    assert max(abs(preview.values[0] - preview.values[9])) > 0.01


def test_old_preview_contract_preserved(dynamic_vehicle, straight_geometry):
    from apex.control.mpc.preview import make_preview

    preview = make_preview(straight_geometry, dynamic_vehicle, lambda s: 2, 1, 4, 0.1)
    assert preview.values.shape == (7, 5)
    np.testing.assert_allclose(preview.progress, [1, 1.2, 1.4, 1.6, 1.8])


def test_offline_generator_reproduces_committed_fixture(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(FIXTURE.parents[2] / "scripts"))
    from task007a.generate import generate

    shutil.copy2(FIXTURE / "track_source.json", tmp_path / "track_source.json")
    generate(tmp_path)
    for name in ["planning_reference.csv", "planning_manifest.json"]:
        assert (tmp_path / name).read_bytes() == (FIXTURE / name).read_bytes()
