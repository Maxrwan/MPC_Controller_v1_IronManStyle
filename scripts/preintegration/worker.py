"""One admitted genuine controller attempt. No automatic retry or fallback promotion."""

import argparse
import resource
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "src", ROOT / "scripts"):
    sys.path.insert(0, str(path))
from apex.preintegration.profile import bootstrap, compose, imported_identities  # noqa: E402
from preintegration.evidence import Journal, assess, write  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=("G0", "G1", "measured-smoke"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    complete, raw, adapters, plant = False, None, None, None
    try:
        admitted = bootstrap(
            ROOT, Path(sys.executable).parent.parent / "lib/python3.12/site-packages"
        )
        write(
            output / "worker-admission.json",
            {
                "source": admitted.source,
                "environment": admitted.environment,
                "native": admitted.native,
            },
        )
        import psutil
        from threadpoolctl import threadpool_info

        from apex.models.errors import ModelValidationError
        from apex.models.tire.config import RACING_TIRE_PHYSICS
        from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
        from apex.preintegration.local import LocalAdapters
        from apex.preintegration.session import ControlSession
        from apex.simulation.asynchronous import AsyncConfig, AsyncRunner

        journal = Journal(output / "events.jsonl")
        construction = time.perf_counter()
        session = ControlSession(lambda: compose(ROOT, admission=admitted), journal=journal)
        construction = time.perf_counter() - construction
        comp = session.components
        # Retain actual resolved configuration before any comparison/result frontier.
        write(output / "resolved.json", comp.snapshot)
        measured = args.case == "measured-smoke"
        sim = AsyncConfig(
            duration=2.0 if measured else 0.24,
            latency_mode="measured" if measured else ("zero" if args.case == "G0" else "injected"),
            injected_delay=0.06 if args.case == "G1" else 0,
            codriver_delay=None if measured else (0 if args.case == "G0" else 0.025),
        )
        write(output / "simulation.json", asdict(sim))
        initial = admitted.source["profile"]["evaluation_protocol"]["initial_state"]
        write(output / "imports-before-run.json", imported_identities(ROOT, admitted.environment))
        segments = []

        class ObservedPlant(DynamicBicycle):
            physical_time = 0.0

            def step(self, x, u, dt):
                if session.buffer.category(self.physical_time) == "exhausted":
                    raise ModelValidationError("NO_NOMINAL_AUTHORITY; fallback is not exported")
                end = super().step(x, u, dt)
                segments.append(
                    {
                        "start": self.physical_time,
                        "end": self.physical_time + dt,
                        "state_before": x,
                        "state_after": end,
                        "control": u,
                        "dt": dt,
                    }
                )
                self.physical_time += dt
                return end

        adapters = LocalAdapters(session, stop_on_preparation_failure=True)
        plant = ObservedPlant(comp.parameters, comp.track, tire_physics=RACING_TIRE_PHYSICS)
        releases = []
        runner = AsyncRunner(
            plant,
            adapters.planner,
            adapters.tracker,
            comp.track,
            sim,
            estimator=comp.estimator,
            release_observer=releases.append,
        )
        comp.urgent = runner.urgent
        wall, cpu = time.perf_counter(), time.process_time()
        raw = runner.run(initial)
        run_wall, run_cpu = time.perf_counter() - wall, time.process_time() - cpu
        # Save returned native observations before any outcome assertion/offline summary.
        write(output / "raw.json", raw)
        write(output / "segments.json", segments)
        write(output / "releases.json", releases)
        adapters.completion()
        write(output / "boundary-times.json", adapters.boundary_times)
        write(output / "feasibility.json", assess(raw, adapters.boundary_times))
        write(
            output / "resources.json",
            {
                "construction_wall_s": construction,
                "run_wall_s": run_wall,
                "run_cpu_s": run_cpu,
                "wall_per_simulated_second": run_wall / raw["end_time"]
                if raw.get("end_time")
                else None,
                "process_threads": psutil.Process().num_threads(),
                "threadpools": threadpool_info(),
                "imports_after_run": imported_identities(ROOT, admitted.environment),
            },
        )
        complete = (
            raw.get("failure") is None
            and raw.get("stop_reason") == "duration"
            and abs(raw.get("end_time", -1) - sim.duration) <= 1e-9
            and not raw.get("fallbacks")
            and session.evidence_valid
            and len(raw.get("controls", [])) > 0
            and all(
                p.get("success") is True
                and p.get("max_slack") is not None
                and p["max_slack"] <= 1e-6
                for p in raw.get("plans", [])
            )
        )
        if args.case == "G1":
            complete = complete and bool(raw.get("codriver_misses"))
    except Exception as error:
        write(
            output / "worker-failure.json",
            {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
        )
        if plant is not None:
            write(output / "partial-segments.json", segments)
        if adapters is not None:
            write(output / "partial-boundary-times.json", adapters.boundary_times)
    write(
        output / "worker-result.json",
        {
            "complete": complete,
            "case": args.case,
            "raw_returned": raw is not None,
            "physical_safety": "NOT_OBSERVED_NOT_VALIDATED",
            "application_check_enforcement": "NOT_OBSERVED_IN_LEGACY_RUNNER",
        },
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
