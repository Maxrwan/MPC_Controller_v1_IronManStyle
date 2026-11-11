"""Approved failed-capture inspection only: no model, controller, probe or simulation execution."""

import copy
import hashlib
import json
import shutil
from decimal import Decimal
from fractions import Fraction

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import nmpc_analysis, storage
from tools.apex_workbench.lap import admission, analysis, config, evidence, ui_data

ORIGINAL = config.RUNS / evidence.FAILED_NATIVE_RECOVERY[0]


@pytest.mark.parametrize("scalar", [int, float, np.float16, np.float32, np.float64])
def test_native_lap_scalars_are_finite_positive_and_json_serializable(scalar):
    value = scalar(31.1719003976093)
    result = analysis.laps({"lap_times": [scalar(1), value]}, 100)
    assert result["lap_time_s"] == float(value)
    assert json.loads(json.dumps(result, allow_nan=False))["lap_time_s"] == float(value)
    assert type(result["lap_time_s"]) in (int, float)
    # Global JSON-only validation retains its original exact-type rule.
    assert nmpc_analysis.numeric(np.float64(1)) is False


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        np.bool_(True),
        "1",
        [1],
        np.array(1.0),
        np.array([1.0]),
        Decimal("1"),
        Fraction(1),
        complex(1),
        np.int64(1),
        np.longdouble(1),
        0,
        -1,
        0.0,
        -0.0,
        float("nan"),
        float("inf"),
        -float("inf"),
        np.float64(0),
        np.float64(-1),
        np.float64("nan"),
        np.float64("inf"),
        np.float32("nan"),
        np.float16("inf"),
    ],
)
def test_invalid_lap_scalar_is_rejected(value):
    with pytest.raises(ValueError, match="Invalid native lap-crossing interval"):
        analysis.laps({"lap_times": [value]}, 100)


@pytest.fixture(scope="module")
def recovered():
    return ui_data.read({"family": "V2", "directory": ORIGINAL})


def test_original_recovery_exact_observations_and_absent_summary(recovered):
    before = {name: storage.sha256(ORIGINAL / name) for name in recovered["anchor"]}
    assert recovered["status"]["state"] == recovered["status"]["scientific_outcome"] == "failed"
    assert recovered["status"]["evidence_state"] == "valid"
    assert recovered["status"]["returncode"] == 2
    assert "summary" not in recovered and not (ORIGINAL / "summary.json").exists()
    assert len(recovered["anchor"]) == 41  # 39 manifest members plus status and manifest.
    assert recovered["raw"]["stop_reason"] == "target_laps"
    assert recovered["raw"]["end_time"] == pytest.approx(62.235)
    metrics = analysis.metrics(recovered)
    assert metrics["recovery"]["mode"] == "failed-native-read-only"
    assert metrics["lap"]["native_crossings"][0]["time_s"] == 31.061572635639408
    assert metrics["lap"]["native_crossings"][0]["complete_circuit"] is False
    assert metrics["lap"]["lap_time_s"] == 31.1719003976093
    assert (
        analysis.laps(
            {"lap_times": list(map(np.float64, recovered["raw"]["lap_times"]))}, 154.76345492731022
        )["lap_time_s"]
        == 31.1719003976093
    )
    sectors = analysis.sectors(recovered, evidence.rows(recovered, "segments", "journal"))
    assert [r["time_s"] for r in sectors["rows"]] == pytest.approx(
        [8.625144717830757, 7.023554059383791, 7.981099618438272, 7.542102001956479]
    )
    start, end = [r["time_s"] for r in metrics["lap"]["native_crossings"]]
    errors = [
        r["racing_error_y_m"]
        for r in recovered["presentation"]["states"]
        if start <= r["time"] < end
    ]
    assert len(errors) == 6234
    assert nmpc_analysis.summary(errors)["rms"] == pytest.approx(0.02095028863796588)
    assert metrics["complete_circuit_lateral_error_m"]["samples"] == 6234
    assert metrics["complete_circuit_lateral_error_m"]["rms"] == pytest.approx(0.02095028863796588)
    assert metrics["successful_native_preparations"] == metrics["preparation_count"] == 623
    assert before == {name: storage.sha256(ORIGINAL / name) for name in recovered["anchor"]}
    with pytest.raises(ValueError, match="summary.json"):
        evidence.read_run(ORIGINAL)  # Strict ingestion does not silently opt into recovery.


@pytest.fixture
def disposable(tmp_path, monkeypatch):
    # Exact byte copy is a negative-test fixture, not a new execution or catalog alias.
    target = tmp_path / "runs" / ORIGINAL.name
    shutil.copytree(ORIGINAL, target)
    monkeypatch.setattr(config, "OUTPUT", tmp_path)
    monkeypatch.setattr(config, "RUNS", tmp_path / "runs")
    return target


@pytest.mark.parametrize(
    "fault", ["native", "derived", "missing", "manifest", "status", "extra", "reseal"]
)
def test_recovery_rejects_changed_incomplete_and_resealed_evidence(disposable, fault):
    p = disposable
    if fault == "native":
        next((p / "native").glob("states-*")).write_text("{}\n")
    elif fault == "derived":
        (p / "presentation.json").write_text("{}")
    elif fault == "missing":
        (p / "post_identity.json").unlink()
    elif fault == "manifest":
        (p / "artifacts.json").write_text("{}")
    elif fault == "status":
        state = storage.read_json(p / "status.json")
        state["returncode"] = 0
        storage.write_json(p / "status.json", state)
    elif fault == "extra":
        storage.write_json(p / "summary.json", {"coverage_completed": True})
    else:
        # An attacker-consistent manifest/status still cannot acquire approved capture identity.
        native = storage.read_json(p / "native.json")
        native["states"]["rows"] -= 1
        storage.write_json(p / "native.json", native)
        manifest = storage.read_json(p / "artifacts.json")
        manifest["native.json"] = {
            "bytes": (p / "native.json").stat().st_size,
            "sha256": storage.sha256(p / "native.json"),
        }
        storage.write_json(p / "artifacts.json", manifest)
        state = storage.read_json(p / "status.json")
        state["manifest_sha256"] = storage.sha256(p / "artifacts.json")
        storage.write_json(p / "status.json", state)
    with pytest.raises((ValueError, OSError)):
        evidence.read_run(p, recover_failed=True)


@pytest.mark.parametrize("fault", ["artifact", "missing", "new_summary"])
def test_recovery_epoch_rejects_replacement_after_read(disposable, fault):
    view = evidence.read_run(disposable, recover_failed=True)
    if fault == "artifact":
        (disposable / "presentation.json").write_text("{}")
    elif fault == "missing":
        (disposable / "post_identity.json").unlink()
    else:
        (disposable / "summary.json").write_text("{}")
    with pytest.raises((ValueError, OSError)):
        evidence.current(view)


def test_failed_native_circuit_cannot_be_controlled_or_accepted(recovered, monkeypatch):
    assert analysis.comparison(recovered, recovered)["classification"].startswith("Noncontrolled")
    other = copy.deepcopy(recovered)
    other.pop("recovery")
    other["summary"] = {"coverage_completed": True}
    assert analysis.comparison(other, other)["classification"].startswith("Noncontrolled")
    policy = config.OUTPUT / "access.json"
    before = hashlib.sha256(policy.read_bytes()).hexdigest()
    # Isolate lifecycle admission from the separately tested stale-source/default-reader gates.
    # Pass the genuine verified failed view, without changing production policy or archive bytes.
    monkeypatch.setattr(admission, "reviewed_source", lambda _: "software-test-source")
    monkeypatch.setattr(admission.evidence, "read_run", lambda _: recovered)
    with pytest.raises(ValueError, match="genuine successful full-lap outcome"):
        admission.acceptance_proposal(ORIGINAL)
    assert hashlib.sha256(policy.read_bytes()).hexdigest() == before


def test_actual_ui_recovery_is_explicit_and_labels_metrics():
    app = AppTest.from_string(
        "from tools.apex_workbench.lap import ui_views,ui_data,analysis\n"
        "import streamlit as st\n"
        f"r=next(r for r in ui_data.recordings('V2') if r['directory'].name=={ORIGINAL.name!r})\n"
        "ui_views.guarded([r], lambda vs: st.json(analysis.metrics(vs[0])))\n"
    ).run(timeout=20)
    assert not app.exception and not app.error
    assert any(
        "descriptive observations from a failed Workbench run" in w.value for w in app.warning
    )
    assert "failed-native-read-only" in app.json[0].value
