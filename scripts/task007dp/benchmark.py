"""Bounded warm-call measurements of both required candidate outputs."""

from time import perf_counter_ns, process_time_ns

import numpy as np
import psutil
from threadpoolctl import threadpool_info

from task007dp.candidates import Candidate


def select_contexts(cases):
    # All four regimes, both host histories, early transition and later/high-excursion data.
    return [
        (name, r)
        for name, case in cases.items()
        if name.startswith("D4-")
        for r in case["releases"]
        if r.plan_id in (1, 2, 10, 18)
    ]


def distribution(values):
    return dict(
        count=len(values),
        median=float(np.median(values)),
        p95=float(np.percentile(values, 95)),
        maximum=float(np.max(values)),
    )


def run(method, track, cases, native, repetitions=30):
    selected = select_contexts(cases)
    wall, cpu = perf_counter_ns(), process_time_ns()
    candidate = Candidate(method, selected[0][1].parameters, track)
    initialization = dict(
        wall_ms=(perf_counter_ns() - wall) / 1e6, cpu_ms=(process_time_ns() - cpu) / 1e6
    )
    wall, cpu = perf_counter_ns(), process_time_ns()
    candidate.precompute([r for _, r in selected])
    precomputation = dict(
        wall_ms=(perf_counter_ns() - wall) / 1e6,
        cpu_ms=(process_time_ns() - cpu) / 1e6,
        jacobian_durations=list(candidate.jacobians),
        context_matrices_cached=False,
    )
    for _ in range(3):
        for _, r in selected:
            candidate(r)
    process = psutil.Process()
    threads = [process.num_threads()]
    samples = []
    batch_wall, batch_cpu = perf_counter_ns(), process_time_ns()
    for repetition in range(repetitions):
        # Rotate the identical selection to reduce fixed first/last-position bias.
        shift = repetition % len(selected)
        for case, r in selected[shift:] + selected[:shift]:
            w, c = perf_counter_ns(), process_time_ns()
            state, control = candidate(r)
            cpu_ms, wall_ms = (process_time_ns() - c) / 1e6, (perf_counter_ns() - w) / 1e6
            samples.append(
                dict(
                    method=method,
                    case=case,
                    plan_id=r.plan_id,
                    repetition=repetition,
                    wall_ms=wall_ms,
                    cpu_ms=cpu_ms,
                    finite=bool(np.isfinite(state).all() and np.isfinite(control).all()),
                )
            )
        threads.append(process.num_threads())
    batch = dict(
        wall_ms=(perf_counter_ns() - batch_wall) / 1e6, cpu_ms=(process_time_ns() - batch_cpu) / 1e6
    )
    return dict(
        method=method,
        selected_contexts=[dict(case=n, plan_id=r.plan_id) for n, r in selected],
        repetitions=repetitions,
        warmup_sweeps=3,
        initialization=initialization,
        precomputation=precomputation,
        native=native,
        threadpools=threadpool_info(),
        observed_process_threads=sorted(set(threads)),
        batch=batch,
        samples=samples,
        wall_ms=distribution([r["wall_ms"] for r in samples]),
        cpu_ms=distribution([r["cpu_ms"] for r in samples]),
    )
