"""Actual synthetic vehicle DARE evidence for every approved C2 multiplier pair."""

import json
from pathlib import Path

import numpy as np

from apex.config import load_vehicle_parameters
from apex.control.baseline.lqr import DesignScales, discrete_matrices
from apex.control.mpc.cost import TerminalSchedule

PAIRS = [(1, 1), (0.5, 1), (0.25, 1), (0, 1), (1, 0.5), (1, 0.25), (1, 0), (0.25, 0.25), (0, 0)]


def audit():
    vehicle = load_vehicle_parameters("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    rows = []
    for vy, r in PAIRS:
        schedule = TerminalSchedule(vehicle, alpha_vy=vy, alpha_r=r)
        q, rr = DesignScales().weights()
        q[2, 2] *= vy
        q[3, 3] *= r
        for speed, p in zip(schedule.nodes, schedule.matrices):
            a, b = discrete_matrices(vehicle, speed, 0.01)
            k = np.linalg.solve(rr + b.T @ p @ b, b.T @ p @ a)
            residual = a.T @ p @ a - p - a.T @ p @ b @ k + q
            normalized = float(np.linalg.norm(residual, np.inf) / max(1, np.linalg.norm(p, np.inf)))
            radius = float(max(abs(np.linalg.eigvals(a - b @ k))))
            minimum = float(np.linalg.eigvalsh(p).min())
            assert normalized < 1e-10 and radius < 1 and minimum >= -1e-9
            rows.append(
                dict(
                    alpha_vy=vy,
                    alpha_r=r,
                    speed_mps=float(speed),
                    q=q.tolist(),
                    p=p.tolist(),
                    riccati_relative_residual=normalized,
                    spectral_radius=radius,
                    minimum_eigenvalue=minimum,
                    symmetry_max=float(abs(p - p.T).max()),
                )
            )
    Path("results/task007c_resume/terminal_audit.json").write_text(
        json.dumps(rows, indent=2) + "\n"
    )
    print("Validated", len(rows), "actual-vehicle DARE solutions")


if __name__ == "__main__":
    audit()
