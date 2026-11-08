"""Isolated component-algebra test against original native retained packet; no experiment."""

import hashlib
import json
import sys
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.apex_workbench import nmpc_scratch as scratch  # noqa: E402
from tools.apex_workbench import nmpc_scratch_worker as observer  # noqa: E402
from tools.apex_workbench import nmpc_weight_worker as native  # noqa: E402

native.bootstrap(scratch.RUNTIME)
import numpy as np  # noqa: E402

from apex.control.mpc.problem import MPCProblem  # noqa: E402
from apex.control.trajectory.packet import TrajectoryPacket  # noqa: E402
from apex.control.trajectory.tracker import LATERAL, TVLQR, TrajectoryTracker  # noqa: E402
from apex.optimization.solvers.ipopt import IpoptSolver  # noqa: E402
from apex.simulation.asynchronous import AsyncRunner  # noqa: E402


def prohibited(*args, **kwargs):
    raise AssertionError("This component test may not solve or execute a simulation")


IpoptSolver.solve = prohibited
AsyncRunner.run = prohibited
parts = observer.resolve(scratch.defaults())
track, _, parameters, config = parts[:4]
problem = MPCProblem(parameters, config)
root = Path(__file__).resolve().parents[3]
original = (
    root
    / "results/apex_workbench_nmpc_weights/runs"
    / "20261103T092919578650Z_8db96af73edb48afa17b8d608c9cb7a9"
    / "experiment"
)
raw_bytes = (original / "raw.json").read_bytes()
assert (
    hashlib.sha256(raw_bytes).hexdigest()
    == "e81b5df5e10164eed1feccc3217292718391f1c0eb89d123cfb70e3b47a13263"
)
raw = json.loads(raw_bytes)
derived = observer.presentation(parts[0], parts[1], raw, parts[2], parts[3], parts[4])
assert len(derived["states"]) == len(raw["states"]) == 400
assert raw["states"][0]["e_y"] != 0
assert derived["states"][0]["racing_error_y_m"] == 0
assert derived["states"][0]["racing_error_heading_rad"] == 0
assert [row["time"] for row in derived["states"]] == [row["time"] for row in raw["states"]]
assert derived["geometry"][0]["x"] == track.sample(0).x
packet = TrajectoryPacket(
    **{
        f.name: raw["packets"][0][f.name]
        for f in fields(TrajectoryPacket)
        if f.name in raw["packets"][0]
    }
)
prediction = json.loads((original / "optimizations.jsonl").read_text().splitlines()[0])[
    "prediction"
]
builder = TVLQR(problem.model, track)
record = observer.packet_observation(
    packet,
    raw["plans"][0],
    SimpleNamespace(last_prediction=prediction),
    SimpleNamespace(gain_builder=builder),
    track,
)
assert record["plan_id"] == raw["plans"][0]["plan_id"] == packet.plan_id
assert record["linearization"]["state_order"] == ["e_y", "e_psi", "vy", "r"]
assert list(map(int, LATERAL)) == [5, 3, 1, 2]
assert [r["time"] for r in record["linearization"]["rows"]] == packet.gain_times.tolist()
assert np.array_equal(record["linearization"]["rows"][0]["K"], packet.gains[:1])
state, command, _ = packet.sample(float(packet.gain_times[0]))
curvature = packet.curvature(float(packet.gain_times[0]))
a, b = (np.asarray(v) for v in builder.jacobian(state, command, curvature))
transition = problem.model.rk4(0.01, 2)
h = 1e-6  # Unit derivative-consistency tolerance, not scientific qualification/refinement.
numerical_a = np.zeros((4, 4))
for column, index in enumerate(LATERAL):
    plus, minus = state.copy(), state.copy()
    plus[index] += h
    minus[index] -= h
    numerical_a[:, column] = (
        (
            np.asarray(transition(plus, command, curvature)[0]).ravel()
            - np.asarray(transition(minus, command, curvature)[0]).ravel()
        )
        / (2 * h)
    )[LATERAL]
plus, minus = command.copy(), command.copy()
plus[0] += h
minus[0] -= h
numerical_b = (
    (
        np.asarray(transition(state, plus, curvature)[0]).ravel()
        - np.asarray(transition(state, minus, curvature)[0]).ravel()
    )
    / (2 * h)
)[LATERAL, None]
np.testing.assert_allclose(a[np.ix_(LATERAL, LATERAL)], numerical_a, rtol=1e-5, atol=1e-7)
np.testing.assert_allclose(b[LATERAL, :1], numerical_b, rtol=1e-5, atol=1e-7)
tracker = TrajectoryTracker(
    parameters, problem.lbx[problem.nx : problem.nx + 2], problem.ubx[problem.nx : problem.nx + 2]
)
tracker.previous = command.copy()
perturbed = state.copy()
perturbed[5] += 0.001
_, error, correction, _ = tracker.command(perturbed, state, command, packet.gains[0])
assert np.isclose(correction[0], -packet.gains[0] @ error[LATERAL], rtol=0, atol=1e-12)
print(
    json.dumps(
        {
            "result": "PASS",
            "nominal_packet": packet.plan_id,
            "native_gain_rows": len(record["linearization"]["rows"]),
            "dt_s": 0.01,
            "A_max_derivative_difference": float(
                np.max(abs(a[np.ix_(LATERAL, LATERAL)] - numerical_a))
            ),
            "B_max_derivative_difference": float(np.max(abs(b[LATERAL, :1] - numerical_b))),
            "native_feedback_sign": "negative",
            "canonical_geometry_and_racing_reference": (
                "PASS; initial racing error zero despite nonzero Frenet e_y"
            ),
            "optimizer_solves": 0,
            "plant_steps": 0,
            "scope": (
                "Component algebra and associations only; retained packet is not a new execution"
            ),
        }
    )
)
