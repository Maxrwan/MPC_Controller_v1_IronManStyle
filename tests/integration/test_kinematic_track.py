"""Real periodic spline coupling; no analytical-geometry substitute in this integration test."""

from math import asin, atan, tan

import numpy as np

from apex.models.vehicle.kinematic import KinematicBicycle
from apex.state import StateIndex as I
from apex.state import state_vector
from apex.track.progress import lap_index


def test_spline_track_multiple_laps(synthetic_vehicle, circle):
    model = KinematicBicycle(synthetic_vehicle, circle)
    beta = asin(0.15 / 5)
    delta = atan(2 * tan(beta))
    x = state_vector([2, 0, 0, -beta, circle.length - 0.1, 0])
    previous_curvature = model.diagnostics(x, [delta, 0]).curvature
    crossings = 0
    seam_jumps = []
    max_lateral_error = 0.0
    for _ in range(850):
        old = x.copy()
        x = model.step(x, [delta, 0], 0.02)
        assert x[I.S_ABS] > old[I.S_ABS]
        diagnostics = model.diagnostics(x, [delta, 0])
        assert diagnostics.track_s < circle.length
        max_lateral_error = max(max_lateral_error, abs(x[I.E_Y]))
        # A 64-point cubic circle is not an exact circle; fixed ideal-circle steering
        # has bounded interpolation/integration drift. Analytical steady motion is
        # tested separately, and no feedback is introduced to conceal this difference.
        assert abs(x[I.E_Y]) < 1e-4
        assert abs(x[I.VY] - x[I.VX] * tan(beta)) < 1e-14
        assert abs(x[I.YAW_RATE] - x[I.VX] / 0.15 * tan(beta)) < 1e-14
        if lap_index(x[I.S_ABS], circle.length) != lap_index(old[I.S_ABS], circle.length):
            crossings += 1
            seam_jumps.append(abs(diagnostics.curvature - previous_curvature))
            assert x[I.S_ABS] - old[I.S_ABS] < 0.05
        previous_curvature = diagnostics.curvature
    assert crossings == 2
    assert max(seam_jumps) < 2e-4
    print(
        f"\nSpline seam crossings={crossings}, final s_abs={x[I.S_ABS]:.12g}, "
        f"max sampled seam curvature change={max(seam_jumps):.12g} 1/m, "
        f"max lateral error={max_lateral_error:.12g} m"
    )
    assert np.all(np.isfinite(x))


def test_step_is_invariant_to_lap_number(synthetic_vehicle, circle):
    model = KinematicBicycle(synthetic_vehicle, circle)
    beta = asin(0.15 / 5)
    control = [atan(2 * tan(beta)), 0.1]
    first = state_vector([2, 0, 0, -beta, circle.length - 0.05, 0.01])
    next_lap = first.copy()
    next_lap[I.S_ABS] += circle.length
    a = model.step(first, control, 0.1)
    b = model.step(next_lap, control, 0.1)
    assert a[I.S_ABS] > circle.length
    assert b[I.S_ABS] > 2 * circle.length
    b[I.S_ABS] -= circle.length
    error = float(np.max(np.abs(a - b)))
    assert error < 1e-11
    print(f"\nEquivalent-lap step maximum component discrepancy={error:.12g} (SI)")
