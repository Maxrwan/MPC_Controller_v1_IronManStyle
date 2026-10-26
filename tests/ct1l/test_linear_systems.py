"""O09-O11 literal controllability spectra, scale sensitivity and PBH modes."""

import numpy as np
import pytest


def test_literal_singular_spectra(pair_factory, inputs):
    from ct1.contracts import Scales
    from ct1.linear_systems import controllability_audit, normalize_pair

    p = pair_factory([[0, 1], [0, 0]], [[0], [1]])
    audit = controllability_audit(p, inputs.metrics["rank"]).unwrap()
    nominal = [c["spectrum"] for c in audit["scale_cases"] if c["case_id"] == "nominal"]
    assert all(s["rank"] == 2 and s["condition_number"] == 1 for s in nominal)
    n = normalize_pair(p, Scales(np.array([2.0, 1.0]), np.array([1.0])))
    C = np.hstack((n.B_scaled, n.A_scaled @ n.B_scaled))
    np.testing.assert_allclose(C, [[0, 0.5], [1, 0]], atol=1e-7, rtol=1e-4)


def test_rank_tolerance_is_not_exact_deficiency(pair_factory, inputs):
    from ct1.linear_systems import controllability_audit

    p = pair_factory([[0, 1e-9], [0, 0]], [[0], [1]])
    cases = controllability_audit(p, inputs.metrics["rank"]).unwrap()["scale_cases"]
    assert [c["spectrum"]["rank"] for c in cases if c["case_id"] == "nominal"] == [2, 2, 1, 1]


@pytest.mark.parametrize(
    "continuous,diagonal,expected",
    [
        (False, [0.5, 0.75], "SUPPORTED_LOCAL_NUMERICAL"),
        (False, [0.5, 1.1], "FAILED_PBH"),
        (False, [0.5, 1.0], "INDETERMINATE"),
        (True, [-1.0, -2.0], "SUPPORTED_LOCAL_NUMERICAL"),
        (True, [-1.0, 1.0], "FAILED_PBH"),
        (True, [-1.0, 0.0], "INDETERMINATE"),
    ],
)
def test_pbh_stable_uncontrollable_and_marginal(
    pair_factory, inputs, continuous, diagonal, expected
):
    from ct1.linear_systems import stabilizability_audit

    p = pair_factory(np.diag(diagonal), [[1], [0]], continuous)
    assert stabilizability_audit(p, inputs.metrics["PBH"]).unwrap()["stabilizability"] == expected
