"""O03/O08 preserve invalid boundaries and unavailable stencils without shifting points."""

from dataclasses import replace

import numpy as np


def test_fixed_stencil_refusal(point):
    from ct1.contracts import FDSteps, MapId, Outcome, Scales
    from ct1.finite_difference import central_pair

    scales = Scales(np.array([0.5, 0.5, 1, 0.1, 0.75, 0.1]), np.array([0.2, 1.0]))
    steps = FDSteps((2e-5, 1e-5, 5e-6), scales.Dx_diagonal_SI, scales.Du_diagonal_SI)
    called = []
    result = central_pair(
        point,
        lambda x, u: called.append(True),
        MapId.C_FIXED,
        scales,
        steps,
        lambda p, m, s: Outcome.unavailable("BOUNDARY", "No central interior"),
    )
    assert result.value is None and not called and point.x[0] == 2


def test_invalid_original_point_is_invalid(inputs, bundle):
    from ct1.contracts import MapId, QualificationPolicy, QualificationStatus
    from ct1.inputs import load_candidate_tuples, load_original_packet
    from ct1.qualification import qualify_point
    from ct1.source_adapter import _with_packet

    p = load_candidate_tuples(inputs, inputs.candidates[0].candidate_id).unwrap()[0]
    q = replace(p, x=(0.0,) + p.x[1:])
    bound = _with_packet(bundle, load_original_packet(inputs, p.packet_id).unwrap())
    policy = QualificationPolicy(
        {},
        {},
        inputs.metrics["finite_difference"],
        inputs.metrics["finite_difference"]["geometry_kappa_s"],
    )
    result = qualify_point(inputs, bound, q, MapId.C_PHYSICAL, policy)
    assert result.status == QualificationStatus.INVALID and q.x[0] == 0
