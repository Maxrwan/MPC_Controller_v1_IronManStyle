# Task 007A — offline racing-reference interface and synthetic GP baseline

## Scope and department ownership

Planning owns the OFFLINE global racing line and velocity profile. The deterministic generator
in scripts/task007a/generate.py is temporary synthetic test infrastructure, not production
Planning. Runtime imports only apex.planning_reference to load, validate and interpolate files.
No generator or optimizer of global references runs while the simulated vehicle moves.
Future Planning files replace this fixture through the same contract.

The user authorized Task 007A following the pre-Task-007 review gate. The frozen runtime remains
always-active APEX NMPC at 10 Hz, a timestamped trajectory buffer and TVLQR at 100 Hz.
No adaptive switching, APEX bypass, Task 007B tuning, identification, energy or opponent logic.

## Synthetic Grand Prix v1 design

The track source is configs/planning/synthetic_grand_prix_v1/track_source.json. It stores 43
ordered SI control points, 0.30 m wheelbase scaling and constant 0.55 m left/right widths.
The existing periodic cubic centerline uses chord parameter internally and numerical arc length
publicly. No real circuit is copied. The 154.763 m lap slightly exceeds the approximate
80–150 m target to retain a well-separated return complex; no arbitrary rescaling was applied.

The long start straight leads east to a nominal 1.2 m-radius approximately 180-degree hairpin.
The short westbound exit leads into a nominal 3 m-radius medium corner. A lower 8 m-radius
sweeper turns the course north through a direction change. A second straight climbs toward
the top technical left/right section; a medium return complex closes onto the start straight.
Spline interpolation slightly changes ideal primitive radii. Sector starts are tied to named
source control-point indices and serialized as centerline arc progress in the manifest.
These are software validation dimensions, not identified APEX geometry or F1 speed scaling.

Closure, tangent and curvature periodicity use the existing spline implementation. Dense
polyline crossing checks are practical sampled checks, not an analytic no-intersection proof.
Projection consistency is checked independently in tests. Positive Frenet denominator and
corridor clearance are checked before reference use. The fixed 1.1 m total width is retained.

## Offline racing-line heuristic

At principal corner anchor indices 6, 11, 17, 31, 36 and 42, add signed periodic Gaussian
lateral-offset lobes: +0.22 m at the inside apex, -0.12 m at entry and exit relative to turn
sign. Width/separation pairs are (1,3), (1.5,4), (4,10), (1,3), (1.8,5), (1,3) metres.
Periodic copies at neighbouring laps ensure smooth blending. Overlapping lobes add; there is
no runtime clipping. Reconstruct world coordinates p_ref(s)=p_center(s)+e_y(s)n_center(s).
A periodic cubic through dense reconstructed points supplies tangent heading and geometric
racing curvature. e_psi_ref is tangent heading relative to centerline tangent, wrapped to ±pi.
This uses track width meaningfully but makes no claim of global time optimality.

## Offline speed heuristic

Use racing-line curvature, not centerline curvature, to set min(3 m/s, sqrt(1.5/|kappa_ref|)).
Apply cyclic forward/backward squared-speed feasibility passes using racing-line segment
lengths, +0.4/-0.6 m/s² limits, until converged. Samples are at most 0.05 m apart and include
a repeated closed endpoint. Runtime periodic cubic interpolation is validated at endpoints
and midpoints; its slight speed and acceleration overshoot is reported, not silently clipped.
Initial validation permits at most 2 m/s² lateral demand and +0.65/-0.85 m/s² speed derivative.
These conservative fixture acceptance thresholds are separate from actuator bounds +2/-3.
No near-limit speed search or production velocity optimizer is included.

## File contract, schema version 1

Required planning_reference.csv columns:

| Column | Meaning |
|---|---|
| s_track_m | Increasing centerline arc progress, 0 through one closed length |
| e_y_ref_m | Signed left-positive offset from centerline |
| e_psi_ref_rad | Nominal body heading relative to centerline tangent |
| kappa_ref_1pm | Signed racing-reference geometric curvature |
| v_ref_mps | Nominal body-longitudinal speed |

Optional a_ref_mps2 means **total longitudinal force divided by mass**, not dvx/dt.
If present, manifest acceleration_semantics must be total_longitudinal_force_over_mass.
This fixture omits it; the optimization input-reference acceleration is zero and APEX selects
longitudinal command from speed tracking. The model retains dvx/dt=a_cmd+r*vy.
Optional x_ref_m/y_ref_m/psi_ref_rad are validated geometry diagnostics. This fixture includes
them plus sector_name. World heading is unwrapped; relative heading is unwrapped before
interpolation and wrapped on output. Debug columns do not drive control.

planning_manifest.json requires schema/reference versions, track name and SHA256 of the
exact track_source.json bytes, generator/source revision, SI units, frame, centerline progress
convention, periodic_cubic_channels interpolation convention and closed length. Explicit
speed/body-heading/acceleration semantics and 0.08 m margin are required. This fixture also
records synthetic-test provenance, offline generator settings and sector start positions.
No wall-clock generation timestamp is necessary: deterministic revision and hashes identify
reproducible input. The source and files live under configs, not only ignored results.

## Runtime loader and validation

PlanningReference checks schema, track hash/length, units, conventions, required channels,
finite data, monotonic progress, dense sampling, duplicate-endpoint seam consistency and
heading bounds. It checks the fixed tracker margin, forward-racing heading, Frenet denominator,
model speed domain [0.5,6] m/s (no standstill), geometric heading/curvature consistency,
approximate grip/steering/rate demand, acceleration/braking and sampled self-intersections.
World-coordinate diagnostics, when supplied, must agree with the Frenet reconstruction.
Validation uses the current synthetic 0.30 m-wheelbase vehicle and its configured limits;
these limits must be reviewed when identified vehicle data replaces the synthetic vehicle.

Lookup wraps finite s_abs modulo the lap length, including multiple laps and negative lookup
coordinates. Physical canonical state progress remains nonnegative; negative reference lookup
is useful for seam tests only. It never extrapolates a nonperiodic tail. Malformed/infeasible
files raise errors before controller construction; runtime does not repair or regenerate them.
Periodic cubic interpolation covers geometry and speed; optional a_ref uses the same policy.

## Curvature audit and APEX adapter

The original seven preview rows remain unchanged for Task 006. Racing-enabled MPC uses 11:
centerline curvature, left/right physical widths, vx_ref, vy_ref, r_ref, delta_ff,
e_y_ref, e_psi_ref, racing curvature, a_ref. An explicit MPCConfig.racing_reference flag
must match the supplied reference object. The flag does not change costs, horizon or solver.

Dynamics, RK4 stage domain checks, physical boundary constraints and trajectory-packet
curvature retain row 0 CENTERLINE curvature. Racing curvature row 9 is used only to construct
nominal yaw-rate and feedforward steering. Stage and terminal costs now subtract nonzero
lateral and heading targets in racing mode. The original seven-row branch is preserved.
TVLQR follows the APEX packet states/controls; it does not directly follow the global file.

The preview's nominal centerline progress advances by
s_dot = vx_ref*cos(e_psi_ref)/(1-kappa_centerline*e_y_ref), using the explicitly zero nominal
lateral velocity. This is the existing Frenet relation with vy_ref=0, not racing-line arc length.
No SciPy spline enters the symbolic NLP; reference samples are numerical parameters.

## Reference-state baseline and approximations

For the loaded geometric tangent convention:

- vx_ref = supplied body-longitudinal speed;
- vy_ref = 0 (explicit zero-sideslip approximation);
- r_ref = vx_ref*kappa_ref;
- e_y_ref/e_psi_ref = supplied geometric offset/relative tangent;
- delta_ff = atan(wheelbase*kappa_ref), a geometric bicycle feedforward;
- a_ref = zero input-reference target when omitted, optional Fx_total/m otherwise.

These are NOT exact nonlinear steady tire-force equilibria. Finite sideslip, transient curvature,
longitudinal/lateral coupling and nonzero speed gradients create model/reference mismatch.
APEX remains responsible for dynamically valid local trajectories. No old centerline steady
cornering formula is silently presented as an exact racing-reference construction. The frozen
terminal schedule still interpolates at 1/2/3 m/s with clipping; the conservative profile stays
near this studied range. Improving reference-state consistency belongs to a reviewed later task.

## Frozen controller and chronology

Candidate C retains 10 Hz, N=4, 0.4 s, four RK4 substeps, exact Hessian, one native thread,
original costs, warm start, smooth combined grip and solver/failure policy. TVLQR retains
100 Hz, Q=diag(100,100,4,1), R=25, longitudinal gain 1, actuator limits and 1 rad/s slew.
The planner's 0.08 m per-side margin remains fixed. Planner preparation includes interpolation,
state prediction and gain preparation. During both planner and codriver computation physical
time advances under the prior applicable trajectory/command, using the unchanged AsyncRunner.

A gated rolling launch at s=1 m avoids the existing near-zero-progress optimizer roundoff
issue at s=0 without changing state validation. The first lap is a startup/transient partial
lap; subsequent laps are complete. No standstill dynamics are invented. Global fallback
retains the existing centerline baseline policy; it is not redesigned into a racing-reference
tracker. Any activation is reported as a limitation of the baseline.

## Future interfaces, not implemented policies

Difficulty logs observe trajectory lateral/heading/vy/r errors, both curvatures, estimated
lateral acceleration, actuator and tire utilization, packet age/reserve, planner prediction
residuals and timing. They never choose controllers. Future supervisory work may compare
cheap/cached feedback, TVLQR and small constraint-aware MPC with hysteresis while APEX remains
always active. No switching is implemented.

The independent loader/sample API and explicit reference-state construction permit a future
controlled direct-TV LQR versus APEX→TVLQR value study. Task 007A does not bypass APEX or run
that benchmark. Such work must define a fair direct-reference packet adapter separately.

## Results and readiness

The primary three-lap measured baseline and zero/injected support laps completed. Detailed
tables are in TASK007A_RESULTS.md. Do not infer near-limit readiness from an offline
feasibility pass alone. Review Task 007A before authorizing Task 007B.

### Primary measured chronology result

The frozen measured run completed its transient lap in 58.632885 s and subsequent complete
laps in 59.019681/59.009765 s (176.665715 s total from the s=1m rolling launch). It recorded
zero planner failures, zero boundary violations and zero global fallback. There was one skipped
planner release and four skipped codriver releases; measured latency and rare tails were retained.
Minimum/mean trajectory reserve was 149.376/349.180 ms, with 50.624 ms below the 200 ms warning
and no time below the 50 ms critical threshold. Maximum front/rear combined tire utilization
was 0.382725/0.305076. These establish conservative integration evidence, not near-limit performance.

Planner solve mean/p95 was 11.647/14.677 ms. Full preparation mean/p95/p99/max was
24.325/31.151/34.850/105.356 ms, including preview, prediction and TVLQR gain preparation.
Codriver full mean/p95/p99/max was 0.859/1.191/1.250/27.105 ms, including physical command
validation. Long tails are not a hard real-time guarantee. Final sector/error tables will
separate global racing-reference tracking from local APEX-packet tracking.

### Racing-reference and sector results

On comparable laps 2–3, centerline-progress-indexed lateral error to the offline racing line
has RMS 6.412 mm and maximum 37.621 mm; body-heading error RMS is 0.015781 rad and
maximum 0.099657 rad. Body-longitudinal speed error RMS is 0.135966 m/s and maximum
0.397572 m/s. These differ from local APEX-packet tracking: the codriver's whole-run lateral
RMS/p95/max is 0.391/0.739/5.144 mm. The online planner creates a feasible local trajectory
that need not exactly match all approximate offline nominal targets.

Comparable-lap lateral RMS by sector (mm): long straight 3.982, hairpin 18.136,
acceleration zone 4.085, medium corner 4.320, fast sweeper 0.806, direction change 2.169,
second straight 0.905, technical section 8.236, return complex 2.803. Full heading/speed/error,
actuator/tire, planner/codriver timing and reserve values are exported in sector_metrics.csv.
All errors are evaluated at actual centerline progress, not by nearest racing-line projection.

The full-run peak steering utilization is 95.33% of the 0.4 rad bound; physical rate utilization
reaches 100%. Comparable-lap maximum acceleration/braking commands are +0.351/-1.127 m/s².
Minimum comparable-lap physical boundary clearance is 0.335 m, with zero time consuming the
0.08 m reserved margin. Combined braking+turning occurs for 37.854 s and acceleration+turning
for 45.476 s over the three-lap run, using |estimated ay|>0.3 and |a_cmd|>0.1 m/s². The finite-
difference lateral-acceleration estimate spans -3.221 to +3.157 m/s²; this is observed actual
motion, not the offline approximate speed-curvature demand (maximum 1.508 m/s²).

The direct 10 ms nonlinear propagation of 310 geometric nominal states exposes an explicit
reference-state residual: maximum |vy_next-vy_ref_next| is approximately 0.0417 m/s and
|r_next-r_ref_next| approximately 0.0230 rad/s. Other channel residuals are exported in
reference_model_residuals.csv. This quantifies the zero-sideslip/geometric feedforward limitation;
it is not an optimizer shooting defect. No controller or physics was retuned to hide it.

Planner/codriver CPU demand is 0.241079/0.085437 core-seconds per simulated second,
0.326516 combined, excluding simulation integration, logging and transport. Effective rates
are 9.9906/99.9798 Hz. Three >10 ms codriver computations caused four skipped releases.
The measured Accelerate API reports SINGLE; average CPU/wall ratios are near one, but exact
native active thread counts are unavailable. These are host observations, not target hardware claims.

### Readiness assessment

The interface and conservative baseline are ready for review. Task 007B should begin only
after reviewing the nominal-state approximation, hairpin speed lag and steering headroom,
plus timing tails. Progressively increase difficulty only with explicit feasibility gates.
Do not jump directly to near-limit profiles or infer a need for adaptive codriver switching:
local packet tracking is already small, while the larger errors are against the offline target.
APEX remains always active and TVLQR remains the sole baseline codriver.

The sampled centerline radius minimum is 0.915 m; designed principal radii are 1.2/3/8 m.
Straight/transition radii tend to infinity as curvature approaches zero, so no finite global
maximum radius is physically meaningful. Both sampled offset boundaries have zero proper
crossings, and the full-width Frenet denominator minimum is 0.399. Seam position/heading/
curvature differences across a 1e-7 m seam neighbourhood are approximately 1e-7 m,
9.78e-9 rad and 8.84e-9 1/m. Numerical arc-length wrapping and projection tests pass.

## Final validation and provenance

479 full regression tests pass in 507.22 s; the focused interface suite passes all 23 tests,
including byte-identical regeneration of the committed CSV/manifest. Three asynchronous log
audits verify command hold, physical motion, packet availability, fixed releases and actuator
limits. All 157 active Python files pass lint/format. Twenty scientific plots are generated;
circuit labels and speed-tracking layout were visually reviewed. Source/fixture hashes for all
three runs match the final numerical implementation. Prior Task 006.4 artifacts are preserved.
Final validation logs, source archive and provenance are under results/task007a.

The implementation is complete for Task 007A. No Task 007B, switching, direct-reference controller
comparison, production Planning, identification, energy, opponents or deployment was implemented.
Reproduction commands are in TASK007A_REPRODUCTION.md.
