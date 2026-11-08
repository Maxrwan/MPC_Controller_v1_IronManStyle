"""Scratch software contracts and independent fixtures; never run a controller."""

import copy
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs, run_catalog, storage
from tools.apex_workbench import nmpc_analysis as analysis
from tools.apex_workbench import nmpc_scratch as scratch
from tools.apex_workbench import nmpc_scratch_panels as panels
from tools.apex_workbench import nmpc_weight_lab as frozen
from tools.apex_workbench.configuration import ROOT


def widget(items, label):
    return next(w for w in items if w.label == label)


def test_explicit_configuration_roundtrip_and_baseline_reset():
    original = scratch.defaults()
    changed = scratch.defaults()
    changed["costs"]["lateral"] = 1.0
    assert scratch.loads(scratch.dumps(changed)) == changed
    assert scratch.defaults() == original and original["costs"]["lateral"] == 2.0
    renamed = copy.deepcopy(changed)
    renamed.update(configuration_id="selected_profile", version=7)
    assert scratch.identity(renamed) == scratch.identity(changed)
    assert scratch.identity(changed) != scratch.identity(original)


@pytest.mark.parametrize(
    "name,value",
    [
        ("lateral", 0),
        ("dynamic", -1),
        ("rate", True),
        ("terminal", -1),
        ("alpha_vy", float("nan")),
        ("alpha_r", float("inf")),
        ("control", "1"),
        ("speed", None),
    ],
)
def test_native_cost_semantics_reject_bad_values(name, value):
    config = scratch.defaults()
    config["costs"][name] = value
    with pytest.raises(ValueError):
        scratch.validate(config)


@pytest.mark.parametrize(
    "name", ["mass", "horizon", "dt", "substeps", "solver", "tire", "steering_rate", "track"]
)
def test_no_general_configuration_editor_or_silent_extra_fields(name):
    value = scratch.defaults()
    value[name] = 1
    with pytest.raises(ValueError):
        scratch.validate(value)


def test_zero_native_terminal_alpha_and_strict_version_identity():
    value = scratch.defaults()
    for name in ["terminal", "alpha_vy", "alpha_r"]:
        value["costs"][name] = 0
    assert scratch.validate(value)["costs"]["terminal"] == 0.0
    for field, item in [
        ("version", True),
        ("configuration_id", "../escape"),
        ("disturbance", "arbitrary"),
        ("scientific_source", "0" * 40),
    ]:
        bad = scratch.defaults()
        bad[field] = item
        with pytest.raises(ValueError):
            scratch.validate(bad)
    with pytest.raises(ValueError, match="Duplicate"):
        scratch.loads('{"schema":1,"schema":2}')


@pytest.fixture(scope="session")
def native_probes():
    # Frozen configuration/algebra only. No AsyncRunner/IPOPT execution.
    baseline = scratch.probe(scratch.defaults())
    varied = scratch.defaults()
    varied["costs"] = dict(
        lateral=1.25,
        dynamic=0.75,
        speed=1.5,
        control=0.8,
        rate=1.2,
        terminal=0.5,
        alpha_vy=0.6,
        alpha_r=0.7,
    )
    return baseline, varied, scratch.probe(varied, check=True)


def test_all_eight_overrides_reach_native_problem_and_constructor(native_probes):
    baseline, varied, report = native_probes
    checks = report["software_checks"]
    assert checks["optimizer_solves"] == checks["plant_steps"] == 0
    assert checks["constructed_costs"] == checks["constructor_costs"] == varied["costs"]
    # Independent literal expression values at x=[1,1,1,1,0,1], u=[1,1], zero reference/prior.
    assert checks["stage_components_unit_fixture"] == pytest.approx([258.325, 20.8, 1.32])
    a, b = copy.deepcopy(baseline["resolved"]), copy.deepcopy(report["resolved"])
    assert a.pop("effective")["costs"] == scratch.PROFILE["baseline_costs"]
    b.pop("effective")
    a["configuration"].pop("costs")
    b["configuration"].pop("costs")
    assert a == b
    assert len(frozen.verify_runtime(scratch.RUNTIME)) == 333
    with pytest.raises(ValueError, match="Unsafe"):
        frozen.verify_runtime(scratch.OUTPUT / "runtime/source")
    assert all(
        str(scratch.RUNTIME) in item["path"]
        for name, item in report["imports"].items()
        if name.startswith("apex") and "path" in item
    )


def test_native_disturbance_is_fixed_and_uses_existing_configuration(native_probes):
    report = scratch.probe(scratch.work_cases()["disturbance"])
    sim = report["resolved"]["simulation"]
    assert (sim["disturbance_time"], sim["disturbance_ey"], sim["disturbance_heading"]) == (
        0.5,
        0.08,
        -0.04,
    )
    assert sim["duration"] == 2.0
    assert report["resolved"]["configuration"] == native_probes[0]["resolved"]["configuration"]


def response(times, errors):
    return [{"time": t, "racing_error_y_m": e} for t, e in zip(times, errors)]


def test_independent_peak_rms_and_real_application_variation():
    result = analysis.summary([0, 3, -4])
    assert result["peak_abs"] == 4 and result["rms"] == pytest.approx(math.sqrt(25 / 3))
    commands = [
        {"time": 0, "application_time": 0.1, "delta": 0.0},
        {"time": 0.1, "application_time": 0.3, "delta": 0.2},
        {"time": 0.2, "application_time": 0.7, "delta": -0.1},
        {"time": 0.3, "application_time": None, "requested_delta": 4},
    ]
    metric = analysis.command_metrics(commands, "delta")
    assert metric["total_variation"] == pytest.approx(0.5)
    assert metric["maximum_observed_increment_rate"] == pytest.approx(1.0)
    assert metric["application_window_s"] == [0.1, 0.7]
    assert metric["rows_without_applied_measurement"] == 1


def test_settling_uses_actual_times_and_persistent_observed_tail():
    rows = response([0.5, 0.6, 0.9, 1.3, 1.8], [0.08, 0.005, 0.03, 0.004, 0.003])
    metric = analysis.settling(rows, start_s=0.5, band_m=0.01, minimum_tail_s=0.25)
    assert metric["settling_time_s"] == pytest.approx(0.8)
    assert analysis.settling(rows[:2], start_s=0.5)["status"] == "insufficient observation window"
    assert (
        analysis.settling(response([0.5, 1, 1.5], [0.08, 0.07, 0.02]), start_s=0.5)[
            "settling_time_s"
        ]
        is None
    )
    with pytest.raises(ValueError):
        analysis.settling(response([0.5, 0.4], [0, 0]), start_s=0)


def matrix_record(matrices):
    return {
        "state_order": ["e_y", "e_psi", "vy", "r"],
        "dt_s": 0.01,
        "feedback": "u = nominal - K @ error",
        "rows": [
            {"time": i * 0.01, "A": a, "B": [[1], [0], [0], [0]], "K": [[0.1, 0, 0, 0]]}
            for i, a in enumerate(matrices)
        ],
    }


def test_local_feedback_sign_order_and_chronological_product():
    record = matrix_record([[[0.9, 0, 0, 0], [0, 0.7, 0, 0], [0, 0, 0.6, 0], [0, 0, 0, 0.5]]] * 2)
    result = analysis.linear_indicators(record)
    assert [r["spectral_radius"] for r in result["rows"]] == pytest.approx([0.8, 0.8])
    assert result["rows"][-1]["finite_horizon_amplification_2norm"] == pytest.approx(0.64)
    for key, value in [
        ("state_order", ["vy", "r", "e_y", "e_psi"]),
        ("dt_s", 0.1),
        ("feedback", "u = nominal + K @ error"),
    ]:
        bad = copy.deepcopy(record)
        bad[key] = value
        with pytest.raises(ValueError):
            analysis.linear_indicators(bad)


def test_instantaneously_stable_matrices_can_amplify_time_varying_error():
    record = matrix_record(
        [
            [[0.6, 10, 0, 0], [0, 0.5, 0, 0], [0, 0, 0.2, 0], [0, 0, 0, 0.2]],
            [[0.6, 0, 0, 0], [10, 0.5, 0, 0], [0, 0, 0.2, 0], [0, 0, 0, 0.2]],
        ]
    )
    result = analysis.linear_indicators(record)
    assert all(row["spectral_radius"] == pytest.approx(0.5) for row in result["rows"])
    assert result["rows"][-1]["finite_horizon_amplification_2norm"] > 100


def policy_fixture(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    for name in scratch.PRODUCERS:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=source)

    git("init", "-q")
    git("add", *scratch.PRODUCERS)
    git(
        "-c",
        "user.name=Scratch fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "Software fixture only",
    )
    candidate = git("rev-parse", "HEAD").decode().strip()
    monkeypatch.setattr(frozen, "git", git)
    monkeypatch.setattr(scratch, "OUTPUT", tmp_path / "scratch")
    monkeypatch.setattr(scratch, "RUNS", scratch.OUTPUT / "runs")
    scratch.OUTPUT.mkdir()
    review = scratch.OUTPUT / "review.json"
    storage.write_json(review, {"outcome": "PASS", "candidate": candidate})
    policy = {
        "schema": "apex-nmpc-scratch-access/1",
        "stage": "reviewed-work",
        "review_record": str(review),
        "review_sha256": storage.sha256(review),
        "reviewed_revision": candidate,
        "producer_sha256": scratch.producer_hashes(),
        "cases": {k: scratch.identity(v) for k, v in scratch.work_cases().items()},
        "used": {},
    }
    storage.write_json(scratch.OUTPUT / "access.json", policy)
    return policy


def test_one_flat_three_attempt_budget_never_resets_history(tmp_path, monkeypatch):
    policy_fixture(tmp_path, monkeypatch)
    for index, config in enumerate(scratch.work_cases().values()):
        assert scratch.access(config)
        scratch.consume(config, "fixture_" + str(index))
        assert scratch.access(config, run_id="fixture_" + str(index))
        with pytest.raises(ValueError, match="consumed"):
            scratch.access(config)
    assert len(storage.read_json(scratch.OUTPUT / "access.json")["used"]) == 3
    unsupported = scratch.defaults()
    unsupported["costs"]["speed"] = 1.5
    with pytest.raises(ValueError):
        scratch.access(unsupported)


def test_source_and_review_changes_close_scratch_gate(tmp_path, monkeypatch):
    policy_fixture(tmp_path, monkeypatch)
    original = scratch.producer_hashes()
    monkeypatch.setattr(
        scratch,
        "producer_hashes",
        lambda: {**original, "tools/apex_workbench/nmpc_analysis.py": "0" * 64},
    )
    with pytest.raises(ValueError, match="stale"):
        scratch.access(scratch.defaults())


def test_saved_draft_is_exclusive_versioned_and_separate(tmp_path, monkeypatch):
    monkeypatch.setattr(scratch, "OUTPUT", tmp_path)
    value = scratch.defaults()
    value["configuration_id"] = "selected"
    path = scratch.saved_configuration(value)
    assert scratch.loads(path.read_text()) == value
    with pytest.raises(FileExistsError):
        scratch.saved_configuration(value)
    value["version"] = 2
    assert scratch.saved_configuration(value) != path


def test_actual_workspace_small_editor_reset_navigation_and_no_run(tmp_path, monkeypatch):
    monkeypatch.setattr(scratch, "OUTPUT", tmp_path / "scratch")
    monkeypatch.setattr(scratch, "RUNS", scratch.OUTPUT / "runs")

    def forbidden(*args, **kwargs):
        raise AssertionError("UI must not start a controller automatically")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    app = AppTest.from_file(
        str(ROOT / "tools/apex_workbench/workspace.py"), default_timeout=45
    ).run()
    widget(app.button, "Open NMPC Scratch / Control Analysis").click().run()
    assert not app.exception and widget(app.button, "Run Scratch experiment").disabled
    assert all(widget(app.number_input, name) for name in scratch.FIELDS)
    assert not any(w.label in {"mass", "horizon", "dt", "solver", "tire"} for w in app.number_input)
    widget(app.number_input, "lateral").set_value(1.25).run()
    widget(app.button, "Reset costs to accepted baseline").click().run()
    assert widget(app.number_input, "lateral").value == 2.0
    widget(app.radio, "Workspace").set_value("Analyze").run()
    assert not app.exception
    widget(app.radio, "Workspace").set_value("Compare").run()
    widget(app.radio, "Comparison source").set_value("NMPC Scratch (unqualified)").run()
    assert not app.exception


def test_real_job_reservation_cancel_and_launch_failure_are_software_only(tmp_path, monkeypatch):
    policy_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(jobs, "RUNS", tmp_path / "legacy")
    monkeypatch.setattr(jobs, "LEASE_ROOT", tmp_path / "lease")
    monkeypatch.setattr(jobs, "preflight", lambda: None)
    monkeypatch.setattr(scratch, "capture", lambda v: {"software_fixture": True})
    launched = []
    original_popen = subprocess.Popen

    def launch(*args, **kwargs):
        if args[0][1:3] == ["-m", "tools.apex_workbench.jobs"]:
            return launched.append((args, kwargs))
        return original_popen(*args, **kwargs)

    monkeypatch.setattr(jobs.subprocess, "Popen", launch)
    directory = jobs.start_run(scratch.ADAPTER, scratch.defaults())
    request = storage.read_json(directory / "request.json")
    assert request["adapter"] == scratch.ADAPTER and request["scratch_capture"]["software_fixture"]
    assert directory.parent == scratch.RUNS and len(launched) == 1
    assert launched[0][1]["env"]["PYTHONPATH"] == str(ROOT)
    monkeypatch.setattr(jobs, "status_for", lambda p: {"state": "running"})
    jobs.cancel_run(directory)
    assert (directory / "cancel.request").exists()

    def failure(*args, **kwargs):
        if args[0][1:3] == ["-m", "tools.apex_workbench.jobs"]:
            raise OSError("Injected launch failure; no process created")
        return original_popen(*args, **kwargs)

    monkeypatch.setattr(jobs.subprocess, "Popen", failure)
    with pytest.raises(OSError):
        jobs.start_run(scratch.ADAPTER, scratch.work_cases()["lateral_1"])
    failed = [p for p in scratch.RUNS.iterdir() if p != directory and not p.name.startswith(".")][0]
    assert storage.read_status(failed)["scientific_outcome"] == "failed"
    assert storage.read_json(scratch.OUTPUT / "access.json")["used"]["lateral_1"] == failed.name


def selected(directory):
    return run_catalog.Run(
        "run-" + hashlib.sha256(("id:" + directory.name).encode()).hexdigest()[:20],
        directory,
        ("owned",),
        (directory,),
        directory.name,
        scratch.ADAPTER,
        "",
        "running",
        "pending",
        "pending",
        (),
    )


@pytest.mark.parametrize("fault", ["foreign", "copy", "archive", "alias", "symlink"])
def test_scratch_lifecycle_rejects_foreign_records_before_mutation(tmp_path, monkeypatch, fault):
    monkeypatch.setattr(scratch, "OUTPUT", tmp_path)
    monkeypatch.setattr(scratch, "RUNS", tmp_path / "runs")
    directory = scratch.RUNS / "fixture_original"
    directory.mkdir(parents=True)
    storage.write_json(
        directory / "request.json",
        {"adapter": scratch.ADAPTER, "run_id": directory.name, "effective": scratch.defaults()},
    )
    record = selected(directory)
    assert scratch.owned(record) == directory
    if fault == "foreign":
        record = replace(record, directory=tmp_path / "archive" / directory.name)
    elif fault == "copy":
        record = replace(record, run_id="other")
    elif fault == "archive":
        record = replace(record, origins=("qualification archive",))
    elif fault == "alias":
        record = replace(record, aliases=(directory, tmp_path / "alias"))
    else:
        (directory / "worker.json").symlink_to(directory / "request.json")

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid record reached lifecycle mutation")

    monkeypatch.setattr(jobs, "status_for", forbidden)
    panels.inspect(record)
    assert not (directory / "cancel.request").exists()


def render_fixture(tmp_path, monkeypatch, native_probes, preset="baseline"):
    """Independent three-row DISPLAY fixture, not a simulation or scientific execution."""
    monkeypatch.setattr(scratch, "OUTPUT", tmp_path)
    monkeypatch.setattr(scratch, "RUNS", tmp_path / "runs")
    directory = scratch.RUNS / ("software_display_" + preset)
    (directory / "experiment").mkdir(parents=True)
    value = copy.deepcopy(scratch.work_cases()[preset])
    resolved = copy.deepcopy(native_probes[0]["resolved"])
    resolved["effective"] = value
    resolved["configuration"]["costs"] = value["costs"]
    captured = {
        "source": frozen.SOURCE,
        "source_sha256": {"fixture": "no_scientific_execution"},
        "resolved": resolved,
        "environment": {"fixture": "display only"},
    }
    request = {
        "record_version": 2,
        "adapter": scratch.ADAPTER,
        "run_id": directory.name,
        "effective": value,
        "scratch_capture": captured,
        "prediction": "software display fixture",
    }
    storage.write_json(directory / "request.json", request)
    for name in ["worker.json", "supervisor.json", "worker_result.json"]:
        storage.write_json(directory / name, {"software_fixture": True})
    raw = {
        "states": [
            {
                "time": t,
                "e_y": y,
                "front_utilization": 0.2,
                "rear_utilization": 0.3,
                "boundary_violation": False,
                "plan_id": 0,
            }
            for t, y in [(0.0, 0.02), (0.5, 0.01), (1.0, 0.0)]
        ],
        "controls": [
            {
                "time": 0.0,
                "application_time": 0.005,
                "delta": 0.1,
                "a_cmd": 1.0,
                "requested_delta": 0.1,
                "requested_a_cmd": 1.0,
            }
        ],
        "plans": [
            {
                "release_time": 0.0,
                "success": True,
                "solve_time": 0.01,
                "planner_total_time": 0.02,
                "max_slack": 0.0,
                "iterations": 2,
                "primal_infeasibility": 0.0,
            }
        ],
        "handoffs": [],
        "packets": [],
        "end_time": 1.0,
        "stop_reason": "software_display_fixture",
        "failure": None,
    }
    presentation = {
        "states": [
            {
                "time": t,
                "x": t,
                "y": y,
                "racing_error_y_m": y,
                "racing_error_heading_rad": 0.0,
                "reference_e_y_m": 0.0,
            }
            for t, y in [(0.0, 0.02), (0.5, 0.01), (1.0, 0.0)]
        ],
        "geometry": [
            {"x": 0, "y": 0, "left_x": 0, "left_y": 1, "right_x": 0, "right_y": -1},
            {"x": 1, "y": 0, "left_x": 1, "left_y": 1, "right_x": 1, "right_y": -1},
        ],
        "limits": {},
        "applied_disturbances": [],
    }
    for name, data in [
        ("raw.json", raw),
        ("presentation.json", presentation),
        ("summary.json", {"software_fixture": True}),
        (
            "pre_execution_identity.json",
            {"source": frozen.SOURCE, "resolved": resolved, "environment": captured["environment"]},
        ),
        (
            "post_execution_identity.json",
            {"adapter_unchanged": True, "environment_unchanged": True},
        ),
    ]:
        storage.write_json(directory / "experiment" / name, data)
    for name in ["packets", "optimizations", "preparations", "plant_segments", "command_requests"]:
        (directory / "experiment" / (name + ".jsonl")).write_text("")
    jobs.finalize(directory, "completed", note="SOFTWARE DISPLAY FIXTURE ONLY; no actual execution")
    return directory


def test_render_replay_steps_analysis_and_controlled_comparison(
    tmp_path, monkeypatch, native_probes
):
    a = render_fixture(tmp_path, monkeypatch, native_probes)
    b = render_fixture(tmp_path, monkeypatch, native_probes, "lateral_1")
    views = [scratch.read_run(p) for p in (a, b)]
    assert analysis.comparison(*views)["classification"].startswith("Controlled")
    app = AppTest.from_string(
        "from tools.apex_workbench.nmpc_scratch_panels import replay\n"
        "from pathlib import Path\nreplay(Path(" + repr(str(a)) + "))",
        default_timeout=45,
    ).run()
    assert not app.exception
    widget(app.button, "Next sample").click().run()
    assert not app.exception and widget(app.select_slider, "Native simulated sample").value == 1
    widget(app.select_slider, "Native simulated sample").set_value(2).run()
    assert widget(app.select_slider, "Native simulated sample").value == 2
    app = AppTest.from_string(
        "from tools.apex_workbench.nmpc_scratch_panels import analysis_panel\nanalysis_panel()",
        default_timeout=45,
    ).run()
    assert not app.exception and not app.error
    app = AppTest.from_string(
        "from tools.apex_workbench.nmpc_scratch_panels import compare_panel\ncompare_panel()",
        default_timeout=45,
    ).run()
    widget(app.multiselect, "Scratch experiments").set_value([a, b]).run()
    assert not app.exception and not app.error


def test_missing_corrupt_and_replaced_evidence_never_retains_analysis(
    tmp_path, monkeypatch, native_probes
):
    directory = render_fixture(tmp_path, monkeypatch, native_probes)
    view = scratch.read_run(directory)
    path = directory / "experiment/presentation.json"
    data = path.read_bytes()
    path.write_bytes(data.replace(b"0.02", b"0.03"))
    with pytest.raises(ValueError):
        scratch.current(view)
    with pytest.raises(ValueError):
        scratch.read_run(directory)
    path.write_bytes(data)
    (directory / "experiment/packets.jsonl").unlink()
    with pytest.raises((OSError, ValueError)):
        scratch.read_run(directory)


def test_actual_frozen_jacobian_gain_and_feedback_associations(tmp_path, native_probes):
    helper = ROOT / "tools/apex_workbench/tests/scratch_observer_check.py"
    result = subprocess.run(
        [sys.executable, "-I", "-B", str(helper)],
        text=True,
        capture_output=True,
        cwd=ROOT,
        timeout=60,
    )
    (tmp_path / "observer_stdout.json").write_text(result.stdout)
    (tmp_path / "observer_stderr.log").write_text(result.stderr)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["result"] == "PASS" and report["native_gain_rows"] == 80
    assert report["optimizer_solves"] == report["plant_steps"] == 0


def test_render_withdraws_stale_plots_after_same_size_replacement(
    tmp_path, monkeypatch, native_probes
):
    import os

    directory = render_fixture(tmp_path, monkeypatch, native_probes)
    current = scratch.current
    calls = []

    def replace_during_render(view):
        calls.append(True)
        if len(calls) == 3:  # read_run return, pre-render, then post-render check.
            path = directory / "experiment/presentation.json"
            stat = path.stat()
            path.write_bytes(path.read_bytes().replace(b"0.02", b"0.03"))
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        current(view)

    monkeypatch.setattr(scratch, "current", replace_during_render)
    app = AppTest.from_string(
        "from tools.apex_workbench.nmpc_scratch_panels import analysis_panel\nanalysis_panel()",
        default_timeout=45,
    ).run()
    assert not app.exception and any("quarantined" in e.value for e in app.error)
    assert not app.get("plotly_chart")


def test_anchor_never_adopts_artifact_replaced_after_ingestion(tmp_path, monkeypatch):
    # Same interleaving as the independently retained failed review; format fixture only.
    baseline = scratch.defaults()
    probes = (
        {
            "resolved": {
                "configuration": {"costs": baseline["costs"]},
                "effective": copy.deepcopy(baseline),
            }
        },
    )
    directory = render_fixture(tmp_path, monkeypatch, probes)
    path = directory / "experiment/presentation.json"
    original = storage.sha256
    replacements = []

    def replace_at_revalidation(selected):
        if selected == path and not replacements:
            data = path.read_bytes()
            changed = data.replace(b"0.02", b"0.03")
            assert len(changed) == len(data) and changed != data
            path.write_bytes(changed)
            replacements.append(True)
        return original(selected)

    monkeypatch.setattr(storage, "sha256", replace_at_revalidation)
    with pytest.raises(ValueError, match="changed|checksum"):
        view = scratch.read_run(directory)
        scratch.current(view)
    assert replacements == [True]
