"""Read-only derived horizon geometry using the pinned canonical Planning implementation.

Fresh isolated process; no controller, plant, optimizer, state propagation or recorded preview
reconstruction. Results are presentation derivatives, not new scientific observations.
"""

import hashlib
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from time import perf_counter

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.apex_workbench import nmpc_weight_lab as frozen

MAX_PACKETS = 512


@lru_cache(maxsize=1)
def geometry():
    from tools.apex_workbench import nmpc_weight_worker as native

    started = perf_counter()
    guard, control, environment = native.bootstrap(frozen.RUNTIME)
    bootstrap_s = perf_counter() - started
    from apex.planning_reference.reference import PlanningReference
    from apex.planning_reference.track import load_track

    folder = frozen.RUNTIME / "configs/planning/task007b/gamma_2p000"
    track, _, identity = load_track(folder / "track_source.json")
    reference = PlanningReference(folder, track, identity, feasibility_policy="advisory")
    return (
        guard,
        control,
        environment,
        track,
        reference,
        bootstrap_s,
        perf_counter() - started - bootstrap_s,
    )


def derive(request):
    warm = geometry.cache_info().currsize > 0
    guard, control, environment, track, reference, bootstrap_s, geometry_s = geometry()
    # Retain the complete approved dependency check on every new projection, including warm ones.
    current_environment = frozen.environment_identity() if warm else environment
    if (
        request["source_sha256"] != frozen.source_hashes()
        or request["environment"] != current_environment
    ):
        raise ValueError("Derived reference source/environment differs from the retained capture")
    packets = request["packets"]
    if len(packets) > MAX_PACKETS or any(len(p["states"]) != 9 for p in packets):
        raise ValueError("Derived reference requires bounded genuine N8 horizons")
    from apex.coordinates.angles import wrap_angle
    from apex.coordinates.frenet import frenet_to_global

    projection_start = perf_counter()
    result = []
    for packet in packets:
        nodes = []
        for state in packet["states"]:
            if len(state) != 6:
                raise ValueError("Canonical predicted state ordering differs")
            ref = reference.sample(state[4])
            actual = frenet_to_global(track, state[4], state[5], state[3])
            target = frenet_to_global(track, state[4], ref["e_y_ref_m"], ref["e_psi_ref_rad"])
            nodes.append(
                {
                    "s_abs_m": state[4],
                    "reference_e_y_m": ref["e_y_ref_m"],
                    "reference_e_psi_rad": ref["e_psi_ref_rad"],
                    "lateral_error_m": state[5] - ref["e_y_ref_m"],
                    "heading_error_rad": wrap_angle(state[3] - ref["e_psi_ref_rad"]),
                    "reference_xy": [target.x, target.y],
                    "predicted_xy": [actual.x, actual.y],
                    "reference_heading_rad": target.psi,
                    "predicted_heading_rad": actual.psi,
                }
            )
        result.append({"id": packet["id"], "nodes": nodes})
    if any(
        n.startswith(("apex.control", "apex.models", "apex.simulation", "casadi"))
        for n in sys.modules
    ):
        raise RuntimeError("Scientific execution modules entered a read-only reference projection")
    frozen.verify_runtime(frozen.RUNTIME, request["source_sha256"])
    return {
        "packets": result,
        "source": frozen.SOURCE,
        "imports": guard.audit(),
        "native_control": control,
        "timing_s": {
            "bootstrap": bootstrap_s,
            "geometry": geometry_s,
            "projection": perf_counter() - projection_start,
        },
        "classification": (
            "DERIVED / pinned PlanningReference.sample at predicted progress; "
            "not retained NMPC preview or actual-future residual"
        ),
    }


class Session:
    """One read-only geometry process, bounded requests and parent-loss cleanup."""

    def __init__(self):
        import atexit
        import threading

        import psutil

        self.lock = threading.Lock()
        self.helper_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        executable = str(Path(sys.executable).parent.parent.resolve() / "bin/python")
        self.process = subprocess.Popen(
            [
                executable,
                "-I",
                "-B",
                str(Path(__file__).resolve()),
                "--serve",
                str(os.getpid()),
                str(psutil.Process().create_time()),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "VECLIB_MAXIMUM_THREADS": "1"},
        )
        atexit.register(self.close)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)

    def query(self, serialized):
        import select

        with self.lock:
            if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != self.helper_sha256:
                self.close()
                raise ValueError(
                    "Read-only reference implementation changed; reopen the application"
                )
            if self.process.poll() is not None:
                raise ValueError("Read-only reference process unavailable; reopen the application")
            self.process.stdin.write(serialized + "\n")
            self.process.stdin.flush()
            ready, _, _ = select.select([self.process.stdout], [], [], 45)
            if not ready:
                self.close()
                raise ValueError("Read-only Planning projection exceeded its bounded deadline")
            line = self.process.stdout.readline()
            if not line:
                raise ValueError("Read-only reference process exited; no projection admitted")
            result = json.loads(line)
            if "error" in result:
                raise ValueError(result["error"])
            return result


@lru_cache(maxsize=1)
def session():
    return Session()


@lru_cache(maxsize=8)
def _project(serialized, helper_sha256):
    result = session().query(serialized)
    if result.get("source") != frozen.SOURCE:
        raise ValueError("Derived reference source identity differs")
    return result


def project(capture, packets):
    """Cache only immutable captured inputs/results; evidence checks remain with the caller."""
    frozen.verify_runtime(frozen.RUNTIME, capture["source_sha256"])
    request = {
        "source_sha256": capture["source_sha256"],
        "environment": capture["environment"],
        "packets": [{"id": p["id"], "states": p["states"]} for p in packets],
    }
    serialized = json.dumps(request, sort_keys=True, allow_nan=False, separators=(",", ":"))
    if len(serialized.encode()) > 2**20:
        raise ValueError("Reference projection input exceeds the bounded transport")
    return _project(serialized, hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def serve():
    import threading

    import psutil

    parent, birth = int(sys.argv[2]), float(sys.argv[3])

    def owner():
        while True:
            try:
                if psutil.Process(parent).create_time() != birth:
                    os._exit(3)
            except psutil.Error:
                os._exit(3)
            __import__("time").sleep(0.5)

    threading.Thread(target=owner, daemon=True).start()
    for line in sys.stdin:
        try:
            if len(line.encode()) > 2**20:
                raise ValueError("Read-only reference input exceeds its bounded request")
            response = derive(json.loads(line))
        except Exception as error:
            response = {"error": "Pinned reference unavailable: " + str(error)}
        print(json.dumps(response, allow_nan=False), flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        serve()
    else:
        print(json.dumps(derive(json.loads(sys.stdin.read())), allow_nan=False))
