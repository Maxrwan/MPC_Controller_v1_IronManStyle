"""Actual workspace routes and retained viewers; no experimental execution before the gate."""

import copy
import hashlib
import os
import shutil
from dataclasses import replace

import pytest
from streamlit.testing.v1 import AppTest

from tools.apex_workbench import jobs, run_catalog, storage
from tools.apex_workbench import nmpc_weight_lab as lab
from tools.apex_workbench import nmpc_weight_panels as panels
from tools.apex_workbench.configuration import ADAPTERS, ROOT
from tools.apex_workbench.tests.test_nmpc_weight_lab import (  # noqa: F401
    fixture_run,
    preflights,
    successor_authority_fixture,
)


def widget(items, label):
    return next(i for i in items if i.label == label)


def application(monkeypatch, tmp_path):
    monkeypatch.setattr(run_catalog, "OWNED_ROOT", tmp_path / "owned")
    monkeypatch.setattr(lab, "OUTPUT", tmp_path / "m0")
    monkeypatch.setattr(lab, "RUNS", tmp_path / "m0/runs")

    def forbidden(*args, **kwargs):
        raise AssertionError("UI test must not execute a controller")

    monkeypatch.setattr(jobs, "start_run", forbidden)
    return AppTest.from_file(
        str(ROOT / "tools/apex_workbench/workspace.py"), default_timeout=45
    ).run()


def test_m0_configuration_gate_and_no_implicit_execution(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Open experimental NMPC Weight Lab M0").click().run()
    assert not app.exception
    assert widget(app.selectbox, "Execution mode").value == "nmpc_weight_lab"
    assert any("EXPERIMENTAL / UNQUALIFIED" in e.value for e in app.warning)
    assert widget(app.button, "Run one authorized M0 attempt").disabled
    widget(app.selectbox, "M0 preset").select("exploratory").run()
    assert not app.exception and widget(app.button, "Run one authorized M0 attempt").disabled
    assert any("100.0" in e.value for e in app.markdown)


def test_repeated_preview_actions_preserve_sealed_evidence(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    protected = [
        "authorizations/" + lab.SUCCESSOR + "/" + name
        for name in (
            "exploratory_software_probe.json",
            "nominal_software_probe.json",
            "software_gate.json",
            "authorization.json",
            "claims/nominal.json",
            "claims/exploratory.json",
            "corrective_review.json",
        )
    ] + [
        "BLOCKED.json",
        "claims/nominal.json",
        "software_gate.json",
        "runs/original_failed/status.json",
        "runs/native_nominal/manifest.json",
        "runs/native_nominal/experiment/raw.json",
        "runs/native_exploratory/manifest.json",
        "runs/native_exploratory/experiment/raw.json",
        "verification_20261103/blocking_evidence.json",
    ]
    for name in protected:
        path = lab.OUTPUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        storage.write_json(path, {"sealed_fixture": name})
    before = {name: (lab.OUTPUT / name).read_bytes() for name in protected}
    reports = []

    def preview_only(preset):
        # Intentionally vary member ordering; no scientific probe/controller is constructed.
        keys = ("a", "b") if len(reports) % 2 else ("b", "a")
        report = {"preset": preset, "imports": dict.fromkeys(keys, "software fixture")}
        reports.append(report)
        return report

    monkeypatch.setattr(lab, "probe", preview_only)
    widget(app.button, "Open experimental NMPC Weight Lab M0").click().run()
    for preset in ("exploratory", "exploratory", "nominal", "nominal"):
        widget(app.selectbox, "M0 preset").select(preset).run()
        widget(app.button, "Validate frozen configuration (no solve)").click().run()
        assert not app.exception and not app.error
        path = panels.preview_path(preset)
        assert path == lab.OUTPUT / "previews" / lab.SUCCESSOR / (preset + ".json")
        assert storage.read_json(path) == reports[-1]
        assert any("non-authoritative" in e.value for e in app.caption)
        assert widget(app.button, "Run one authorized M0 attempt").disabled
        assert {name: (lab.OUTPUT / name).read_bytes() for name in protected} == before
    assert len(reports) == 4
    assert not list((lab.OUTPUT / "previews").rglob(".pending-*"))


@pytest.mark.parametrize("link", ["previews", "namespace", "file"])
def test_preview_rejects_linked_destinations(monkeypatch, tmp_path, link):
    monkeypatch.setattr(lab, "OUTPUT", tmp_path / "m0")
    sealed = lab.authority_root() / "nominal_software_probe.json"
    sealed.parent.mkdir(parents=True)
    storage.write_json(sealed, {"sealed": True})
    before = sealed.read_bytes()
    path = lab.OUTPUT / "previews"
    if link == "namespace":
        path.mkdir()
        path = path / lab.SUCCESSOR
    elif link == "file":
        path = path / lab.SUCCESSOR / "nominal.json"
        path.parent.mkdir(parents=True)
    path.symlink_to(sealed if link == "file" else sealed.parent)
    with pytest.raises(ValueError, match="Unsafe M0"):
        panels.publish_preview("nominal", {"mutable": True})
    assert sealed.read_bytes() == before


def test_preview_rejects_unknown_preset(monkeypatch, tmp_path):
    monkeypatch.setattr(lab, "OUTPUT", tmp_path / "m0")
    with pytest.raises(ValueError, match="M0 accepts only"):
        panels.publish_preview("../../authorizations", {})
    assert not lab.OUTPUT.exists()


def test_preview_atomic_replace_and_failed_write_preserve_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(lab, "OUTPUT", tmp_path / "m0")
    sealed = lab.authority_root() / "nominal_software_probe.json"
    sealed.parent.mkdir(parents=True)
    storage.write_json(sealed, {"sealed": True})
    before = sealed.read_bytes()
    preview = panels.preview_path("nominal")
    preview.parent.mkdir(parents=True)
    os.link(sealed, preview)
    panels.publish_preview("nominal", {"mutable": True})
    assert sealed.read_bytes() == before
    assert storage.read_json(preview) == {"mutable": True}
    published = preview.read_bytes()
    with pytest.raises(ValueError):
        panels.publish_preview("nominal", {"nonfinite": float("nan")})
    assert preview.read_bytes() == published
    assert sealed.read_bytes() == before
    assert not list(preview.parent.glob(".pending-*"))


@pytest.mark.parametrize("swap_at", ["directory_open", "temporary_open", "replace"])
def test_preview_directory_swap_cannot_redirect_to_sealed_claim(monkeypatch, tmp_path, swap_at):
    monkeypatch.setattr(lab, "OUTPUT", tmp_path / "m0")
    sealed = lab.authority_root() / "claims/nominal.json"
    sealed.parent.mkdir(parents=True)
    storage.write_json(sealed, {"sealed_claim": "must stay unchanged"})
    before = sealed.read_bytes()
    preview = panels.preview_path("nominal")
    preview.parent.mkdir(parents=True)
    moved = preview.parent.with_name("detached_preview_namespace")
    swapped = []

    def swap():
        preview.parent.rename(moved)
        preview.parent.symlink_to(sealed.parent, target_is_directory=True)
        swapped.append(True)

    original_open, original_replace = os.open, os.replace

    def swap_open(name, flags, *args, **kwargs):
        if not swapped and (
            (swap_at == "directory_open" and name == lab.SUCCESSOR and flags & os.O_DIRECTORY)
            or (swap_at == "temporary_open" and str(name).startswith(".pending-"))
        ):
            swap()
        return original_open(name, flags, *args, **kwargs)

    def swap_replace(*args, **kwargs):
        if swap_at == "replace" and not swapped:
            swap()
        return original_replace(*args, **kwargs)

    monkeypatch.setattr(panels.os, "open", swap_open)
    monkeypatch.setattr(panels.os, "replace", swap_replace)
    with pytest.raises((OSError, ValueError)):
        panels.publish_preview("nominal", {"mutable": "must never reach sealed claim"})
    assert swapped == [True]
    assert sealed.read_bytes() == before
    assert list(sealed.parent.iterdir()) == [sealed]
    assert not list(moved.glob(".pending-*"))
    if swap_at != "directory_open":
        assert storage.read_json(moved / "nominal.json") == {
            "mutable": "must never reach sealed claim"
        }


def test_preview_does_not_bypass_strict_evidence_or_source_gate(tmp_path, monkeypatch):
    root, gate, review, _ = successor_authority_fixture(tmp_path, monkeypatch)
    # Seal one disposable fixture evidence file; never reseal actual retained authority.
    sealed = root / "nominal_software_probe.json"
    storage.write_json(sealed, {"fixture": "original"})
    gate["evidence_sha256"] = {str(sealed.relative_to(lab.OUTPUT)): storage.sha256(sealed)}
    storage.write_json(root / "software_gate.json", gate)
    review["software_gate_sha256"] = storage.sha256(root / "software_gate.json")
    storage.write_json(root / "corrective_review.json", review)
    authority = storage.read_json(root / "authorization.json")
    authority["corrective_review_sha256"] = storage.sha256(root / "corrective_review.json")
    storage.write_json(root / "authorization.json", authority)
    assert lab.verify_gate(check_environment=False) == gate
    panels.publish_preview("nominal", {"fixture": "changed preview"})
    assert lab.verify_gate(check_environment=False) == gate
    original = sealed.read_bytes()
    storage.write_json(sealed, {"fixture": "changed sealed evidence"})
    with pytest.raises(ValueError, match="Software gate evidence changed"):
        lab.verify_gate(check_environment=False)
    sealed.write_bytes(original)
    changed = dict(lab.adapter_hashes())
    changed["tools/apex_workbench/nmpc_weight_panels.py"] = "0" * 64
    monkeypatch.setattr(lab, "adapter_hashes", lambda: changed)
    with pytest.raises(ValueError):
        lab.verify_gate(check_environment=False)


def test_existing_legacy_forms_and_lab_stay_available(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.radio, "Workspace").set_value("Run").run()
    for name in ["dynamic_demo", "lqr_baseline", "dynamic_lab"]:
        widget(app.selectbox, "Execution mode").select(name).run()
        assert not app.exception
        assert widget(app.button, "Start run")
    assert set(ADAPTERS) == {
        "dynamic_demo",
        "lqr_baseline",
        "dynamic_lab",
        "nmpc_weight_lab",
        "nmpc_scratch",
    }


def test_original_P_and_C0_viewers_use_readonly_original_evidence(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.button, "Inspect retained Performance P GP archive").click().run()
    assert not app.exception and not app.error
    assert any("Verified retained P/VIS-1R" in e.value for e in app.success)
    widget(app.radio, "Workspace").set_value("Home").run()
    widget(app.button, "Inspect retained C0 descriptive-only archive").click().run()
    assert not app.exception and not app.error
    assert any("SOURCE UNVERIFIED" in e.value for e in app.warning)
    assert len(app.table) == 3 and not app.dataframe and not app.json and not app.code


def test_m0_compare_separate_from_qualified_comparison(monkeypatch, tmp_path):
    app = application(monkeypatch, tmp_path)
    widget(app.radio, "Workspace").set_value("Compare").run()
    widget(app.radio, "Comparison source").set_value("NMPC Weight Lab M0 (unqualified)").run()
    assert not app.exception
    assert any("EXPERIMENTAL / UNQUALIFIED" in e.value for e in app.warning)
    assert widget(app.multiselect, "M0 retained attempts").options == []
    assert not app.success


def test_comparison_requires_exact_non_treatment_identity(preflights):  # noqa: F811
    a = {
        "request": {
            "run_id": "fixture_nominal",
            "effective": {"preset": "nominal"},
            "nmpc_capture": {"resolved": preflights["nominal"]["resolved"]},
        }
    }
    b = {
        "request": {
            "run_id": "fixture_exploratory",
            "effective": {"preset": "exploratory"},
            "nmpc_capture": {"resolved": preflights["exploratory"]["resolved"]},
        }
    }
    assert "unqualified" in panels.comparison(a, b)
    altered = copy.deepcopy(b)
    altered["request"]["nmpc_capture"]["resolved"]["vehicle"]["mass"] += 1
    with pytest.raises(ValueError):
        panels.comparison(a, altered)
    with pytest.raises(ValueError):
        panels.comparison(a, a)


def test_native_plot_clocks_and_missingness_are_not_reconstructed():
    raw = {
        "states": [{"time": 0.0, "e_y": 0.1}, {"time": 0.005, "e_y": 0.2}],
        "controls": [
            {"time": 0.0, "application_time": 0.005, "requested_delta": 0.1, "delta": 0.2}
        ],
    }
    state = panels.signal(raw, "e_y")
    control = panels.commands(raw)
    assert list(state.data[0].x) == [0.0, 0.005] and state.data[0].mode == "markers"
    assert list(control.data[0].x) == [0.0] and list(control.data[1].x) == [0.005]
    assert list(control.data[0].y) == [0.1] and list(control.data[1].y) == [0.2]
    raw["controls"][0]["application_time"] = None
    assert len(panels.commands(raw).data[1].x) == 0
    assert lab.descriptive_metrics(None) == {"state_samples": 0, "coverage": "unavailable"}


def test_cancel_request_is_owned_marker_and_retains_partial_bytes(tmp_path, monkeypatch):
    directory = tmp_path / "fixture_cancel"
    directory.mkdir()
    (directory / "partial.jsonl").write_text('{"retained":true}\n')
    monkeypatch.setattr(jobs, "status_for", lambda directory: {"state": "running"})
    jobs.cancel_run(directory)
    assert (directory / "cancel.request").exists()
    assert (directory / "partial.jsonl").read_text() == '{"retained":true}\n'


def owned_fixture(tmp_path, monkeypatch, preflights):  # noqa: F811
    directory = fixture_run(tmp_path, preflights)
    monkeypatch.setattr(lab, "OUTPUT", tmp_path)
    monkeypatch.setattr(lab, "RUNS", tmp_path / "runs")
    storage.write_json(tmp_path / "BLOCKED.json", {"software_fixture_original_block": True})
    monkeypatch.setattr(
        lab,
        "ORIGINAL_ANCHORS",
        {
            "software_gate.json": storage.sha256(tmp_path / "software_gate.json"),
            "claims/nominal.json": storage.sha256(tmp_path / "claims/nominal.json"),
            "BLOCKED.json": storage.sha256(tmp_path / "BLOCKED.json"),
        },
    )
    catalog = run_catalog.discover(
        owned_root=tmp_path / "legacy", qualification_root=tmp_path / "none", include_nmpc=True
    )
    return directory, catalog.runs[0], catalog


@pytest.mark.parametrize(
    "fault",
    [
        "foreign_root",
        "archive",
        "symlink_directory",
        "symlink_request",
        "alias",
        "conflict",
        "selected_id",
        "selected_adapter",
        "request_adapter",
        "case",
        "claim",
        "original_claim_rebind",
        "original_claim_extra",
        "captured_adapter",
        "captured_source",
        "captured_config",
        "captured_environment",
        "symlink_status",
        "symlink_worker",
        "symlink_supervisor",
        "symlink_execution",
        "symlink_manifest",
        "symlink_nested",
    ],
)
def test_invalid_inspection_never_reaches_lifecycle(
    tmp_path,
    monkeypatch,
    preflights,  # noqa: F811
    fault,
):
    directory, selected, _ = owned_fixture(tmp_path, monkeypatch, preflights)
    if fault == "foreign_root":
        selected = replace(selected, directory=tmp_path / "legacy" / directory.name)
    elif fault == "archive":
        selected = replace(selected, origins=("qualification archive",))
    elif fault == "symlink_directory":
        link = directory.parent / "linked"
        link.symlink_to(directory, target_is_directory=True)
        selected = replace(selected, directory=link)
    elif fault == "symlink_request":
        original = directory / "request.json"
        other = directory / "saved_request.json"
        original.rename(other)
        original.symlink_to(other)
    elif fault == "alias":
        selected = replace(selected, aliases=(directory, tmp_path / "copy"))
    elif fault == "conflict":
        selected = replace(selected, conflict=True)
    elif fault == "selected_id":
        selected = replace(selected, run_id="forged")
    elif fault == "selected_adapter":
        selected = replace(selected, adapter="dynamic_lab")
    elif fault == "request_adapter":
        request = storage.read_json(directory / "request.json")
        storage.write_json(directory / "request.json", dict(request, adapter="dynamic_lab"))
    elif fault == "case":
        selected = replace(selected, case="exploratory")
    elif fault == "claim":
        storage.write_json(tmp_path / "claims/nominal.json", {"run_id": "forged"})
    elif fault in {"original_claim_rebind", "original_claim_extra"}:
        claim = storage.read_json(tmp_path / "claims/nominal.json")
        if fault == "original_claim_rebind":
            copied = directory.with_name("copied_original_identity")
            shutil.copytree(directory, copied)
            request = storage.read_json(copied / "request.json")
            storage.write_json(copied / "request.json", dict(request, run_id=copied.name))
            claim["run_id"] = copied.name
            selected = replace(
                selected,
                directory=copied,
                aliases=(copied,),
                run_id=copied.name,
                key="run-" + hashlib.sha256(("id:" + copied.name).encode()).hexdigest()[:20],
            )
        else:
            claim["unsupported_extra"] = "changed original bytes"
        storage.write_json(tmp_path / "claims/nominal.json", claim)
    elif fault.startswith("captured_"):
        request = storage.read_json(directory / "request.json")
        captured = request["nmpc_capture"]
        if fault == "captured_adapter":
            captured["adapter_sha256"][lab.PRODUCERS[0]] = "0" * 64
        elif fault == "captured_source":
            captured["source_sha256"][next(iter(captured["source_sha256"]))] = "0" * 64
        elif fault == "captured_config":
            captured["resolved"]["vehicle"]["mass"] += 1
        else:
            captured["environment"]["python"] = "forged"
        storage.write_json(directory / "request.json", request)
    elif fault.startswith("symlink_"):
        name = {
            "status": "status.json",
            "worker": "worker.json",
            "supervisor": "supervisor.json",
            "execution": "execution.json",
            "manifest": "artifacts.json",
            "nested": "experiment/plant_segments.jsonl",
        }[fault.removeprefix("symlink_")]
        path = directory / name
        other = tmp_path / ("outside_" + path.name)
        path.rename(other)
        path.symlink_to(other)
    # Compare every fixture byte and prohibit all potentially mutating entry points.
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid M0 inspection reached a lifecycle mutation path")

    for name in ("status_for", "cancel_run", "_reconcile_locked", "finalize"):
        monkeypatch.setattr(jobs, name, forbidden)
    panels.inspect(selected)
    after = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after


def test_actual_workspace_quarantines_forged_archive_route(tmp_path, monkeypatch, preflights):  # noqa: F811
    _, selected, catalog = owned_fixture(tmp_path, monkeypatch, preflights)
    selected = replace(selected, origins=("qualification archive",), state="running")
    monkeypatch.setattr(
        run_catalog, "discover", lambda **kwargs: replace(catalog, runs=(selected,))
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Forged archive reached lifecycle from actual workspace")

    monkeypatch.setattr(jobs, "status_for", forbidden)
    app = AppTest.from_file(
        str(ROOT / "tools/apex_workbench/workspace.py"), default_timeout=45
    ).run()
    widget(app.radio, "Workspace").set_value("Inspect").run()
    assert not app.exception
    assert any("quarantined" in e.value for e in app.error)
    assert not any("Cancel M0" in b.label for b in app.button)


def test_owned_active_refresh_and_cancel_keep_partial_bytes(tmp_path, monkeypatch, preflights):  # noqa: F811
    directory, selected, _ = owned_fixture(tmp_path, monkeypatch, preflights)
    events = []

    def active(path):
        assert path == directory
        events.append("status")
        return {"state": "running", "evidence_state": "pending"}

    monkeypatch.setattr(jobs, "status_for", active)
    monkeypatch.setattr(panels.st, "button", lambda label: label == "Cancel M0 owned run")
    monkeypatch.setattr(panels.st, "rerun", lambda: events.append("rerun"))
    before = (directory / "experiment/plant_segments.jsonl").read_bytes()
    panels.inspect(selected)
    assert (directory / "cancel.request").exists()
    assert (directory / "experiment/plant_segments.jsonl").read_bytes() == before
    assert events == ["status", "status", "rerun"]


@pytest.mark.parametrize(
    "fault", ["gate_config", "gate_environment", "gate_id", "claim_rebind", "claim_extra"]
)
def test_successor_rebinding_never_reaches_lifecycle(tmp_path, monkeypatch, preflights, fault):  # noqa: F811
    root, gate, _, _ = successor_authority_fixture(tmp_path, monkeypatch, preflights)
    monkeypatch.setattr(lab, "RUNS", tmp_path / "runs")
    run_id = gate["run_ids"]["nominal"]
    directory = lab.RUNS / run_id
    directory.mkdir(parents=True)
    lab.claim("nominal", run_id, captured=True)
    captured = {
        "source": lab.SOURCE,
        "profile_sha256": lab.PROFILE_SHA,
        "runtime": str(lab.RUNTIME),
        "source_sha256": lab.source_hashes(),
        "adapter_sha256": gate["adapter_sha256"],
        "environment": copy.deepcopy(gate["environment"]),
        "resolved": copy.deepcopy(gate["resolved_snapshots"]["nominal"]),
        "authorization_id": lab.SUCCESSOR,
        "authorization_sha256": storage.sha256(root / "authorization.json"),
        "software_gate_sha256": storage.sha256(root / "software_gate.json"),
    }
    request = {
        "run_id": run_id,
        "adapter": lab.ADAPTER,
        "effective": {"preset": "nominal"},
        "nmpc_capture": captured,
    }
    storage.write_json(directory / "request.json", request)
    storage.write_json(directory / "status.json", {"state": "running"})
    selected = run_catalog.Run(
        "run-" + hashlib.sha256(("id:" + run_id).encode()).hexdigest()[:20],
        directory,
        ("owned",),
        (directory,),
        run_id,
        lab.ADAPTER,
        "nominal",
        "running",
        "running",
        "pending",
        (),
    )
    assert lab.owned_run(selected)[0] == directory  # The unmodified chain really authenticates.
    if fault.startswith("gate_"):
        changed = copy.deepcopy(gate)
        if fault == "gate_config":
            changed["resolved_snapshots"]["nominal"]["vehicle"]["mass"] += 1
            captured["resolved"] = changed["resolved_snapshots"]["nominal"]
        elif fault == "gate_environment":
            changed["environment"]["python"] = "forged"
            captured["environment"] = changed["environment"]
        else:
            changed["run_ids"]["nominal"] = "20261103T000000000000Z_" + "c" * 32
        storage.write_json(root / "software_gate.json", changed)
        captured["software_gate_sha256"] = storage.sha256(root / "software_gate.json")
        storage.write_json(directory / "request.json", request)
    else:
        path = lab.claim_path("nominal")
        claim = storage.read_json(path)
        if fault == "claim_extra":
            claim["unsupported_extra"] = True
        else:
            new_id = "20261103T000000000000Z_" + "c" * 32
            copied = directory.with_name(new_id)
            shutil.copytree(directory, copied)
            request["run_id"] = claim["run_id"] = new_id
            storage.write_json(copied / "request.json", request)
            selected = replace(
                selected,
                directory=copied,
                aliases=(copied,),
                run_id=new_id,
                key="run-" + hashlib.sha256(("id:" + new_id).encode()).hexdigest()[:20],
            )
        storage.write_json(path, claim)
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("Rebound successor reached a lifecycle call")

    for name in ("status_for", "cancel_run", "_reconcile_locked", "finalize"):
        monkeypatch.setattr(jobs, name, forbidden)
    panels.inspect(selected)
    with pytest.raises(ValueError):
        lab.retained_authority(storage.read_json(selected.directory / "request.json"))
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
