"""Load an offline speed polynomial without modifying the nominal request."""

import json

import numpy as np
from scipy.interpolate import PPoly


def load_speed_polynomial(path, length, samples, speeds):
    data = json.loads(path.read_text())
    knots = np.asarray(data["knots_m"], dtype=float)
    coefficients = np.asarray(data["coefficients"], dtype=float)
    if (
        knots.ndim != 1
        or len(knots) < 2
        or coefficients.shape != (4, len(knots) - 1)
        or not np.isfinite(knots).all()
        or not np.isfinite(coefficients).all()
        or knots[0] != 0
        or abs(knots[-1] - length) > 1e-8
        or np.any(np.diff(knots) <= 0)
    ):
        raise ValueError("Malformed serialized speed polynomial")
    spline = PPoly(coefficients, knots, extrapolate="periodic")
    # Check every cubic extremum as well as both sides of every interval endpoint.
    candidates = []
    for i, width in enumerate(np.diff(knots)):
        roots = np.roots(np.polyder(coefficients[:, i]))
        locations = [0.0, width] + [
            r.real for r in roots if abs(r.imag) < 1e-10 and 0 < r.real < width
        ]
        candidates.extend(np.polyval(coefficients[:, i], locations))
        if (
            i
            and abs(
                coefficients[-1, i] - np.polyval(coefficients[:, i - 1], knots[i] - knots[i - 1])
            )
            > 1e-8
        ):
            raise ValueError("Discontinuous speed polynomial")
    if min(candidates) < 0.5 - 1e-12 or max(candidates) > 6 + 1e-12:
        raise ValueError("Speed polynomial outside dynamic domain")
    if abs(np.polyval(coefficients[:, -1], knots[-1] - knots[-2]) - coefficients[-1, 0]) > 1e-8:
        raise ValueError("Malformed polynomial seam")
    if not np.allclose(spline(samples), speeds, atol=1e-9, rtol=0):
        raise ValueError("Speed polynomial/CSV mismatch")
    return spline
