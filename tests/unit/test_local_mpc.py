"""Convex lateral QP, physical local parity, reusable solvers and per-update replacement."""

from dataclasses import replace
from time import perf_counter

import numpy as np
import pytest
from scipy.linalg import solve_discrete_are

from apex.control.local_mpc.model import LocalModel
from apex.control.local_mpc.qp import OSQPWorkspace, condense
from apex.control.local_mpc.tracker import LinearMPCTracker, LocalMPCConfig
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.control.trajectory.packet import TrajectoryBuffer, TrajectoryPacket
from apex.control.trajectory.tracker import LATERAL, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle


def packet():
    times = np.arange(5) * 0.1
    x = np.zeros((5, 6))
    x[:, 0] = 2
    x[:, 4] = times * 2
    return TrajectoryPacket(
        0,
        0,
        0,
        0,
        0,
        times,
        x,
        np.zeros((4, 2)),
        x[0],
        x[0],
        "Solve_Succeeded",
        0.01,
        0.02,
        times[:-1],
        np.tile([1, 2, 0.1, 0.1], (4, 1)),
        np.zeros(5),
    )


def setup(p, n=5, **kwargs):
    model = LocalModel(SymbolicBicycle(p, RACING_TIRE_PHYSICS))
    tracker = LinearMPCTracker(p, [-0.4, -3], [0.4, 2], model, LocalMPCConfig(horizon=n, **kwargs))
    buffer = TrajectoryBuffer()
    buffer.insert(packet(), 0)
    return tracker, buffer


@pytest.mark.parametrize("n", [3, 5, 8, 10, 15])
def test_hessian_constraints_and_unconstrained_lqr(dynamic_vehicle, n):
    tracker, buffer = setup(dynamic_vehicle, n)
    model = tracker.local_model
    matrices, nominal, terminal = model.horizon(buffer.active, 0, n)
    error = np.array([0.005, 0.002, 0.0, 0.0])
    h, g, lo, hi = condense(matrices, error, nominal, 0, model.q, 25, terminal, -10, 10, 10)
    assert h.shape == (n, n) and np.linalg.eigvalsh(h).min() > 0
    solver = OSQPWorkspace(n)
    solution, info = solver.solve(h, g, lo, hi)
    assert info["success"]
    a, b, _ = matrices[0]
    p = solve_discrete_are(a, b, model.q, np.array([[25.0]]))
    gain = np.linalg.solve(25 + b.T @ p @ b, b.T @ p @ a)
    assert solution[0] == pytest.approx(float((-gain @ error).item()), abs=2e-6)
    assert solver.dimensions()["constraint_nonzeros"] == 3 * n - 1


def test_future_nominal_changes_respect_absolute_and_rate_constraints(dynamic_vehicle):
    tracker, buffer = setup(dynamic_vehicle)
    matrices, nominal, terminal = tracker.local_model.horizon(buffer.active, 0, 5)
    nominal[:] = [0.3, 0.3, -0.2, -0.2, 0.1]
    h, g, lo, hi = condense(
        matrices,
        np.array([0.2, 0.1, 0, 0]),
        nominal,
        0.2,
        tracker.local_model.q,
        25,
        terminal,
        -0.4,
        0.4,
        0.01,
    )
    solver = OSQPWorkspace(5)
    solution, info = solver.solve(h, g, lo, hi)
    assert info["success"]
    actual = nominal + solution
    assert np.max(abs(actual)) <= 0.4 + 1e-5
    assert np.max(abs(np.diff(np.r_[0.2, actual]))) <= 0.01 + 1e-5


def test_local_jacobian_and_affine_defect_match_numpy(dynamic_vehicle, straight_geometry):
    model = LocalModel(SymbolicBicycle(dynamic_vehicle, RACING_TIRE_PHYSICS))
    plant = DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    nominal = np.array([2.0, 0.02, 0.1, 0.02, 1.0, 0.01])
    u = np.array([0.02, 0.1])
    next_ref = nominal.copy()
    next_ref[4] += 0.02
    a, b, c = model.matrices(nominal, u, 0, next_ref)
    assert a.shape == (4, 4) and b.shape == (4, 1) and c.shape == (4,)
    perturb = np.array([1e-5, -2e-5, 2e-5, -1e-5])
    steering = 1e-5
    x = nominal.copy()
    x[LATERAL] += perturb
    command = u + np.array([steering, 0])
    propagated = plant.step(plant.step(x, command, 0.005), command, 0.005)
    np.testing.assert_allclose(
        a @ perturb + b[:, 0] * steering + c, (propagated - next_ref)[LATERAL], atol=2e-8
    )
    assert np.linalg.norm(c) > 0  # A linearly interpolated reference need not satisfy dynamics.


def test_solver_reuse_shift_and_determinism(dynamic_vehicle, monkeypatch):
    tracker, buffer = setup(dynamic_vehicle)
    state = np.array([2.0, 0, 0, 0, 0, 0.01])
    first, _ = tracker.update(state, buffer, 0)
    workspace = tracker.workspaces[5]
    old = tracker.solution.copy()
    guesses = []
    original = workspace.solve

    def spy(h, g, lower, upper, warm):
        guesses.append(warm.copy())
        return original(h, g, lower, upper, warm)

    monkeypatch.setattr(workspace, "solve", spy)
    tracker.update(state, buffer, 0.01)
    np.testing.assert_allclose(guesses[0], np.r_[old[1:], old[-1]])
    assert tracker.workspaces[5] is workspace and workspace.calls == 2
    duplicate, b = setup(dynamic_vehicle)
    np.testing.assert_allclose(first, duplicate.update(state, b, 0)[0], atol=1e-12)


def test_qp_failure_replaces_only_lateral_and_keeps_longitudinal(dynamic_vehicle):
    tracker, buffer = setup(dynamic_vehicle)
    tracker.failure_times.add(0.0)
    state = np.array([2.1, 0, 0, 0, 0, 0.03])
    command, _ = tracker.update(state, buffer, 0)
    baseline = TrajectoryTracker(dynamic_vehicle, [-0.4, -3], [0.4, 2])
    expected = baseline.update(state, buffer, 0)[0]
    np.testing.assert_array_equal(command, expected)
    assert command[1] == pytest.approx(-0.1)
    assert tracker.records[-1]["local_fallback"]


def test_full_deadline_overrun_returns_tvlqr(dynamic_vehicle):
    tracker, buffer = setup(dynamic_vehicle)
    state = np.array([2.0, 0, 0, 0, 0, 0.01])
    command, diagnostics = tracker.update(state, buffer, 0)
    replacement = tracker.finalize_update(state, command, diagnostics, perf_counter() - 1)
    assert tracker.records[-1]["fallback_reason"] == "full_update_deadline_exceeded"
    assert replacement[0] == tracker.records[-1]["replacement_delta"]


def test_horizon_shortens_without_extrapolation_and_clone_owns_workspace(dynamic_vehicle):
    tracker, buffer = setup(dynamic_vehicle, n=15)
    clone = tracker.clone()
    clone.forecast_command([2.0, 0, 0, 0, 0.7, 0], buffer, 0.35)
    assert 5 in clone.workspaces and tracker.workspaces[15].calls == 0
    assert clone.workspaces[15] is not tracker.workspaces[15]
    assert tracker.solution is None and not tracker.records


def test_missing_future_packet_has_one_step_fallback(dynamic_vehicle):
    tracker, buffer = setup(dynamic_vehicle)
    command, _ = tracker.update([2.0, 0, 0, 0, 0.799, 0], buffer, 0.399)
    assert np.isfinite(command).all()
    assert tracker.records[-1]["fallback_reason"] == "insufficient_local_horizon"


def test_reject_bad_configuration():
    for config in [{"horizon": 0}, {"horizon": 20}, {"rate_weight": -1}, {"deadline": 0}]:
        with pytest.raises(ValueError):
            LocalMPCConfig(**config)


def test_invalid_packet_still_rejected(dynamic_vehicle):
    tracker, buffer = setup(dynamic_vehicle)
    with pytest.raises(ValueError):
        replace(packet(), states=np.full((5, 6), np.nan))
    with pytest.raises(ValueError):
        tracker.update([2, 0, 0, 0, 0, 0], buffer, 0.5)


@pytest.mark.parametrize("kind", ["status", "nonfinite", "residual", "nonfinite_residual"])
def test_reject_qp_output_and_use_valid_tvlqr(dynamic_vehicle, monkeypatch, kind):
    tracker, buffer = setup(dynamic_vehicle)

    def bad_solve(*_args):
        return np.full(5, np.nan) if kind == "nonfinite" else np.zeros(5), dict(
            success=kind != "status",
            status="injected",
            dual_residual=np.nan
            if kind == "nonfinite_residual"
            else (1 if kind == "residual" else 0),
        )

    monkeypatch.setattr(tracker.workspaces[5], "solve", bad_solve)
    command, _ = tracker.update([2.0, 0, 0, 0, 0, 0.01], buffer, 0)
    assert np.isfinite(command).all() and tracker.records[-1]["local_fallback"]
    assert command[0] == tracker.records[-1]["replacement_delta"]


@pytest.mark.parametrize("mode,delay,misses", [("zero", 0.0, 0), ("injected", 0.15, 1)])
def test_mpc_closed_loop_keeps_high_rate_during_planning(
    dynamic_vehicle, straight_geometry, mode, delay, misses
):
    from apex.control.mpc.controller import make_mpc
    from apex.control.mpc.problem import MPCConfig
    from apex.control.trajectory.planner import TrajectoryPlanner
    from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

    controller = make_mpc(
        dynamic_vehicle,
        straight_geometry,
        config=MPCConfig(horizon=4, dt=0.1, substeps=4, tire_physics=RACING_TIRE_PHYSICS),
    )
    tracker, _ = setup(dynamic_vehicle)
    runner = AsyncRunner(
        DynamicBicycle(dynamic_vehicle, straight_geometry, tire_physics=RACING_TIRE_PHYSICS),
        TrajectoryPlanner(controller, straight_geometry),
        tracker,
        straight_geometry,
        AsyncConfig(duration=0.4, latency_mode=mode, injected_delay=delay),
    )
    r = runner.run([2.0, 0, 0, 0, 1.0, 0])
    assert r["failure"] is None and not r["fallbacks"]
    if misses:
        assert len(r["misses"]) >= misses
    else:
        assert not r["misses"]
    assert len(r["controls"]) == 40
    assert r["states"][-1]["s_abs"] > 1.77


def test_replay_preserves_packet_values_and_availability(tmp_path, monkeypatch):
    import json
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    from codriver_study.replay import PacketReplay

    saved = packet()
    (tmp_path / "trajectory_packets.json").write_text(json.dumps([saved.as_dict()]))
    event = dict(plan_id=0, release_time=0.0, completion_time=0.0, planner_total_time=0.02)
    (tmp_path / "events.json").write_text(json.dumps({"plans": [event]}))
    replay = PacketReplay(tmp_path)
    a, metadata = replay.prepare(0, saved.states[0], 0, 0, None, None, startup=True)
    b, _ = replay.prepare(0, saved.states[0], 0, 0, None, None, startup=True)
    np.testing.assert_array_equal(a.states, saved.states)
    np.testing.assert_array_equal(a.controls, b.controls)
    np.testing.assert_array_equal(a.timestamps, b.timestamps)
    assert a.actual_completion_time == b.actual_completion_time == 0
    assert metadata["replay"] and metadata["planner_cpu_time"] == 0
    with pytest.raises(ValueError):
        replay.prepare(0, saved.states[0], 0.1, 0, None, None)
