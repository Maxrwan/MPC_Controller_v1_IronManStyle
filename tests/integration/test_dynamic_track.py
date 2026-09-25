"""Actual periodic-spline coupling: continuous multi-lap state, no controller."""

import numpy as np

from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.state import StateIndex as I
from apex.state import state_vector
from apex.track.progress import lap_index


def test_dynamic_spline_multilap(dynamic_vehicle, circle):
    model = DynamicBicycle(dynamic_vehicle, circle)
    x = state_vector([2, 0.024, 0.4, -np.arctan2(0.024, 2), circle.length - 0.1, 0])
    crossings = 0
    maxey = 0
    for _ in range(3500):
        previous = x.copy()
        x = model.step(x, [0.06, 0])
        assert np.all(np.isfinite(x))
        assert x[I.S_ABS] > previous[I.S_ABS]
        d = model.diagnostics(x, [0.06, 0])
        assert 0 <= d.track_s < circle.length
        assert np.all(np.isfinite([d.fyf, d.fyr, d.fzf, d.fzr]))
        assert d.fzf > 0 and d.fzr > 0
        if lap_index(x[I.S_ABS], circle.length) > lap_index(previous[I.S_ABS], circle.length):
            crossings += 1
        maxey = max(maxey, abs(x[I.E_Y]))
    assert crossings >= 2
    assert maxey < 0.2
    print(
        f"\nDynamic spline crossings={crossings}, final s_abs={x[I.S_ABS]:.12g} m, "
        f"max |ey|={maxey:.12g} m"
    )


def test_dynamic_lap_equivalence(dynamic_vehicle, circle):
    model = DynamicBicycle(dynamic_vehicle, circle)
    a = state_vector([2, 0.024, 0.4, -0.012, circle.length - 0.003, 0.02])
    b = a.copy()
    b[I.S_ABS] += circle.length
    a = model.step(a, [0.06, 0.1])
    b = model.step(b, [0.06, 0.1])
    assert a[I.S_ABS] > circle.length and b[I.S_ABS] > 2 * circle.length
    b[I.S_ABS] -= circle.length
    error = float(np.max(np.abs(a - b)))
    assert error < 1e-11
    print(f"\nDynamic equivalent-lap max discrepancy={error:.12g} (SI)")
