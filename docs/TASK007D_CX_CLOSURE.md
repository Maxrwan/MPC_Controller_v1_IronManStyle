# Task007D-CX — Studies 1 and 2 WORK protocol

Authoritative [Primary specification](TASK007D_CX_SPEC.txt), preserved byte-for-byte from the
user's file (which arrived with a duplicate `.txt` extension). The later WORK authorization
limits execution to Studies 1 and 2. Study 3, full laps, final architecture selection and
Performance/Efficiency freezing are **NOT EXECUTED — AWAITING ENGINEERING REVIEW**.

## Predeclared protocol (before new outcomes)

Base: `77ba86f28e24d2780d01b5b0058e5405dde3d6ec`. Keep all runtime source unchanged.
Reuse the frozen C worker construction: N8, dt .1, H .8, Q/R/W as specified, lambda=0,
alpha_vy=alpha_r=1, gamma2, original A predictor, TVLQR, model, solver, warm starts, reserve,
constraints and 0.08 m synthetic margin. Canonical state order and SI units are unchanged.
No random input; fresh processes set PYTHONHASHSEED=0 and native Accelerate SINGLE.

Study 1: 2 s, gamma2, 5 ms imposed codriver delay, start at s_abs=1 m with the exact retained
C1 state/Planning fixture. Variable A receives the retained steady 30 ms sequence and repeating
23/47/61/39 ms sequence. Reuse fixed C70 C1 evidence only after fixture/source audit and a
recorded-packet scheduler replay proves current physical events/inputs reproduce the retained
history. This replay is a compatibility check, not a fresh optimizer experiment. The two retained
source differences concern urgent-demand bookkeeping; neither retained run triggered urgent demand.

Study 2: 10 repetitions EACH of A, C70 and C80; 2 simulated seconds per run, same gamma2,
state, fixture and imposed 5 ms codriver delay. Runtime planner availability uses each fresh
measured `planner_total_time` (prediction + optimization + gain preparation). Startup preparation
is reported separately and excluded from runtime deadline denominators. No future duration enters
prediction. Measured codriver costs are descriptive; its physical delay stays imposed and matched.
This isolates preparation timing and is not a fully measured actuator/embedded timing campaign.
The balanced order rotates A/C70/C80 by repetition; preserve every attempted run and outlier.
Two seconds matches the accepted pilot, supports repeated deadline observations and avoids an
unauthorized full-lap extension. It limits sector/long-horizon conclusions. No reduction below
10 is planned; any resource-based reduction requires a recorded objective reason before resuming.

## Gates and decision method

Before either study: focused mathematical, model validity, chronology, diagnostic noninterference,
fixed scheduling and legacy fingerprint tests. No complete regression in WORK. Guard/disk floor
1 GiB before each worker; fresh output directories; no workers alongside tests, analysis, plotting,
compression or benchmarks. Record process checks, source/fixture/vehicle/environment hashes,
actual thread counts and CPU/wall ratio. Ordinary host activity remains a limitation.

Stop the affected study branch on boundary crossing, ANY predicted slack >1e-6 m (conservative
existing pilot gate), solver/preparation/model failure, invalid chronology/authority, unexpected
fallback/exhaustion, nonpositive reserve, or prerequisite parity/semantic failure. Save failures;
do not tune or repair controller semantics and continue. Rejected handoffs and incomplete coverage
are reported explicitly. Misses alone are outcomes: keep single-solve busy behavior and evaluate
consequences. No evidence is silently replaced.

Use the Primary priority ordering: validity, chronology, deadline reliability, reserve, jitter
robustness, smoothness, tracking, responsiveness, progress, computational cost. No composite score.
A candidate cannot win by sacrificing validity or reserve. A pending deadline at observation end
is censored, not a hit/miss. Report resolved denominator, ready/completed count, attempts, actual
miss consequences, per-run distributions/ranges and descriptive Wilson intervals for fractions
(with correlated cycles/host limitations). P99 is reported only with >=100 samples and labeled
empirical/unstable in small tails. No independence or real-time guarantee claim.

Study 1: compare exact common 10 ms event samples, wrap heading differences, retain all sample
residuals and separate states, requested/applied controls, reference, authority, reserve and
acceptance times. First numerical divergence threshold 1e-12 (reporting only). Also report first
engineering-scale difference: vx/vy .001 m/s, r .001 rad/s, epsi .0001 rad, progress/ey .001 m,
steering .0001 rad, acceleration .001 m/s2. These descriptive thresholds are not safety tolerances.
Keep absolute values and RMS; no threshold changes after outcomes. Progress interpolation is
supplementary, derived, restricted to observed overlap. Audit RK4 partitions and simultaneous events;
never change integration to force equality. Fixed and variable comparisons share timing histories
but also change forecast targets, which must remain explicit in causal interpretation.

Study 2: compare complete 0–1.99 s common-grid coverage and matched requested 2 s duration.
Preserve whole observed physical extrema separately (including off-grid samples), all misses,
packet age, first TVLQR use, acceptance latency, reserve and censored cases. Keep nominal/actual
variation distinct; use six wrapped state errors. Report per-run uncertainty, not pooled samples
as independent repetitions. Responsiveness is actual accepted authority latency, not just offset.
No full-lap/progress extrapolation or safety certification from center clearance.

Study 3 recommendation requires all gates, credible deadline/reserve behavior, a material reduction
in jitter sensitivity and a defensible quality/responsiveness tradeoff versus fresh measured A.
Mixed results or consequential tails support INSUFFICIENT EVIDENCE. Any recommendation is for
Engineering Review only; this assignment never launches Study 3 or changes defaults.
