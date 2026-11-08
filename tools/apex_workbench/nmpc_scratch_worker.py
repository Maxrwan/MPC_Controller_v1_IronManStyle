"""Source-isolated composition and read-only observers over frozen NMPC/TVLQR/AsyncRunner."""

import json
import sys
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter, process_time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.apex_workbench import nmpc_scratch as scratch  # noqa: E402
from tools.apex_workbench import nmpc_weight_lab as frozen  # noqa: E402
from tools.apex_workbench import nmpc_weight_worker as native  # noqa: E402
from tools.apex_workbench import storage  # noqa: E402


def resolve(value):
    from apex.control.mpc.cost import CostScales

    value = scratch.validate(value)
    track, reference, parameters, baseline, sim, timing, initial, resolved = native.resolve(
        "nominal"
    )
    if asdict(baseline.costs) != scratch.PROFILE["baseline_costs"]:
        raise ValueError("Profile no longer matches native accepted cost defaults")
    config = replace(baseline, costs=CostScales(**value["costs"]))
    if value["disturbance"] != "none":
        disturbance = scratch.PROFILE["disturbance"]
        sim = replace(
            sim,
            disturbance_time=disturbance["time_s"],
            disturbance_ey=disturbance["e_y_increment_m"],
            disturbance_heading=disturbance["heading_increment_rad"],
        )
        geometry = track.sample(initial[4])
        if (
            not 0 < sim.disturbance_time < sim.duration
            or not -geometry.right_width < initial[5] + sim.disturbance_ey < geometry.left_width
            or 1 - geometry.curvature * (initial[5] + sim.disturbance_ey)
            <= config.denominator_margin
        ):
            raise ValueError("Declared disturbance fails the initial geometry/domain precheck")
    resolved = {
        **resolved,
        "preset": "nmpc_scratch",
        "effective": value,
        "configuration": asdict(config),
        "simulation": asdict(sim),
    }
    resolved.pop("stage_coefficients")
    return (
        track,
        reference,
        parameters,
        config,
        sim,
        timing,
        initial,
        frozen.canonical_snapshot(resolved),
    )


def construct_controller(parts):
    from apex.control.mpc.controller import make_mpc

    track, reference, parameters, config, *_, resolved = parts
    return make_mpc(
        parameters,
        track,
        config=config,
        speed_reference=reference,
        racing_reference=reference,
        solver_options=resolved["solver_options"],
        warm_start=True,
    )


def xy(track, states):
    from apex.coordinates.frenet import frenet_to_global

    return [
        [pose.x, pose.y]
        for row in states
        for pose in [frenet_to_global(track, float(row[4]), float(row[5]), float(row[3]))]
    ]


def packet_observation(packet, event, controller, planner, track):
    """Read actual packet/gain/Jacobian outputs; never recompute a gain or alter the packet."""
    if packet is None or event.get("success") is not True:
        return {
            "plan_id": event["plan_id"],
            "packet": None,
            "availability": "No validated native packet for this preparation",
        }
    import numpy as np

    from apex.control.trajectory.tracker import LATERAL

    if packet.plan_id != event["plan_id"]:
        raise ValueError("Native packet/preparation association differs")
    linear = []
    for time, gain in zip(packet.gain_times, packet.gains):
        state, command, _ = packet.sample(float(time))
        curvature = (
            packet.curvature(float(time))
            if len(packet.curvatures)
            else track.sample(state[4] % track.length).curvature
        )
        a, b = planner.gain_builder.jacobian(state, command, curvature)
        linear.append(
            {
                "time": float(time),
                "A": np.asarray(a)[np.ix_(LATERAL, LATERAL)].tolist(),
                "B": np.asarray(b)[LATERAL, :1].tolist(),
                "K": gain.reshape(1, 4).tolist(),
            }
        )
    prediction = controller.last_prediction
    reference_xy = None
    if prediction and len(prediction.get("preview_progress", [])) == len(packet.timestamps):
        preview = np.asarray(prediction["preview"])
        states = np.zeros((len(packet.timestamps), 6))
        states[:, 4], states[:, 5], states[:, 3] = (
            prediction["preview_progress"],
            preview[7],
            preview[8],
        )
        reference_xy = xy(track, states)
    return {
        "plan_id": packet.plan_id,
        "release_time": event["release_time"],
        "capture_phase": (
            "prepare return before scheduler stamps simulated completion; use "
            "raw plan/packet/handoff records for actual scheduling"
        ),
        "packet": asdict(packet),
        "prediction_xy": xy(track, packet.states),
        "reference_xy": reference_xy,
        "linearization": {
            "state_order": ["e_y", "e_psi", "vy", "r"],
            "dt_s": planner.gain_builder.dt,
            "feedback": "u = nominal - K @ error",
            "scope": (
                "One nominal packet's lateral subsystem; excludes clamps, "
                "handoffs, longitudinal coupling"
            ),
            "rows": linear,
        },
    }


def presentation(track, reference, raw, parameters, config, sim):
    import numpy as np

    from apex.coordinates.angles import wrap_angle
    from apex.coordinates.frenet import frenet_to_global

    geometry = []
    for progress in np.linspace(0, track.length, 401):
        g = track.sample(float(progress % track.length))
        left = frenet_to_global(track, progress, g.left_width, 0)
        right = frenet_to_global(track, progress, -g.right_width, 0)
        geometry.append(
            {
                "s": float(progress),
                "x": g.x,
                "y": g.y,
                "left_x": left.x,
                "left_y": left.y,
                "right_x": right.x,
                "right_y": right.y,
            }
        )
    states = []
    for row in raw["states"]:
        ref = reference.sample(row["s_abs"])
        pose = frenet_to_global(track, row["s_abs"], row["e_y"], row["e_psi"])
        states.append(
            {
                "time": row["time"],
                "x": pose.x,
                "y": pose.y,
                "reference_e_y_m": ref["e_y_ref_m"],
                "reference_heading_rad": ref["e_psi_ref_rad"],
                "racing_error_y_m": row["e_y"] - ref["e_y_ref_m"],
                "racing_error_heading_rad": wrap_angle(row["e_psi"] - ref["e_psi_ref_rad"]),
            }
        )
    applied = [
        {
            "native_trigger": t,
            "application_time_s": t["time"],
            "e_y_increment_m": sim.disturbance_ey,
            "heading_increment_rad": sim.disturbance_heading,
        }
        for t in raw["triggers"]
        if t.get("kind") == "approved_state_perturbation"
    ]
    return {
        "geometry": geometry,
        "states": states,
        "applied_disturbances": applied,
        "derivation": (
            "Canonical frenet_to_global and original PlanningReference.sample "
            "at native s_abs; no resampled plant states"
        ),
        "limits": {
            "delta_rad": parameters.maximum_steering_angle,
            "a_cmd_upper_mps2": parameters.maximum_acceleration,
            "a_cmd_lower_mps2": -parameters.maximum_braking_deceleration,
            "steering_rate_radps": config.steering_rate,
        },
    }


def run(directory, captured):
    directory = Path(directory)
    request = storage.read_json(directory / "request.json")
    if request["run_id"] != directory.name or request["adapter"] != scratch.ADAPTER:
        raise ValueError("Scratch worker request identity differs")
    scratch.access(request["effective"], run_id=directory.name)
    output = directory / "experiment"
    output.mkdir(exist_ok=False)
    guard, raw = None, None
    try:
        guard, native_control, environment = native.bootstrap(captured["runtime"])
        if (
            captured["producer_sha256"] != scratch.producer_hashes()
            or environment != captured["environment"]
        ):
            raise ValueError("Scratch source/environment changed after admission")
        parts = resolve(request["effective"])
        frozen.same_configuration(parts[-1], captured["resolved"])
        track, reference, parameters, config, sim, timing, initial, resolved = parts
        import psutil
        from task007dcx.worker import RecordedPlant
        from threadpoolctl import threadpool_info

        from apex.control.trajectory.planner import TrajectoryPlanner
        from apex.control.trajectory.tracker import TrajectoryTracker
        from apex.models.tire.config import RACING_TIRE_PHYSICS
        from apex.simulation.asynchronous import AsyncRunner

        controller = construct_controller(parts)
        sampled_threads, observer_seconds = [], []

        class Planner(TrajectoryPlanner):
            def prepare(self, *args, **kwargs):
                sampled_threads.append(psutil.Process().num_threads())
                packet, event = super().prepare(*args, **kwargs)
                start = perf_counter()
                native.append(
                    output / "optimizations.jsonl",
                    native.solution_observation(event, controller.last_prediction),
                )
                native.append(output / "preparations.jsonl", event)
                native.append(
                    output / "packets.jsonl",
                    packet_observation(packet, event, controller, self, track),
                )
                observer_seconds.append(perf_counter() - start)
                return packet, event

        class Plant(RecordedPlant):
            def step(self, *args, **kwargs):
                result = super().step(*args, **kwargs)
                native.append(output / "plant_segments.jsonl", self.segments[-1])
                return result

        class Tracker(TrajectoryTracker):
            def update(self, state, buffer, time):
                proposed, diagnostics = super().update(state, buffer, time)
                native.append(
                    output / "command_requests.jsonl",
                    native.request_observation(
                        time, buffer.active_plan_id, proposed.tolist(), diagnostics
                    ),
                )
                return proposed, diagnostics

        planner = Planner(controller, track)
        problem = controller.problem
        tracker = Tracker(
            parameters,
            problem.lbx[problem.nx : problem.nx + 2],
            problem.ubx[problem.nx : problem.nx + 2],
        )
        plant = Plant(parameters, track, tire_physics=RACING_TIRE_PHYSICS)
        runner = AsyncRunner(plant, planner, tracker, track, sim, timing=timing)
        storage.write_json(
            output / "pre_execution_identity.json",
            {
                "source": frozen.SOURCE,
                "module_sha256": guard.audit(),
                "environment": environment,
                "resolved": resolved,
                "native_control": native_control,
                "threadpools": threadpool_info(),
                "classification": scratch.BANNER,
            },
            exclusive=True,
        )
        wall, cpu = perf_counter(), process_time()
        raw = runner.run(initial)
        wall, cpu = perf_counter() - wall, process_time() - cpu
        storage.write_json(output / "raw.json", raw, exclusive=True)
        storage.write_json(
            output / "presentation.json",
            presentation(track, reference, raw, parameters, config, sim),
            exclusive=True,
        )
        summary = {
            "failure": raw.get("failure"),
            "stop_reason": raw.get("stop_reason"),
            "coverage": frozen.coverage(raw),
            "host_wall_s": wall,
            "host_cpu_s": cpu,
            "sampled_thread_counts": sorted(set(sampled_threads)),
            "observer_host_seconds": sum(observer_seconds),
            "clock_note": (
                "Native simulated availability is controlled; host observer "
                "overhead is separate from native recorded preparation duration"
            ),
            "classification": scratch.BANNER,
        }
        storage.write_json(output / "summary.json", summary, exclusive=True)
        if raw.get("failure") or not summary["coverage"]["requested_duration_completed"]:
            raise RuntimeError(
                "Native Scratch failure/early stop retained: "
                + str(raw.get("failure") or raw.get("stop_reason"))
            )
        return summary
    finally:
        environment = frozen.environment_identity()
        storage.write_json(
            output / "post_execution_identity.json",
            {
                "raw_result_available": raw is not None,
                "module_sha256": guard.audit() if guard else {},
                "adapter_unchanged": scratch.producer_hashes() == captured["producer_sha256"],
                "environment_unchanged": environment == captured["environment"],
            },
            exclusive=True,
        )
        frozen.verify_runtime(captured["runtime"], captured["source_sha256"])
        if (
            scratch.producer_hashes() != captured["producer_sha256"]
            or environment != captured["environment"]
        ):
            raise ValueError("Scratch source/dependencies changed during execution")


def main():
    mode, runtime = sys.argv[1:]
    guard, native_control, environment = native.bootstrap(runtime)
    parts = resolve(scratch.loads(sys.stdin.read()))
    result = {
        "resolved": parts[-1],
        "environment": environment,
        "native": native_control,
        "imports": guard.audit(),
    }
    if mode == "--check":
        import casadi as ca

        from apex.control.mpc import controller as controller_module
        from apex.control.mpc.cost import stage_components
        from apex.control.mpc.problem import MPCProblem

        problem = MPCProblem(parts[2], parts[3])
        result["software_checks"] = {
            "constructed_costs": asdict(problem.config.costs),
            "stage_components_unit_fixture": [
                float(v)
                for v in stage_components(
                    ca.DM([1, 1, 1, 1, 0, 1]),
                    ca.DM([1, 1]),
                    ca.DM.zeros(2),
                    ca.DM.zeros(11),
                    parts[3].costs,
                )
            ],
            "optimizer_solves": 0,
            "plant_steps": 0,
        }
        original = controller_module.make_mpc

        def observe(*args, **kwargs):
            result["software_checks"]["constructor_costs"] = asdict(kwargs["config"].costs)

        try:
            controller_module.make_mpc = observe
            construct_controller(parts)
        finally:
            controller_module.make_mpc = original
        result["software_checks"]["constructor_observer"] = (
            "software-only substituted make_mpc; no optimizer instantiated"
        )
    elif mode != "--probe":
        raise ValueError("Only no-solve Scratch preflight modes are available on this CLI")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
