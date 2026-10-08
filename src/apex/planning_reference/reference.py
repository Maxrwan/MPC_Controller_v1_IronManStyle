"""Strict serialized Planning contract, periodic lookup and offline acceptance gates."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from apex.coordinates.angles import wrap_angle

REQUIRED = ["s_track_m", "e_y_ref_m", "e_psi_ref_rad", "kappa_ref_1pm", "v_ref_mps"]


def intersection_count(xy):
    """Proper nonadjacent polyline crossings; dense approximation, not a spline proof."""
    a, b = xy[:-1], xy[1:]
    count = 0

    def cross(x, y):
        return x[..., 0] * y[..., 1] - x[..., 1] * y[..., 0]

    for i in range(len(a) - 2):
        j = np.arange(i + 2, len(a))
        if i == 0:
            j = j[j != len(a) - 1]
        u, v = b[i] - a[i], b[j] - a[j]
        denominator = cross(u, v)
        valid = abs(denominator) > 1e-12
        t = np.divide(cross(a[j] - a[i], v), denominator, out=np.zeros(len(j)), where=valid)
        w = np.divide(cross(a[j] - a[i], u), denominator, out=np.zeros(len(j)), where=valid)
        count += int(np.sum(valid & (t > 0) & (t < 1) & (w > 0) & (w < 1)))
    return count


class PlanningReference:
    def __init__(self, folder, track, track_identity, *, feasibility_policy="strict"):
        if feasibility_policy not in {"strict", "advisory"}:
            raise ValueError("Unknown feasibility policy")
        self.feasibility_policy = feasibility_policy
        folder = Path(folder)
        m = json.loads((folder / "planning_manifest.json").read_text())
        expected = dict(
            schema_version=1,
            track_sha256=track_identity,
            units="SI",
            frame="world_xy_m; Frenet left-positive; radians CCW",
            progress="centerline_arc_length_m",
            interpolation="periodic_cubic_channels",
            speed_semantics="body_longitudinal_mps",
            heading_semantics="body heading approximated by racing-line tangent; "
            "zero nominal sideslip",
            tracker_margin_m=0.08,
            minimum_speed_mps=0.5,
            maximum_speed_mps=6.0,
        )
        if "aggression_factor" in m:
            gamma = m["aggression_factor"]
            if (
                isinstance(gamma, bool)
                or not isinstance(gamma, (int, float))
                or not np.isfinite(gamma)
                or gamma < 1
            ):
                raise ValueError("Invalid aggression factor")
            if m.get("aggression_policy") != "scale_base_speed_then_global_cap":
                raise ValueError("Invalid aggression policy")
        polynomial_speed = m.get("interpolation") == "periodic_cubic_geometry_serialized_speed"
        if polynomial_speed:
            expected["interpolation"] = "periodic_cubic_geometry_serialized_speed"
        for key, value in expected.items():
            if m.get(key) != value:
                raise ValueError("Invalid Planning manifest: " + key)
        for key in ["reference_version", "track_name", "generator_revision"]:
            if not isinstance(m.get(key), str) or not m[key]:
                raise ValueError("Missing " + key)
        if not np.isclose(m.get("closed_track_length_m", np.nan), track.length, atol=1e-8, rtol=0):
            raise ValueError("Track length mismatch")
        f = pd.read_csv(folder / "planning_reference.csv")
        if not set(REQUIRED) <= set(f):
            raise ValueError("Missing Planning channels")
        numeric = f.select_dtypes(include=np.number)
        if len(f) < 8 or not np.isfinite(numeric.to_numpy()).all():
            raise ValueError("Nonfinite reference")
        try:
            values = f[REQUIRED].to_numpy(float)
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid channel dimensions") from error
        if not np.isfinite(values).all():
            raise ValueError("Nonfinite required channels")
        s = values[:, 0]
        if s[0] != 0 or np.any(np.diff(s) <= 0) or abs(s[-1] - track.length) > 1e-8:
            raise ValueError("Nonmonotonic or malformed periodic progress")
        if np.diff(s).max() > 0.1:
            raise ValueError("Reference sampling too sparse")
        if np.any(abs(f.e_psi_ref_rad) > np.pi):
            raise ValueError("Invalid relative heading")
        for key in REQUIRED[1:] + (["a_ref_mps2"] if "a_ref_mps2" in f else []):
            if not np.isclose(f[key].iloc[0], f[key].iloc[-1], atol=1e-8, rtol=0):
                raise ValueError("Malformed seam: " + key)
        if (
            "a_ref_mps2" in f
            and m.get("acceleration_semantics") != "total_longitudinal_force_over_mass"
        ):
            raise ValueError("Ambiguous acceleration semantics")
        s[-1] = track.length
        self.track, self.manifest, self.frame, self.length = track, m, f, track.length
        self.s = s
        self.splines = {}
        for key in ["e_y_ref_m", "e_psi_ref_rad", "kappa_ref_1pm", "v_ref_mps"] + (
            ["a_ref_mps2"] if "a_ref_mps2" in f else []
        ):
            data = f[key].to_numpy().copy()
            if key == "e_psi_ref_rad":
                data = np.unwrap(data)
            if abs(data[-1] - data[0]) > 1e-8:
                raise ValueError("Relative heading winding mismatch")
            data[-1] = data[0]
            self.splines[key] = CubicSpline(s, data, bc_type="periodic")
        if polynomial_speed:
            from apex.planning_reference.speed_polynomial import load_speed_polynomial

            self.splines["v_ref_mps"] = load_speed_polynomial(
                folder / "speed_polynomial.json", track.length, s, f.v_ref_mps.to_numpy()
            )
        self.validation = self._validate()

    def __call__(self, s):
        return self.sample(s)["v_ref_mps"]

    def sample(self, s_abs):
        if not np.isfinite(s_abs):
            raise ValueError("Nonfinite lookup progress")
        s = float(s_abs % self.length)
        result = {key: float(spline(s)) for key, spline in self.splines.items()}
        result["e_psi_ref_rad"] = wrap_angle(result["e_psi_ref_rad"])
        result["v_ref_mps"] = float(self.splines["v_ref_mps"](s))
        result["a_ref_mps2"] = (
            float(self.splines["a_ref_mps2"](s)) if "a_ref_mps2" in self.frame else 0.0
        )
        return result

    def _validate(self):
        # Sample twice the serialized density, including interval midpoints.
        s = np.sort(np.r_[self.s, (self.s[:-1] + self.s[1:]) / 2])
        g = np.array([self.track.centerline.geometry(x) for x in s])
        ey = self.splines["e_y_ref_m"](s)
        epsi = self.splines["e_psi_ref_rad"](s)
        kr = self.splines["kappa_ref_1pm"](s)
        v = self.splines["v_ref_mps"](s)
        if np.any((v < 0.5 - 1e-12) | (v > 6 + 1e-12)):
            raise ValueError("Speed outside dynamic domain")
        left = np.array([self.track.left_width(x) for x in s])
        right = np.array([self.track.right_width(x) for x in s])
        clearance = np.minimum(left - ey, right + ey)
        if clearance.min() < 0.08:
            raise ValueError("Frozen tracker margin violated")
        if np.min(np.cos(epsi)) <= 0.2:
            raise ValueError("Reference is not forward racing")
        denominator = 1 - g[:, 3] * ey
        if denominator.min() <= 0.1:
            raise ValueError("Invalid Frenet denominator")
        xy = g[:, :2] + ey[:, None] * np.c_[-np.sin(g[:, 2]), np.cos(g[:, 2])]
        xy[-1] = xy[0]
        curve = CubicSpline(s, xy, bc_type="periodic")
        d, dd = curve(s, 1), curve(s, 2)
        metric = np.linalg.norm(d, axis=1)
        geometric_heading = np.arctan2(d[:, 1], d[:, 0])
        heading_error = np.array(
            [wrap_angle(a - b - c) for a, b, c in zip(geometric_heading, g[:, 2], epsi)]
        )
        geometric_curvature = (d[:, 0] * dd[:, 1] - d[:, 1] * dd[:, 0]) / metric**3
        if abs(heading_error).max() > 0.005 or abs(geometric_curvature - kr).max() > 0.03:
            raise ValueError("Inconsistent racing-reference geometry")
        delta = np.arctan(0.30 * kr)
        rate = np.gradient(delta, s) * v / metric
        accel = np.diff(v**2) / (2 * np.linalg.norm(np.diff(xy, axis=0), axis=1))
        warnings = []
        if max(v * v * abs(kr)) > 2.0:
            warnings.append("Initial baseline lateral grip reserve exceeded")
        if max(abs(delta)) > 0.4 or max(abs(rate)) > 1.0:
            warnings.append("Steering/rate infeasible")
        if accel.max() > 0.65 or accel.min() < -0.85:
            warnings.append("Acceleration/braking infeasible")
        if warnings and self.feasibility_policy == "strict":
            raise ValueError(warnings[0])
        if "a_ref_mps2" in self.frame:
            a = self.frame.a_ref_mps2.to_numpy(float)
            if not np.isfinite(a).all() or a.min() < -3 or a.max() > 2:
                raise ValueError("Invalid a_ref")
        for key, expected in [("x_ref_m", xy[::2, 0]), ("y_ref_m", xy[::2, 1])]:
            if key in self.frame and not np.allclose(self.frame[key], expected, atol=1e-6, rtol=0):
                raise ValueError("Inconsistent debug coordinates")
        if "psi_ref_rad" in self.frame:
            error = np.array(
                [wrap_angle(a - b) for a, b in zip(self.frame.psi_ref_rad, geometric_heading[::2])]
            )
            if max(abs(error)) > 0.005:
                raise ValueError("Inconsistent world heading")
        crossings = intersection_count(g[:, :2])
        ref_crossings = intersection_count(xy)
        if crossings or ref_crossings:
            raise ValueError("Self-intersecting track/reference")
        seam0 = self.track.centerline.geometry(0)
        seam1 = self.track.centerline.geometry(self.length - 1e-7)
        return dict(
            accepted=True,
            **(
                {"feasibility_policy": "advisory", "feasibility_warnings": warnings}
                if self.feasibility_policy == "advisory"
                else {}
            ),
            samples=len(s),
            lap_length_m=self.length,
            centerline_curvature_min=float(g[:, 3].min()),
            centerline_curvature_max=float(g[:, 3].max()),
            reference_curvature_min=float(kr.min()),
            reference_curvature_max=float(kr.max()),
            speed_min=float(v.min()),
            speed_max=float(v.max()),
            minimum_boundary_clearance_m=float(clearance.min()),
            minimum_frenet_denominator=float(denominator.min()),
            maximum_lateral_demand_mps2=float(max(v * v * abs(kr))),
            maximum_steering_rad=float(max(abs(delta))),
            maximum_steering_rate_rad_s=float(max(abs(rate))),
            acceleration_max=float(accel.max()),
            braking_min=float(accel.min()),
            geometric_heading_error_max=float(max(abs(heading_error))),
            geometric_curvature_error_max=float(max(abs(geometric_curvature - kr))),
            sampled_self_intersections=crossings,
            reference_self_intersections=ref_crossings,
            seam_position_gap_m=float(np.linalg.norm(np.array(seam0[:2]) - seam1[:2])),
            seam_heading_gap_rad=abs(wrap_angle(seam0[2] - seam1[2])),
            seam_curvature_gap=abs(seam0[3] - seam1[3]),
            caveat="Conservative synthetic gates and dense polyline intersection checks; "
            "not a global dynamic feasibility proof",
        )
