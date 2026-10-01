"""Paired fixed-input timing and independent nonlinear/local prediction checks."""

import json
from dataclasses import fields
from time import perf_counter, process_time

import numpy as np
import pandas as pd
import psutil
from async_study.analysis import read_csv
from run_lqr_baseline import make_track
from threading_study.config import ROOT
from threading_study.worker import stats

from apex.config import load_vehicle_parameters
from apex.control.local_mpc.model import LocalModel
from apex.control.local_mpc.tracker import LinearMPCTracker, LocalMPCConfig
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.control.trajectory.packet import TrajectoryBuffer, TrajectoryPacket
from apex.control.trajectory.tracker import LATERAL, TrajectoryTracker
from apex.models.tire.config import RACING_TIRE_PHYSICS
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.state import STATE_NAMES


def run(args, native):
    p = load_vehicle_parameters(ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    track = make_track("oval")
    model = LocalModel(SymbolicBicycle(p, RACING_TIRE_PHYSICS))
    plant = DynamicBicycle(p, track, tire_physics=RACING_TIRE_PHYSICS)
    folder = args.output / args.name
    if args.action == "parity":
        parity(folder, p, track, model, plant, args.horizon)
        return
    source = ROOT / "results/asynchronous_planner_tracker/async_measured"
    names = {f.name for f in fields(TrajectoryPacket)}
    packets = {
        v["plan_id"]: TrajectoryPacket(**{k: x for k, x in v.items() if k in names})
        for v in json.loads((source / "trajectory_packets.json").read_text())
    }
    commands = read_csv(source / "controls.csv").iloc[::4].head(800)
    states = read_csv(source / "states.csv")
    samples = []
    for row in commands.itertuples():
        state = np.array(
            [getattr(row, "reference_" + k) + getattr(row, "error_" + k) for k in STATE_NAMES]
        )
        previous = states.iloc[np.argmin(abs(states.time - row.time))][["delta", "a_cmd"]].to_numpy(
            float
        )
        samples.append((row.time, state, previous, packets[row.plan_id]))
    rows = []
    for repeat in range(3):
        order = ["tvlqr", "mpc_warm", "mpc_cold"]
        order = order[repeat:] + order[:repeat]
        for name in order:
            before = psutil.Process().memory_info().rss
            tracker = (
                TrajectoryTracker(p, [-0.4, -3], [0.4, 2])
                if name == "tvlqr"
                else LinearMPCTracker(
                    p,
                    [-0.4, -3],
                    [0.4, 2],
                    model,
                    LocalMPCConfig(
                        horizon=args.horizon,
                        rate_weight=args.weight,
                        varying=args.model == "ltv",
                        warm_start=name == "mpc_warm",
                    ),
                )
            )
            memory = psutil.Process().memory_info().rss - before
            buffer = TrajectoryBuffer()
            for time, state, previous, packet in samples:
                buffer.active = packet
                tracker.previous = previous.copy()
                start, cpu = perf_counter(), process_time()
                command, diagnostics = tracker.update(state, buffer, time)
                plant.diagnostics(state, command)
                if isinstance(tracker, LinearMPCTracker):
                    validated = tracker.finalize_update(state, command, diagnostics, start)
                    if not np.array_equal(validated, command):
                        plant.diagnostics(state, validated)
                wall, cpu_used = perf_counter() - start, process_time() - cpu
                record = tracker.records[-1] if isinstance(tracker, LinearMPCTracker) else {}
                rows.append(
                    dict(
                        controller=name,
                        replicate=repeat,
                        time=time,
                        total_time=wall,
                        cpu_time=cpu_used,
                        construction_rss_delta=memory,
                        **{
                            k: record.get(k, 0)
                            for k in [
                                "iterations",
                                "solver_time",
                                "update_time",
                                "solver_update_time",
                                "solve_wall_time",
                                "workspace_setup_time",
                                "model_assembly_time",
                                "local_fallback",
                            ]
                        },
                        deadline_exceeded=wall > 0.01,
                    )
                )
    frame = pd.DataFrame(rows)
    frame.to_csv(folder / "samples.csv", index=False)
    result = {}
    for name, group in frame.groupby("controller"):
        result[name] = {
            k: stats(group[k])
            for k in [
                "total_time",
                "cpu_time",
                "iterations",
                "solver_time",
                "update_time",
                "solver_update_time",
                "solve_wall_time",
                "workspace_setup_time",
                "model_assembly_time",
            ]
        }
        result[name].update(
            updates=len(group),
            deadline_exceedances=int(group.deadline_exceeded.sum()),
            local_fallbacks=int(group.local_fallback.sum()),
            core_demand_100hz=float(group.cpu_time.mean() * 100),
            mean_effective_cores=float(group.cpu_time.sum() / group.total_time.sum()),
            maximum_construction_rss_delta=int(group.construction_rss_delta.max()),
        )
    (folder / "timing.json").write_text(
        json.dumps(dict(native_control=native, results=result), indent=2) + "\n"
    )


def parity(folder, p, track, model, plant, n):
    rows = []
    for speed in [1.0, 2.0, 3.0]:
        for progress in [0.0, 4.0, 8.0, 12.0]:
            curvature = track.sample(progress).curvature
            for steering in [0.0, 0.15, 0.3]:
                initial = np.array([speed, 0.0, 0.0, 0.0, progress, 0.0])
                u = np.array([steering, 0.0])
                nominal = [initial]
                for _ in range(n):
                    nominal.append(plant.step(plant.step(nominal[-1], u, 0.005), u, 0.005))
                matrices = []
                for i in range(n):
                    k = track.sample(nominal[i][4] % track.length).curvature
                    matrices.append(model.matrices(nominal[i], u, k, nominal[i + 1]))
                for magnitude in [0.001, 0.01, 0.05]:
                    error = magnitude * np.array([1.0, 0.5, 0.2, 0.2])
                    actual = initial.copy()
                    actual[LATERAL] += error
                    predicted = error.copy()
                    for a, b, c in matrices:
                        predicted = a @ predicted + c
                        actual = plant.step(plant.step(actual, u, 0.005), u, 0.005)
                    difference = predicted - (actual - nominal[-1])[LATERAL]
                    rows.append(
                        dict(
                            speed=speed,
                            progress=progress,
                            curvature=curvature,
                            steering=steering,
                            error_scale=magnitude,
                            horizon=n,
                            **dict(
                                zip(
                                    ["error_ey", "error_epsi", "error_vy", "error_r"],
                                    map(float, difference),
                                )
                            ),
                        )
                    )
    pd.DataFrame(rows).to_csv(folder / "prediction_errors.csv", index=False)
    (folder / "parity.json").write_text(
        json.dumps(
            dict(
                cases=len(rows),
                horizon=n,
                dt=0.01,
                basis="Independent NumPy plant refreshes geometry every 5ms; "
                "local Jacobians use nominal stage curvature",
            ),
            indent=2,
        )
        + "\n"
    )
