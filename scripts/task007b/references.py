"""Offline controlled aggression: preserve the accepted line and scale speed only."""

import csv
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track

BASE = Path("configs/planning/synthetic_grand_prix_v1")
PACKAGES = Path("configs/planning/task007b")


def package_name(gamma):
    return f"gamma_{gamma:.3f}".replace(".", "p")


def generate(gammas):
    track, _, identity = load_track(BASE / "track_source.json")
    original = pd.read_csv(BASE / "planning_reference.csv", float_precision="round_trip")
    for gamma in gammas:
        if not np.isfinite(gamma) or gamma < 1:
            raise ValueError("Gamma must be finite and >=1")
        folder = PACKAGES / package_name(gamma)
        folder.mkdir(parents=True, exist_ok=True)
        frame = original.copy()
        frame["v_ref_mps"] = np.minimum(gamma * original.v_ref_mps, 6.0)
        # Exact accepted fixture bytes at gamma=1; geometric values unchanged at all levels.
        if gamma == 1:
            shutil.copyfile(BASE / "planning_reference.csv", folder / "planning_reference.csv")
        else:
            with (BASE / "planning_reference.csv").open(newline="") as stream:
                reader = csv.DictReader(stream)
                fields = reader.fieldnames
                rows = list(reader)
            for row, value in zip(rows, frame.v_ref_mps):
                row["v_ref_mps"] = format(value, ".17g")
            with (folder / "planning_reference.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
        shutil.copyfile(BASE / "track_source.json", folder / "track_source.json")
        manifest = json.loads((BASE / "planning_manifest.json").read_text())
        manifest.update(
            aggression_factor=gamma,
            aggression_policy="scale_base_speed_then_global_cap",
            reference_version=f"task007b-gamma-{gamma:g}",
            base_reference_sha256=hashlib.sha256(
                (BASE / "planning_reference.csv").read_bytes()
            ).hexdigest(),
            generator_revision="task007b-speed-scaling-v2",
        )
        if gamma * original.v_ref_mps.max() >= 6:
            # Split the ORIGINAL cubic exactly at cap crossings OFFLINE. No refitting,
            # smoothing or runtime clipping: serialize the resulting piecewise law.
            base = CubicSpline(original.s_track_m, original.v_ref_mps, bc_type="periodic")
            knots, coefficients = [], []
            for i, width in enumerate(np.diff(base.x)):
                polynomial = gamma * base.c[:, i]
                shifted = polynomial.copy()
                shifted[-1] -= 6
                roots = np.roots(shifted)
                cuts = (
                    [0.0]
                    + sorted(
                        r.real
                        for r in roots
                        if abs(r.imag) < 1e-9 and 1e-10 < r.real < width - 1e-10
                    )
                    + [width]
                )
                for lo, hi in zip(cuts[:-1], cuts[1:]):
                    knots.append(float(base.x[i] + lo))
                    if np.polyval(polynomial, (lo + hi) / 2) >= 6:
                        coefficients.append([0.0, 0.0, 0.0, 6.0])
                    else:
                        translated = np.poly1d(polynomial)(np.poly1d([1.0, lo])).c
                        coefficients.append(np.pad(translated, (4 - len(translated), 0)).tolist())
            knots.append(float(base.x[-1]))
            (folder / "speed_polynomial.json").write_text(
                json.dumps(
                    dict(knots_m=knots, coefficients=np.asarray(coefficients).T.tolist()), indent=2
                )
                + "\n"
            )
            manifest["interpolation"] = "periodic_cubic_geometry_serialized_speed"
        (folder / "planning_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        reference = PlanningReference(folder, track, identity, feasibility_policy="advisory")
        (folder / "planning_validation.json").write_text(
            json.dumps(reference.validation, indent=2) + "\n"
        )
        print(folder, reference.validation["feasibility_warnings"], flush=True)
