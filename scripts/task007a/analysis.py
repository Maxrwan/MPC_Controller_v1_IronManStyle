"""Post-run scientific figures and physical-time racing/sector observations."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from async_study.analysis import audit

from apex.coordinates.angles import wrap_angle
from apex.planning_reference.reference import PlanningReference, intersection_count
from apex.planning_reference.track import load_track


def analyze(output, fixture):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output, fixture = Path(output), Path(fixture)
    output.mkdir(parents=True, exist_ok=True)
    track, source, identity = load_track(fixture / "track_source.json")
    ref = PlanningReference(fixture, track, identity)
    frame = ref.frame
    s = frame.s_track_m.to_numpy()
    g = np.array([track.centerline.geometry(x) for x in s])
    normal = np.c_[-np.sin(g[:, 2]), np.cos(g[:, 2])]
    left, right = g[:, :2] + 0.55 * normal, g[:, :2] - 0.55 * normal

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(output / (name + ".png"), dpi=140)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.plot(*g[:, :2].T, label="centerline")
    ax.plot(*left.T, "k-", lw=0.7, label="boundaries")
    ax.plot(*right.T, "k-", lw=0.7)
    ax.plot(frame.x_ref_m, frame.y_ref_m, label="offline racing line", lw=1)
    offsets = {
        "long_straight": (-5, 15),
        "hairpin": (20, 10),
        "acceleration_zone": (10, -25),
        "medium_corner": (-65, -40),
        "fast_sweeper": (10, 0),
        "direction_change": (-105, 0),
        "second_straight": (-85, 0),
        "technical_section": (-30, 15),
        "return_complex": (10, 0),
    }
    ax.annotate("", xy=(11, 0), xytext=(7, 0), arrowprops={"arrowstyle": "->"})
    for sector in ref.manifest["sectors"]:
        x, y, *_ = track.centerline.geometry(sector["start_s_m"])
        ax.annotate(
            sector["name"].replace("_", " "),
            (x, y),
            fontsize=8,
            xytext=offsets[sector["name"]],
            textcoords="offset points",
            arrowprops={"arrowstyle": "-", "color": "gray"},
        )
    ax.set(xlabel="World x [m]", ylabel="World y [m]", title="Synthetic Grand Prix v1")
    ax.axis("equal")
    ax.legend()
    save(fig, "circuit_and_racing_line")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, bounds, title in zip(
        axes,
        [(21, 26.5, -3.2, 0.8), (3, 11, 19, 24)],
        ["Hairpin racing-line detail", "Technical direction change"],
    ):
        ax.plot(*g[:, :2].T, label="centerline")
        ax.plot(*left.T, "k-", lw=0.7)
        ax.plot(*right.T, "k-", lw=0.7)
        ax.plot(frame.x_ref_m, frame.y_ref_m, label="racing line")
        ax.set(xlim=bounds[:2], ylim=bounds[2:], title=title, xlabel="x [m]", ylabel="y [m]")
        ax.set_aspect("equal")
        ax.legend()
    save(fig, "racing_line_details")
    geometry_signals = [
        ("offset", frame.e_y_ref_m, "Lateral offset [m]"),
        ("centerline_curvature", g[:, 3], "Centerline curvature [1/m]"),
        ("reference_curvature", frame.kappa_ref_1pm, "Racing curvature [1/m]"),
        ("velocity_profile", frame.v_ref_mps, "Reference speed [m/s]"),
        (
            "lateral_demand",
            frame.v_ref_mps**2 * abs(frame.kappa_ref_1pm),
            "Approximate lateral demand [m/s²]",
        ),
    ]
    for name, y, label in geometry_signals:
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(s, y)
        ax.set(xlabel="Centerline progress [m]", ylabel=label)
        save(fig, name)
    delta = np.arctan(0.3 * frame.kappa_ref_1pm)
    metric = np.linalg.norm(np.gradient(np.c_[frame.x_ref_m, frame.y_ref_m], s, axis=0), axis=1)
    fig, axes = plt.subplots(2, 1, sharex=True, figsize=(10, 5))
    axes[0].plot(s, delta)
    axes[0].set_ylabel("Steering [rad]")
    axes[1].plot(s, np.gradient(delta, s) * frame.v_ref_mps / metric)
    axes[1].set(xlabel="Progress [m]", ylabel="Steering rate [rad/s]")
    save(fig, "reference_actuator_demand")
    geometry_validation = dict(
        lap_length_m=track.length,
        total_width_m=1.1,
        centerline_curvature_min=float(g[:, 3].min()),
        centerline_curvature_max=float(g[:, 3].max()),
        minimum_sampled_radius_m=float(1 / max(abs(g[:, 3]))),
        full_corridor_frenet_denominator_min=float(min(1 - 0.55 * abs(g[:, 3]))),
        left_boundary_crossings=intersection_count(left),
        right_boundary_crossings=intersection_count(right),
    )
    (output / "track_validation.json").write_text(json.dumps(geometry_validation, indent=2) + "\n")
    all_sectors = []
    all_laps = []
    for path in sorted(output.glob("*/summary.json")):
        folder = path.parent
        summary = json.loads(path.read_text())
        summary.setdefault("architecture", "tvlqr")
        path.write_text(json.dumps(summary, indent=2) + "\n")
        state = pd.read_csv(folder / "states.csv")
        control = pd.read_csv(folder / "controls.csv")
        plans = pd.read_csv(folder / "plans.csv")
        reserves = pd.read_csv(folder / "reserves.csv")
        x = state.s_abs.to_numpy() % track.length
        state["progress"] = x
        state["lap"] = (state.s_abs / track.length).astype(int) + 1
        goals = pd.DataFrame([ref.sample(a) for a in x])
        geometry = np.array([track.centerline.geometry(a) for a in x])
        state["racing_lateral_error"] = state.e_y - goals.e_y_ref_m
        state["racing_heading_error"] = [
            wrap_angle(a - b) for a, b in zip(state.e_psi, goals.e_psi_ref_rad)
        ]
        state["racing_speed_error"] = state.vx - goals.v_ref_mps
        state["reference_speed"] = goals.v_ref_mps
        state["centerline_curvature"] = geometry[:, 3]
        state["racing_curvature"] = goals.kappa_ref_1pm
        state["lateral_acceleration"] = np.gradient(state.vy, state.time) + state.vx * state.r
        state["steering_utilization"] = abs(state.delta) / 0.4
        state["boundary_clearance"] = 0.55 - abs(state.e_y)
        state["margin_activity"] = state.boundary_clearance < 0.08
        starts = np.array([a["start_s_m"] for a in ref.manifest["sectors"]])
        names = np.array([a["name"] for a in ref.manifest["sectors"]])
        state["sector"] = names[np.maximum(0, np.searchsorted(starts, x, side="right") - 1)]
        state["reserve"] = np.interp(state.time, reserves.time, reserves.reserve)
        intervals = np.diff(np.r_[state.time, summary["end_time"]])
        state["interval"] = np.maximum(intervals, 0)
        application_intervals = np.diff(np.r_[0, control.application_time])
        rates = np.divide(
            np.diff(np.r_[summary["startup"]["prepositioned_control"][0], control.delta]),
            application_intervals,
            out=np.zeros(len(control)),
            where=application_intervals > 1e-12,
        )
        for key, column in [
            ("abs_trajectory_ey", "error_e_y"),
            ("abs_trajectory_epsi", "error_e_psi"),
            ("trajectory_vy_error", "error_vy"),
            ("trajectory_r_error", "error_r"),
        ]:
            state[key] = np.interp(
                state.time,
                control.time,
                abs(control[column]) if key.startswith("abs") else control[column],
            )
        state["steering_rate_utilization"] = np.interp(
            state.time, control.application_time, abs(rates)
        )
        state["codriver_time"] = np.interp(state.time, control.time, control.total_time)
        valid_plans = plans[~plans.startup]
        for key in ["solve_time", "planner_total_time"]:
            state[key] = np.interp(state.time, valid_plans.release_time, valid_plans[key])
        packets = {
            p["plan_id"]: p for p in json.loads((folder / "trajectory_packets.json").read_text())
        }
        state["trajectory_age"] = [
            max(0, t - packets[int(pid)]["planner_release_time"]) if int(pid) in packets else np.nan
            for t, pid in zip(state.time, state.plan_id)
        ]
        completed = [
            p
            for p in json.loads((folder / "events.json").read_text())["plans"]
            if "prediction_error" in p and p.get("completed")
        ]
        if completed:
            times = np.array([p["completion_time"] for p in completed])
            indices = np.searchsorted(times, state.time, side="right") - 1
            for key, channel in [
                ("apex_prediction_ey_error", 5),
                ("apex_prediction_heading_error", 3),
            ]:
                errors = np.array([p["prediction_error"][channel] for p in completed])
                state[key] = np.where(indices >= 0, errors[np.maximum(indices, 0)], np.nan)
        state.to_csv(folder / "difficulty_signals.csv", index=False)

        def metrics(group):
            w = group.interval.to_numpy()
            w = w / w.sum()
            result = {
                key + "_rms": float(np.sqrt(np.sum(w * group[key] ** 2)))
                for key in ["racing_lateral_error", "racing_heading_error", "racing_speed_error"]
            }
            for key in [
                "racing_lateral_error",
                "racing_heading_error",
                "racing_speed_error",
                "delta",
                "a_cmd",
                "front_utilization",
                "rear_utilization",
                "steering_rate_utilization",
                "lateral_acceleration",
            ]:
                result[key + "_max_abs"] = float(group[key].abs().max())
            result.update(
                acceleration_max=float(group.a_cmd.max()),
                braking_min=float(group.a_cmd.min()),
                reserve_min=float(group.reserve.min()),
                boundary_clearance_min=float(group.boundary_clearance.min()),
                margin_activity_seconds=float(group[group.margin_activity].interval.sum()),
            )
            for key in ["solve_time", "planner_total_time", "codriver_time"]:
                result[key + "_mean"] = float(np.sum(w * group[key]))
                result[key + "_p95"] = float(group[key].quantile(0.95))
            return result

        laps = []
        for lap, group in state.groupby("lap"):
            if group.interval.sum() <= 0:
                continue
            row = dict(
                case=folder.name,
                lap=int(lap),
                phase="startup_transient" if lap == 1 else "comparable",
                **metrics(group),
            )
            laps.append(row)
            all_laps.append(row)
        comparable = state[(state.lap >= 2) & (state.lap <= 3)]
        if comparable.empty:
            comparable = state
        sectors = []
        for sector, group in comparable.groupby("sector", sort=False):
            row = dict(case=folder.name, sector=sector, **metrics(group))
            sectors.append(row)
            all_sectors.append(row)
        pd.DataFrame(laps).to_csv(folder / "lap_metrics.csv", index=False)
        pd.DataFrame(sectors).to_csv(folder / "sector_metrics.csv", index=False)
        signals = [
            "abs_trajectory_ey",
            "abs_trajectory_epsi",
            "trajectory_vy_error",
            "trajectory_r_error",
            "centerline_curvature",
            "racing_curvature",
            "lateral_acceleration",
            "steering_utilization",
            "steering_rate_utilization",
            "front_utilization",
            "rear_utilization",
            "trajectory_age",
            "reserve",
        ]
        summary["racing_metrics_comparable"] = metrics(comparable)
        summary["observed_supervisor_ranges"] = {
            k: dict(min=float(state[k].min()), max=float(state[k].max())) for k in signals
        }
        summary["lap_metrics"] = laps
        summary["combined_demand_observations"] = {
            "braking_while_turning_seconds": float(
                state.interval[
                    (state.a_cmd < -0.1) & (state.lateral_acceleration.abs() > 0.3)
                ].sum()
            ),
            "acceleration_while_turning_seconds": float(
                state.interval[(state.a_cmd > 0.1) & (state.lateral_acceleration.abs() > 0.3)].sum()
            ),
            "thresholds": "|estimated ay| > 0.3m/s2 and |a_cmd| > 0.1m/s2",
        }
        (folder / "racing_analysis.json").write_text(json.dumps(summary, indent=2) + "\n")
        if folder.name != "measured":
            continue
        world = (
            geometry[:, :2]
            + state.e_y.to_numpy()[:, None] * np.c_[-np.sin(geometry[:, 2]), np.cos(geometry[:, 2])]
        )
        fig, ax = plt.subplots(figsize=(8, 9))
        ax.plot(frame.x_ref_m, frame.y_ref_m, label="offline reference")
        ax.plot(*world.T, label="actual", alpha=0.7, lw=0.7)
        ax.axis("equal")
        ax.legend()
        ax.set(xlabel="x [m]", ylabel="y [m]")
        save(fig, "actual_vs_reference")
        for key, label in [
            ("racing_lateral_error", "Racing lateral error [m]"),
            ("racing_heading_error", "Racing heading error [rad]"),
            ("racing_speed_error", "Speed error [m/s]"),
            ("front_utilization", "Front tire utilization"),
            ("rear_utilization", "Rear tire utilization"),
            ("solve_time", "Planner solve [s]"),
            ("planner_total_time", "Planner preparation [s]"),
            ("codriver_time", "Codriver update [s]"),
            ("reserve", "Trajectory reserve [s]"),
        ]:
            fig, ax = plt.subplots(figsize=(10, 3))
            for lap, group in state.groupby("lap"):
                ax.plot(group.progress, group[key], label=f"lap {lap}", alpha=0.65, lw=0.7)
            ax.set(xlabel="Centerline progress [m]", ylabel=label)
            ax.legend()
            save(fig, key)
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(s, frame.v_ref_mps, label="reference")
        last = state[state.lap == 3]
        ax.plot(last.progress, last.vx, label="actual lap 3")
        ax.legend()
        ax.set(xlabel="Progress [m]", ylabel="Speed [m/s]")
        save(fig, "speed_tracking")
        fig, ax = plt.subplots(figsize=(10, 4))
        table = pd.DataFrame(sectors)
        ax.bar(table.sector, table.racing_lateral_error_rms * 1000)
        ax.tick_params(axis="x", rotation=35)
        ax.set_ylabel("Racing lateral RMS [mm]")
        save(fig, "sector_summary")
    pd.DataFrame(all_sectors).to_csv(output / "sector_metrics.csv", index=False)
    pd.DataFrame(all_laps).to_csv(output / "lap_metrics.csv", index=False)
    audit(output)
    from task007a.report import generate

    generate(output, track, ref)
