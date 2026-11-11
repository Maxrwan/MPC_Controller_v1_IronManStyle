# PRIMARY APEX — WORKBENCH V2 FINAL REPLAY IMPROVEMENTS AND FULL-LAP UNBLOCK

**Decision: ACCEPT V2 PRESENTATION DIRECTION; AUTHORIZE BOUNDED FINAL CORRECTION**

Repository: `Maxrwan/MPC_Controller_v1_IronManStyle`

Branch: `codex/workbench-v2-ui`

Starting delivery: `e45059cb0fff41a8610761e83bdd69c4a2dff1e2`

Reviewed UI: `b1cc8b3d7b306a56adf99a63d8dc689c13856114`

Frozen scientific source: `48adbdf64d492592d15e23c917aca71fa58aa8a5`

## Objective

Complete the final practical improvements to APEX Workbench V2, then enable and attempt its first genuine full-lap baseline simulation.

The current interface has passed hands-on Primary inspection and is accepted as the presentation foundation.

Do not redesign the interface again.

## 1. Follow-camera modes

Extend the existing Canvas replay with:

- Whole circuit — existing view.
- Recording window — existing view.
- Follow Vehicle — vehicle-centered camera with smooth translation.
- Follow Prediction — close-up automatically framing the current available NMPC horizon.

Preserve the existing elapsed-time browser clock, native data and playback controls.

Camera movement must be smooth, including during turns and packet handoffs.

Camera smoothing must not modify actual positions, timestamps or scientific measurements.

No additional simulation or optimization is authorized for visual testing.

## 2. Steering-wheel visualization

Replace the current two-tire steering graphic with a compact animated steering wheel.

Use the actual recorded applied front-axle steering angle, not a reconstructed tire angle.

Implement:

- Animated steering-wheel rotation.
- Actual steering command in radians and degrees.
- Optional nominal-command overlay.
- A clearly labeled configurable visual steering ratio, default 12:1.

The display angle is:

theta_visual = ratio × delta_applied.

This is an illustrative passenger-car-style steering-wheel mapping, not a measured steering-column or RC-servo relationship.

Do not implement Ackermann geometry, modify actuator calibration or change control commands.

## 3. NMPC Prediction Microscope

Upgrade the existing active-packet explorer into a visually useful close-up.

Automatically follow each genuinely available active trajectory packet during playback.

For each N=8 horizon:

- Render all nine actual predicted state nodes.
- Display the eight corresponding control intervals without inventing a terminal command.
- Display the relevant Planning racing reference.
- Allow a selected node with enlarged details.
- Show predicted lateral and heading tracking error at each node.
- Draw an interpretable lateral-error connector and heading-deviation indicator where supported.
- Display numerical errors in meters and degrees, with optional radians.
- Provide a label-visibility toggle for all nodes versus selected node only.
- Support manual inspection of historical packets without treating them as active or valid.

Use the genuine packet state ordering:

[vx, vy, r, e_psi, s_abs, e_y].

For each predicted state, evaluate the pinned Planning reference at the appropriate predicted progress using the existing accepted reference semantics.

Calculate:

lateral_error = predicted_e_y - reference_e_y

heading_error = wrap(predicted_e_psi - reference_e_psi)

These are racing-reference tracking errors, not actual-future prediction residuals.

Reconstructed reference values must be identified as derived. Do not fabricate missing native NMPC preview information.

Preserve packet completion, validity, timestamp coverage, control authority and correct actual-application chronology.

Only available, active packets may automatically drive the live explorer.

## 4. Playback practicality

Preserve the existing smooth browser playback.

The active prediction display must update during playback without requiring the user to pause.

Decouple camera animation from expensive annotations and diagnostics.

Retain the existing bounded recording payload and evidence-integrity checks.

For full-lap recordings, investigate lightweight window prefetch and automatic continuation between verified 10-second windows, avoiding a manual window switch where technically practical.

Never bypass per-window integrity validation or load an unbounded full-lap payload.

If seamless switching cannot be implemented simply, preserve the existing reliable window playback and report that limitation.

## 5. Full-lap resource correction

The previous full-lap gate rejected the conservative 551.42816-second CPU projection against a 480-second ceiling.

Authorize these changes to the dedicated V2 Full Lap profile only:

- Wall ceiling: 900 seconds.
- CPU ceiling: 720 seconds.
- RSS ceiling: unchanged at 768 MiB.
- Output ceiling: unchanged at 256 MiB.
- Single-file ceiling: unchanged at 4 MiB.
- Simulation ceiling: unchanged at 80 seconds.
- Lap-crossing and completion rules: unchanged.

Preserve the existing conservative pilot projection method.

Do not change accepted V1 limits, V2 Extended limits, controller mathematics, solver settings, vehicle dynamics or scheduling assumptions.

## 6. Restore legitimate V2 execution admission

Inspect the current V2 reviewed-WORK access policy and its exact producer hashes.

The UI changes were reviewed but V2 source bindings and resource admission have not yet been transitioned to an operational state.

Resolve this explicitly using updated, source-bound Primary authorization.

Preserve:

- The valid historical 10-second pilot.
- Its consumed attempt.
- The unused full-lap attempt.
- All earlier reviews, source hashes and retained numerical evidence.
- Existing worker ownership and resource enforcement.

Do not disable or bypass integrity checks or fabricate an earlier review.

Ensure the UI's full-lap status reflects the actual current execution policy rather than displaying the old historical resource decision as a permanent blocker.

## 7. Risk-proportional validation

Run focused automated and actual-browser checks for:

- Follow-camera movement and view switching.
- Steering-wheel mapping and nominal/applied distinction.
- All nine predicted nodes and eight controls.
- Lateral/heading error definitions and units.
- Missing reference or packet information.
- Automatic packet handoffs.
- No historical packet acquiring active authority.
- Browser playback timing and responsiveness.
- Full-lap resource admission and source binding.
- Cancellation, source-integrity rejection and retained evidence preservation.

Use one focused independent Engineering Review for changed scientific-display semantics and execution admission.

Do not repeat the entire historical scientific Verification campaign.

## 8. Conditional genuine numerical execution

After successful focused review, host-capacity preflight and source-identity checks, authorize one actual baseline Full Lap attempt using the existing synthetic GP gamma2 scenario.

No disturbance, weight changes, repeated pilot or automatic retry.

Retain the result even if the vehicle fails, reaches a resource limit or fails to complete a full circuit.

Report actual lap/sector timing and essential control metrics only if genuinely observed.

If successful, prepare a source-bound acceptance transition for ordinary repeatable, user-triggered V2 experiments within the existing finite approved profile.

Do not introduce automated parameter sweeps or expanded scenario families.

## 9. Completion

Provide:

- Exact implementation revision.
- Focused test results.
- Browser observations.
- Full-lap attempt result or clearly identified blocker.
- Source/policy integrity outcome.
- Launch instructions.
- Remaining limitations.

Stop at:

`WORKBENCH_V2_FINAL_READY_FOR_PRIMARY_ACCEPTANCE`

Do not implement ROS 2, Docker, System Identification, new control mathematics or other Workbench features.

**Priority: Finish a practical, visually informative racing-control laboratory and enable genuine full-lap experimentation.**