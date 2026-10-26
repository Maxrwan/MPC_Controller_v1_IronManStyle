"""O02/O03: independently defined local geometry, not a replacement racing track."""

import math

import numpy as np


def test_parabola_arc_derivative():
    from ct1.contracts import GeometrySnapshot
    from ct1.geometry import geometry_jet

    # Descending coefficients c(q)=(q,q^2/2) on [0,2]. s(1) is a literal closed form.
    coeff = np.array([[0.0, 0.0], [0.0, 0.5], [1.0, 0.0], [0.0, 0.0]])
    s = (math.sqrt(2) + math.asinh(1)) / 2
    snap = GeometrySnapshot(
        np.array([0.0, 2.0]),
        np.array([0.0, 10.0]),
        (coeff,),
        10.0,
        lambda value: 1.0,
        lambda value: 0.0,
        "a" * 64,
    )
    jet = geometry_jet(snap, s).unwrap()
    assert abs(jet.kappa_1pm - 1 / (2 * math.sqrt(2))) < 1e-7
    assert abs(jet.kappa_s_1pm2 - (-3 / 8)) < 1e-7


def test_c2_knot_is_not_averaged():
    from ct1.contracts import GeometrySnapshot
    from ct1.geometry import geometry_jet

    # Left local q+1 coordinate: c=(q,0); right: c=(q,q^3/6).
    left = np.array([[0.0, 0.0], [0.0, 0.0], [1.0, 0.0], [-1.0, 0.0]])
    right = np.array([[0.0, 1 / 6], [0.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
    snap = GeometrySnapshot(
        np.array([-1.0, 0.0, 1.0]),
        np.array([0.0, 1.0, 2.0]),
        (left, right),
        2.0,
        lambda s: 0.0,
        lambda s: 0.0,
        "a" * 64,
    )
    assert geometry_jet(snap, 1.0).unwrap().kappa_s_1pm2 is None
    assert geometry_jet(snap, 1.0, side="left").unwrap().kappa_s_1pm2 == 0
    assert abs(geometry_jet(snap, 1.0, side="right").unwrap().kappa_s_1pm2 - 1) < 1e-7


def test_heading_local_lift():
    from ct1.geometry import check_heading_chart

    eps = 1e-5
    out = check_heading_chart(math.pi - eps, (-math.pi + eps,)).unwrap()
    assert abs(out.lifted_endpoints_rad[0] - (math.pi + eps)) < 1e-7
    assert check_heading_chart(0.0, (math.pi,)).value is None


def test_read_only_source_snapshot(bundle):
    from ct1.geometry import snapshot_geometry

    before = bundle.track.centerline._spline.c.copy()
    snap = snapshot_geometry(bundle).unwrap()
    assert not snap.segment_coefficients[0].flags.writeable
    assert np.array_equal(before, bundle.track.centerline._spline.c)


def test_circle_local_jet_not_a_global_cubic_circle():
    from ct1.contracts import GeometrySnapshot
    from ct1.geometry import geometry_jet

    # Third-order Taylor jet of (cos(q),sin(q)) at q=0; exact differential data there.
    coef = np.array([[0.0, -1 / 6], [-1 / 2, 0.0], [0.0, 1.0], [1.0, 0.0]])
    snap = GeometrySnapshot(
        np.array([0.0, 1.0]),
        np.array([0.0, 1.0]),
        (coef,),
        1.0,
        lambda s: 0.0,
        lambda s: 1.0,
        "a" * 64,
    )
    jet = geometry_jet(snap, 0.0, side="right").unwrap()
    assert abs(jet.kappa_1pm - 1.0) < 1e-7 and abs(jet.kappa_s_1pm2) < 1e-5
