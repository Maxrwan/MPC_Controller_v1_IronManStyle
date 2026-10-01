"""Independent event-log audits and scientific figures for Task006.3."""

import json
import shutil
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from run_lqr_baseline import make_track

from apex.control.trajectory.packet import TrajectoryPacket
from apex.state import STATE_NAMES


def read_csv(path):
    try:
        return pd.read_csv(path, float_precision="round_trip")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def audit(root):
    records = []
    for path in sorted(root.glob("*/summary.json")):
        r, folder = json.loads(path.read_text()), path.parent
        if r["architecture"] == "sync":
            continue
        s, u = read_csv(folder / "states.csv"), read_csv(folder / "controls.csv")
        assert not s.empty and not u.empty, folder
        assert np.isfinite(s[list(STATE_NAMES) + ["time", "delta", "a_cmd"]]).all().all()
        assert np.all(np.diff(s.time) > 0) and np.max(np.diff(s.time)) <= 0.005 + 1e-9
        assert np.all(np.diff(u.time) > 0) and np.all(np.diff(u.application_time) > 0)
        np.testing.assert_allclose(
            u.application_time - u.time, u.physical_latency, atol=1e-9, rtol=0
        )
        dt = r["config"]["tracker_dt"]
        np.testing.assert_allclose(u.time / dt, np.round(u.time / dt), atol=1e-7, rtol=0)
        initial = np.array(r["startup"]["prepositioned_control"])
        index = np.searchsorted(u.application_time, s.time, side="right") - 1
        expected = np.tile(initial, (len(s), 1))
        mask = index >= 0
        expected[mask] = u[["delta", "a_cmd"]].to_numpy()[index[mask]]
        np.testing.assert_array_equal(s[["delta", "a_cmd"]], expected)
        increments = np.diff(np.r_[initial[0], u.delta])
        intervals = np.diff(np.r_[0.0, u.application_time])
        assert np.all(abs(increments) <= intervals + 1e-8)
        assert np.max(abs(s.delta)) <= 0.4 + 1e-10
        assert np.min(s.a_cmd) >= -3 - 1e-10 and np.max(s.a_cmd) <= 2 + 1e-10
        assert max(s.front_utilization.max(), s.rear_utilization.max()) <= 1 + 1e-10
        events = json.loads((folder / "events.json").read_text())
        plans = [p for p in events["plans"] if not p["startup"]]
        for a, b in zip(plans, plans[1:]):
            assert b["release_time"] >= a["completion_time"] - 1e-9
        packet_fields = {f.name for f in fields(TrajectoryPacket)}
        packets = {
            p["plan_id"]: TrajectoryPacket(**{k: v for k, v in p.items() if k in packet_fields})
            for p in json.loads((folder / "trajectory_packets.json").read_text())
        }
        accepted = {h["plan_id"]: h["time"] for h in events["handoffs"] if h["accepted"]}
        accepted[0] = 0.0
        for row in u[u["mode"] == "trajectory"].itertuples():
            packet = packets[row.plan_id]
            assert row.time >= accepted[row.plan_id] - 1e-9
            assert row.time >= packet.actual_completion_time - 1e-9
            assert row.time < packet.horizon_end_time + 1e-9
            ref, nominal, _ = packet.sample(row.time)
            np.testing.assert_allclose(
                ref, [getattr(row, "reference_" + key) for key in STATE_NAMES], atol=1e-9, rtol=0
            )
            np.testing.assert_allclose(nominal, [row.nominal_delta, row.nominal_a_cmd], atol=1e-12)
        missing = read_csv(folder / "codriver_misses.csv")
        expected_releases = int(np.ceil((r["end_time"] - 1e-9) / dt))
        # Last launched update may be in flight when the lap target is crossed.
        assert len(u) + len(missing) in (expected_releases, expected_releases - 1)
        records.append(
            dict(
                case=folder.name,
                plant_rows=len(s),
                codriver_applications=len(u),
                solver_nonoverlap=True,
                held_commands_verified=True,
                timestamped_references_verified=True,
                rate_limit_verified=True,
            )
        )
    assert records
    (root / "verification.json").write_text(json.dumps(records, indent=2) + "\n")
    print("Audited", len(records), "asynchronous cases")
    synchronous = [
        p.parent
        for p in root.glob("*/summary.json")
        if json.loads(p.read_text())["architecture"] == "sync"
    ]
    if synchronous:
        with TemporaryDirectory(prefix="apex-sync-audit-") as temporary:
            destination = Path(temporary)
            for folder in synchronous:
                (destination / folder.name).symlink_to(folder.resolve(), target_is_directory=True)
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "audit_mpc_results.py"),
                    "--output",
                    str(destination),
                ],
                check=True,
            )
            shutil.copyfile(
                destination / "verification.json", root / "synchronous_verification.json"
            )


def analyze(root):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = []
    summaries = {}
    for path in sorted(root.glob("*/summary.json")):
        r, name = json.loads(path.read_text()), path.parent.name
        summaries[name] = r
        synchronous = r["architecture"] == "sync"
        row = dict(
            case=name,
            architecture=r["architecture"],
            stop_reason=r["stop_reason"],
            completed=len(r["lap_times"]) == 2,
            failure=r["failure"],
            **r["full_run"],
            lap_times=json.dumps(r["lap_times"]),
        )
        if synchronous:
            commands = read_csv(path.parent / "controls.csv")
            row.update(
                delay=r.get("requested_delay"),
                planner_misses=r["timing"]["missed_deadlines"],
                codriver_misses=None,
                planner_effective_hz=r["timing"]["effective_update_hz"],
                solver_failures=r["solver_failures"],
                fallback_events=r["fallbacks"],
                boundary_violations=r["boundary_violations"],
                max_front_utilization=r["max_front_combined_utilization"],
                max_rear_utilization=r["max_rear_combined_utilization"],
                steering_total_variation=r["steering_total_variation"],
                acceleration_total_variation=float(abs(np.diff(commands.a_cmd)).sum()),
            )
        else:
            row.update(
                {
                    k: r[k]
                    for k in [
                        "planner_misses",
                        "codriver_misses",
                        "planner_effective_hz",
                        "codriver_effective_hz",
                        "solver_failures",
                        "planner_failures",
                        "forecast_or_gain_failures",
                        "fallback_events",
                        "boundary_violations",
                        "urgent_triggers",
                        "max_front_utilization",
                        "max_rear_utilization",
                        "steering_total_variation",
                        "acceleration_total_variation",
                        "max_steering_rate",
                        "total_core_demand",
                        "planner_core_demand",
                        "codriver_core_demand",
                        "codriver_computational_exceedances",
                    ]
                }
            )
            row["delay"] = (
                r["config"]["injected_delay"] if r["config"]["latency_mode"] != "measured" else None
            )
            row.update({"reserve_" + k: v for k, v in r["reserve"].items()})
            row.update(
                {
                    "planner_" + key + "_" + stat: value
                    for key, values in r.get("planner_timing", {}).items()
                    for stat, value in values.items()
                }
            )
            row.update(
                {
                    "codriver_" + key + "_" + stat: value
                    for key, values in r["codriver_timing"].items()
                    for stat, value in values.items()
                }
            )
            row.update(
                {
                    "tracking_" + key + "_" + stat: value
                    for key, values in r["tracker_envelope"].items()
                    for stat, value in values.items()
                }
            )
            events = json.loads((path.parent / "events.json").read_text())
            completed = [v for v in events["plans"] if not v["startup"] and v.get("completed")]
            if completed:
                for i, key in enumerate(STATE_NAMES):
                    error = np.array([v["prediction_error"][i] for v in completed])
                    row["prediction_" + key + "_rms"] = float(np.sqrt(np.mean(error**2)))
                    row["prediction_" + key + "_max"] = float(abs(error).max())
                row["delay_error_p95_abs"] = float(
                    np.percentile([abs(v["delay_estimation_error"]) for v in completed], 95)
                )
        row["completed_without_fallback"] = row["completed"] and row.get("fallback_events", 0) == 0
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "experiments.csv", index=False)

    def save(fig, path):
        fig.tight_layout()
        fig.savefig(path, dpi=130)
        plt.close(fig)

    for name, r in summaries.items():
        if r["architecture"] == "sync":
            continue
        folder = root / name
        s, u = read_csv(folder / "states.csv"), read_csv(folder / "controls.csv")
        reserve, h = read_csv(folder / "reserves.csv"), read_csv(folder / "handoffs.csv")
        events = json.loads((folder / "events.json").read_text())
        plans = [p for p in events["plans"] if not p["startup"]]
        fig, ax = plt.subplots()
        track = make_track("oval")
        geometry = [track.sample(v) for v in np.linspace(0, track.length, 500)]
        ax.plot([g.x for g in geometry], [g.y for g in geometry], "--", label="centerline")
        points = []
        for row in s.iloc[::5].itertuples():
            g = track.sample(row.s_abs % track.length)
            points.append([g.x - row.e_y * np.sin(g.heading), g.y + row.e_y * np.cos(g.heading)])
        ax.plot(*np.asarray(points).T, label="physical plant")
        ax.set(xlabel="X [m]", ylabel="Y [m]", title=name)
        ax.axis("equal")
        ax.legend()
        save(fig, folder / "track_trajectory.png")
        for key, reference, actual, ylabel in [
            ("e_y", "reference_e_y", "e_y", "Lateral position [m]"),
            ("e_psi", "reference_e_psi", "e_psi", "Heading error [rad]"),
            ("steering", "nominal_delta", "delta", "Steering [rad]"),
            ("acceleration", "nominal_a_cmd", "a_cmd", "Acceleration command [m/s²]"),
        ]:
            fig, ax = plt.subplots()
            ax.plot(u.time, u[reference], label="nominal plan", alpha=0.8)
            if actual in ("e_y", "e_psi"):
                ax.plot(s.time, s[actual], label="actual")
            else:
                ax.plot(u.application_time, u[actual], label="actual applied")
            ax.set(xlabel="Physical time [s]", ylabel=ylabel)
            ax.legend()
            save(fig, folder / (key + ".png"))
        fig, ax = plt.subplots()
        ax.plot(u.time, u.delta_correction)
        ax.set(xlabel="Physical time [s]", ylabel="Steering feedback correction [rad]")
        save(fig, folder / "steering_correction.png")
        fig, ax = plt.subplots()
        ax.plot(reserve.time, reserve.reserve)
        ax.axhline(0.20, color="orange", linestyle="--", label="warning")
        ax.axhline(0.05, color="red", linestyle="--", label="critical")
        ax.set(xlabel="Physical time [s]", ylabel="Active reserve [s]")
        ax.legend()
        save(fig, folder / "reserve.png")
        fig, ax = plt.subplots()
        ax.plot(
            [p["release_time"] for p in plans],
            [1000 * p["planner_total_time"] for p in plans],
            label="measured planner work",
        )
        ax.plot(
            [p["release_time"] for p in plans],
            [1000 * p["physical_delay"] for p in plans],
            label="physical planner latency",
        )
        ax.set(xlabel="Release time [s]", ylabel="Duration [ms]")
        ax.legend()
        save(fig, folder / "planner_computation.png")
        fig, ax = plt.subplots(figsize=(10, 4))
        for p in plans:
            ax.plot(
                [p["release_time"], p["completion_time"]], [p["plan_id"]] * 2, "b-", linewidth=1
            )
        if not h.empty:
            accepted = h[h.accepted]
            ax.scatter(
                accepted.time, accepted.plan_id, s=5, color="green", label="accepted handoff"
            )
        ax.set(xlabel="Physical time [s]", ylabel="Plan ID", title="Release → completion; handoffs")
        ax.legend()
        save(fig, folder / "planner_timeline.png")
        fig, axes = plt.subplots(4, 1, figsize=(9, 8), sharex=True)
        for ax, key, unit in zip(axes, ["e_y", "e_psi", "vy", "r"], ["m", "rad", "m/s", "rad/s"]):
            ax.plot(u.time, u["error_" + key])
            ax.set_ylabel(key + " [" + unit + "]")
        axes[-1].set_xlabel("Physical time [s]")
        save(fig, folder / "tracking_errors.png")
        fig, axes = plt.subplots(3, 2, figsize=(10, 7), sharex=True)
        for ax, key in zip(axes.ravel(), STATE_NAMES):
            if not h.empty and "error_" + key in h:
                ax.plot(h.time, h["error_" + key], ".", markersize=3)
            ax.set_ylabel(key + " mismatch [SI]")
        axes[2, 0].set_xlabel("Handoff time [s]")
        axes[2, 1].set_xlabel("Handoff time [s]")
        save(fig, folder / "handoff_mismatch.png")
        fig, ax = plt.subplots()
        ax.plot(s.time, s.front_utilization, label="front")
        ax.plot(s.time, s.rear_utilization, label="rear")
        ax.axhline(1, color="red", linestyle="--")
        ax.set(xlabel="Physical time [s]", ylabel="Combined tire utilization")
        ax.legend()
        save(fig, folder / "tire_utilization.png")
    sweep = frame[frame.case.str.match(r"^(codriver|sync)_\d+ms$")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for architecture, group in sweep.groupby("architecture"):
        group = group.sort_values("delay")
        axes[0].plot(group.delay * 1000, group.rms_e_y * 1000, "o-", label=architecture)
        successful = group[group.completed_without_fallback]
        axes[1].plot(successful.delay * 1000, successful.rms_e_y * 1000, "o-", label=architecture)
        for row in group.itertuples():
            label = "stopped" if not row.completed else "fallback" if row.fallback_events else None
            if label:
                axes[0].annotate(label, (row.delay * 1000, row.rms_e_y * 1000), fontsize=8)
    for ax, title in zip(
        axes, ["All runs (unequal durations if stopped)", "Two laps without fallback"]
    ):
        ax.set(xlabel="Injected planner delay [ms]", ylabel="Lateral RMS [mm]", title=title)
        ax.margins(x=0.15)
        ax.legend()
    save(fig, root / "latency_vs_tracking.png")
    fig, ax = plt.subplots(figsize=(11, 5))
    async_rows = frame[frame.architecture != "sync"]
    x = np.arange(len(async_rows))
    ax.bar(x - 0.2, async_rows.planner_misses, 0.4, label="planner releases missed")
    ax.bar(x + 0.2, async_rows.codriver_misses, 0.4, label="codriver releases missed")
    ax.set_xticks(x, async_rows.case, rotation=55, ha="right")
    ax.legend()
    save(fig, root / "planner_vs_codriver_misses.png")
    from async_study.report import generate

    generate(root)
    print(
        frame[["case", "completed", "rms_e_y", "planner_misses", "codriver_misses"]].to_string(
            index=False
        )
    )
