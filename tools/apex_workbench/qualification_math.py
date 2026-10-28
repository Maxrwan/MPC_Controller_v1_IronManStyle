"""Accepted finite-grid calculations only. This module never creates qualification evidence."""

from math import isfinite

from apex.coordinates.angles import wrap_angle
from tools.apex_workbench.lab_configuration import CASES, CRITERIA, GRIDS
from tools.apex_workbench.lab_evidence import STATE_NAMES

UNITS = ["m/s", "m/s", "rad/s", "rad", "m", "m"]


def _window(run, grid):
    h, steps, _ = GRIDS[grid]
    states, diagnostics = run["states"], run["diagnostics"]
    if len(states) != steps + 1 or len(diagnostics) != steps + 1:
        raise ValueError("Qualification requires complete native-grid coverage")
    for k, (s, d) in enumerate(zip(states, diagnostics)):
        if s["time"] != k * h or d["time"] != k * h:
            raise ValueError("Qualification native timestamps disagree with integer ticks")
        values = [s[name] for name in STATE_NAMES] + [
            d[name]
            for name in (
                "alpha_f",
                "alpha_r",
                "front_lateral_utilization",
                "rear_lateral_utilization",
            )
        ]
        if any(type(v) not in (float, int) or not isfinite(v) for v in values):
            raise ValueError("Nonfinite or ill-typed qualification sample")
        if type(s["boundary_violation"]) is not bool:
            raise ValueError("Missing native sampled corridor flag")
    summary = run["summary"]
    coverage = (
        summary["horizon_reached"] is True
        and summary["runner_stop_reason"] == "duration"
        and summary["failure"] is None
    )
    slip = max(abs(d[key]) for d in diagnostics for key in ("alpha_f", "alpha_r"))
    utilization = max(
        d[key]
        for d in diagnostics
        for key in ("front_lateral_utilization", "rear_lateral_utilization")
    )
    nonnegative = all(
        d[key] >= 0
        for d in diagnostics
        for key in ("front_lateral_utilization", "rear_lateral_utilization")
    )
    corridor = sum(s["boundary_violation"] for s in states)
    return {
        "coverage": coverage,
        "maximum_absolute_slip_rad": slip,
        "maximum_lateral_utilization": utilization,
        "sampled_corridor_violations": corridor,
        "satisfied": bool(
            coverage
            and nonnegative
            and slip <= CRITERIA["maximum_absolute_slip_rad"]
            and utilization <= CRITERIA["maximum_lateral_utilization"]
            and corridor <= CRITERIA["maximum_sampled_corridor_violations"]
        ),
    }


def _distance(a, b, channel):
    difference = a[channel] - b[channel]
    if not isfinite(difference):
        raise ValueError("Nonfinite shared-time state difference")
    return abs(wrap_angle(difference) if channel == "e_psi" else difference)


def calculate(family):
    """Pure results may be tested with synthetic fixtures, never published as real evidence."""
    if set(family) != set(CASES) or any(set(family[c]) != set(GRIDS) for c in CASES):
        raise ValueError("Protocol requires exactly the five accepted cases and three grids")
    cases = {}
    for case in CASES:
        runs = family[case]
        windows = {grid: _window(runs[grid], grid) for grid in GRIDS}
        components = {}
        for channel, unit in zip(STATE_NAMES, UNITS):
            coarse = runs["nominal"]["states"]
            half = runs["half"]["states"]
            fine = runs["quarter"]["states"]
            d0 = max(_distance(coarse[k], half[2 * k], channel) for k in range(101))
            d1 = max(_distance(half[2 * k], fine[4 * k], channel) for k in range(101))
            error = max(_distance(coarse[k], fine[4 * k], channel) for k in range(101))
            tolerance = CRITERIA["state_tolerance_per_channel_SI"]
            floor = CRITERIA["refinement_roundoff_floor_per_channel_SI"]
            components[channel] = {
                "unit": unit,
                "d0": d0,
                "d1": d1,
                "nominal_finest": error,
                "refinement_ratio": d0 / d1 if d0 > floor and d1 > floor else None,
                "satisfied": bool(
                    error <= tolerance and d1 <= CRITERIA["refinement_contraction"] * d0 + floor
                ),
            }
        cases[case] = {
            "components": components,
            "native_windows": windows,
            "numerical_satisfied": all(c["satisfied"] for c in components.values())
            and all(w["coverage"] for w in windows.values()),
            "sampled_window_satisfied": all(w["satisfied"] for w in windows.values()),
            "satisfied": all(c["satisfied"] for c in components.values())
            and all(w["satisfied"] for w in windows.values()),
        }
    pairs = {}
    for case in CASES[1:]:
        base, treatment = family["VDL1_BASE"]["nominal"], family[case]["nominal"]
        signal = max(
            abs(base["states"][k]["r"] - treatment["states"][k]["r"]) for k in range(20, 101)
        )
        threshold = CRITERIA["yaw_signal_margin"] * max(
            CRITERIA["state_tolerance_per_channel_SI"],
            cases["VDL1_BASE"]["components"]["r"]["nominal_finest"],
            cases[case]["components"]["r"]["nominal_finest"],
        )
        pairs[case] = {
            "baseline": "VDL1_BASE",
            "treatment": case,
            "peak_yaw_difference_rad_per_s": signal,
            "required_signal_rad_per_s": threshold,
            "excitation_sufficient": signal >= threshold,
            "satisfied": bool(
                signal >= threshold and cases["VDL1_BASE"]["satisfied"] and cases[case]["satisfied"]
            ),
        }
    return {
        "schema": "apex-vdl-calculation/1",
        "authority": "calculation_only_not_qualification_evidence",
        "physical_validity": "not_established",
        "cases": cases,
        "pairs": pairs,
        "all_criteria_satisfied": all(p["satisfied"] for p in pairs.values()),
    }
