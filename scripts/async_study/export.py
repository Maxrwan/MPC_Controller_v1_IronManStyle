"""Freeze the architecture and explicit lateral-only replacement interface."""

import hashlib
import json

from threading_study.config import ROOT


def export(root):
    source = ROOT / "results/mpc_parameter_study/selected_candidates.json"
    measured_path = root / "async_measured/summary.json"
    measured = json.loads(measured_path.read_text()) if measured_path.exists() else None
    selected = dict(
        task="006.3",
        candidate=json.loads(source.read_text())["C"],
        candidate_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        native_threads=1,
        planner_hz=10,
        codriver_hz=100,
        tracker_margin_m=0.08,
        lateral_method="finite_horizon_TVLQR",
        lateral_state_order=["e_y", "e_psi", "vy", "r"],
        lateral_q_diagonal=[100.0, 100.0, 4.0, 1.0],
        lateral_r=25.0,
        discretization="approved grip-model RK4, dt=0.01, two substeps",
        gains="planner-side finite-horizon Riccati; terminal DARE at final linearization",
        longitudinal="a_star + 1.0*(vx_star-vx), clipped to shared physical domain",
        steering_rate_rad_per_second=1.0,
        delay_estimator=dict(
            kind="rolling_median", initial_seconds=0.017, window=10, maximum_seconds=0.30
        ),
        reserve_thresholds_seconds=dict(
            warning=0.20, critical=0.05, minimum_acceptance=0.05, exhaustion=0
        ),
        urgent_trigger=dict(
            lateral_m=0.05, heading_rad=0.10, consecutive_samples=2, maximum_pending=1
        ),
        handoff_error_limits_canonical=[0.5, 0.5, 1.0, 0.20, 0.75, 0.15],
        runtime_timing="event-driven, no overlap; measured full preparation and codriver delay",
        injected_cases="deterministic planner delay; zero codriver latency",
        startup="gated preparation and command prepositioning, then synthetic 2m/s launch",
        exhaustion="latched Task005 fallback inside documented domain; otherwise clean termination",
        tracking_reference="linear X with unwrapped heading/progress; ZOH U, K and curvature",
        implemented_tasks=["006.3"],
        excluded_tasks=["006.4", "007"],
    )
    (root / "selected_architecture.json").write_text(json.dumps(selected, indent=2) + "\n")
    handoff = dict(
        replace_only="lateral TVLQR correction",
        preserve=[
            "APEX candidate",
            "packet timestamps and nominal X/U",
            "buffer and handoff rules",
            "longitudinal P correction",
            "actuator/grip/rate bounds",
            "fallback policy",
            "experiments",
        ],
        model_dimensions=dict(
            canonical_state=6, lateral_state=4, lateral_input=1, A=[4, 4], B=[4, 1]
        ),
        lateral_canonical_indices=[5, 3, 1, 2],
        frequency_hz=100,
        deadline_seconds=0.01,
        baseline_design=selected,
        comparison_protocol=[
            "First replay identical saved packets and availability times for both trackers.",
            "Keep validity gates; report rejected or exhausted packets.",
            "Then compare closed-loop replanning, which naturally changes nominal trajectories.",
        ],
        packet_sources=[
            str(p.relative_to(root)) for p in sorted(root.glob("*/trajectory_packets.json"))
        ],
        baseline_measurement="async_measured/summary.json" if measured else None,
        host_budget_caveat="Codriver total includes validation; benchmark the full replacement.",
        target_hardware_claim=None,
        measured_host_codriver_seconds=measured["codriver_timing"]["total_time"]
        if measured
        else None,
        measured_host_algorithm_core_demand={
            owner: measured[owner + "_core_demand"] for owner in ["planner", "codriver", "total"]
        }
        if measured
        else None,
        untrimmed_packet_numeric_payload_bytes=260 * 8,
        gain_numeric_payload_bytes=40 * 4 * 8,
        memory_caveat="Numeric arrays only; Python objects, allocator and model memory excluded.",
    )
    (root / "task0064_handoff.json").write_text(json.dumps(handoff, indent=2) + "\n")
