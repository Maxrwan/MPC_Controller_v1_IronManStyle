# Task 007C — near-limit formulation diagnosis

Status: stopped at the reproduction gate; both unchanged repetitions of E/F fail to reproduce
the original rejected behavior. C1–C4 below remain an unexecuted protocol. Task 007B is explicitly accepted. No diagnostic controller
changes may be tested until all six anchors are reproduced, including the rejected high-demand
behavior. The study may report unresolved causes; it must not force a final controller.

## Frozen controls

Planning line, curvature, track, speed-generation method and gamma scaling remain fixed.
Plant equations, combined-grip law, parameters, integration, actuator limits and chronology are
unchanged. Always-active APEX remains at 10 Hz; TVLQR remains the sole 100 Hz codriver.
No scheduler, adaptive codriver, global Planning optimizer or physical-model work is authorized.

## Ordered experiment protocol

1. Reproduce anchors A–F with the archived Task 007B fixtures and unchanged controller source.
   A/B: gamma=1, lambda=0/2, three laps. C/D: gamma=2, lambda=0/2, three laps.
   E/F: gamma=2.5, lambda=1/2, one-lap screens matching the original rejected cases.
   Compare complete laps separately from rolling-start screens. Retain every outcome.
2. C1: lambda=0, gamma=1.5,1.6,1.7,1.8,1.9,2,2.1,2.2. Reuse the anchor at gamma=2 when
   appropriate. Repeat only informative points with lambda=2.
3. C2: keep N4, dt=0.1 s, lambda=0 initially. At gamma=1.8 and 2, test alpha pairs
   (1,1),(.5,1),(.25,1),(0,1),(1,.5),(1,.25),(1,0),(.25,.25),(0,0).
   Include a high-demand point if physical validity permits, then a minimal progress-enabled
   follow-up. Do not combine a horizon change with these initial ablations.
4. C3: retain baseline dynamic-state costs; vary N=4/6/8 with dt=0.1 s and four RK4 substeps
   fixed. Use gamma=1.8,2,2.1 and a known oscillatory case if feasible. Lambda=0 first;
   progress-enabled follow-up only where informative.
5. C4: baseline costs/horizon, selected transition gamma values, static lambda=0,.5,1,2,4.
   Reuse prior cells. Report fastest safe, smoothest safe, first observed degradation and
   whether any positive reward helps. No combined score or final scheduling function.

Benchmarks are serialized fresh native SINGLE workers. No tests, rendering or bulk analysis
compete with measured workers. Zero/injected cases are chronology support, not primary timing.
Screen first; confirm useful comparisons with two complete laps. Physical domain/boundary/fallback
failures trigger review before repeating that region. Rejected cases remain in all reports.

## C2 equations to implement only after the anchor gate

Stage error order is [vx,vy,r,epsi,ey]. Candidate C becomes
Q_stage = diag(4, 4*alpha_vy, alpha_r, 200, 200).
Existing control, increment, progress and slack terms are unchanged. Multipliers are finite,
nonnegative and default to one. Nonlinear states and all their constraints remain in the NLP.

The separate terminal DARE retains the existing 100 Hz linear design model and steering R=25.
Its state order is [ey,epsi,vy,r], and
Q_DARE = diag(100,100,4*alpha_vy,alpha_r).
At each existing speed node 1/2/3 m/s, solve the same discrete Riccati equation with that Q.
Interpolate the resulting P schedule exactly as before. Preserve terminal speed weight 4.
Never zero rows/columns of P manually. Verify symmetry, PSD, Riccati residual and stabilizing
closed-loop poles, including alpha=0. This schedule belongs only to the NMPC terminal cost;
TVLQR's own gain construction stays unchanged.

## Oscillation measurement protocol

Keep within-prediction and realized active-plan measurements distinct. For every accepted NLP
trajectory, report steering/heading/ey/vy/r total variation, steering-rate reversals, rate-limit
activity, and steering/heading peak-to-peak range. Heading is unwrapped before variation.
Use actual stage dt for input increments; separate a packet's within-horizon metric from changes
between replans. Active-packet steering is zero-order held, so its jumps must not be described
as continuous steering-rate violations. Actual applied rate retains the existing physical audit.

For sector/lap comparisons, reset differences at each separate traversal. Report raw totals,
per-second/per-meter totals, reversal counts and peak-to-peak ranges. Exclude numerical chatter
with an explicitly reported small derivative deadband and check sensitivity. Compare to nominal
geometric activity so expected direction changes are not automatically called oscillation.

Onset is a vector of observations, not a scalar score: repeated extra reversals, increased
planned heading/lateral/dynamic-state variation, persistent actuator-rate activity, physical
feasibility margins and visual coherence. Any relative inspection thresholds must be reported
alongside the individual measurements; no single threshold alone establishes the conclusion.

## Interpretation

Distinguish Planning demand limitation (smooth feasible adaptation), APEX formulation limitation
(undesirable plan before local tracking fails), codriver limitation (reasonable plan but poor
local tracking), and mixed/unresolved evidence. Nonzero beta is neither intrinsically bad nor
unconditionally acceptable. Analyze hairpin, technical section and fast sweeper separately.
The optional temporary progress gate is not automatic: it is permitted only if C4 gives clear
support for that isolated diagnostic. Production scheduling and adaptive codriver remain deferred.

Horizon comparisons must not equate a longer observation window with more oscillation.
Within-prediction exports retain full-horizon totals, time/distance-normalized variation and a
common first 0.4 s prefix for N4/N6/N8. Sector comparisons use the same physical region.
