"""O14-O17 literal noncommuting products, unit-dependent norms, affine defects/progress."""

import math

import numpy as np


def test_noncommuting_product_order(pair_factory):
    from ct1.closed_loop import transition_products
    from ct1.contracts import (
        ApplicabilityAudit,
        ClosedLoopSample,
        IndexInterval,
        ProductIntervals,
        Scales,
    )

    key = pair_factory(np.eye(2), [[1], [0]]).parent_key
    seq = tuple(
        ClosedLoopSample(
            key,
            i * 0.01,
            (i + 1) * 0.01,
            np.array(m),
            np.zeros(4),
            i,
            "DESIGN_CONDITIONAL",
            ApplicabilityAudit(),
        )
        for i, m in enumerate(([[0.5, 2], [0, 0.5]], [[0.5, 0], [2, 0.5]]))
    )

    class Token:
        def poll(self):
            pass

    out = transition_products(
        seq,
        ProductIntervals((IndexInterval(0, 2, 0.0, 0.02),), (0.01,), "DESIGN_CONDITIONAL"),
        Scales(np.ones(2), np.ones(1)),
        Token(),
    ).unwrap()["products"][0]
    np.testing.assert_allclose(out["Phi_endpoint"], [[0.25, 1], [1, 4.25]], atol=1e-7, rtol=1e-4)
    assert abs(out["endpoint_norm"] - (9 + 4 * math.sqrt(5)) / 4) <= 1e-7


def test_normalized_transient_norm_is_unit_dependent():
    raw = np.array([[1.0, 2.0], [0.0, 1.0]])
    dx = np.array([2.0, 1.0])
    scaled = raw * dx[None, :] / dx[:, None]
    np.testing.assert_allclose(scaled, [[1, 1], [0, 1]], atol=1e-7, rtol=1e-4)
    assert abs(np.linalg.norm(raw, 2) - (1 + math.sqrt(2))) < 1e-7
    assert abs(np.linalg.norm(scaled, 2) - (1 + math.sqrt(5)) / 2) < 1e-7


def test_nominal_defect_sign(point):
    from ct1.closed_loop import nominal_defects
    from ct1.contracts import EvaluationKey, HeadingChart, MapId, MapSemantics, NominalSample

    key = EvaluationKey("TOY", "TOY", MapId.D_TRACKER, point.kappa_policy, "a" * 64, 0)
    x = np.array(point.x)
    u = np.array(point.u)
    next_x = x.copy()
    next_x[5] += 0.02
    sample = NominalSample(key, 1.0, x, u, 1.01, next_x, np.zeros(4), True)
    semantics = MapSemantics(
        MapId.D_TRACKER,
        0.01,
        2,
        point.kappa_policy,
        0.0,
        HeadingChart(0.0, (0.0,), (0,), True),
        "DESIGN_CONDITIONAL",
    )
    d = nominal_defects((sample,), lambda x, u: x.copy(), semantics).unwrap()["defects"][0]
    assert abs(d["d_dimensional"][5] + 0.02) < 1e-7


def test_full_feedback_ignores_progress():
    from ct1.closed_loop import feedback_matrix

    G = feedback_matrix(np.array([1.0, 2.0, 3.0, 4.0]))
    assert np.array_equal(G[:, 4], [0, 0])
    A = np.eye(6)
    B = np.zeros((6, 2))
    B[0, 1] = 1
    B[1, 0] = 1
    e = np.array([0, 0, 0, 0, 1, 0])
    assert np.array_equal((A - B @ G) @ e, e)


def test_affine_forced_convolution_has_declared_sign():
    from ct1.closed_loop import _forced_step

    # e0=0, d0=[1,0], A1 swaps channels, d1=[0,2]: e2=[0,3].
    e1 = _forced_step(np.zeros(2), np.eye(2), np.array([1.0, 0.0]), np.ones(2))
    e2 = _forced_step(e1, np.array([[0.0, 1.0], [1.0, 0.0]]), np.array([0.0, 2.0]), np.ones(2))
    np.testing.assert_allclose(e2, [0.0, 3.0], atol=1e-7, rtol=1e-4)


def test_censored_prefix_does_not_backfill_endpoint(pair_factory):
    from ct1.closed_loop import transition_products
    from ct1.contracts import (
        ApplicabilityAudit,
        ClosedLoopSample,
        IndexInterval,
        OutcomeStatus,
        ProductIntervals,
        Scales,
    )

    key = pair_factory(np.eye(2), [[1], [0]]).parent_key
    seq = tuple(
        ClosedLoopSample(
            key,
            i * 0.01,
            (i + 1) * 0.01,
            np.eye(2),
            np.zeros(4),
            i,
            "DESIGN_CONDITIONAL",
            ApplicabilityAudit(),
        )
        for i in range(2)
    )

    class Token:
        count = 0

        def poll(self):
            self.count += 1
            if self.count == 2:
                raise TimeoutError("literal clock stop")

    result = transition_products(
        seq,
        ProductIntervals((IndexInterval(0, 2, 0.0, 0.02),), (0.02,), "DESIGN_CONDITIONAL"),
        Scales(np.ones(2), np.ones(1)),
        Token(),
    )
    assert result.status == OutcomeStatus.RESOURCE_CENSORED
    data = result.value["products"][0]
    assert data["completed_range"]["end_index_exclusive"] == 1
    assert data["endpoint_norm"] is None and data["Phi_endpoint"] is None
    assert data["norm_scope"] == "COMPLETED_PREFIX_ONLY"
