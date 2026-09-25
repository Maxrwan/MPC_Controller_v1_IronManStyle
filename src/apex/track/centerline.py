"""Periodic cubic centerline with numerical arc-length coordinates."""

from math import atan2, isfinite

import numpy as np
from numpy.polynomial import polynomial as poly
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import quad
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

from apex.coordinates.angles import wrap_angle
from apex.track.progress import wrap_progress


def _unit_interval_roots(coefficients: NDArray[np.float64]) -> list[float]:
    """Real polynomial roots on a bounded, normalized spline segment."""
    scale = float(np.max(np.abs(coefficients)))
    if scale == 0:
        return []
    roots = poly.polyroots(coefficients / scale)
    return [
        float(np.clip(r.real, 0, 1))
        for r in roots
        if abs(r.imag) <= 1e-9 and -1e-12 <= r.real <= 1 + 1e-12
    ]


class PeriodicCenterline:
    """Ordered, simple closed centerline; public progress is numerical arc length.

    Internally CubicSpline uses raw cumulative chord length q. Arc length is
    integrated per segment, and queries invert it with bounded root finding.
    Inputs require at least four distinct points; one repeated endpoint is removed.
    """

    def __init__(self, waypoints: ArrayLike) -> None:
        points = np.array(waypoints, dtype=np.float64, copy=True)
        if points.ndim != 2 or points.shape[1] != 2 or len(points) < 4:
            raise ValueError("centerline requires at least four x,y waypoints")
        if not np.all(np.isfinite(points)):
            raise ValueError("waypoints must be finite")
        extent = float(np.max(np.ptp(points, axis=0)))
        tolerance = max(1e-12, extent * 1e-12)
        if np.linalg.norm(points[-1] - points[0]) <= tolerance:
            points = points[:-1]
        if len(points) < 4:
            raise ValueError("centerline requires at least four distinct waypoints")
        for i in range(len(points)):
            if np.any(np.linalg.norm(points[i + 1 :] - points[i], axis=1) <= tolerance):
                raise ValueError("duplicate or indistinguishable waypoints")
        relative = points - points[0]
        singular = np.linalg.svd(relative - relative.mean(axis=0), compute_uv=False)
        if singular[0] <= tolerance or singular[1] <= singular[0] * 1e-10:
            raise ValueError("centerline is degenerate or nearly collinear")
        self._origin = points[0].copy()
        self._waypoints = points
        closed = np.vstack([relative, relative[0]])
        chords = np.linalg.norm(np.diff(closed, axis=0), axis=1)
        self._q = np.concatenate([[0.0], np.cumsum(chords)])
        if not np.all(np.isfinite(self._q)) or np.any(np.diff(self._q) <= 0):
            raise ValueError("waypoint scale cannot be represented reliably")
        self._spline = CubicSpline(self._q, closed, bc_type="periodic", axis=0)
        # Store ascending coefficients in t=(q-q_i)/h_i, t in [0,1].
        self._segments = [
            self._spline.c[::-1, i, :] * h ** np.arange(4)[:, None] for i, h in enumerate(chords)
        ]
        self._check_tangents(chords)
        arc = [self._integral(i, float(h)) for i, h in enumerate(chords)]
        self._arc = np.concatenate([[0.0], np.cumsum(arc)])
        if not np.all(np.isfinite(self._arc)) or np.any(np.diff(self._arc) <= 0):
            raise ValueError("invalid numerical arc lengths")

    @property
    def length(self) -> float:
        """Numerically integrated spline circumference [m]."""
        return float(self._arc[-1])

    @property
    def chord_length(self) -> float:
        """Raw waypoint polygon perimeter, not the public progress period."""
        return float(self._q[-1])

    @property
    def waypoints(self) -> NDArray[np.float64]:
        """Return a copy, without a duplicated closure waypoint."""
        return self._waypoints.copy()

    def _check_tangents(self, chords: NDArray[np.float64]) -> None:
        for coefficients, h in zip(self._segments, chords, strict=True):
            dx = poly.polyder(coefficients[:, 0]) / h
            dy = poly.polyder(coefficients[:, 1]) / h
            speed2 = poly.polyadd(poly.polymul(dx, dx), poly.polymul(dy, dy))
            candidates = [0.0, 1.0, *_unit_interval_roots(poly.polyder(speed2))]
            # Evaluate derivative vectors, avoiding cancellation in speed-squared polynomial.
            minimum = min(np.hypot(poly.polyval(t, dx), poly.polyval(t, dy)) for t in candidates)
            if not isfinite(minimum) or minimum <= 1e-8:
                raise ValueError("centerline has a zero or nearly zero tangent")

    def _integral(self, segment: int, offset: float) -> float:
        start = self._q[segment]
        value, _ = quad(
            lambda q: float(np.linalg.norm(self._spline(q, 1))),
            start,
            start + offset,
            epsabs=1e-11,
            epsrel=1e-11,
        )
        return float(value)

    def _parameter(self, s: float) -> float:
        wrapped = wrap_progress(s, self.length)
        i = min(int(np.searchsorted(self._arc, wrapped, side="right") - 1), len(self._q) - 2)
        target = wrapped - self._arc[i]
        if target == 0:
            return float(self._q[i])
        h = self._q[i + 1] - self._q[i]
        offset = brentq(lambda d: self._integral(i, d) - target, 0.0, h, xtol=1e-12, rtol=1e-13)
        return float(self._q[i] + offset)

    def geometry(self, s: float) -> tuple[float, float, float, float]:
        """Return x, y, wrapped tangent heading, and signed curvature at any s."""
        q = self._parameter(s)
        point = self._spline(q) + self._origin
        dx, dy = self._spline(q, 1)
        ddx, ddy = self._spline(q, 2)
        speed = float(np.hypot(dx, dy))
        if not isfinite(speed) or speed <= 1e-8:
            raise ValueError("cannot query a degenerate centerline tangent")
        curvature = (dx * ddy - dy * ddx) / speed**3
        return float(point[0]), float(point[1]), wrap_angle(atan2(dy, dx)), float(curvature)

    def project_point(self, x: float, y: float) -> float:
        """Return nearest wrapped arc progress by bounded per-segment minimization.

        Squared distance to each cubic has a degree-five derivative. Evaluate its
        real stationary roots in [0,1] plus both endpoints, then choose the global
        minimum. This avoids a sampling-resolution-dependent coarse search.
        Equal-distance ambiguity is resolved deterministically by segment order.
        """
        if not isfinite(x) or not isfinite(y):
            raise ValueError("point coordinates must be finite")
        point = np.array([x, y]) - self._origin
        best_distance = float("inf")
        best_i, best_t = 0, 0.0
        for i, coefficients in enumerate(self._segments):
            residual = coefficients.copy()
            residual[0] -= point
            derivative = poly.polyadd(
                poly.polymul(residual[:, 0], poly.polyder(residual[:, 0])),
                poly.polymul(residual[:, 1], poly.polyder(residual[:, 1])),
            )
            candidates = [0.0, 1.0, *_unit_interval_roots(derivative)]
            for t in candidates:
                error = poly.polyval(t, residual)
                distance = float(np.dot(error, error))
                if distance < best_distance:
                    best_distance, best_i, best_t = distance, i, t
        s = self._arc[best_i] + self._integral(
            best_i, best_t * (self._q[best_i + 1] - self._q[best_i])
        )
        return wrap_progress(float(s), self.length)
