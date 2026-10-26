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


# L2B literal metadata oracles. These bodies are UNEXECUTED at the amendment stage.
def _literal_grid(n, population="DESIGN_CONDITIONAL"):
    class Sample:
        def __init__(self, i):
            self.time_s = i / 100
            self.next_time_s = (i + 1) / 100
            self.original_gain_index = 9 + i
            self.authority_scope = population

        @property
        def Acl(self):
            raise AssertionError("Selection must never inspect a matrix or growth result")

    return tuple(Sample(i) for i in range(n))


def test_predeclared_interval_indices_literal_short_medium_and_80():
    from ct1.closed_loop import _product_selection

    # Hand enumeration of the assignment rule, not implementation-produced golden data.
    cases = (
        (0, [], 0, 0),
        (1, [(0, 1)], 1, 0),
        (3, [(0, 3), (0, 1), (1, 2), (2, 3)], 6, 2),
        (10, [(0, 10), (0, 1), (4, 5), (9, 10), (0, 5), (2, 7), (5, 10)], 55, 48),
        (
            80,
            [
                (0, 80),
                (0, 1),
                (39, 40),
                (79, 80),
                (0, 5),
                (37, 42),
                (75, 80),
                (0, 10),
                (35, 45),
                (70, 80),
                (0, 20),
                (30, 50),
                (60, 80),
                (0, 40),
                (20, 60),
                (40, 80),
            ],
            3240,
            3224,
        ),
    )
    for n, expected, total, omitted in cases:
        panel = _product_selection(_literal_grid(n), "TOY", "DESIGN_CONDITIONAL")
        assert [
            (r.start_index_inclusive, r.end_index_exclusive) for r in panel["intervals"]
        ] == expected
        assert panel["exhaustive_nonempty_interval_count"] == total
        assert panel["omitted_interval_count"] == omitted
        assert panel["selected_interval_count"] == len(expected) <= 16
        assert panel["full_interval_prefixes_scanned_if_complete"] == n
        assert not panel["exhaustive_stability_verification"]


def test_short_panel_never_clips_an_unavailable_window():
    from ct1.closed_loop import _product_selection

    p = _product_selection(_literal_grid(3), "TOY", "DESIGN_CONDITIONAL")
    assert p["unavailable_window_lengths_steps"] == [5, 10, 20, 40]
    assert [(r.start_index_inclusive, r.end_index_exclusive) for r in p["intervals"]] == [
        (0, 3),
        (0, 1),
        (1, 2),
        (2, 3),
    ]


def test_population_metadata_is_never_substituted():
    import pytest
    from ct1.closed_loop import _product_selection

    with pytest.raises(ValueError, match="cross-population"):
        _product_selection(_literal_grid(3), "TOY", "OBSERVED_AUTHORITY")
    observed = _product_selection((), "TOY", "OBSERVED_AUTHORITY")
    assert observed["factor_count"] == 0 and observed["intervals"] == ()
    assert observed["selected_interval_count"] == 0


def test_original_authority_keeps_only_complete_original_factors():
    from types import SimpleNamespace

    from ct1.worker import _metadata_product_plans

    packet = SimpleNamespace(gain_times_s=(1.0, 1.01, 1.02), timestamps_s=(1.0, 1.03))
    h = SimpleNamespace(authority=SimpleNamespace(start_s=1.005, end_s=1.035, expiry_s=1.035))
    plans = _metadata_product_plans(packet, (0, 1, 2), 1.005, h, "TOY")
    p = plans["OBSERVED_AUTHORITY"]
    assert p["factor_count"] == 2
    assert [(r.start_index_inclusive, r.end_index_exclusive) for r in p["intervals"]] == [
        (0, 2),
        (0, 1),
        (1, 2),
    ]
    assert p["intervals"][0].start_time_s == 1.01
    missing = _metadata_product_plans(packet, (0, 1, 2), 1.005, None, "TOY")
    assert missing["DESIGN_CONDITIONAL"]["factor_count"] == 3
    assert missing["OBSERVED_AUTHORITY"]["factor_count"] == 0


def test_full_selected_interval_scans_actual_prefix_peak(pair_factory):
    from ct1.closed_loop import _product_selection, transition_products
    from ct1.contracts import ApplicabilityAudit, ClosedLoopSample, ProductIntervals, Scales

    key = pair_factory(np.eye(2), [[1], [0]]).parent_key
    # Literal products: diag(2,1/2), diag(1/2,1/4), diag(1/2,1/8).
    # Worst prefix norm is 2 at 0.01s; the final norm is only 1/2.
    matrices = (
        np.array([[2.0, 0.0], [0.0, 0.5]]),
        np.array([[0.25, 0.0], [0.0, 0.5]]),
        np.array([[1.0, 0.0], [0.0, 0.5]]),
    )
    seq = tuple(
        ClosedLoopSample(
            key,
            i / 100,
            (i + 1) / 100,
            m,
            np.zeros(4),
            i,
            "DESIGN_CONDITIONAL",
            ApplicabilityAudit(),
        )
        for i, m in enumerate(matrices)
    )

    class Token:
        def poll(self):
            pass

    full = _product_selection(seq, "TOY", "DESIGN_CONDITIONAL")["intervals"][0]
    result = transition_products(
        seq,
        ProductIntervals((full,), (0.01,), "DESIGN_CONDITIONAL"),
        Scales(np.ones(2), np.ones(1)),
        Token(),
    ).unwrap()["products"][0]
    np.testing.assert_allclose(result["Phi_endpoint"], [[0.5, 0], [0, 0.125]], atol=1e-7, rtol=1e-4)
    assert result["endpoint_norm"] == 0.5 and result["max_transient_norm"] == 2.0
    assert result["peak_time_s"] == 0.01


def test_exact_four_normalization_populations_without_retuning():
    from types import SimpleNamespace

    from ct1.closed_loop import _product_normalizations
    from ct1.contracts import Scales

    cases = (
        (
            "full",
            ("vx", "vy", "r", "e_psi", "s_abs", "e_y"),
            [0.5, 0.5, 1.0, 0.1, 0.75, 0.1],
            [0.2, 1.0],
            [0.5, 0.5, 1.0, 0.1, 0.75, 0.01],
            [0.5, 0.5, 1.0, 0.1, 0.75, 1.0],
        ),
        (
            "lateral",
            ("e_y", "e_psi", "vy", "r"),
            [0.1, 0.1, 0.5, 1.0],
            [0.2],
            [0.01, 0.1, 0.5, 1.0],
            [1.0, 0.1, 0.5, 1.0],
        ),
        ("speed", ("vx",), [0.5], [1.0], [0.05], [5.0]),
    )
    for sub, names, dx, du, low, high in cases:
        original = Scales(np.array(dx), np.array(du))
        panel = _product_normalizations(SimpleNamespace(subsystem=sub, state_names=names), original)
        assert [name for name, _ in panel] == [
            "nominal_scaled",
            "raw_SI_unit_dependent",
            "selected_coordinate_x0.1",
            "selected_coordinate_x10",
        ]
        for (_, actual), expected in zip(panel, (dx, [1.0] * len(dx), low, high), strict=True):
            np.testing.assert_allclose(actual.Dx_diagonal_SI, expected, atol=1e-7, rtol=1e-4)
            assert np.array_equal(actual.Du_diagonal_SI, du)
        assert np.array_equal(original.Dx_diagonal_SI, dx)
