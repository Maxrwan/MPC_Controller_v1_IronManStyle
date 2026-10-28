"""Focused software checks only. No three-grid scientific qualification campaign."""

import csv
import shutil
from copy import deepcopy
from dataclasses import asdict

import pytest

from tools.apex_workbench import comparison, configuration, jobs, plots, storage
from tools.apex_workbench import lab_configuration as contract
from tools.apex_workbench.dynamic_lab import PrescribedInputs, construct
from tools.apex_workbench.lab_evidence import read_record
from tools.apex_workbench.lab_reporting import summarize
from tools.apex_workbench.tests.test_corrections import finished, reseal_fixture
from tools.apex_workbench.worker import execute

# Literal accepted values, independent of adapter normalization/factory output.
BASE = dict(
    name="synthetic_dynamic_test_vehicle",
    mass=2.0,
    yaw_inertia=0.025,
    wheelbase=0.30,
    lf=0.15,
    lr=0.15,
    cg_height=0.04,
    vehicle_width=None,
    vehicle_length=None,
    front_cornering_stiffness=45.0,
    rear_cornering_stiffness=45.0,
    tire_road_friction_coefficient=1.0,
    maximum_steering_angle=0.4,
    maximum_steering_rate=None,
    maximum_acceleration=2.0,
    maximum_braking_deceleration=3.0,
    maximum_speed=6.0,
)


@pytest.mark.parametrize(
    "case,override,delta,fy,r_dot,vy_dot",
    [
        ("VDL1_BASE", {}, 0.020, 0.900, 5.40, 0.4500),
        ("VDL1_IZ_HIGH", {"yaw_inertia": 0.030}, 0.020, 0.900, 4.50, 0.4500),
        ("VDL1_STEER_HIGH", {}, 0.025, 1.125, 6.75, 0.5625),
        ("VDL1_CF_HIGH", {"front_cornering_stiffness": 54.0}, 0.020, 1.080, 6.48, 0.5400),
        ("VDL1_CR_HIGH", {"rear_cornering_stiffness": 54.0}, 0.020, 0.900, 5.40, 0.4500),
    ],
)
def test_literal_snapshots_canonical_components_and_immediate_oracles(
    case, override, delta, fy, r_dot, vy_dot
):
    from apex.config import load_vehicle_parameters
    from apex.models.tire.linear import LinearAxleTire
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer

    resolved = contract.resolve(contract.request_for(case))
    assert resolved["base_parameters"] == BASE
    assert resolved["effective_parameters"] == {**BASE, **override}
    assert resolved["parameter_overrides"] == override
    assert resolved["initial_state"] == [2.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert resolved["schedule"]["segments"] == [
        {"start_tick": 0, "delta_rad": 0.0, "a_cmd_m_per_s2": 0.0},
        {"start_tick": 20, "delta_rad": delta, "a_cmd_m_per_s2": 0.0},
    ]
    model = construct(resolved)
    assert type(model) is DynamicBicycle
    assert type(model.tire_model) is LinearAxleTire
    assert type(model.load_model) is QuasiStaticLongitudinalLoadTransfer
    assert model.force_allocation is None and model.v_dynamic_min == 0.5
    assert asdict(model.parameters) == {**BASE, **override}
    assert asdict(load_vehicle_parameters(configuration.ROOT / contract.VEHICLE_SOURCE)) == BASE
    d = model.diagnostics([2, 0, 0, 0, 0, 0], [delta, 0])
    dx = model.derivative([2, 0, 0, 0, 0, 0], [delta, 0])
    assert [d.fyf, d.fyr, d.fzf, d.fzr] == pytest.approx([fy, 0, 9.81, 9.81], abs=1e-12)
    assert dx[:3] == pytest.approx([0, vy_dot, r_dot], abs=1e-12)


@pytest.mark.parametrize(
    "key,value",
    [
        ("case_id", "VDL1_MASS_HIGH"),
        ("case_id", None),
        ("case_id", True),
        ("contract_id", "unknown"),
        ("runner_profile", "legacy"),
        ("grid_id", "half"),
        ("grid_id", "quarter"),
        ("treatment", "mass"),
        ("case_id", float("nan")),
    ],
)
def test_strict_registry_and_qualification_admission(key, value):
    with pytest.raises(ValueError):
        configuration.validate("dynamic_lab", {**contract.request_for(), key: value})


def test_snapshot_conflict_and_base_yaml_rejected():
    values = contract.request_for()
    with pytest.raises(ValueError):
        configuration.validate("dynamic_lab", {**values, "mass": 3})
    with pytest.raises(ValueError):
        contract.resolve(values, vehicle_yaml="mass: 2")
    resolved = contract.resolve(values)
    for key, value in [
        ("mass", True),
        ("yaw_inertia", 0.026),
        ("vehicle_width", 0),
        ("lf", 0.12),
        ("maximum_speed", None),
    ]:
        damaged = deepcopy(resolved)
        damaged["effective_parameters"][key] = value
        with pytest.raises(ValueError, match="conflicts"):
            contract.validate_resolved(values, damaged)
    assert contract.resolve(values) == resolved


@pytest.mark.parametrize("h,onset,steps", [(0.005, 20, 100), (0.0025, 40, 200), (0.00125, 80, 400)])
def test_integer_input_ticks_and_reset_without_simulation(h, onset, steps):
    schedule = dict(
        dt_plant_s=h,
        duration_ticks=steps,
        dt_input_ticks=1,
        segments=[
            dict(start_tick=0, delta_rad=0.0, a_cmd_m_per_s2=0.0),
            dict(start_tick=onset, delta_rad=0.02, a_cmd_m_per_s2=0.0),
        ],
    )
    provider = PrescribedInputs(schedule)
    for _ in range(2):
        provider.reset()
        for k in range(steps):
            assert provider.compute_control(None, {"time": k * h, "dt": h}) == [
                0.0 if k < onset else 0.02,
                0.0,
            ]
        with pytest.raises(ValueError):
            provider.compute_control(None, {"time": steps * h, "dt": h})
    provider.reset()
    with pytest.raises(ValueError, match="clock"):
        provider.compute_control(None, {"time": h, "dt": h})


@pytest.mark.parametrize("ticks", [[1], [0, 0], [0, 20, 10], [0, 20.5], [0, 100], [-1, 20]])
def test_bad_schedule_rejected_without_snapping(ticks):
    schedule = contract.resolve(contract.request_for())["schedule"]
    schedule["segments"] = [dict(start_tick=k, delta_rad=0.02, a_cmd_m_per_s2=0.0) for k in ticks]
    with pytest.raises(ValueError):
        PrescribedInputs(schedule)


def test_constant_provider_grammar_and_copy():
    schedule = contract.resolve(contract.request_for())["schedule"]
    schedule["segments"] = schedule["segments"][:1]
    provider = PrescribedInputs(schedule)
    schedule["segments"][0]["delta_rad"] = 0.4
    assert provider.compute_control(None, {"time": 0.0, "dt": 0.005}) == [0.0, 0.0]


def test_canonical_runner_and_diagnostic_byte_parity(tmp_path):
    from run_dynamic_bicycle_demo import synthetic_track

    from apex.config import load_vehicle_parameters
    from apex.coordinates.frenet import frenet_to_global
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.simulation.runner import RunConfig, SimulationRunner
    from apex.state import CONTROL_NAMES, STATE_NAMES

    class LiteralStep:
        def compute_control(self, state, context):
            return [0.0 if context["time"] < 0.100 else 0.020, 0.0]

    adapted, reference = tmp_path / "adapted", tmp_path / "reference"
    execute("dynamic_lab", contract.request_for(), adapted)
    p = load_vehicle_parameters(
        configuration.ROOT / "configs/vehicles/synthetic_dynamic_test_vehicle.yaml"
    )
    track = synthetic_track()
    model = DynamicBicycle(p, track, default_dt=0.005)
    result = SimulationRunner(
        model,
        LiteralStep(),
        track,
        RunConfig(
            duration=0.5,
            dt_plant=0.005,
            dt_control=0.005,
            target_laps=None,
            latency=None,
            stop_on_boundary=False,
        ),
    ).run([2.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    result.write_csv(reference)
    assert len(result.states) == 101 and len(result.controls) == 100
    rows = [
        {
            "time": row["time"],
            **asdict(
                model.diagnostics([row[k] for k in STATE_NAMES], [row[k] for k in CONTROL_NAMES])
            ),
        }
        for row in result.states
    ]
    with (reference / "diagnostics.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for name in ("states.csv", "controls.csv", "diagnostics.csv"):
        assert (adapted / name).read_bytes() == (reference / name).read_bytes()
    xy = list(csv.DictReader((adapted / "trajectory_xy.csv").open()))
    for observed, row in zip(xy, result.states):
        pose = frenet_to_global(track, row["s_abs"], row["e_y"], row["e_psi"])
        assert [float(observed[k]) for k in ("x", "y")] == [pose.x, pose.y]
    assert result.states[0]["vx"] == 2.0
    assert result.controls[19]["delta"] == 0.0 and result.controls[20]["delta"] == 0.020
    assert result.states[-1]["delta"] == 0.020 and result.controls[-1]["time"] == 0.495
    with pytest.raises(FileExistsError):
        execute("dynamic_lab", contract.request_for(), adapted)


@pytest.fixture(scope="module")
def lab_runs(tmp_path_factory):
    root = tmp_path_factory.mktemp("real-lab-workers")
    runs = []
    for case in ("VDL1_BASE", "VDL1_STEER_HIGH"):
        directory = jobs.start_run(
            "dynamic_lab",
            contract.request_for(case),
            "Software smoke only; no scientific qualification",
            runs=root,
        )
        status = finished(directory)
        assert status["state"] == "completed", (status, (directory / "stderr.log").read_text())
        runs.append(directory)
    return runs


def test_real_worker_candidate_and_csv_plots(lab_runs):
    record = read_record(lab_runs[0])
    assert record["summary"]["horizon_reached"]
    assert record["summary"]["numerical_qualification"] == "not_qualified"
    assert record["summary"]["qualification_record"] is None
    for paths in (lab_runs, list(reversed(lab_runs))):
        decision = comparison.eligibility(*paths)
        assert decision["classification"] == "controlled_candidate", decision
        assert decision["numerical_qualification"] == "not_qualified"
        assert decision["declared_treatment"]["key"] == "post_step_delta"
    figure = plots.series([("actual", lab_runs[0])], ["alpha_f"], "rad", source="diagnostics.csv")
    assert list(figure.data[0].y) == [r["alpha_f"] for r in record["diagnostics"]]
    assert plots.trajectory(lab_runs[0]).data


@pytest.mark.parametrize(
    "relative",
    [
        "experiment/controls.csv",
        "experiment/diagnostics.csv",
        "experiment/resolved_lab.json",
        "experiment/summary.json",
        "experiment/telemetry_contract.json",
        "experiment/geometry.csv",
        "experiment/trajectory_xy.csv",
        "execution.json",
        "worker.json",
        "supervisor.json",
        "numerical_environment.json",
    ],
)
def test_missing_lab_evidence_blocks_state_only_display(lab_runs, tmp_path, relative):
    damaged = tmp_path / "damaged"
    shutil.copytree(lab_runs[0], damaged)
    (damaged / relative).unlink()
    with pytest.raises(storage.IntegrityError):
        plots.read_frame(damaged, "states.csv")
    assert comparison.eligibility(damaged, lab_runs[1])["classification"] == "invalid"


@pytest.mark.parametrize(
    "relative",
    ["experiment/diagnostics.csv", "experiment/resolved_lab.json", "experiment/controls.csv"],
)
def test_changed_lab_bytes_quarantined(lab_runs, tmp_path, relative):
    damaged = tmp_path / "changed"
    shutil.copytree(lab_runs[0], damaged)
    with (damaged / relative).open("a") as stream:
        stream.write("changed bytes\n")
    with pytest.raises(storage.IntegrityError):
        plots.read_frame(damaged, "states.csv")


def test_false_qualification_extra_changes_and_source_mismatch(lab_runs, tmp_path):
    damaged = tmp_path / "false-qualification"
    shutil.copytree(lab_runs[0], damaged)
    for name in ("experiment/summary.json", "worker_result.json"):
        summary = storage.read_json(damaged / name)
        summary["numerical_qualification"] = "grid-qualified"
        storage.write_json(damaged / name, summary)
    reseal_fixture(damaged)  # Deliberately rebound disposable test fixture, never a real run.
    assert comparison.eligibility(damaged, lab_runs[1])["classification"] == "invalid"
    source = tmp_path / "source-change"
    shutil.copytree(lab_runs[1], source)
    request = storage.read_json(source / "request.json")
    request["provenance"]["source_sha256"]["tools/apex_workbench/dynamic_lab.py"] = "0" * 64
    storage.write_json(source / "request.json", request)
    reseal_fixture(source)
    assert comparison.eligibility(lab_runs[0], source)["classification"] == "illustrative"
    request["lab_resolved"]["initial_state"][1] = 0.1
    storage.write_json(source / "request.json", request)
    reseal_fixture(source)
    assert comparison.eligibility(lab_runs[0], source)["classification"] == "invalid"


def test_handled_canonical_failure_retains_partial_without_terminal(tmp_path, monkeypatch):
    from apex.models.errors import ModelValidationError
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle

    def fail(self, state, action, dt):
        raise ModelValidationError("injected software failure; no physical claim")

    monkeypatch.setattr(DynamicBicycle, "step", fail)
    summary = execute("dynamic_lab", contract.request_for(), tmp_path / "partial")
    assert not summary["horizon_reached"] and summary["state_rows"] == 1
    assert "injected software failure" in summary["failure"]
    assert summary["numerical_qualification"] == "invalid_or_incomplete"
    assert (tmp_path / "partial/states.csv").read_text().count("\n") == 2


def test_real_worker_rejects_conflicting_snapshot_before_physics(lab_runs, tmp_path):
    failed = tmp_path / "failed"
    failed.mkdir()
    request = storage.read_json(lab_runs[0] / "request.json")
    request["lab_resolved"]["effective_parameters"]["mass"] = 3.0
    jobs.write_json(failed / "request.json", request)
    jobs.supervise(failed)
    assert storage.read_status(failed)["scientific_outcome"] == "failed"
    assert storage.artifact_json(failed, "execution.json")["scientific_outcome"] == "failed"
    assert "snapshot conflicts" in (failed / "stderr.log").read_text()
    assert not (failed / "experiment/states.csv").exists()


def test_model_window_filters_never_qualify_numerics(lab_runs):
    record = read_record(lab_runs[0])
    for key, value in (("alpha_f", 0.051), ("front_lateral_utilization", 1.01)):
        diagnostics = deepcopy(record["diagnostics"])
        diagnostics[0][key] = value  # Synthetic reporting input, not a simulated trajectory.
        summary = summarize(record["states"], diagnostics, "duration", None)
        assert summary["sampled_model_window"]["status"] == "outside_window"
        assert summary["numerical_qualification"] == "not_qualified"


def test_lab_ui_retained_outputs_and_comparison(lab_runs, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(configuration, "RUNS", lab_runs[0].parent)
    app = AppTest.from_file(
        str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=30
    ).run()
    next(box for box in app.selectbox if box.label == "Experiment").select("dynamic_lab").run()
    assert not app.exception
    assert not app.number_input
    assert any(box.label == "Synthetic laboratory case" for box in app.selectbox)
    assert app.get("plotly_chart")
    assert any("not_qualified" in item.value for item in app.caption)
    app.radio[0].set_value("Compare runs").run()
    app.multiselect[0].set_value([p.name for p in lab_runs]).run()
    assert not app.exception and not app.error
    assert any("Controlled candidate" in item.value for item in app.info)


@pytest.mark.parametrize("artifact", ["numerical_environment.json", "request.json"])
def test_incomplete_numerical_identity_cannot_be_candidate(lab_runs, tmp_path, artifact):
    damaged = tmp_path / "incomplete"
    shutil.copytree(lab_runs[0], damaged)
    value = storage.read_json(damaged / artifact)
    if artifact == "request.json":
        value["provenance"]["packages"].pop("numpy")
    else:
        value = {}
    storage.write_json(damaged / artifact, value)
    reseal_fixture(damaged)
    assert comparison.eligibility(damaged, lab_runs[1])["classification"] == "invalid"


def test_actual_lab_form_submission(lab_runs, monkeypatch):
    from streamlit.testing.v1 import AppTest

    original_start = jobs.start_run
    monkeypatch.setattr(configuration, "RUNS", lab_runs[0].parent)
    launched = []

    def start(adapter, values, prediction):
        directory = original_start(adapter, values, prediction, runs=lab_runs[0].parent)
        launched.append(directory)
        return directory

    monkeypatch.setattr(jobs, "start_run", start)
    app = AppTest.from_file(
        str(configuration.ROOT / "tools/apex_workbench/app.py"), default_timeout=30
    ).run()
    next(box for box in app.selectbox if box.label == "Experiment").select("dynamic_lab").run()
    next(button for button in app.button if button.label == "Run experiment").click().run()
    assert not app.exception and len(launched) == 1
    assert finished(launched[0])["state"] == "completed"
    app.run()
    assert not app.exception and not app.error and app.get("plotly_chart")
    assert read_record(launched[0])["request"]["effective"]["case_id"] == "VDL1_BASE"
