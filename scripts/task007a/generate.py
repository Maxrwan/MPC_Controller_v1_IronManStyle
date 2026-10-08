"""OFFLINE synthetic test fixture, never imported by the runtime controller."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from apex.coordinates.angles import wrap_angle
from apex.planning_reference.track import load_track


def generate(folder):
    folder = Path(folder)
    track, source, identity = load_track(folder / "track_source.json")
    s = np.linspace(0, track.length, int(np.ceil(track.length / 0.05)) + 1)
    geometry = np.array([track.centerline.geometry(x) for x in s])
    anchors = [track.project_point(*point) for point in source["control_points_m"]]
    offset = np.zeros_like(s)
    # Signed inside-apex Gaussian and outside-entry/exit lobes, periodically repeated.
    for index, width, separation in [
        (6, 1.0, 3.0),
        (11, 1.5, 4.0),
        (17, 4.0, 10.0),
        (31, 1.0, 3.0),
        (36, 1.8, 5.0),
        (42, 1.0, 3.0),
    ]:
        sign = np.sign(track.sample(anchors[index]).curvature)
        for lap in [-1, 0, 1]:
            distance = s - anchors[index] + lap * track.length
            offset += sign * (
                0.22 * np.exp(-0.5 * (distance / width) ** 2)
                - 0.12 * np.exp(-0.5 * ((distance - separation) / width) ** 2)
                - 0.12 * np.exp(-0.5 * ((distance + separation) / width) ** 2)
            )
    offset[-1] = offset[0]
    xy = geometry[:, :2] + offset[:, None] * np.c_[-np.sin(geometry[:, 2]), np.cos(geometry[:, 2])]
    xy[-1] = xy[0]
    curve = CubicSpline(s, xy, bc_type="periodic")
    first, second = curve(s, 1), curve(s, 2)
    heading = np.unwrap(np.arctan2(first[:, 1], first[:, 0]))
    curvature = (first[:, 0] * second[:, 1] - first[:, 1] * second[:, 0]) / np.linalg.norm(
        first, axis=1
    ) ** 3
    epsi = np.array([wrap_angle(a - b) for a, b in zip(heading, geometry[:, 2])])
    # Conservative curvature envelope and cyclic acceleration/braking feasibility passes.
    speed = np.minimum(3.0, np.sqrt(1.5 / np.maximum(abs(curvature[:-1]), 1e-6)))
    ds_line = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    for _ in range(30):
        before = speed.copy()
        for i in range(len(speed)):
            j = (i + 1) % len(speed)
            speed[j] = min(speed[j], np.sqrt(speed[i] ** 2 + 2 * 0.4 * ds_line[i]))
        for i in range(len(speed) - 1, -1, -1):
            j = (i + 1) % len(speed)
            speed[i] = min(speed[i], np.sqrt(speed[j] ** 2 + 2 * 0.6 * ds_line[i]))
        if np.max(abs(before - speed)) < 1e-12:
            break
    speed = np.r_[speed, speed[0]]
    starts = [(anchors[i], name) for i, name in source["sector_anchor_indices"]]
    sectors = [next(name for start, name in reversed(starts) if x >= start - 1e-8) for x in s[:-1]]
    sectors.append(sectors[0])
    frame = pd.DataFrame(
        dict(
            s_track_m=s,
            e_y_ref_m=offset,
            e_psi_ref_rad=epsi,
            kappa_ref_1pm=curvature,
            v_ref_mps=speed,
            x_ref_m=xy[:, 0],
            y_ref_m=xy[:, 1],
            psi_ref_rad=heading,
            sector_name=sectors,
        )
    )
    frame.to_csv(folder / "planning_reference.csv", index=False, float_format="%.12g")
    manifest = dict(
        schema_version=1,
        reference_version="synthetic-gp-conservative-v1",
        track_name=source["name"],
        track_sha256=identity,
        closed_track_length_m=track.length,
        generator_revision="task007a-test-fixture-v1",
        synthetic_test_only=True,
        units="SI",
        frame="world_xy_m; Frenet left-positive; radians CCW",
        progress="centerline_arc_length_m",
        interpolation="periodic_cubic_channels",
        heading_semantics="body heading approximated by racing-line tangent; zero nominal sideslip",
        speed_semantics="body_longitudinal_mps",
        acceleration_semantics="omitted",
        tracker_margin_m=0.08,
        minimum_speed_mps=0.5,
        maximum_speed_mps=6.0,
        generation=dict(
            sample_spacing_max_m=0.05,
            lateral_acceleration_limit_mps2=1.5,
            acceleration_limit_mps2=0.4,
            braking_limit_mps2=0.6,
            speed_cap_mps=3.0,
            offline_only=True,
        ),
        sectors=[dict(start_s_m=a, name=b) for a, b in starts],
    )
    (folder / "planning_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        "Generated", len(frame), "samples; length", track.length, "speed", speed.min(), speed.max()
    )
