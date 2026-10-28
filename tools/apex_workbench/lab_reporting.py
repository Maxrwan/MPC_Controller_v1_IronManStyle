"""Sampled diagnostics reporting; no dynamics, qualification campaign or physical claims."""

from math import isfinite

from tools.apex_workbench.lab_configuration import CRITERIA

DIAGNOSTIC_UNITS = {
    "alpha_f": "rad",
    "alpha_r": "rad",
    "fyf": "N",
    "fyr": "N",
    "fzf": "N",
    "fzr": "N",
    "fzf_static": "N",
    "fzr_static": "N",
    "cf": "N/rad",
    "cr": "N/rad",
    "cf_eff": "N/rad",
    "cr_eff": "N/rad",
    "fx_total": "N",
    "a_cmd": "m/s^2",
    "mu": "1",
    "front_lateral_utilization": "1",
    "rear_lateral_utilization": "1",
    "frenet_denominator": "1",
    "track_s": "m",
    "curvature": "1/m",
}
OPTIONAL_DIAGNOSTIC_UNITS = {
    "fx_front": "N",
    "fx_rear": "N",
    "front_friction_capacity": "N",
    "rear_friction_capacity": "N",
    "front_lateral_capacity": "N",
    "rear_lateral_capacity": "N",
    "front_combined_utilization": "1",
    "rear_combined_utilization": "1",
}
LIMITATIONS = [
    "unmeasured synthetic parameters",
    "unsaturated linear axle tires",
    "provisional quasi-static loads",
    "ideal instantaneous steering",
    "sampled model window; no physical validation",
]


def summarize(states, diagnostics, stop_reason, failure):
    horizon = bool(
        states and states[-1]["time"] == 0.5 and stop_reason == "duration" and not failure
    )
    if len(states) != len(diagnostics) or not states:
        raise ValueError("Incomplete sampled diagnostic coverage")
    extrema = {}
    for key in DIAGNOSTIC_UNITS:
        values = [float(row[key]) for row in diagnostics]
        if not all(isfinite(v) for v in values):
            raise ValueError("Nonfinite laboratory diagnostic: " + key)
        low, high = (
            min(range(len(values)), key=values.__getitem__),
            max(range(len(values)), key=values.__getitem__),
        )
        peak = max(range(len(values)), key=lambda i: abs(values[i]))
        extrema[key] = {
            "min": values[low],
            "min_time_s": states[low]["time"],
            "max": values[high],
            "max_time_s": states[high]["time"],
            "max_abs": abs(values[peak]),
            "max_abs_time_s": states[peak]["time"],
            "unit": DIAGNOSTIC_UNITS[key],
        }
    violations = sum(bool(row["boundary_violation"]) for row in states)
    reasons = []
    if any(
        extrema[k]["max_abs"] > CRITERIA["maximum_absolute_slip_rad"]
        for k in ("alpha_f", "alpha_r")
    ):
        reasons.append("sampled slip exceeds provisional 0.050 rad teaching filter")
    if any(
        extrema[k]["max"] > CRITERIA["maximum_lateral_utilization"]
        for k in ("front_lateral_utilization", "rear_lateral_utilization")
    ):
        reasons.append("sampled lateral demand exceeds synthetic mu*Fz diagnostic")
    if violations:
        reasons.append("sampled CG corridor violation")
    window = (
        "outside_window"
        if reasons
        else "within_provisional_sampled_window"
        if horizon
        else "unknown"
    )
    return {
        "schema": "apex-vdl-run-summary/1",
        "configuration_validity": "admissible",
        "runner_stop_reason": stop_reason,
        "failure": failure,
        "horizon_reached": horizon,
        "intended_horizon_s": 0.5,
        "last_retained_time_s": states[-1]["time"],
        "state_rows": len(states),
        "diagnostic_rows": len(diagnostics),
        "sampled_boundary_violations": violations,
        "diagnostic_extrema": extrema,
        "numerical_qualification": "not_qualified" if horizon else "invalid_or_incomplete",
        "qualification_record": None,
        "excitation": "unqualified; requires a permitted pair and numerical qualification",
        "sampled_model_window": {"status": window, "reasons": reasons},
        "limitations": list(LIMITATIONS),
        "evidence_integrity": "pending external manifest commit; verify on consumption",
        "terminal_diagnostics": "last held command; informational"
        if horizon
        else "last retained/attempted interval; partial execution",
    }
