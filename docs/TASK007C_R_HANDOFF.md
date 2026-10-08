# APEX handoff — Task007C-R complete

Updated 2026-10-05. Only Task007C-R was performed. Task007C C1–C4 remain unexecuted.
Prior Task007C handoff is preserved in `docs/TASK007C_HANDOFF.md`.

## Gate and next authorized scope

**YES: scientifically safe to resume original C1–C4 intent.** The failed reproduction is resolved:
restoring original physical delay histories reproduces the original rejected E/F states,
commands, predictions and handoffs exactly. This is not physical safety approval for E/F.
Keep always-active APEX and fixed TVLQR. No controller mathematics was improved in this task.

Recommended continuation: original Task007C C1–C4 with matched fixed/replayed physical timing to
isolate formulation effects, followed by serialized measured repeats. Retain all failures and
distributions. Do not change scientific intent or infer improvement from one convenient run.
Adaptive switching and later features remain deferred.

## Verified findings

- R1: ten E, ten F and two C fixed planner35 ms/codriver1 ms runs; all pairwise state, prediction,
  control, warm-start, input, objective, iteration and tracking differences exactly zero.
- R2: five E, five F original-history replays; exact pairwise and original/replay agreement.
  E sweeper TV6.328775414 rad / rate saturation2.35 s; F slack0.027471299 m / clearance0.060095466 m.
  Stable C first-lap prefix also matches exactly (old C covers three laps).
- R3: E/F cross histories exhaust codriver traces; retain supported prefixes without invented tail.
  E under F: slack0.031305 m, clearance0.055730 m. F under E: slack0.139694 m,
  clearance−0.062492 m. Both cover the analyzed sectors.
- R4: ten E and ten F sequential measured runs; all lap completions retained. Sweeper TV>3 rad
  in2/10 each; material slack in0/10 E and5/10 F; boundary crossing in1/10 F.
- R5/R6: nine selected roles, eight unique NLP requests; E before/first-divergence coincide.
  All180 repeats and fresh solver reconstructions match captured solutions exactly.
  All45 warm-start variants and90 state probes succeed without material alternative branches.
- R7: E plan100 at t10 s / source progress43.337091502 m; one planner delay changed by
  −5/−2/−1/+1/+2/+5 ms. All pre-intervention states and selected NLP solutions match.
  Next optimizer inputs differ at10.1 s. Completed laps: −1ms31.427644329 s,
  +1ms31.746225688 s, +5ms32.161077088 s vs baseline32.206657233 s.
  Other probes exhaust the trace at32.21 s. No delay tail was invented.
- Classification A+B: deterministic under fixed history and latency-history sensitive.
  No observed identical-input solver nondeterminism or alternate warm-start branch in sampled
  requests. Local state probes do not establish a separate pure-state closed-loop causal effect.

## Validation and preservation

518 regression tests passed in785.22 s. Scoped Ruff checks passed. Independent chronology audit
passed62 asynchronous cases (61 study runs plus one smoke case). Configuration audit covers all61
study runs, exact fixture bytes, vehicle YAML/captured values, frozen runtime/config/options and
original Task007C E/F anchors. Early B0's missing old loader body is not reconstructed; all1765
retained old previews match current lookup exactly. Historical675 Task007B and293 Task007C
artifact hashes are preserved; final source/result manifest and ZIP are in the result directory.

Backend: Python3.12.14, CasADi3.8.1, IPOPT3.14.19, installed MUMPS/Accelerate, native SINGLE.
Separate100-solve CPU/wall0.999857 and max observed process threads1 at20 ms polling. Measured
campaigns had no concurrent tests/analysis. Offline sensitivity solve times are not benchmarks.

## Scope of edits

Only preexisting runtime change: `src/apex/simulation/asynchronous.py` optional `timing` keyword
and explicit replay exhaustion. New runtime module: `src/apex/simulation/diagnostic_timing.py`.
Normal measured timing remains default. Study-only exact-NLP capture wraps the solver in
`scripts/task007cr/`; it does not change controller/plant/model/options/TVLQR mathematics.
Full-regression timing tests cover zero/injected/measured behavior, skipped deadlines, held
commands, moving physics, replay exhaustion, exact request reconstruction and overwrite protection.

## Read next

- `docs/TASK007C_R_RESULTS.md`: required36-section final report and gate evidence.
- `docs/TASK007C_R_REPRODUCIBILITY.md`: frozen protocol, timing definitions and caveats.
- `docs/TASK007C_R_REPRODUCTION.md`: commands; do not overlap measured runs with numerical work.
- `results/task007cr/DISTRIBUTIONS.md`, `outcomes.csv`, `outcome_distributions.json`.
- `repeatability.json`, `first_divergence.json`, `timing_sensitivity.json`, `numerical_summary.json`.
- Eight required figures and two14-panel telemetry overlays under `results/task007cr/`.
- `configuration_audit.json`, `backend_audit.json`, `verification.json`, `provenance.json`.

## Limits that must remain visible

Reproducibility does not establish safety: all fixed-history F repeats cross the boundary.
The data are synthetic, not measured APEX parameters. Finite trace exhaustion censors lap results.
Ready time differs from accepted handoff; changed delays also alter the estimator and partition
RK4 integration. Do not claim isolated continuous-time causality or chaos. Old exact guesses/
duals were unavailable; new equivalent requests were captured during exact history replay.
Instrumentation copy overhead remains within measured availability; serialization is post-run.
