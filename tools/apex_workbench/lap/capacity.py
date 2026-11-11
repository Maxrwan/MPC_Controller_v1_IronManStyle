"""One host observation per requested launch; presentation processes are not scientific workers."""

import datetime
import os
import shutil
from pathlib import Path

import psutil

from tools.apex_workbench import storage

from . import config


def scientific_command(command):
    names = {Path(c).name for c in command}
    return bool(
        names & {"pytest", "nmpc_scratch_worker.py", "nmpc_weight_worker.py"}
        or set(command)
        & {
            "tools.apex_workbench.lap.execution",
            "tools.apex_workbench.worker",
            "tools.apex_workbench.nmpc_scratch_worker",
            "tools.apex_workbench.nmpc_weight_worker",
        }
        or any("task007d" in c or "pi_compute_benchmark" in c for c in command)
    )


def observe(value):
    value = config.validate(value)
    full = value["mode"] == "full_lap"
    limits = config.limits(value)
    # Preserve the historical full-lap reserves; Extended retains the existing 1GiB disk floor.
    memory_floor = 2 * limits["sampled_rss_bytes"] if full else 0
    disk_floor = 2**30 + (2 * limits["sampled_output_bytes"] if full else 0)
    memory = psutil.virtual_memory().available
    disk = shutil.disk_usage(config.ROOT).free
    conflicts = [
        {"pid": p.pid, "command": p.info["cmdline"]}
        for p in psutil.process_iter(["pid", "cmdline"])
        if scientific_command(p.info["cmdline"] or [])
    ]
    roots = {
        config.ROOT,
        Path("/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle"),
        Path("/Users/marwansaber/.codex/worktrees/pre-int-w1/MPC_Controller_v1_IronManStyle"),
    }
    guards = []
    for root in roots:
        for directory, folders, files in os.walk(root / "results", followlinks=False):
            for name in set(folders + files) & {"MEASURED_ACTIVE", "D3_ACTIVE"}:
                path = Path(directory) / name
                try:
                    inactive = path.is_file() and storage.read_json(path).get("active") is False
                except (OSError, ValueError, TypeError, AttributeError):
                    inactive = False
                if not inactive:
                    guards.append(str(path))
    reasons = []
    if memory <= memory_floor:
        reasons.append(f"Insufficient available memory: {memory} bytes; need >{memory_floor}")
    if disk <= disk_floor:
        reasons.append(f"Insufficient disk capacity: {disk} bytes; need >{disk_floor}")
    if conflicts:
        reasons.append("Existing scientific compute/test worker: " + str(conflicts))
    if guards:
        reasons.append("Active or unverified scientific measurement guard: " + str(guards))
    return {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "mode": value["mode"],
        "memory_available_bytes": memory,
        "required_available_ram_bytes": memory_floor,
        "disk_free_bytes": disk,
        "required_disk_bytes": disk_floor,
        "conflicting_processes": conflicts,
        "active_guards": guards,
        "status": "BLOCKED" if reasons else "PASS",
        "reasons": reasons,
    }


def require(value):
    observation = observe(value)
    if observation["status"] != "PASS":
        raise RuntimeError("Launch preflight blocked: " + "; ".join(observation["reasons"]))
    return observation
