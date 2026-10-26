"""D01: source-bound read-only cubic jets, physical arc derivatives and local charts."""

from __future__ import annotations

from math import isfinite, pi
from typing import Literal

from .contracts import (
    BranchSpec,
    GeometryJet,
    GeometrySnapshot,
    HeadingChart,
    MapId,
    Outcome,
    QualificationStatus,
    Reason,
    SourceBundle,
    StencilDomain,
)


def snapshot_geometry(bundle: SourceBundle) -> Outcome[GeometrySnapshot]:
    try:
        import hashlib
        import json

        import numpy as np

        path = "src/apex/track/centerline.py"
        expected = json.loads(
            (bundle.root / "docs/ct1/preservation_and_provenance.json").read_text()
        )["source_files"]
        h = next(b["sha256"] for b in expected if b["path"] == path)
        if hashlib.sha256((bundle.root / path).read_bytes()).hexdigest() != h:
            raise ValueError("Changed geometry source")
        c = bundle.track.centerline
        q = np.array(c._q, dtype=float, copy=True)
        arc = np.array(c._arc, dtype=float, copy=True)
        coeff = np.array(c._spline.c, dtype=float, copy=True)
        if coeff.shape != (4, len(q) - 1, 2) or arc.shape != q.shape:
            raise ValueError("Unsupported cubic representation")
        if (
            not np.array_equal(q, c._spline.x)
            or not np.isfinite(coeff).all()
            or not np.all(np.diff(q) > 0)
            or not np.all(np.diff(arc) > 0)
        ):
            raise ValueError("Invalid cubic/arc representation")
        q.setflags(write=False)
        arc.setflags(write=False)
        segments = []
        for i in range(len(q) - 1):
            z = np.array(coeff[:, i, :], copy=True)
            z.setflags(write=False)
            segments.append(z)
        return Outcome.available(
            GeometrySnapshot(
                q,
                arc,
                tuple(segments),
                float(c.length),
                c._parameter,
                lambda s: bundle.track.sample(s).curvature,
                bundle.binding_set_sha256,
            )
        )
    except (AttributeError, KeyError, ValueError, StopIteration, OSError) as exc:
        return Outcome.unavailable("GEOMETRY_REPRESENTATION_UNAVAILABLE", str(exc))


def geometry_jet(
    snapshot: GeometrySnapshot, s_abs_m: float, *, side: Literal["auto", "left", "right"] = "auto"
) -> Outcome[GeometryJet]:
    try:
        import numpy as np

        if not isfinite(s_abs_m) or s_abs_m < 0:
            raise ValueError("Nonnegative finite unwrapped progress required")
        if side not in ("auto", "left", "right"):
            raise ValueError("Unknown side")
        s = s_abs_m % snapshot.length_m
        q = float(snapshot.q_from_s(s))
        knots = np.asarray(snapshot.q_knots)
        rough = max(0, min(int(np.searchsorted(knots, q, side="right") - 1), len(knots) - 2))
        uncertainty = 1e-12 + 1e-13 * abs(q - float(knots[rough]))
        close = np.flatnonzero(np.abs(knots - q) <= uncertainty)
        knot = int(close[0]) if len(close) else None
        exact = next((i for i, a in enumerate(snapshot.arc_knots_m) if s == float(a)), None)
        if knot is not None and exact is None:
            return Outcome.unavailable(
                "INVERSION_BRANCH_UNRESOLVED",
                "Source root tolerances do not resolve the nearby segment; no arbitrary knot tolerance",
            )
        if exact is not None:
            knot = exact
        if knot is not None and side == "auto":
            chosen = max(0, min(knot, len(knots) - 2))
            qeval = q
            dk = None
            qualification = QualificationStatus.QUALIFIED_BRANCH_SPECIFIC
        else:
            if knot is not None:
                if side == "left":
                    chosen = (knot - 1) % (len(knots) - 1)
                    qeval = float(knots[-1] if knot == 0 else knots[knot])
                else:
                    chosen = knot % (len(knots) - 1)
                    qeval = float(knots[chosen])
            else:
                chosen = max(
                    0, min(int(np.searchsorted(knots, q, side="right") - 1), len(knots) - 2)
                )
                qeval = q
            dk = 0.0
            qualification = (
                QualificationStatus.QUALIFIED
                if knot is None
                else QualificationStatus.QUALIFIED_BRANCH_SPECIFIC
            )
        z = qeval - float(knots[chosen])
        coef = snapshot.segment_coefficients[chosen]
        c1 = (3 * coef[0] * z + 2 * coef[1]) * z + coef[2]
        c2 = 6 * coef[0] * z + 2 * coef[1]
        c3 = 6 * coef[0]
        speed = float(np.hypot(*c1))
        if speed <= 1e-8:
            raise ValueError("Accepted tangent domain violated")
        n = float(c1[0] * c2[1] - c1[1] * c2[0])
        k = n / speed**3
        if dk is not None:
            dk = float(
                (c1[0] * c3[1] - c1[1] * c3[0]) / speed**4 - 3 * n * np.dot(c1, c2) / speed**6
            )
        branch = BranchSpec(
            "UNRESOLVED"
            if knot is not None and side == "auto"
            else side.upper()
            if knot is not None
            else "SMOOTH",
            chosen,
            (float(knots[chosen]), float(knots[chosen + 1])),
            (float(snapshot.arc_knots_m[chosen]), float(snapshot.arc_knots_m[chosen + 1])),
            inversion_metadata={
                "q_uncertainty_proxy": uncertainty,
                "certified_bound": False,
                "xtol": 1e-12,
                "rtol": 1e-13,
                "quadrature_epsabs": 1e-11,
                "quadrature_epsrel": 1e-11,
            },
        )
        return Outcome.available(
            GeometryJet(
                s_abs_m,
                s,
                q,
                chosen,
                k,
                dk,
                tuple(tuple(float(v) for v in row) for row in (c1, c2, c3)),
                branch,
                qualification,
                ()
                if dk is not None
                else (
                    Reason(
                        "KNOT_SIDE_UNRESOLVED",
                        "C2 curvature has no unique third derivative; request explicit LEFT or RIGHT",
                    ),
                ),
            )
        )
    except (ValueError, IndexError, ArithmeticError) as exc:
        return Outcome.unavailable("CURVATURE_BRANCH_UNAVAILABLE", str(exc))


def check_geometry_stencil(
    snapshot: GeometrySnapshot, s_values_m: tuple[float, ...], *, branch: BranchSpec | None
) -> Outcome[StencilDomain]:
    jets = []
    for s in s_values_m:
        r = geometry_jet(
            snapshot,
            s,
            side=branch.side.lower()
            if branch is not None and branch.side in ("LEFT", "RIGHT")
            else "auto",
        )
        if r.value is None or r.value.kappa_s_1pm2 is None:
            return Outcome.unavailable(
                "STENCIL_KNOT_UNRESOLVED", "No unique smooth physical curvature derivative"
            )
        jets.append(r.value)
    if len({j.segment_index for j in jets}) != 1:
        return Outcome.unavailable(
            "STENCIL_CROSSES_KNOT", "Piecewise event-map derivative not implemented"
        )
    return Outcome.available(
        StencilDomain(MapId.C_PHYSICAL, "geometry", (), (), (), (), jets[0].branch, True, ())
    )


def check_heading_chart(
    theta_rad: float, endpoints_rad: tuple[float, ...]
) -> Outcome[HeadingChart]:
    if not isfinite(theta_rad) or not all(isfinite(t) for t in endpoints_rad):
        return Outcome.unavailable("HEADING_NONFINITE", "No finite chart")
    lifted = []
    multiples = []
    for t in endpoints_rad:
        d = (t - theta_rad + pi) % (2 * pi) - pi
        if abs(d) == pi:
            return Outcome.unavailable(
                "HEADING_CHART_AMBIGUOUS", "Antipodal heading has no unique local lift"
            )
        z = theta_rad + d
        lifted.append(z)
        multiples.append(round((z - t) / (2 * pi)))
    return Outcome.available(HeadingChart(theta_rad, tuple(lifted), tuple(multiples), True))
