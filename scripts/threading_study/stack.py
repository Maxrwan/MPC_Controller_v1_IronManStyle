"""Inspect installed binaries and calibrate the native BLAS mechanism separately."""

import contextlib
import ctypes
import io
import json
import os
import platform
import resource
import subprocess
from pathlib import Path
from time import perf_counter, process_time

from threading_study.config import OUT, configure_accelerate


def command(args):
    result = subprocess.run(args, capture_output=True, text=True)
    return {
        "command": args,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def loaded_libraries():
    dyld = ctypes.CDLL(None)
    dyld._dyld_image_count.restype = ctypes.c_uint32
    dyld._dyld_get_image_name.argtypes = [ctypes.c_uint32]
    dyld._dyld_get_image_name.restype = ctypes.c_char_p
    return [dyld._dyld_get_image_name(i).decode() for i in range(dyld._dyld_image_count())]


def inspect_stack():
    import casadi as ca
    import numpy as np
    import scipy
    from threadpoolctl import threadpool_info

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        np.show_config()
        scipy.show_config()
    path = Path(ca.__file__).parent
    probe_code = (
        "import casadi as c;x=c.SX.sym('x');"
        "s=c.nlpsol('p','ipopt',{'x':x,'f':x*x},{'ipopt.print_level':5});s(x0=1)"
    )
    import sys

    probe = command([sys.executable, "-c", probe_code])
    (OUT / "ipopt_banner.log").write_text(probe["stdout"] + probe["stderr"])
    # Load the installed plugin in this process before inspecting dyld/runtime pools.
    ca.load_nlpsol("ipopt")
    report = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "logical_cores": os.cpu_count(),
        "topology": command(
            [
                "sysctl",
                "machdep.cpu.brand_string",
                "hw.physicalcpu",
                "hw.logicalcpu",
                "hw.perflevel0.physicalcpu",
                "hw.perflevel1.physicalcpu",
            ]
        ),
        "power": command(["pmset", "-g", "batt"]),
        "power_configuration": command(["pmset", "-g", "custom"]),
        "thermal": command(["pmset", "-g", "therm"]),
        "load": list(os.getloadavg()),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "casadi": ca.__version__,
        "casadi_plugins": ca.CasadiMeta.plugins(),
        "numpy_scipy_configuration": output.getvalue(),
        "threadpoolctl": threadpool_info(),
        "loaded_libraries": loaded_libraries(),
        "ipopt_dependencies": command(["otool", "-L", str(path / "libipopt.3.dylib")]),
        "mumps_dependencies": command(["otool", "-L", str(path / "libcoinmumps.3.dylib")]),
        "mumps_thread_symbols": command(["nm", "-u", str(path / "libcoinmumps.3.dylib")]),
        "affinity": "Not controlled; no P-core-only/E-core-only measurements",
        "threadpoolctl_limitation": (
            "Empty listing is not proof of no Accelerate threads; "
            "use native API, process CPU time and sampled thread counts"
        ),
    }
    (OUT / "stack.json").write_text(json.dumps(report, indent=2) + "\n")
    print(output.getvalue())
    print("Wrote stack.json and ipopt_banner.log")


def probe(threads, folder):
    native = configure_accelerate(threads)
    import numpy as np
    import psutil
    from threading_study.worker import stats
    from threadpoolctl import threadpool_info

    folder = Path(folder)
    rng = np.random.default_rng(622)
    a = rng.standard_normal((2048, 2048))
    b = rng.standard_normal((2048, 2048))
    result = np.empty_like(a)
    for _ in range(3):
        np.matmul(a, b, out=result)
    rows = []
    start = perf_counter()
    for _ in range(12):
        wall, cpu = perf_counter(), process_time()
        np.matmul(a, b, out=result)
        rows.append({"cpu": process_time() - cpu, "wall": perf_counter() - wall})
    end = perf_counter()
    report = {
        "native_control": native,
        "workload": "Separate dense BLAS calibration, NOT NMPC",
        "measurement_start": start,
        "measurement_end": end,
        "wall": stats([r["wall"] for r in rows]),
        "cpu": stats([r["cpu"] for r in rows]),
        "effective_cores": sum(r["cpu"] for r in rows) / sum(r["wall"] for r in rows),
        "threads_after": psutil.Process().num_threads(),
        "threadpoolctl": threadpool_info(),
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "checksum": float(result.sum()),
        "observations": rows,
    }
    (folder / "summary.json").write_text(json.dumps(report, indent=2) + "\n")


def component_probe(workload, threads, folder):
    """Supplementary print profiling, separate from the timed primary experiment."""
    native = configure_accelerate(threads)
    import numpy as np
    import pandas as pd
    from threading_study.config import ROOT
    from threading_study.worker import frozen, make_controller

    from apex.state import STATE_NAMES

    folder = Path(folder)
    record = frozen(workload)
    source = (
        ROOT / "results/mpc_parameter_study/runs" / record["experiment_id"] / "solver_events.csv"
    )
    frame = pd.read_csv(source)
    c = make_controller(workload, {"ipopt.print_level": 5, "ipopt.print_timing_statistics": "yes"})
    outputs = []
    for i in range(2):
        row = frame.iloc[i]
        state = np.array([row[f"x_sample_{k}"] for k in STATE_NAMES])
        c.compute_control(
            state, {"dt": c.config.dt, "previous_control": [row.previous_delta, row.previous_a_cmd]}
        )
        outputs.append(c.diagnostics())
    (folder / "summary.json").write_text(
        json.dumps(
            {
                "native_control": native,
                "workload": workload,
                "note": (
                    "Two supplementary calls with timing-print diagnostics; "
                    "not pooled benchmark data"
                ),
                "outputs": outputs,
            },
            indent=2,
        )
        + "\n"
    )
