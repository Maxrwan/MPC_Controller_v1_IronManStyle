"""O05/O06/O08 method-matched independent value FD/analytical/source AD checks."""

from dataclasses import replace

import numpy as np


def test_manual_and_independent_fd(parameters, point, jet, inputs):
    from ct1.analytic import continuous_pair
    from ct1.contracts import FDSteps, MapId, Outcome, Scales, StencilDomain
    from ct1.crosscheck_numpy import crosscheck_f
    from ct1.finite_difference import central_pair, compare_pairs

    manual = continuous_pair(point, parameters, jet, policy=point.kappa_policy).unwrap()
    scales = Scales(np.array([0.5, 0.5, 1, 0.1, 0.75, 0.1]), np.array([0.2, 1.0]))
    steps = FDSteps((2e-5, 1e-5, 5e-6), scales.Dx_diagonal_SI, scales.Du_diagonal_SI)
    guard = lambda p, m, s: Outcome.available(
        StencilDomain(m, p.tuple_id, tuple(range(8)), s.multipliers, (), (), None, True, ())
    )
    fd = central_pair(
        point,
        lambda x, u: crosscheck_f(x, u, parameters, curvature=0.0),
        MapId.C_FIXED,
        scales,
        steps,
        guard,
    ).unwrap()
    fd = replace(
        fd,
        pairs_per_step=tuple(
            replace(
                p,
                key=replace(p.key, source_binding_set_sha256=manual.key.source_binding_set_sha256),
            )
            for p in fd.pairs_per_step
        ),
    )
    assert compare_pairs(manual, fd, inputs.metrics["finite_difference"])["comparison"] == "PASS"
    bad = replace(manual, key=replace(manual.key, map_id=MapId.C_PHYSICAL))
    assert (
        compare_pairs(bad, fd, inputs.metrics["finite_difference"])["comparison"]
        == "INCOMPARABLE_METHOD_SEMANTICS"
    )


def test_original_ad_matches_manual(bundle, parameters, point):
    from ct1.analytic import continuous_pair
    from ct1.contracts import MapId
    from ct1.geometry import geometry_jet, snapshot_geometry
    from ct1.source_adapter import _curvature, source_symbolic_pair

    jet = geometry_jet(snapshot_geometry(bundle).unwrap(), point.x[4]).unwrap()
    k = _curvature(bundle, point)
    jet = replace(jet, kappa_1pm=k, kappa_s_1pm2=0.0)
    ad = source_symbolic_pair(bundle, point, MapId.C_FIXED).unwrap()
    manual = continuous_pair(point, parameters, jet, policy=point.kappa_policy).unwrap()
    np.testing.assert_allclose(ad.A, manual.A, atol=1e-7, rtol=1e-4)
    np.testing.assert_allclose(ad.B, manual.B, atol=1e-7, rtol=1e-4)


def test_actual_frozen_curvature_is_one_scalar_across_stencil(point):
    from ct1.source_adapter import _curvature, _with_fixed_curvature

    class Track:
        length = 10.0

        def sample(self, s):
            return type("Sample", (), {"curvature": s})()

    class Bundle:
        track = Track()

    bound = _with_fixed_curvature(Bundle(), 0.25)
    assert _curvature(bound, replace(point, x=point.x[:4] + (2.0, 0.0))) == 0.25
    assert _curvature(bound, replace(point, x=point.x[:4] + (3.0, 0.0))) == 0.25
