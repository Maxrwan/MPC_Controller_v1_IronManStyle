"""Fresh frozen-source NMPC worker; composition/recording only, no dynamics or cost equations."""

import base64
import importlib.abc
import importlib.machinery
import importlib.metadata
import json
import os
import sys
import traceback
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter, process_time

WORKBENCH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKBENCH))
from tools.apex_workbench import nmpc_weight_lab as lab  # noqa: E402
from tools.apex_workbench import storage  # noqa: E402

PREFIXES = ("apex", "task007d", "task007dcx", "task007dvis", "threading_study")
DEPENDENCIES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "casadi": "casadi",
    "psutil": "psutil",
    "threadpoolctl": "threadpoolctl",
    "pandas": "pandas",
    "yaml": "PyYAML",
    "osqp": "osqp",
    "matplotlib": "matplotlib",
}


class FrozenImports(importlib.abc.MetaPathFinder):
    def __init__(self, runtime, expected):
        self.runtime, self.expected = runtime, expected
        self.prefixes = set(PREFIXES) | {
            Path(name.split("/", 2)[1]).stem
            for name in expected
            if name.startswith("scripts/") and len(name.split("/")) >= 2
        }
        self.dependency_files = {}
        for name in DEPENDENCIES.values():
            distribution = importlib.metadata.distribution(name)
            for entry in distribution.files or ():
                if entry.hash is not None and entry.hash.mode == "sha256":
                    self.dependency_files[str(Path(distribution.locate_file(entry)).resolve())] = (
                        entry.hash.value
                    )

    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root not in self.prefixes and root not in DEPENDENCIES:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None:
            raise ImportError("Ambiguous frozen module: " + fullname)
        if root in DEPENDENCIES:
            if not spec.origin:
                self.dependency_namespace(root, spec.submodule_search_locations)
            else:
                self.check_dependency(Path(spec.origin))
        elif spec.origin is None:
            self.namespace(spec.submodule_search_locations)
        else:
            self.check(Path(spec.origin))
        return spec

    def check_dependency(self, path):
        path = path.resolve()
        digest = base64.urlsafe_b64encode(bytes.fromhex(storage.sha256(path))).decode().rstrip("=")
        if self.dependency_files.get(str(path)) != digest:
            raise ImportError("Numerical dependency import path/hash mismatch: " + str(path))

    def dependency_namespace(self, root, locations):
        paths = [Path(p).resolve() for p in locations or ()]
        distribution = importlib.metadata.distribution(DEPENDENCIES[root])
        package_root = Path(distribution.locate_file(root)).resolve()
        if (
            len(paths) != 1
            or not paths[0].is_relative_to(package_root)
            or not any(p.startswith(str(paths[0]) + "/") for p in self.dependency_files)
        ):
            raise ImportError("Ambiguous/uninventoried dependency namespace")
        return [str(p) for p in paths]

    def namespace(self, locations):
        paths = [Path(p).resolve() for p in locations or ()]
        if len(paths) != 1 or not paths[0].is_relative_to(self.runtime):
            raise ImportError("Ambiguous/outside frozen namespace")
        prefix = str(paths[0].relative_to(self.runtime)) + "/"
        if not any(name.startswith(prefix) for name in self.expected):
            raise ImportError("Uninventoried frozen namespace")
        return [str(p) for p in paths]

    def check(self, path):
        path = path.resolve()
        if not path.is_relative_to(self.runtime):
            raise ImportError("Scientific import escaped frozen runtime: " + str(path))
        name = str(path.relative_to(self.runtime))
        if name not in self.expected or storage.sha256(path) != self.expected[name]:
            raise ImportError("Scientific import hash mismatch: " + name)

    def audit(self):
        result = {}
        for name, module in list(sys.modules.items()):
            root = name.split(".")[0]
            if root in self.prefixes or root in DEPENDENCIES:
                if getattr(module, "__file__", None) is None:
                    paths = (
                        self.dependency_namespace(root, module.__path__)
                        if root in DEPENDENCIES
                        else self.namespace(module.__path__)
                    )
                    result[name] = {"namespace_paths": paths}
                else:
                    path = Path(module.__file__).resolve()
                    self.check_dependency(path) if root in DEPENDENCIES else self.check(path)
                    result[name] = {"path": str(path), "sha256": storage.sha256(path)}
        return result


def bootstrap(runtime):
    runtime = Path(runtime).resolve()
    expected = lab.verify_runtime(runtime)
    script_roots = {Path(n.split("/", 2)[1]).stem for n in expected if n.startswith("scripts/")}
    if any(name.split(".")[0] in set(PREFIXES) | script_roots for name in sys.modules):
        raise ImportError("Scientific modules were imported before isolation")
    sys.dont_write_bytecode = True
    for key in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "BLIS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ.pop(key, None)
    # Keep the adapter namespace but remove every other source/script checkout search root.
    sys.path[:] = [p for p in sys.path if p and Path(p).name not in {"src", "scripts"}]
    sys.path[:0] = [str(runtime / "src"), str(runtime / "scripts")]
    guard = FrozenImports(runtime, expected)
    sys.meta_path.insert(0, guard)
    os.chdir(runtime)
    from threading_study.config import configure_accelerate

    native = configure_accelerate(1)
    if native.get("set_status") != 0 or native.get("mode_name") != "single":
        raise RuntimeError("Approved Accelerate SINGLE control unavailable")
    environment = lab.environment_identity()
    return guard, native, environment


def resolve(preset):
    from task007dcx.worker import frozen_config, geometry
    from task007dvis.protocol import Case, availability

    lab.validate({"preset": preset})
    track, reference, parameters = geometry()
    nominal = frozen_config()
    config = replace(nominal, costs=replace(nominal.costs, lateral=lab.PRESETS[preset]))
    sim, timing = availability(Case("weight_m0_" + preset, "A", "controlled", 2.0))
    ref = reference.sample(1.0)
    initial = [
        ref["v_ref_mps"],
        0.0,
        ref["v_ref_mps"] * ref["kappa_ref_1pm"],
        ref["e_psi_ref_rad"],
        1.0,
        ref["e_y_ref_m"],
    ]
    if reference.manifest["aggression_factor"] != 2.0 or nominal.costs.lateral != 2:
        raise ValueError("Frozen scenario/nominal contract differs")
    resolved = {
        "preset": preset,
        "configuration": asdict(config),
        "simulation": asdict(sim),
        "initial_state": initial,
        "vehicle": asdict(parameters),
        "timing": {
            "mode": timing.mode,
            "planner_pattern_s": list(timing.planner[:4]),
            "history_length": len(timing.planner),
            "codriver_delay_s": 0.005,
            "startup": "prelaunch; no imposed replay entry consumed",
        },
        "solver_options": {"ipopt.warm_start_init_point": "yes"},
        "warm_start": True,
        "architecture": "A/original predictor",
        "gamma": 2.0,
        "stage_coefficients": [4, 4, 1, 100 * config.costs.lateral, 100 * config.costs.lateral],
    }
    return track, reference, parameters, config, sim, timing, initial, resolved


def execution_configuration(preset, captured):
    """Real capture-to-worker boundary, shared by execution and the no-solve boundary probe."""
    parts = resolve(preset)
    resolved = lab.same_configuration(parts[-1], captured["resolved"])
    return (*parts[:-1], resolved)


def software_checks(parameters, config):
    """Cost/constraint algebra checks only. Never solve or run/step a plant/controller."""
    import casadi as ca
    import numpy as np

    from apex.control.mpc.cost import CostScales, stage_components, terminal_cost
    from apex.control.mpc.problem import MPCProblem

    nominal = replace(config, costs=replace(config.costs, lateral=2.0))
    treatment = replace(config, costs=replace(config.costs, lateral=1.0))
    a, b = MPCProblem(parameters, nominal), MPCProblem(parameters, treatment)
    for name in ("lbx", "ubx", "lbg", "ubg"):
        if not np.array_equal(getattr(a, name), getattr(b, name)):
            raise ValueError("Treatment altered constraint bounds")
    x, u, previous, preview = (
        ca.DM([1, 1, 1, 1, 0, 1]),
        ca.DM.zeros(2),
        ca.DM.zeros(2),
        ca.DM.zeros(11),
    )
    terms = [stage_components(x, u, previous, preview, CostScales(lateral=s)) for s in (2.0, 1.0)]
    if [float(t[0]) for t in terms] != [409.0, 209.0]:
        raise ValueError("Stage coefficients differ from accepted contract")
    # Same accepted expression and terminal matrix input, independent of lateral stage scale.
    terminal = float(terminal_cost(x, preview, ca.DM.eye(4)))
    if terminal != 8.0 or any(float(t[1]) != 0 or float(t[2]) != 0 for t in terms):
        raise ValueError("Unchanged component accounting check failed")
    return {
        "stage_unit_error_tracking": [409.0, 209.0],
        "terminal_same_input": terminal,
        "bounds_identical": True,
        "optimizer_solves": 0,
        "plant_steps": 0,
        "fixture": "algebraic unit-error cost test, not a physical trajectory",
    }


def append(path, value):
    with path.open("a") as stream:
        stream.write(json.dumps(value, allow_nan=False, default=lambda x: x.tolist()) + "\n")
        stream.flush()


def solution_observation(event, prediction):
    """Use exact successful native plan diagnostics; never carry a prior solver result forward."""
    if event.get("solver_attempted") is not True or event.get("success") is not True:
        return {
            "plan_id": event["plan_id"],
            "objective_components": None,
            "availability": "native successful solution accounting unavailable",
        }
    components = event.get("objective_components")
    if not isinstance(components, dict):
        return {
            "plan_id": event["plan_id"],
            "objective_components": None,
            "availability": "native event did not publish validated components",
        }
    return {
        "plan_id": event["plan_id"],
        "release_time": event["release_time"],
        "status": event["status"],
        "objective_components": components,
        "prediction": prediction,
        "accounting": (
            "native MPCController post-solve evaluate_components on validated optimum; "
            "not native IPOPT instrumentation"
        ),
        "authority": "not evidence of command/packet application",
    }


def request_observation(time, plan_id, proposed, diagnostics):
    return {
        "time": time,
        "plan_id": plan_id,
        "proposed": proposed,
        "diagnostics": diagnostics,
        "source": "native live TrajectoryTracker.update return",
        "availability": (
            "proposal before native runner validation/application-time rate clamp; "
            "not an applied command"
        ),
    }


def run(directory, captured):
    directory = Path(directory).resolve()
    output = directory / "experiment"
    output.mkdir(exist_ok=False)
    guard = None
    raw = None
    try:
        guard, native, environment = bootstrap(captured["runtime"])
        if (
            lab.adapter_hashes() != captured["adapter_sha256"]
            or environment != captured["environment"]
        ):
            raise ValueError("Execution adapter/environment changed after admission")
        track, reference, parameters, config, sim, timing, initial, resolved = (
            execution_configuration(
                storage.read_json(directory / "request.json")["effective"]["preset"], captured
            )
        )
        import psutil
        from task007dcx.worker import RecordedPlant
        from threadpoolctl import threadpool_info

        from apex.control.mpc.controller import make_mpc
        from apex.control.trajectory.planner import TrajectoryPlanner
        from apex.control.trajectory.tracker import TrajectoryTracker
        from apex.models.tire.config import RACING_TIRE_PHYSICS
        from apex.simulation.asynchronous import AsyncRunner

        controller = make_mpc(
            parameters,
            track,
            config=config,
            speed_reference=reference,
            racing_reference=reference,
            solver_options=resolved["solver_options"],
            warm_start=True,
        )
        samples = []

        class Planner(TrajectoryPlanner):
            def prepare(self, *args, **kwargs):
                samples.append(psutil.Process().num_threads())
                packet, event = super().prepare(*args, **kwargs)
                append(
                    output / "optimizations.jsonl",
                    solution_observation(event, controller.last_prediction),
                )
                append(output / "preparations.jsonl", event)
                samples.append(psutil.Process().num_threads())
                return packet, event

        class Plant(RecordedPlant):
            def step(self, *args, **kwargs):
                value = super().step(*args, **kwargs)
                append(output / "plant_segments.jsonl", self.segments[-1])
                return value

        class Tracker(TrajectoryTracker):
            def update(self, state, buffer, time):
                proposed, diagnostics = super().update(state, buffer, time)
                append(
                    output / "command_requests.jsonl",
                    request_observation(
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
                "source": lab.SOURCE,
                "module_sha256": guard.audit(),
                "environment": environment,
                "native_control": native,
                "resolved": resolved,
                "tracker": asdict(tracker.config),
                "threadpools": threadpool_info(),
                "classification": lab.BANNER,
            },
            exclusive=True,
        )
        lab.verify_runtime(captured["runtime"], captured["source_sha256"])
        wall, cpu = perf_counter(), process_time()
        raw = runner.run(initial)
        wall, cpu = perf_counter() - wall, process_time() - cpu
        storage.write_json(output / "raw.json", raw, exclusive=True)
        summary = {
            "failure": raw.get("failure"),
            "stop_reason": raw.get("stop_reason"),
            "end_time": raw.get("end_time"),
            "pending_at_end": raw.get("pending_at_end"),
            "host_wall_seconds": wall,
            "host_cpu_seconds": cpu,
            "cpu_wall_ratio": cpu / wall,
            "observed_process_thread_counts": sorted(set(samples)),
            "classification": lab.BANNER,
            "metrics": lab.descriptive_metrics(raw),
            "modeled_delays_are_not_host_timings": True,
            "coverage": lab.coverage(raw),
        }
        storage.write_json(output / "summary.json", summary, exclusive=True)
        if raw.get("failure"):
            raise RuntimeError("Native runner failure retained: " + str(raw["failure"]))
        if not summary["coverage"]["requested_duration_completed"]:
            raise RuntimeError("Native early termination retained: " + str(raw.get("stop_reason")))
        return summary
    except BaseException as error:
        lab.record_block(directory, error, captured)
        raise
    finally:
        post_environment = lab.environment_identity()
        storage.write_json(
            output / "post_execution_identity.json",
            {
                "module_sha256": guard.audit() if guard else {},
                "raw_result_available": raw is not None,
                "adapter_unchanged": lab.adapter_hashes() == captured["adapter_sha256"],
                "environment_unchanged": post_environment == captured["environment"],
                "partial_policy": (
                    "Retain native journals; absent raw result is unavailable, never reconstructed"
                ),
            },
            exclusive=True,
        )
        lab.verify_runtime(captured["runtime"], captured["source_sha256"])
        if lab.adapter_hashes() != captured["adapter_sha256"]:
            raise ValueError("Execution adapter changed during numerical execution")
        if post_environment != captured["environment"]:
            raise ValueError("Numerical dependencies changed during execution")


def main():
    mode, preset, runtime = sys.argv[1:]
    guard, native, environment = bootstrap(runtime)
    if mode == "--boundary":
        parts = execution_configuration(preset, json.load(sys.stdin))
    else:
        parts = resolve(preset)
    _, _, parameters, config, sim, _, _, resolved = parts
    result = {
        "resolved": lab.canonical_snapshot(resolved),
        "imports": guard.audit(),
        "native": native,
        "environment": environment,
    }
    if mode == "--check":
        result["software_checks"] = software_checks(parameters, config)
    elif mode == "--boundary":
        result["boundary"] = {
            "native_failed_plan_ids_is_tuple": type(sim.failed_plan_ids) is tuple,
            "optimizer_solves": 0,
            "plant_steps": 0,
        }
    elif mode != "--probe":
        raise ValueError("Unknown software preflight mode")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise SystemExit(2)
