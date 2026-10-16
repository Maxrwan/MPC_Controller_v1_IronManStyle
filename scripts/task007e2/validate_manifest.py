"""Read-only E2 manifest checks. Standard library only; never import APEX/numerics.

This validates the limited JSON Schema vocabulary in the companion schema, not
arbitrary external schemas. Unknown keywords fail closed. Semantic checks bind
values to retained summaries and parsed source without constructing a controller.
"""

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import tomllib
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "configs/performance/apex_performance_synthetic_v1.json"
EVIDENCE = "docs/task007e/e2/evidence_links.json"
SCHEMA = "docs/task007e/e2/performance_profile.schema.json"
BASE = "835eefb0aafe2f982a0ba05847d4e731079ff52d"
WORKER = "8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae"
FROZEN = "c6990572045e61ee443dc715de9e8c44396e5b41"
SUMMARY = "docs/task007d/vis/vis1l/evidence/controlled_A/summary.json"


def require(condition, label):
    if not condition:
        raise ValueError(label)


def read(path):
    def reject(value):
        raise ValueError("Nonfinite JSON: " + value)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result

    return json.loads((ROOT / path).read_text(), parse_constant=reject, object_pairs_hook=unique)


@lru_cache(maxsize=None)
def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def tree(path):
    return ast.parse((ROOT / path).read_text())


def literal(node):
    if isinstance(node, ast.Call) and ast.unparse(node.func) == "np.array":
        node = node.args[0]
    return ast.literal_eval(node)


def constant(path, name):
    for node in tree(path).body:
        if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == name:
            return literal(node.value)
    raise ValueError("Missing constant: " + name)


def defaults(path, name):
    cls = next(n for n in tree(path).body if isinstance(n, ast.ClassDef) and n.name == name)
    return {
        n.target.id: literal(n.value)
        for n in cls.body
        if isinstance(n, ast.AnnAssign)
        and n.value is not None
        and not isinstance(n.value, ast.Call)
    }


def function_defaults(path, owner, name):
    cls = next(n for n in tree(path).body if isinstance(n, ast.ClassDef) and n.name == owner)
    f = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return {
        a.arg: literal(d) for a, d in zip(f.args.args[-len(f.args.defaults) :], f.args.defaults)
    }


def schema_check(value, schema, location="$ "):
    allowed = {
        "$schema",
        "$id",
        "title",
        "type",
        "const",
        "required",
        "properties",
        "additionalProperties",
    }
    require(not set(schema) - allowed, "Unsupported schema keyword")
    kinds = {"object": dict, "array": list, "string": str, "boolean": bool}
    if "type" in schema:
        require(schema["type"] in kinds, "Unsupported schema type")
        require(type(value) is kinds[schema["type"]], location + "type")
    if "const" in schema:
        require(
            type(value) is type(schema["const"]) and value == schema["const"], location + "const"
        )
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        require(set(schema.get("required", [])) <= set(value), location + "required")
        if schema.get("additionalProperties") is False:
            require(set(value) <= set(properties), location + "additionalProperties")
        for key in value.keys() & properties.keys():
            schema_check(value[key], properties[key], location + "/" + key)


def artifact_checks(value):
    count = 0
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            path = value["path"]
            require(not Path(path).is_absolute() and ".." not in Path(path).parts, "Local path")
            require(digest(path) == value["sha256"], "Artifact hash: " + path)
            count += 1
        for item in value.values():
            count += artifact_checks(item)
    elif isinstance(value, list):
        for item in value:
            count += artifact_checks(item)
    return count


def semantic_checks(m, evidence):
    schema_check(m, read(SCHEMA))
    p, protocol = m["profile"], m["evaluation_protocol"]
    a = read(SUMMARY)
    b = read("docs/task007d/vis/vis1l/evidence/measured_A_1/summary.json")
    nmpc = p["nmpc"]
    require(p["architecture"] == "A" and p["predictor"] == "A_legacy", "Architecture A only")
    require(m["schema_file"] == SCHEMA and m["evidence_index"] == EVIDENCE, "References")
    for field, name in [
        ("state_order", "STATE_NAMES"),
        ("state_units", "STATE_UNITS"),
        ("control_order", "CONTROL_NAMES"),
        ("control_units", "CONTROL_UNITS"),
    ]:
        require(p["coordinates"][field] == list(constant("src/apex/state.py", name)), name)
    config = nmpc["configuration"]
    require(config == a["configuration"] == b["configuration"], "Recorded MPCConfig")
    source = defaults("src/apex/control/mpc/problem.py", "MPCConfig")
    source["costs"] = defaults("src/apex/control/mpc/cost.py", "CostScales")
    f = next(
        n
        for n in tree("scripts/task007dcx/worker.py").body
        if isinstance(n, ast.FunctionDef) and n.name == "frozen_config"
    )
    call = next(n.value for n in f.body if isinstance(n, ast.Return))
    for kw in call.keywords:
        if kw.arg == "costs":
            source["costs"].update({k.arg: literal(k.value) for k in kw.value.keywords})
        elif kw.arg == "tire_physics":
            require(ast.unparse(kw.value) == "RACING_TIRE_PHYSICS", "Racing tire selector")
            tire = next(
                n.value
                for n in tree("src/apex/models/tire/config.py").body
                if isinstance(n, ast.Assign) and n.targets[0].id == "RACING_TIRE_PHYSICS"
            )
            source[kw.arg] = dict(
                zip(["model", "longitudinal_allocation"], map(literal, tire.args))
            )
        else:
            source[kw.arg] = literal(kw.value)
    require(config == source, "Parsed worker construction/defaults")
    require(nmpc["horizon_seconds"] == config["dt"] * config["horizon"], "Horizon")
    n = config["horizon"]
    require(
        nmpc["decision_dimensions"]
        == dict(
            states=6 * (n + 1),
            controls=2 * n,
            slacks=2 * (n + 1),
            total=8 * (n + 1) + 2 * n,
            shooting_equalities=6 * (n + 1),
        ),
        "Full sequence",
    )
    cost = "src/apex/control/mpc/cost.py"
    scales = config["costs"]
    weights = constant(cost, "STATE_WEIGHTS")
    multipliers = [
        scales["speed"],
        scales["dynamic"] * scales["alpha_vy"],
        scales["dynamic"] * scales["alpha_r"],
        scales["lateral"],
        scales["lateral"],
    ]
    require(nmpc["stage_cost"]["Q_diagonal"] == [x * y for x, y in zip(weights, multipliers)], "Q")
    for key, name, scale in [
        ("R_diagonal", "INPUT_WEIGHTS", "control"),
        ("W_diagonal", "RATE_WEIGHTS", "rate"),
    ]:
        require(nmpc["stage_cost"][key] == [x * scales[scale] for x in constant(cost, name)], key)
    for key in ["alpha_vy", "alpha_r"]:
        require(nmpc["stage_cost"][key] == nmpc["terminal"][key] == scales[key], key)
    require(nmpc["stage_cost"]["lambda_s"] == config["progress_weight"], "lambda_s")
    require(nmpc["terminal"]["multiplier"] == scales["terminal"], "terminal multiplier")
    design = defaults("src/apex/control/baseline/lqr.py", "DesignScales")
    q = [1 / design[k] ** 2 for k in ["e_y", "e_psi", "vy_error", "r_error"]]
    r = [1 / design["delta_feedback"] ** 2]
    require(
        nmpc["terminal"]["design_Q_diagonal"] == p["tracker"]["Q_diagonal"] == q,
        "DARE Q exact floating expression",
    )
    require(
        nmpc["terminal"]["design_R_diagonal"] == p["tracker"]["R_diagonal"] == r,
        "DARE R exact floating expression",
    )
    require(
        p["tracker"]["configuration"]
        == a["tracker_configuration"]
        == b["tracker_configuration"]
        == defaults("src/apex/control/trajectory/tracker.py", "TrackerConfig"),
        "Tracker",
    )
    solver = constant("src/apex/optimization/solvers/ipopt.py", "DEFAULT_OPTIONS")
    for path in ["scripts/task007dcx/worker.py", "scripts/task007dvis/worker.py"]:
        call = next(
            n
            for n in ast.walk(tree(path))
            if isinstance(n, ast.Call) and ast.unparse(n.func) == "make_mpc"
        )
        kw = {k.arg: k.value for k in call.keywords}
        require(literal(kw["warm_start"]) is True, "Worker warm-start")
        solver.update(literal(kw["solver_options"]))
    require(nmpc["solver"]["explicit_effective_options"] == solver, "IPOPT options")
    require(
        nmpc["warm_start"]["enabled"] is True
        and nmpc["warm_start"]["dual_multipliers_supplied"] is False,
        "Primal warm start",
    )
    slack = nmpc["constraints"]["slack"]
    require(
        slack["linear_penalty"] == constant(cost, "SLACK_LINEAR")
        and slack["quadratic_penalty"] == constant(cost, "SLACK_QUADRATIC"),
        "Slack weights",
    )
    scheduling = p["scheduling"]
    for field, key in [
        ("planner_dt_s", "planner_dt"),
        ("tracker_dt_s", "tracker_dt"),
        ("maximum_plant_step_s", "plant_dt"),
        ("committed_prefix_prediction", "committed_prefix_prediction"),
        ("fixed_handoff_offset", "fixed_handoff_offset"),
    ]:
        require(scheduling[field] == a["simulation"][key] == b["simulation"][key], key)
    require(
        scheduling["committed_prefix_prediction"] is False
        and scheduling["fixed_handoff_offset"] is None,
        "Legacy policy",
    )
    delay = function_defaults(
        "src/apex/control/trajectory/prediction.py", "RollingDelay", "__init__"
    )
    require(
        [scheduling["delay_estimator"][k] for k in ["initial_s", "window_completions", "maximum_s"]]
        == [delay[k] for k in ["initial", "window", "maximum"]],
        "Delay estimator",
    )
    require(
        protocol["controlled_planner_delay_pattern_s"]
        == list(constant("scripts/task007dvis/protocol.py", "PATTERN")),
        "Timing pattern",
    )
    require(protocol["initial_state"] == a["initial_state"] == b["initial_state"], "Initial")
    require(
        protocol["simulation_records"]
        == {"controlled_A": a["simulation"], "measured_A_1": b["simulation"]},
        "Simulation records",
    )
    for s in protocol["simulation_records"].values():
        require(
            s["codriver_delay"] == protocol["codriver_imposed_delay_s"] == 0.005
            and s["laps"] == protocol["requested_seam_crossings"] == 2
            and s["duration"] == protocol["maximum_physical_duration_s"] == 80,
            "VIS protocol",
        )
    require(
        "codriver_delay" not in scheduling and "duration" not in scheduling,
        "Do not promote experiment values",
    )
    expected_vehicle = {}
    for line in (ROOT / p["vehicle"]["file"]["path"]).read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            key, v = line.split(":", 1)
            expected_vehicle[key] = v.strip() if key == "name" else float(v)
    for key in p["vehicle"]["unknown_fields"]:
        expected_vehicle[key] = None
    require(p["vehicle"]["parameters"] == expected_vehicle, "Vehicle fields")
    constraints = nmpc["constraints"]
    for field, key in [
        ("denominator_min", "denominator_margin"),
        ("minimum_axle_load_N", "minimum_axle_load"),
        ("steering_rate_rad_s", "steering_rate"),
    ]:
        require(constraints[field] == config[key], "Constraint: " + field)
    require(
        constraints["vx_m_s"] == [config["minimum_speed"], expected_vehicle["maximum_speed"]],
        "Speed bounds",
    )
    limits = [
        [-expected_vehicle["maximum_steering_angle"], expected_vehicle["maximum_steering_angle"]],
        [
            -expected_vehicle["maximum_braking_deceleration"],
            expected_vehicle["maximum_acceleration"],
        ],
    ]
    require(
        constraints["control_box"] == limits
        and p["tracker"]["control_lower"] == [v[0] for v in limits]
        and p["tracker"]["control_upper"] == [v[1] for v in limits],
        "Control limits",
    )
    require(
        constraints["steering_increment_max_per_stage_rad"]
        == config["steering_rate"] * config["dt"],
        "Slew bound",
    )
    require(
        slack["shape"] == [2, n + 1] and slack["lower"] == 0 and slack["upper"] is None,
        "Slack domain",
    )
    require(
        constraints["longitudinal_fraction_bound"]
        == 1 - constant("src/apex/models/tire/grip.py", "LONGITUDINAL_MARGIN"),
        "Grip margin",
    )
    require(
        p["vehicle"]["file"]["sha256"] == a["vehicle_sha256"] == b["vehicle_sha256"],
        "Vehicle identity",
    )
    require(
        {f["path"]: f["sha256"] for f in p["planning"]["files"]}
        == a["fixture_sha256"]
        == b["fixture_sha256"],
        "Planning constituent identity",
    )
    planning = read(p["planning"]["package"] + "/planning_manifest.json")
    require(p["planning"]["gamma"] == planning["aggression_factor"] == 2, "Gamma")
    require(p["planning"]["track_length_m"] == planning["closed_track_length_m"], "Track length")
    require(
        config["tracker_margin"]
        == p["planning"]["reference_margin_m"]
        == planning["tracker_margin_m"],
        "Synthetic corridor margin",
    )
    e1 = read("docs/task007e/e1/fallback_domain_register.json")
    require(
        p["fallback"]["admission"] == e1["domain"]["entry_guard"]
        and p["physical_validity"] == e1["domain"]["model_guards"],
        "E1 domain binding",
    )
    for key in [
        "guaranteed_recovery",
        "braking_to_standstill",
        "continuous_corridor_enforcement",
        "swept_body_safety",
        "application_time_eligibility_recheck",
        "uninterrupted_trajectory_guaranteed",
        "a_exhaustion_observed_in_VIS",
    ]:
        require(p["fallback"][key] is False, "Fallback unsupported claim: " + key)
    provenance = m["provenance"]
    require(
        [
            provenance[k]
            for k in [
                "manifest_preparation_base_revision",
                "scientific_worker_revision",
                "frozen_executable_ancestor",
            ]
        ]
        == [BASE, WORKER, FROZEN],
        "Revision roles",
    )
    inventory = provenance["current_runtime_source_inventory"]
    require(
        inventory["path"] == SUMMARY
        and inventory["json_pointer"] == "/source_sha256"
        and inventory["entries"] == len(a["source_sha256"]),
        "Inventory reference",
    )
    env = m["environment"]
    for key in ["native_configuration", "observed_process_thread_counts", "threadpool_inventory"]:
        src = {"native_configuration": "native", "threadpool_inventory": "threadpools"}.get(
            key, key
        )
        require(env[key] == a[src] == b[src], "Native observations: " + key)
    expected_env = read("docs/task007e/e0/verification_applicability.json")["environment"]
    require(env["tested"] == expected_env, "Recorded environment")
    require(
        platform.python_version() == expected_env["python"].split()[0]
        and platform.platform() == expected_env["platform"],
        "Current audit environment",
    )
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    versions = {v["name"]: v["version"] for v in lock["package"]}
    for name, version in expected_env["packages"].items():
        require(
            importlib.metadata.version(name) == version == versions[name], "Dependency: " + name
        )
    report = read("docs/task007d/vis/vis1l/summary.json")
    for case, summary in [("controlled_A", a), ("measured_A_1", b)]:
        out = evidence["A"][case]
        retained = report[case]
        lap = retained["coverage"]["windows"][1]
        require(out["physical_summary"] == summary["physical"], "Physical summary: " + case)
        require(out["full_lap_time_s"] == lap["end"] - lap["start"], "Lap: " + case)
        require(out["timing"] == retained["timing"], "Timing: " + case)
        require(
            out["forecast_matches"]
            == summary["active_A_forecast_exact_matches"]
            == out["runtime_release_count"]
            == summary["release_count"],
            "Forecast count",
        )
        for key, value in out["native_run_metrics"].items():
            require(value == retained["native_run_metrics"][key], "Native metric: " + key)
    c = evidence["comparison_only_not_profile_settings"]["measured_C70_1"]
    require(
        c["full_lap_time_s"] is None
        and c["complete_laps"] == 0
        and c["end_s"] == 48.67
        and c["fixed_misses"] == 30
        and c["terminal_consecutive_misses"] == 8
        and c["export_complete"] is False,
        "Preserve censored comparative outcome",
    )
    for case in ["measured_C70_2", "measured_A_2"]:
        require(
            evidence["comparison_only_not_profile_settings"][case]["status"]
            == report[case]["status"],
            "Unexecuted outcome",
        )
    return 1


def validate(m, evidence):
    semantic_checks(m, evidence)
    references = artifact_checks(m) + artifact_checks(evidence)
    inventory = read(SUMMARY)["source_sha256"]
    for path, expected in inventory.items():
        require(digest(path) == expected, "Scientific source changed: " + path)
    # Compare existing files only: E2 adds an inert configuration and audit tool.
    scope = [
        "src",
        "pyproject.toml",
        "uv.lock",
        "configs/vehicles",
        "configs/planning",
        "scripts/task007dcx",
        "scripts/task007dvis",
        "scripts/threading_study",
        "scripts/run_task007dvis.py",
    ]
    pairs = [(FROZEN, WORKER), (WORKER, BASE)]
    differences = []
    for earlier, later in pairs:
        names = subprocess.check_output(
            ["git", "diff", "--name-only", earlier, later, "--", *scope], cwd=ROOT, text=True
        ).splitlines()
        # Three VIS1L report additions after worker, separately hash-bound via evidence.
        allowed = {"scripts/task007dvis/long_report.py", "scripts/task007dvis/long_figures.py"}
        require(not set(names) - allowed, "Executable equivalence: " + str(names))
        differences.append(dict(earlier=earlier, later=later, offline_additions=names))
    return dict(
        passed=True,
        source_inventory_hashes=len(inventory),
        artifact_references=references,
        exact_source_comparisons=differences,
    )


def negative_checks(m, e):
    mutations = [
        ("N", ["profile", "nmpc", "configuration", "horizon"], 9),
        ("Q", ["profile", "nmpc", "stage_cost", "Q_diagonal"], [4, 4, 1, 100, 100]),
        ("order", ["profile", "coordinates", "control_order"], ["a_cmd", "delta"]),
        ("freeze", ["flags", "frozen"], True),
        ("B", ["profile", "scheduling", "committed_prefix_prediction"], True),
        ("fallback", ["profile", "fallback", "guaranteed_recovery"], True),
        (
            "solver",
            ["profile", "nmpc", "solver", "explicit_effective_options", "ipopt.max_iter"],
            50,
        ),
        ("fixture", ["profile", "planning", "files"], []),
        ("thread observation", ["environment", "observed_process_thread_counts"], [2]),
    ]
    passed = []
    for name, path, value in mutations:
        changed = copy.deepcopy(m)
        target = changed
        for k in path[:-1]:
            target = target[k]
        target[path[-1]] = value
        try:
            semantic_checks(changed, e)
        except ValueError:
            passed.append(name)
        else:
            raise ValueError("Mutation not rejected: " + name)
    corrupted = copy.deepcopy(e)
    corrupted["A"]["controlled_A"]["summary"]["sha256"] = "0" * 64
    try:
        artifact_checks(corrupted)
    except ValueError:
        passed.append("evidence hash")
    else:
        raise ValueError("Corrupted evidence hash accepted")
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    m, e = read(MANIFEST), read(EVIDENCE)
    result = validate(m, e)
    result.update(
        schema=m["schema"],
        audited_source_revision=BASE,
        manifest_sha256=digest(MANIFEST),
        evidence_index_sha256=digest(EVIDENCE),
        schema_sha256=digest(SCHEMA),
        validator_sha256=digest(str(Path(__file__).relative_to(ROOT))),
        negative_checks=negative_checks(m, e),
        validation_method=(
            "profile schema vocabulary, static AST, exact JSON, hashes; no numerical constructors"
        ),
        new_pytest_executions=0,
        new_simulations=0,
        new_solver_calls=0,
        environment=dict(python=platform.python_version(), platform=platform.platform()),
    )
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x") as out:
            out.write(encoded)
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
