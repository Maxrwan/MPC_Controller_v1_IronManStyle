# Track model specification — Task 002

## Scope and assumptions

Tracks are closed, planar, and assumed non-self-intersecting. Ordered waypoints follow
race direction; the first point defines progress zero. Forward racing is the primary
use case. Either clockwise or counterclockwise point order is supported as the declared
forward race direction; reversing motion/direction during a run is not implemented.
No vehicle dynamics, controller, race completion, or episode logic belongs in this layer.

## CSV and validation

CSV requires unique headers including `x,y`, in metres. Additional named columns are
ignored. UTF-8 (including BOM) is accepted. Call `load_centerline_csv(path)` or
`load_track_csv(path, left_width=..., right_width=...)`; widths are always explicit.
At least four distinct waypoints must remain after removing one repeated final point.
The implementation removes an endpoint within max(1e-12 m, extent*1e-12) of the first.
Other repeated/indistinguishable points, nonfinite coordinates, malformed rows, and
collinear/nearly collinear point clouds are rejected. The collinearity threshold is a
small/large singular-value ratio of 1e-10. No complete self-intersection detector exists;
users must verify both input order and spline shape. Overshoot can invalidate sparse inputs.

## Periodic spline and numerical arc length: choice A

Let q denote cumulative raw waypoint chord length. Append the first point once for
construction of independent x(q), y(q) using SciPy `CubicSpline(..., bc_type="periodic")`.
The spline is C2 at knots and the closure seam. q is **not** true arc length.

The public progress s uses numerical spline arc length:

    s(q) = integral from 0 to q of sqrt(x'(u)^2 + y'(u)^2) du
    L = s(q_end)

Each segment's arc length is integrated by adaptive SciPy `quad`, with absolute and
relative tolerances 1e-11. Cumulative segment lengths locate the interval for a query.
Bounded `brentq` inverts the local integral with xtol=1e-12 and rtol=1e-13. Public
`length`, sample progress, projection progress and race-progress utilities all use L.
`centerline.chord_length` exposes only the polygon perimeter for diagnostics.
Numerical integration is not symbolic exactness; spline-fit error relative to an unknown
physical centerline remains separate from integration error.

The raw q derivatives are sufficient for parameterization-invariant geometry:

    psi_t = wrap_angle(atan2(y', x'))
    kappa = (x' y'' - y' x'') / (x'^2 + y'^2)^(3/2)
    unit tangent = [cos(psi_t), sin(psi_t)]
    left normal = [-sin(psi_t), cos(psi_t)]

Tangent-speed minima are checked on each segment using stationary roots of squared
speed plus endpoints. A q-tangent norm <=1e-8 is rejected, rather than divided through;
query-time checks also guard degeneracy. Heading's stored scalar may jump at its angle
branch cut; geometric tangent continuity must be compared modulo wrapping.

## Geometry, widths and boundaries

`TrackSample` is frozen and contains track_s, x, y, heading, curvature, left_width and
right_width. `ClosedTrack.sample(s)` accepts arbitrary finite positive or negative
geometric progress and wraps internally. Negative geometric queries do not authorize
negative race progress. The returned track_s is in [0,L).

Task 002 widths are independent, finite, positive constants, specified by callers.
`left_width(s)` and `right_width(s)` allow future spatial variation without changing
controller interfaces. Widths are measured normal to the centerline:

    left boundary = p_c + left_width(s) * n
    right boundary = p_c - right_width(s) * n
    valid lateral corridor: -right_width(s) <= e_y <= left_width(s)

Conversions do not clip lateral positions or enforce track containment. Boundary-offset
curves may overlap or become singular on tight bends; no corridor topology check exists.
Synthetic circle dimensions and widths in tests/plotting are not physical project defaults.

## Cartesian and Frenet transforms

`GlobalPose(x,y,psi)` is frozen, finite, and normalizes psi to (-pi,pi]. The single
canonical function is `apex.coordinates.angles.wrap_angle`; -pi maps to +pi.

`frenet_to_global(track, s, e_y, e_psi=0)` implements:

    x = x_c - e_y sin(psi_t)
    y = y_c + e_y cos(psi_t)
    psi = wrap_angle(psi_t + e_psi)

For global projection, minimize squared Cartesian distance to the centerline. Each
cubic segment is expressed with normalized parameter t in [0,1]. The derivative of
squared distance is a degree-five polynomial (a constant factor is omitted). Solve
for its real roots within that segment, add both endpoints, evaluate distances, and
choose the closest candidate across all segments. Roots use imaginary tolerance 1e-9
and endpoint tolerance 1e-12. This is a bounded numerical root-finding alternative to
dense coarse search plus scalar refinement, avoiding a coarse-grid resolution setting.
It is O(number of segments) polynomial solves per projection, not optimized for real time.
Floating-point polynomial conditioning still limits pathological geometries.

Convert the chosen q into public arc progress. Then:

    e_y = (p - p_c) dot n
    e_psi = wrap_angle(psi_global - psi_t)

`project_point` omits heading; `project_pose` includes it. Both return a frozen
`FrenetProjection(track_s, e_y, e_psi, s_abs)`; absent pose heading is None, and absent
previous_s_abs means returned s_abs is None because the lap cannot be inferred.
Nearest-point coordinates are locally invertible only where the closest centerline point
is unique and the normal map is regular (in particular, 1-kappa*e_y must not vanish).
Points near medial axes, far outside the corridor, or near overlapping normals can be
ambiguous even on simple circuits. Equal numerical distances use first-segment order;
the previous-progress hint selects lap equivalence, not a different geometric branch.

## Wrapped geometry versus continuous race progress

- `wrap_progress(s,L)` gives track_s in [0,L). Negative geometry input is supported.
- `lap_index(s_abs,L)` requires nonnegative finite s_abs and returns its lap index.
- `unwrap_progress(track_s, previous_s_abs,L)` chooses the nearest nonnegative
  `track_s + k*L`. Exact half-lap ties prefer the forward equivalent.

Unwrapping assumes consecutive true progress changes are less than L/2. It cannot infer
missed laps; provide an expected/current progress hint when appropriate. It deliberately
does not clamp small backward changes caused by measurement noise. Seam crossing changes
lap equivalence without resetting s_abs. No lap crossing terminates anything here.

Exactly represented n*L values are recognized explicitly as seam values; there is no
arbitrary epsilon snapping. Adjacent representable values on either side remain distinct.
Finite precision can erase sub-lap detail for extremely large lap counts; there is no
software lap limit, but float64 is not infinite precision. Overflowing progress/length
ratios are rejected. Tests include one million laps and nextafter values around seams.

## Validation and limitations

The 64-waypoint synthetic radius-5-m circle differs from analytical circumference by
4.06222e-6 m, versus 1.26150e-2 m for its raw chord polygon. Maximum sampled curvature
error is 1.60896e-4 1/m (about 0.08045% of 0.2 1/m). More waypoints improve geometric fit;
arc-length reparameterization does not turn a cubic interpolant into an exact circle.

Tests include both directions, an ellipse with semiaxes 7 m and 3 m, nonuniform samples,
translated geometry, independent Gauss-Legendre integration and finite-difference unit
speed, invalid inputs, signed offsets, pose round trips, and repeated laps. Regression
metrics can be reproduced with `pytest -q -s tests/regression/test_geometry_accuracy.py`.
Round-trip tolerance is 1e-8 m for progress/Cartesian position and 1e-9 for lateral/heading
checks in the unit suite. These establish numerical correctness on tested fixtures, not
universal accuracy guarantees for arbitrary tracks.

TODO: validated real track data, varying widths, corridor/topology checks, branch-aware
projection, reverse-motion policy, and performance work when justified by real timing needs.
