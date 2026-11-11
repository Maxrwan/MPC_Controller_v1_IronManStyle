"""Explicit once-only full-lap driver; no retries, loops, sweeps or implicit acceptance."""

import datetime
import os
import shutil
import sys
import time
from pathlib import Path

import psutil

from tools.apex_workbench import jobs, storage

from . import admission, analysis, config, evidence, execution


def host(budget):
    jobs.preflight()
    conflicts = []
    for process in psutil.process_iter(["pid", "cmdline"]):
        command = process.info["cmdline"] or []
        names = {Path(c).name for c in command}
        if (
            names
            & {"pytest", "nmpc_scratch_worker.py", "nmpc_weight_worker.py", "reference_view.py"}
            or "tools.apex_workbench.lap.execution" in command
            or any(
                "task007d" in c or "pi_compute_benchmark" in c or "streamlit" == c for c in command
            )
        ):
            conflicts.append({"pid": process.pid, "command": command})
    roots = [
        config.ROOT,
        Path("/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle"),
        Path("/Users/marwansaber/.codex/worktrees/pre-int-w1/MPC_Controller_v1_IronManStyle"),
    ]
    guards = []
    for root in roots:
        for directory, folders, files in os.walk(root / "results", followlinks=False):
            for name in set(folders + files) & {"MEASURED_ACTIVE", "D3_ACTIVE"}:
                path = Path(directory) / name
                guards.append(
                    {
                        "path": str(path),
                        "inactive": path.is_file()
                        and storage.read_json(path).get("active") is False,
                    }
                )
    memory = psutil.virtual_memory().available
    free = shutil.disk_usage(config.ROOT).free
    # Same full-lap host rules as the reviewed original driver: two complete worker allowances,
    # and the original disk floor plus two complete output allowances. No pilot-only relaxation.
    memory_floor = 2 * config.PROFILE["limits"]["full_lap"]["sampled_rss_bytes"]
    disk_floor = 2**30 + 2 * config.PROFILE["limits"]["full_lap"]["sampled_output_bytes"]
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "memory_available_bytes": memory,
        "required_available_ram_bytes": memory_floor,
        "disk_free_bytes": free,
        "required_disk_bytes": disk_floor,
        "cpu_count": psutil.cpu_count(),
        "cpu_percent_half_second": psutil.cpu_percent(interval=0.5),
        "conflicting_processes": conflicts,
        "external_guards": guards,
        "budget": budget,
        "status": "PASS",
    }
    if (
        conflicts
        or not all(g["inactive"] for g in guards)
        or memory <= memory_floor
        or free <= disk_floor
        or memory <= 2 * budget["conservative_extrapolation"]["sampled_rss_bytes"]
        or free <= 2**30 + 2 * budget["conservative_extrapolation"]["sampled_output_bytes"]
    ):
        result["status"] = "BLOCKED"
    return result


def start_once():
    policy_path = config.safe(config.OUTPUT / "access.json")
    policy = storage.read_json(policy_path)
    source = admission.reviewed_source(
        storage.read_json(config.safe(Path(policy["review_record"])))
    )
    if policy["stage"] != "reviewed-work" or "full_lap" in policy["used"]:
        raise ValueError("The single full-lap attempt is already consumed or not in WORK")
    claim_path = config.safe(config.OUTPUT / "full_lap_final_claim.json")
    if claim_path.exists():
        raise ValueError("The once-only claim already exists; preserve it and do not retry")
    pilot = evidence.read_run(config.RUNS / policy["used"]["pilot"])
    budget = analysis.resource_budget(pilot)
    capacity = host(budget)
    observation = config.safe(
        config.OUTPUT / ("final_host_preflight_" + str(time.time_ns()) + ".json")
    )
    storage.write_json(observation, capacity, exclusive=True)
    if capacity["status"] != "PASS":
        raise RuntimeError(
            "Host-capacity preflight BLOCKED; no claim or numerical attempt: " + str(observation)
        )
    if storage.read_json(policy_path) != policy:
        raise ValueError("Execution policy changed during host preflight")
    source_record = config.safe(
        config.OUTPUT / ("final_source_preflight_" + str(time.time_ns()) + ".json")
    )
    try:
        frozen = config.v1.frozen
        scientific_hashes = frozen.source_hashes()
        frozen.verify_runtime(config.v1.RUNTIME, scientific_hashes)
        environment = frozen.environment_identity()
        if environment != pilot["request"]["capture"]["environment"]:
            raise ValueError("Approved numerical environment differs from the retained pilot")
        storage.write_json(
            source_record,
            {
                "status": "PASS",
                "reviewed_revision": source,
                "producer_sha256": config.producers(),
                "source_sha256": scientific_hashes,
                "environment": environment,
            },
            exclusive=True,
        )
    except Exception as error:
        storage.write_json(
            source_record,
            {
                "status": "BLOCKED",
                "error": str(error),
                "claim_consumed": False,
                "scientific_execution_started": False,
            },
            exclusive=True,
        )
        raise
    declared = {
        "pilot_manifest_sha256": pilot["status"]["manifest_sha256"],
        "budget": budget,
        "reviewed_revision": source,
        "policy_identity": config.policy_identity(policy),
        "host": capacity,
        "host_record": str(observation),
        "source_record": str(source_record),
    }
    storage.write_json(
        config.safe(config.OUTPUT / "full_lap_preflight.json"), declared, exclusive=True
    )
    value = config.defaults("full_lap")
    config.access(value)
    claim = {
        "reviewed_revision": source,
        "review_sha256": policy["review_sha256"],
        "authority_sha256": policy["authority_sha256"],
        "policy_sha256_before": storage.sha256(policy_path),
        "effective": value,
        "host_record": str(observation),
        "maximum_attempts": 1,
        "automatic_retry": False,
    }
    storage.write_json(claim_path, claim, exclusive=True)
    directory = execution.start(value)
    storage.write_json(
        config.safe(config.OUTPUT / "full_lap_final_launch.json"),
        {"run_id": directory.name, "directory": str(directory)},
        exclusive=True,
    )
    print(str(directory), flush=True)
    return directory


if __name__ == "__main__":
    if sys.argv[1:] != ["--execute"]:
        raise SystemExit(
            "Requires explicit --execute after independent PASS and source-bound policy install"
        )
    start_once()
