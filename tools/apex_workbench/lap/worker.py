"""Long-run composition and compact observers; frozen scientific files are never edited."""

import json
import sys
from dataclasses import replace
from pathlib import Path
from time import perf_counter, process_time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.apex_workbench import nmpc_scratch_worker as short
from tools.apex_workbench import nmpc_weight_worker as native
from tools.apex_workbench import storage
from tools.apex_workbench.lap import config, evidence
from tools.apex_workbench.lap.analysis import laps


def resolve(value):
    value = config.validate(value)
    parts = list(short.resolve(value["scratch"]))
    parts[4] = replace(parts[4], duration=value["maximum_simulation_s"], laps=2)
    from dataclasses import asdict

    parts[-1] = config.v1.frozen.canonical_snapshot(
        {
            **parts[-1],
            "preset": "nmpc_lap_v2",
            "simulation": asdict(parts[4]),
            "effective": value,
            "track_length_m": parts[0].length,
            "sector_fractions": config.PROFILE["sectors_fraction"],
            "lap_rule": config.PROFILE["lap_rule"],
        }
    )
    return tuple(parts)


def probe(value):
    import subprocess

    # -I excludes cwd, so use the absolute bootstrap file, which adds only the adapter root.
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--probe"]
    completed = subprocess.run(
        command,
        input=config.canonical(value),
        capture_output=True,
        text=True,
        cwd=config.OUTPUT.parent.parent,
        timeout=60,
        env={
            **__import__("os").environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        },
    )
    if completed.returncode:
        raise RuntimeError(
            "V2 no-solve source/environment probe failed: " + completed.stderr[-3000:]
        )
    return json.loads(completed.stdout)


def run(directory, request):
    captured = request["capture"]
    start_wall, start_cpu = perf_counter(), process_time()
    guard, control, environment = native.bootstrap(captured["runtime"])
    parts = resolve(request["effective"])
    config.v1.frozen.same_configuration(parts[-1], captured["resolved"])
    if environment != captured["environment"] or config.producers() != captured["producer_sha256"]:
        raise ValueError("V2 source/environment changed after admission")
    from apex.control.trajectory.planner import TrajectoryPlanner
    from apex.control.trajectory.tracker import TrajectoryTracker
    from apex.models.tire.config import RACING_TIRE_PHYSICS
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.simulation.asynchronous import AsyncRunner

    track, reference, parameters, mpc, sim, timing, initial, resolved = parts
    controller = short.construct_controller(parts)
    journal = evidence.Chunks(directory / "journal")

    class Planner(TrajectoryPlanner):
        def prepare(self, *args, **kwargs):
            packet, event = super().prepare(*args, **kwargs)
            packet_data = packet.as_dict() if packet else None
            if packet_data:
                packet_data = {
                    k: v
                    for k, v in packet_data.items()
                    if k not in {"gain_times", "gains", "curvatures"}
                }
            journal.append(
                "preparations",
                {
                    "phase": "prepare_return_before_scheduler_completion_stamp",
                    "event": event,
                    "packet": packet_data,
                },
            )
            return packet, event

    class Plant(DynamicBicycle):
        physical_time = 0.0

        def step(self, state, command, dt):
            result = super().step(state, command, dt)
            journal.append(
                "segments",
                {
                    "start": self.physical_time,
                    "end": self.physical_time + dt,
                    "state_before": state,
                    "state_after": result,
                    "control": command,
                },
            )
            self.physical_time += dt
            return result

    class Tracker(TrajectoryTracker):
        def update(self, state, buffer, time):
            command, diagnostics = super().update(state, buffer, time)
            journal.append(
                "requests",
                native.request_observation(
                    time, buffer.active_plan_id, command.tolist(), diagnostics
                ),
            )
            return command, diagnostics

    planner = Planner(controller, track)
    problem = controller.problem
    tracker = Tracker(
        parameters,
        problem.lbx[problem.nx : problem.nx + 2],
        problem.ubx[problem.nx : problem.nx + 2],
    )
    plant = Plant(parameters, track, tire_physics=RACING_TIRE_PHYSICS)
    storage.write_json(
        directory / "pre_identity.json",
        {
            "resolved": resolved,
            "environment": environment,
            "native_control": control,
            "imports": guard.audit(),
        },
        exclusive=True,
    )
    raw = None
    try:
        raw = AsyncRunner(plant, planner, tracker, track, sim, timing=timing).run(initial)
        journal.close()
        evidence.store_raw(directory, raw)
        display = short.presentation(track, reference, raw, parameters, mpc, sim)
        chunks = evidence.Chunks(directory / "derived")
        try:
            for row, state in zip(display.pop("states"), raw["states"], strict=True):
                vector = [state[k] for k in ("vx", "vy", "r", "e_psi", "s_abs", "e_y")]
                derivative = plant.derivative(vector, [state["delta"], state["a_cmd"]])
                chunks.append(
                    "states",
                    {
                        **row,
                        "dvx_dt_mps2": float(derivative[0]),
                        "dvy_dt_mps2": float(derivative[1]),
                        "body_ax_mps2": float(derivative[0] - state["r"] * state["vy"]),
                        "body_ay_mps2": float(derivative[1] + state["r"] * state["vx"]),
                    },
                )
            for packet in raw["packets"]:
                chunks.append("prediction_xy", short.xy(track, packet["states"]))
        finally:
            chunks.close()
        display["state_rows"] = len(raw["states"])
        display["acceleration_source"] = (
            "Canonical DynamicBicycle.derivative at retained state/held command; "
            "body accelerations remove/add rotating-frame r*vy/r*vx terms. "
            "SI m/s²; synthetic derived, not measurements."
        )
        storage.write_json(directory / "presentation.json", display, exclusive=True)
        lap = laps(raw, track.length, initial[4])
        completed = not raw.get("failure") and (
            lap["completed_laps"] >= 1
            if request["effective"]["mode"] == "full_lap"
            else raw.get("stop_reason") == "duration"
        )
        summary = {
            "coverage_completed": completed,
            "lap": lap,
            "failure": raw.get("failure"),
            "stop_reason": raw.get("stop_reason"),
            "native_end_time_s": raw.get("end_time"),
            "worker_wall_s": perf_counter() - start_wall,
            "worker_cpu_s": process_time() - start_cpu,
            "retained_native_bytes": sum(
                p.stat().st_size for p in (directory / "native").iterdir()
            ),
            "total_recorded_bytes": sum(
                p.stat().st_size for p in directory.rglob("*") if p.is_file()
            ),
            "classification": config.PROFILE["classification"],
        }
        storage.write_json(directory / "summary.json", summary, exclusive=True)
        return summary
    finally:
        journal.close()
        end_environment = config.v1.frozen.environment_identity()
        config.v1.frozen.verify_runtime(captured["runtime"], captured["source_sha256"])
        post = {
            "raw_available": raw is not None,
            "source_unchanged": config.producers() == captured["producer_sha256"],
            "environment_unchanged": environment == end_environment,
            "imports": guard.audit(),
        }
        storage.write_json(directory / "post_identity.json", post, exclusive=True)
        if not post["source_unchanged"] or not post["environment_unchanged"]:
            raise ValueError("V2 source/environment changed during execution")


def main():
    value = config.validate(json.loads(sys.stdin.read()))
    guard, control, environment = native.bootstrap(config.v1.RUNTIME)
    print(
        json.dumps(
            {
                "resolved": resolve(value)[-1],
                "environment": environment,
                "native_control": control,
                "imports": guard.audit(),
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
