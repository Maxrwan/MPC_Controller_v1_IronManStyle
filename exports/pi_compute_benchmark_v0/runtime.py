"""Compose the frozen profile exactly as the referenced PRE-INT-W1 producer does.

This portable adapter has no PRE-INT evidence driver, claims, or hardware endpoint.
"""

import json
from dataclasses import asdict

import numpy as np
from common import ROOT

from apex.config import load_vehicle_parameters
from apex.control.mpc.controller import MPCController
from apex.control.mpc.cost import CostScales
from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.control.trajectory.planner import TrajectoryPlanner
from apex.control.trajectory.tracker import TrackerConfig, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.optimization.solvers.ipopt import DEFAULT_OPTIONS, IpoptSolver
from apex.planning_reference.reference import PlanningReference
from apex.planning_reference.track import load_track

VENDOR = ROOT / "vendor"


def load():
    manifest = json.loads(
        (VENDOR / "configs/performance/apex_performance_synthetic_v1.json").read_text()
    )["profile"]
    p = load_vehicle_parameters(VENDOR / manifest["vehicle"]["file"]["path"])
    folder = VENDOR / manifest["planning"]["package"]
    track, _, identity = load_track(folder / "track_source.json")
    reference = PlanningReference(folder, track, identity, feasibility_policy="advisory")
    return manifest, p, track, reference


def compose(tracker_class=TrajectoryTracker):
    manifest, p, track, reference = load()
    config = MPCConfig(
        horizon=8,
        dt=0.1,
        substeps=4,
        costs=CostScales(lateral=2),
        tire_physics=RACING_TIRE_PHYSICS,
        tracker_margin=0.08,
        racing_reference=True,
        progress_weight=0,
    )
    options = {**DEFAULT_OPTIONS, "ipopt.warm_start_init_point": "yes"}
    assert asdict(config) == manifest["nmpc"]["configuration"]
    assert options == manifest["nmpc"]["solver"]["explicit_effective_options"]
    assert asdict(TrackerConfig()) == manifest["tracker"]["configuration"]
    assert asdict(p) == manifest["vehicle"]["parameters"]
    problem = MPCProblem(p, config)
    solver = IpoptSolver(problem, options)
    controller = MPCController(
        p, track, solver, problem, reference, warm_start=True, racing_reference=reference
    )
    tracker = tracker_class(
        p, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
    )
    assert tracker.lower.tolist() == manifest["tracker"]["control_lower"]
    assert tracker.upper.tolist() == manifest["tracker"]["control_upper"]
    snapshot = {
        "architecture": "A",
        "mpc": asdict(config),
        "tracker": asdict(tracker.config),
        "solver": options,
        "vehicle": asdict(p),
        "warm_start": True,
        "planning": manifest["planning"],
        "reference_validation": reference.validation,
    }
    return controller, TrajectoryPlanner(controller, track), tracker, track, snapshot


def select_scenarios():
    """Rank serialized geometry samples, then admit reference states without tuning."""
    _, p, track, reference = load()
    s = reference.s[:-1]
    k = np.array([track.sample(float(x)).curvature for x in s])
    gradient = np.gradient(k, s)
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    scores = {"straight": -abs(k), "high_curvature": abs(k), "curvature_transition": abs(gradient)}
    selected = []
    for name, score in scores.items():
        for index in np.argsort(-score, kind="stable"):
            progress = float(s[index])
            ref = reference.sample(progress)
            x = [
                ref["v_ref_mps"],
                0.0,
                ref["v_ref_mps"] * ref["kappa_ref_1pm"],
                ref["e_psi_ref_rad"],
                progress,
                ref["e_y_ref_m"],
            ]
            u = [float(np.arctan(p.wheelbase * ref["kappa_ref_1pm"])), ref["a_ref_mps2"]]
            try:
                plant.diagnostics(x, u)
            except ValueError:
                continue
            if any(abs(progress - row["s_track_m"]) < 0.1 for row in selected):
                continue
            selected.append(
                {
                    "name": name,
                    "s_track_m": progress,
                    "initial_state": x,
                    "reference": ref,
                    "initial_validation_control": u,
                    "track_curvature_1pm": float(k[index]),
                    "track_curvature_gradient_1pm2": float(gradient[index]),
                    "serialized_row_index": int(index),
                }
            )
            break
        else:
            raise ValueError("No valid reference state for " + name)
    return {
        "duration_s": 2.0,
        "track_length_m": track.length,
        "selection": "Stable descending rank on serialized Planning s rows excluding seam "
        "duplicate: minimum |track curvature|; maximum |track curvature|; "
        "maximum |numpy.gradient(track curvature, s)|. Admit model-valid "
        "reference state and feedforward control; distinct starts >=0.1 m.",
        "windows": selected,
    }
