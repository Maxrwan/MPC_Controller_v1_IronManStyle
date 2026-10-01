# Pre-Task-007 review gate: control-side racing-reference requirements

Task 006.4 does not implement Task 007. The Planning department owns the offline global racing
line and velocity profile. The control team will consume and validate that reference; it will
not generate either product inside the next controller task.

## Required data contract

Provide a versioned, SI-unit, progress-indexed periodic reference with track identity, frame,
origin/direction, period/length, source revision and interpolation convention. Distinguish the
reference's indexing coordinate from racing-line arc length. The current control coordinate
is centerline Frenet progress; conversion is required if Planning uses another coordinate.

Required channels:

- s: monotonically increasing samples over one lap, with an explicit closed-track seam.
- e_y_ref(s): signed lateral offset in the existing left-positive Frenet frame.
- e_psi_ref(s): reference heading relative to centerline tangent, with an explicit body-heading
  versus velocity-tangent/slip convention. Unwrap before interpolation.
- kappa_ref(s): racing-reference curvature, with signed convention and sufficient smoothness.
- v_ref(s): speed profile with an explicit body-longitudinal versus path-speed definition.
- Optional a_ref(s): acceleration feedforward with its physical meaning specified. The current
  dynamic command is Fx/m; it is not automatically identical to d(vx)/dt.
- Racing-line world coordinates, or enough validated geometry to reconstruct them and check
  consistency with the offsets and headings.

Centerline curvature used in Frenet coordinate dynamics must remain distinct from racing-line
reference curvature. Replacing one silently with the other would change the model incorrectly.

## Periodic interpolation and validation

Reference lookup must support continuous s_abs across laps while wrapping only lookup progress.
Require consistent endpoints, headings, curvature, speed and optional acceleration at the seam.
Specify duplicate-endpoint handling and out-of-domain behavior; reject NaN, nonmonotonic,
wrong-unit or mismatched-track data. Interpolation must not introduce boundary or actuator
violations between samples. Validate geometric consistency, derivatives/smoothness and plausible
sampling resolution before the reference is enabled. No indefinite extrapolation.

## Feasibility and controller interfaces

Check against the frozen plant/model validity domain, speed limits, tire/load/longitudinal force
domain, steering angle and steering-rate limits, physical track widths and the unchanged 0.08 m
tracker margin. The current model excludes standstill; start/stop portions need a separately
approved mode rather than low-speed regularization invented by the controller.

Define how canonical nominal vx,vy,r,heading/progress/lateral states and feedforward steering/
acceleration are obtained consistently from Planning's channels. Specify what happens when
optional a_ref is absent. Do not assume a kinematic yaw/steering relation is automatically an
adequate grip-limited dynamic reference at racing speed.

Infeasible references must be rejected or escalated through an agreed feasibility policy.
Do not silently change the racing line, reduce speeds, clip reference channels or claim an
unvalidated emergency maneuver. Preserve explicit planner failure, reserve and fallback logic.
Reference replacement needs versioned atomic handoff and continuity validation.

## Review inputs before authorizing Task 007

Bring the frozen Task 006.4 controller recommendation and timing budget, Planning's sample
reference plus schema, track/vehicle calibration status, validation tolerances and feasibility
policy. Decide ownership of reference repair, speed conventions, seam interpolation and
low-speed handling. Then specify the controller-side reference adapter and tests. No racing-line
generator, velocity-profile optimizer, ROS integration or target deployment is included here.
