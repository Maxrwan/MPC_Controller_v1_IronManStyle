"""Descriptions of executable accepted adapters; scenario proposals are not presets."""

EXPERIMENTS = {
    "dynamic_demo": {
        "name": "Dynamic bicycle response",
        "mode": "Open loop",
        "purpose": "Inspect the original prescribed-input vehicle response on its fixed track.",
        "behavior": "Longitudinal/lateral/yaw motion under the Task004 input schedule.",
        "inputs": (
            "Duration [s], RK4 timestep [s]; original vehicle, track and input schedule fixed."
        ),
        "measurements": "States, state-row steering/a_cmd, stored XY and original summary.",
        "composition": (
            "Canonical DynamicBicycle, linear axle tires, original Task004 CLI; no controller."
        ),
        "limits": (
            "Synthetic parameters; unsaturated tires; no V0.2 finite-case qualification claim."
        ),
    },
    "lqr_baseline": {
        "name": "Scheduled LQR/PI tracking",
        "mode": "Closed loop",
        "purpose": "Investigate tracking and recovery using the existing Task005 baseline.",
        "behavior": (
            "Nonlinear plant tracking with separate scheduled linear LQR design and speed PI."
        ),
        "inputs": "Circle/oval, duration [s], speed [m/s], initial e_y [m] and e_psi [rad].",
        "measurements": (
            "States, actual controls/references, available gains/flags and original summaries."
        ),
        "composition": (
            "Task005 run_case; canonical plant/SimulationRunner, 200 Hz plant/100 Hz control."
        ),
        "limits": (
            "Perfect-state synthetic baseline; not TVLQR/NMPC, racing robustness or "
            "physical validation."
        ),
    },
    "dynamic_lab": {
        "name": "Finite vehicle-dynamics sensitivity",
        "mode": "Open loop",
        "purpose": "Compare approved single-factor synthetic yaw/steering/stiffness responses.",
        "behavior": (
            "BASE versus independently changed yaw inertia, steering, front or rear stiffness."
        ),
        "inputs": (
            "Five accepted cases, nominal grid only; fixed initial state and "
            "prescribed ZOH schedule."
        ),
        "measurements": (
            "States, applied controls, slip/force/load/stiffness/utilization "
            "diagnostics and stored XY."
        ),
        "composition": (
            "Canonical DynamicBicycle, linear axle tires/quasi-static loads, RK4/SimulationRunner."
        ),
        "limits": (
            "0.500 s, 0.005 s nominal grid, steering onset 0.100 s. Qualification "
            "requires exact selected Q; no physical validation."
        ),
    },
}

CASES = {
    "VDL1_BASE": "Baseline: reference synthetic vehicle and accepted steering step.",
    "VDL1_IZ_HIGH": "Yaw-inertia sensitivity: only the accepted Iz treatment differs from BASE.",
    "VDL1_STEER_HIGH": (
        "Steering sensitivity: only prescribed steering amplitude differs from BASE."
    ),
    "VDL1_CF_HIGH": "Front-stiffness sensitivity: only nominal front cornering stiffness differs.",
    "VDL1_CR_HIGH": "Rear-stiffness sensitivity: only nominal rear cornering stiffness differs.",
}
