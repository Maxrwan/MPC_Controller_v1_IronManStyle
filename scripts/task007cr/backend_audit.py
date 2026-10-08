"""Separate exact-NLP CPU/thread observation, never concurrent with measured campaigns."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from threading_study.config import configure_accelerate, environment

OUT = Path("results/task007cr")


def worker():
    native = configure_accelerate(1)
    import platform
    import re

    import casadi as ca
    import numpy as np
    import scipy
    from task007cr.snapshot import reconstruct
    from threading_study.stack import loaded_libraries
    from threadpoolctl import threadpool_info

    folder = OUT / "smoke_fixed"
    m = json.loads((folder / "nlp_model.json").read_text())
    r = json.loads((folder / "nlp_snapshots.json").read_text())[1]
    solver, _ = reconstruct(m)
    wall = time.perf_counter()
    cpu = time.process_time()
    for _ in range(100):
        solver(
            x0=r["initial"], p=r["parameters"], **{k: m[k] for k in ["lbx", "ubx", "lbg", "ubg"]}
        )
    elapsed = time.perf_counter() - wall
    used = time.process_time() - cpu
    header = (Path(ca.__file__).parent / "include/coin-or/IpoptConfig.h").read_text()
    report = dict(
        python=sys.version,
        os=platform.platform(),
        hardware=platform.machine(),
        cpu_brand=subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True
        ).stdout.strip(),
        casadi=ca.__version__,
        numpy=np.__version__,
        scipy=scipy.__version__,
        ipopt=re.search(r'#define IPOPT_VERSION "([^"]+)"', header).group(1),
        solver_options=m["solver_options"],
        linear_solver=m["solver_options"].get(
            "ipopt.linear_solver", "IPOPT installed default; inspect linked MUMPS below"
        ),
        libraries=loaded_libraries(),
        threadpoolctl=threadpool_info(),
        native_control=native,
        environment={
            k: os.environ.get(k)
            for k in [
                "VECLIB_MAXIMUM_THREADS",
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "PYTHONHASHSEED",
            ]
        },
        solve_batch_wall_seconds=elapsed,
        solve_batch_cpu_seconds=used,
        cpu_core_seconds_per_second=used / elapsed,
    )
    (OUT / "backend_audit.json").write_text(json.dumps(report, indent=2) + "\n")


def main():
    if "--worker" in sys.argv:
        worker()
        return
    import psutil

    with (OUT / "backend_audit.log").open("w") as log:
        process = subprocess.Popen(
            [sys.executable, __file__, "--worker"], env=environment(1), stdout=log, stderr=log
        )
        samples = []
        while process.poll() is None:
            try:
                p = psutil.Process(process.pid)
                samples.append(
                    dict(
                        time=time.monotonic(),
                        threads=p.num_threads(),
                        cpu=p.cpu_times().user + p.cpu_times().system,
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            time.sleep(0.02)
        if process.returncode:
            raise RuntimeError("See backend_audit.log")
    report = json.loads((OUT / "backend_audit.json").read_text())
    report["sampled_max_process_threads"] = max(s["threads"] for s in samples)
    report["thread_sample_period_s"] = 0.02
    report["samples"] = samples
    report["thread_audit_limit"] = (
        "Polling can miss shorter transients; native SINGLE API and solve CPU/wall ratio "
        "provide additional evidence."
    )
    (OUT / "backend_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Observed max threads", report["sampled_max_process_threads"])


if __name__ == "__main__":
    main()
