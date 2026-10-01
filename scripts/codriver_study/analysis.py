"""Independent paired metrics, audits and scientific figures for local codrivers."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from async_study.analysis import audit as audit_physics
from async_study.analysis import read_csv
from threading_study.worker import stats


def audit(root):
    audit_physics(root)
    records = []
    for path in sorted(root.glob("*/summary.json")):
        r = json.loads(path.read_text())
        folder = path.parent
        controls = read_csv(folder / "controls.csv")
        qp = read_csv(folder / "qp_events.csv")
        if not qp.empty:
            good = qp[~qp.local_fallback]
            assert (good.constraint_violation <= 1e-5).all()
            assert (good.dual_residual <= 1e-3).all()
            for row in qp[qp.local_fallback].itertuples():
                command = controls[abs(controls.time - row.time) < 1e-8]
                if not command.empty:
                    np.testing.assert_allclose(
                        command.requested_delta, row.replacement_delta, atol=1e-12
                    )
                    np.testing.assert_allclose(
                        command.requested_a_cmd, row.replacement_a_cmd, atol=1e-12
                    )
            if r["scenario"] == "qp_failure":
                assert any(abs(qp[qp.local_fallback].time - 6) < 1e-8)
                assert r["fallback_events"] == 0
        if r["phase"] == "replay":
            source = {
                p["plan_id"]: p
                for p in json.loads(
                    (Path(r["replay_source"]) / "trajectory_packets.json").read_text()
                )
            }
            for packet in json.loads((folder / "trajectory_packets.json").read_text()):
                original = source[packet["plan_id"]]
                for key in [
                    "timestamps",
                    "states",
                    "controls",
                    "gain_times",
                    "gains",
                    "curvatures",
                ]:
                    np.testing.assert_array_equal(packet[key], original[key])
                assert (
                    abs(packet["actual_completion_time"] - original["actual_completion_time"])
                    < 1e-8
                )
            records.append(
                dict(case=folder.name, identical_nominal_packets=True, availability_verified=True)
            )
        else:
            records.append(dict(case=folder.name, physical_chronology_verified=True))
    (root / "local_verification.json").write_text(json.dumps(records, indent=2) + "\n")
    print("QP fallback and frozen-packet audits:", len(records), "cases")


def metrics(folder, r):
    u = read_csv(folder / "controls.csv")
    s = read_csv(folder / "states.csv")
    q = read_csv(folder / "qp_events.csv")
    initial = r["startup"]["prepositioned_control"][0]
    intervals = np.diff(np.r_[0.0, u.application_time])
    increments = np.diff(np.r_[initial, u.delta])
    rates = np.divide(increments, intervals, out=np.zeros(len(intervals)), where=intervals > 1e-12)
    elapsed = float(intervals.sum())
    row = dict(
        case=folder.name,
        controller=r["architecture"],
        phase=r["phase"],
        scenario=r["scenario"],
        horizon=r["local_config"]["horizon"],
        rate_weight=r["local_config"]["rate_weight"],
        varying=r["local_config"]["varying"],
        warm_start=r["local_config"]["warm_start"],
        delay=r["config"]["injected_delay"],
        latency_mode=r["config"]["latency_mode"],
        completed=len(r["lap_times"]) == 2,
        stop_reason=r["stop_reason"],
        lap_times=json.dumps(r["lap_times"]),
        **r["full_run"],
    )
    for key in [
        "planner_misses",
        "codriver_misses",
        "codriver_computational_exceedances",
        "planner_effective_hz",
        "codriver_effective_hz",
        "solver_failures",
        "planner_failures",
        "fallback_events",
        "boundary_violations",
        "urgent_triggers",
        "max_front_utilization",
        "max_rear_utilization",
        "steering_total_variation",
        "acceleration_total_variation",
        "planner_core_demand",
        "codriver_core_demand",
        "total_core_demand",
        "qp_local_fallbacks",
    ]:
        row[key] = r[key]
    row.update(
        steering_rate_rms=float(np.sqrt(np.sum(rates**2 * intervals) / elapsed)),
        steering_rate_max=float(abs(rates).max()),
        steering_rate_limit_seconds=float(intervals[np.isclose(abs(rates), 1, atol=1e-5)].sum()),
        steering_correction_rms=float(np.sqrt(np.mean(u.delta_correction**2))),
        steering_correction_max=float(u.delta_correction.abs().max()),
        applied_steering_correction_rms=float(np.sqrt(np.mean((u.delta - u.nominal_delta) ** 2))),
        applied_steering_correction_max=float((u.delta - u.nominal_delta).abs().max()),
        final_rss_mib=r["rss_final_bytes"] / 2**20,
        peak_rss_mib=r["rss_lifetime_peak_bytes"] / 2**20,
        construction_rss_delta_mib=(r["rss_after_construction_bytes"] - r["rss_before_bytes"])
        / 2**20,
    )
    for key, values in r["tracker_envelope"].items():
        row.update({"tracking_" + key + "_" + stat: v for stat, v in values.items()})
    for key, values in r["codriver_timing"].items():
        row.update({"codriver_" + key + "_" + stat: v for stat, v in values.items()})
    row.update(
        compute_ratio_mean=r["codriver_timing"]["total_time"]["mean"] / 0.01,
        compute_ratio_p95=r["codriver_timing"]["total_time"]["p95"] / 0.01,
        effective_cores=r["codriver_timing"]["cpu_time"]["mean"]
        / r["codriver_timing"]["total_time"]["mean"],
    )
    if not q.empty:
        for key in [
            "iterations",
            "solver_time",
            "update_time",
            "solver_update_time",
            "model_assembly_time",
            "workspace_setup_time",
        ]:
            if key in q:
                row.update({"qp_" + key + "_" + k: v for k, v in stats(q[key].dropna()).items()})
        row["qp_non_deadline_fallbacks"] = int(
            (q.local_fallback & (q.fallback_reason != "full_update_deadline_exceeded")).sum()
        )
    perturb = r["config"]["disturbance_time"]
    row["recovery_seconds"] = None
    if perturb is not None:
        post = s[(s.time >= perturb) & (s.time <= perturb + 5)]
        for sample in post.itertuples():
            if sample.time + 1 > post.time.iloc[-1]:
                break
            window = post[(post.time >= sample.time) & (post.time <= sample.time + 1)]
            if (window.e_y.abs() <= 0.02).all() and (window.e_psi.abs() <= 0.05).all():
                row["recovery_seconds"] = float(sample.time - perturb)
                break
        row["disturbance_peak_local_error"] = float(
            u[(u.time >= perturb) & (u.time <= perturb + 5)].error_e_y.abs().max()
        )
    return row


def analyze(root):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = [
        metrics(p.parent, json.loads(p.read_text())) for p in sorted(root.glob("*/summary.json"))
    ]
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "experiments.csv", index=False)
    parity_path = root / "model_parity/prediction_errors.csv"
    if parity_path.exists():
        parity = pd.read_csv(parity_path)
        errors = ["error_ey", "error_epsi", "error_vy", "error_r"]
        groups = []
        for condition in ["speed", "steering", "curvature", "error_scale"]:
            for value, group in parity.groupby(condition):
                groups.append(
                    dict(
                        condition=condition,
                        value=value,
                        cases=len(group),
                        **{name + "_max_abs": float(group[name].abs().max()) for name in errors},
                    )
                )
        pd.DataFrame(groups).to_csv(parity_path.parent / "summary_by_condition.csv", index=False)

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(root / (name + ".png"), dpi=140)
        plt.close(fig)

    replay_names = ["replay_tvlqr", "replay_N8"]
    if all((root / name / "controls.csv").exists() for name in replay_names):
        fig, axes = plt.subplots(2, 1, sharex=True)
        for name in replay_names:
            u = read_csv(root / name / "controls.csv")
            axes[0].plot(u.time, u.error_e_y * 1000, label=name, alpha=0.8)
            axes[1].plot(u.time, u.error_e_psi, label=name, alpha=0.8)
        axes[0].set(ylabel="Lateral error [mm]", title="Identical offered packet replay")
        axes[1].set(xlabel="Physical time [s]", ylabel="Heading error [rad]")
        axes[0].legend()
        save(fig, "packet_replay_comparison")

    for scenario in ["nominal", "disturbance", "stress"]:
        names = [f"tvlqr_{scenario}", f"mpc_{scenario}"]
        if not all((root / n / "summary.json").exists() for n in names):
            continue
        for key, column, label in [
            ("trajectory_lateral", "error_e_y", "Lateral trajectory error [m]"),
            ("trajectory_heading", "error_e_psi", "Heading trajectory error [rad]"),
            ("steering", "delta", "Steering [rad]"),
            ("steering_correction", "delta_correction", "Steering correction [rad]"),
            ("steering_rate", None, "Steering rate [rad/s]"),
            ("cumulative_variation", None, "Cumulative steering variation [rad]"),
        ]:
            fig, ax = plt.subplots()
            for name in names:
                u = read_csv(root / name / "controls.csv")
                values = (
                    u[column]
                    if column
                    else (
                        np.r_[0, np.diff(u.delta) / np.diff(u.application_time)]
                        if key == "steering_rate"
                        else np.r_[0, np.cumsum(abs(np.diff(u.delta)))]
                    )
                )
                ax.plot(u.time, values, label=name.split("_")[0], alpha=0.8)
            ax.set(xlabel="Physical time [s]", ylabel=label, title=scenario)
            ax.legend()
            save(fig, scenario + "_" + key)
        if scenario != "nominal":
            fig, ax = plt.subplots()
            start = 5 if scenario == "disturbance" else 7.7
            for name in names:
                s = read_csv(root / name / "states.csv")
                s = s[(s.time >= start - 0.1) & (s.time <= start + 2)]
                ax.plot(s.time - start, s.e_y, label=name.split("_")[0])
            ax.axhline(0.02, color="gray", linestyle="--")
            ax.axhline(-0.02, color="gray", linestyle="--")
            ax.set(xlabel="Time since perturbation [s]", ylabel="Centerline lateral error [m]")
            ax.legend()
            save(fig, scenario + "_recovery")
    selected = frame[
        (frame.phase == "closed")
        & (frame.scenario == "nominal")
        & (frame.latency_mode == "measured")
    ]
    if not selected.empty:
        for key, label in [
            ("compute_ratio_p95", "p95 full update / 10 ms"),
            ("codriver_core_demand", "Codriver CPU-core-seconds per second"),
            ("steering_rate_limit_seconds", "Time at steering-rate limit [s]"),
        ]:
            fig, ax = plt.subplots()
            ax.bar(selected.controller, selected[key])
            ax.set_ylabel(label)
            save(fig, key)
        fig, ax = plt.subplots()
        samples = [
            read_csv(root / n / "controls.csv").total_time.to_numpy() * 1000 for n in selected.case
        ]
        ax.boxplot(samples, tick_labels=list(selected.controller), showfliers=True)
        ax.axhline(10, color="red", linestyle="--")
        ax.set_ylabel("Full codriver update [ms]")
        save(fig, "compute_distributions")
        fig, ax = plt.subplots()
        ax.scatter(selected.codriver_total_time_p95 * 1000, selected.tracking_e_y_rms * 1000)
        for r in selected.itertuples():
            ax.annotate(r.controller, (r.codriver_total_time_p95 * 1000, r.tracking_e_y_rms * 1000))
        ax.set(xlabel="Full-update p95 [ms]", ylabel="Trajectory lateral RMS [mm]")
        save(fig, "tracking_vs_compute")
    horizons = frame[frame.case.str.match(r"^replay_N\d+$")].sort_values("horizon")
    if not horizons.empty:
        for key, label, name in [
            ("qp_solver_time_p95", "QP solve p95 [ms]", "horizon_timing"),
            ("tracking_e_y_rms", "Trajectory lateral RMS [mm]", "horizon_tracking"),
        ]:
            fig, ax = plt.subplots()
            ax.plot(horizons.horizon, horizons[key] * 1000, "o-")
            ax.set(xlabel="Local horizon steps", ylabel=label)
            save(fig, name)
    from codriver_study.report import generate

    generate(root, frame)
    print(
        frame[
            ["case", "completed", "rms_e_y", "qp_local_fallbacks", "compute_ratio_p95"]
        ].to_string(index=False)
    )
