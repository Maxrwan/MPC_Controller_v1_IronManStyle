# Task007D-D4 — bounded A/B timing sensitivity

## Frozen protocol (declared before execution)

Starting point: clean main `784e86ff0aceb5f779b475fdfb6cf7d0d94912ec`.
Reuse D3's release capture, offline matched forecasts, target reconstruction, metrics and
conservative gates. No core predictor, scheduler, NMPC, TVLQR, estimator or model edits.

| Regime | Planner delay | Codriver delay | Active architectures | Duration per run |
|---|---:|---:|---|---:|
| D4-R1 | 35 ms | 0 ms | A, B | 2 s |
| D4-R2 | 35 ms | 5 ms | A, B | 2 s |
| D4-R3 | 60 ms | 5 ms | A, B | 2 s |
| D4-R4 | 60 ms | 15 ms | A, B | 2 s |
| D3 reference (retained) | 35 ms | 15 ms | A, B | 2 s |

Eight new runs maximum, sequential fresh SINGLE workers; never overlap with tests, rendering
or analysis. Run A then B within each regime, inspect the gate before continuing. A scientific
gate stops that regime branch; a semantic/causality defect stops all further execution for
review. Keep unsuccessful cases. Existing MEASURED_ACTIVE guard and 1 GiB disk floor remain.
No rerun of D3, full laps, measured repetitions or gamma 1.8 extensions.

Use exactly the D3 gamma 2.0 Planning package and reference-derived initial state at s_abs=1m.
N=8, dt=0.1s, H=0.8s, substeps=4; Q=diag(4,4,1,200,200), R=diag(25,1), W=diag(1,0.1),
lambda_s=0, alpha_vy=alpha_r=1, margin=0.08m, unchanged smooth combined grip, IPOPT/options,
primal warm starts, TVLQR, urgent policy, rolling estimator and variable-availability handoffs.
The pilot CLI gains explicit seconds-valued delay options, retaining its D3 35/15ms defaults.

Keep A-host and B-host physical histories separate. For each release, score both causal
forecasts against the same state at release+estimated delay. Reuse D3 angular wrapping,
labelled off-event reconstruction and censoring. Pending categories are none, due_now
(application at release within existing 1e-10s event tolerance), and future. A zero-delay
command can still be pending at release: never call it none. Do not alter grids to create
no-pending cases. Verify that contract with existing isolated tests if absent naturally.

Report all/first/subsequent runtime releases separately, with per-state signed mean, RMS,
max absolute error, p95 only for >=20 comparable releases, signed B-A RMS change, percent
reduction and per-release better/worse/tie counts. Compare absolute errors with a 1e-12 SI
roundoff tie band per channel; do not aggregate different states. Missing forecasts/truth
remain null, excluded explicitly. Log estimated target, imposed readiness and accepted
handoff separately for every release. Reuse same-time handoff continuity without relabeling
it as target prediction error. Physical comparison ends at the last common recorded time.

Scientific gates: any observed boundary crossing, predicted slack >1e-6m, solver/preparation/
model failure, chronology/authority violation, unexplained exhaustion, future-information
access, target reconstruction failure or offline active-forecast mismatch. Do not repair
core semantics or tune controller weights as part of D4.

## Outcome and decision boundary

**D4 complete; all eight prescribed runs finished.** No gate triggered, no runs were replaced,
and no additional urgent diagnostic or measured repetitions were launched. D3 gamma2 A/B
is reused as reference, with identical configuration, fixture/vehicle hashes, initial state
and every `src/` module hash verified. Architecture A remains the default.

**B lowers aggregate matched-target RMS in every state in every regime, including after the
first runtime release is excluded. Its advantage is not restricted to 15 ms codriver latency.**
However, this is not consistent per-release or post-transient superiority. At low latency,
large improvements in the first two releases outweigh numerous later increases in heading/
lateral error. At60/15ms, B also materially reduces physical clearance despite lower forecast
RMS. Retain B as a **research candidate**, with refinement/causal review justified before
selecting it for a future fixed-handoff architecture. Do not change production defaults or
interpret this as approval to implement Architecture C.

## Prediction accuracy by timing regime

Each of eight new runs has 19 releases and 19 comparable pairs: 152 new matched contexts.
D3 reference adds 38 historical contexts, kept separately. Both forecasts in a row share
release state/packet/applied/pending inputs, estimate, target and scoring history. A-host
and B-host trajectories are separate strata, not independent repetitions of one history.
All active forecasts match runtime NMPC inputs exactly (152/152); zero forecast failures,
missing targets or exclusions. Eighteen targets per run are recorded event states; one
(the first, 0.117 s) is labelled RK4 reconstruction. There is no future-truth correction.

Positive percentages below mean B RMS reduction; negative percentages mean deterioration.
State units are vx/vy[m/s], r[rad/s], e_psi[rad], s_abs/e_y[m]. There are no scalar aggregates.

| Regime / host history | vx reduction | vy | r | e_psi | s_abs | e_y |
|---|---:|---:|---:|---:|---:|---:|

| D4-R1_A | 99.86% | 97.46% | 97.73% | 83.85% | 63.67% | 83.35% |
| D4-R1_B | 99.86% | 97.46% | 98.04% | 86.55% | 65.78% | 86.16% |
| D4-R2_A | 35.17% | 66.08% | 80.10% | 57.13% | 37.83% | 56.38% |
| D4-R2_B | 37.02% | 65.36% | 83.24% | 63.82% | 40.16% | 62.91% |
| D4-R3_A | 44.45% | 77.19% | 89.20% | 77.05% | 36.93% | 63.93% |
| D4-R3_B | 48.12% | 80.75% | 91.64% | 82.18% | 41.26% | 71.16% |
| D4-R4_A | 39.38% | 78.35% | 30.94% | 45.24% | 43.53% | 47.32% |
| D4-R4_B | 38.92% | 78.02% | 29.53% | 44.02% | 43.18% | 46.03% |
| D3-ref_A | 28.88% | 16.74% | 47.06% | 69.12% | 57.13% | 69.50% |
| D3-ref_B | 28.08% | 17.14% | 47.18% | 69.11% | 56.90% | 69.48% |

Full signed means, RMS, maxima, changes and win/loss counts for every state, host and
first/subsequent stratum are in [accuracy_by_phase.csv](task007d/d4/accuracy_by_phase.csv).
P95 is deliberately null: only 19 total, 1 first and 18 subsequent samples per stratum, below
D3's predeclared 20-sample threshold. No confidence intervals or statistical independence
are claimed. Below are absolute primary A-host errors; B-host values are fully retained
in the CSV/JSON rather than pooled with them.

| Regime / state | A signed mean | A RMS | A max abs | B signed mean | B RMS | B max abs |
|---|---:|---:|---:|---:|---:|---:|
| D4-R1 / vx | -2.78373e-05 | 0.000186465 | 0.000774716 | -5.70568e-08 | 2.60653e-07 | 1.02376e-06 |
| D4-R1 / vy | 8.62656e-05 | 0.000353384 | 0.00152073 | 3.8253e-06 | 8.97041e-06 | 1.75588e-05 |
| D4-R1 / r | -0.000375895 | 0.0135859 | 0.0462959 | 0.000128998 | 0.000308829 | 0.000611048 |
| D4-R1 / e_psi | -4.73816e-05 | 0.000239197 | 0.000989255 | -1.78477e-05 | 3.8632e-05 | 7.44132e-05 |
| D4-R1 / s_abs | -6.5228e-07 | 3.27091e-06 | 1.30626e-05 | -5.4588e-07 | 1.18822e-06 | 3.81398e-06 |
| D4-R1 / e_y | -4.59933e-06 | 2.22701e-05 | 9.27419e-05 | -1.64303e-06 | 3.70726e-06 | 7.11833e-06 |
| D4-R2 / vx | -5.10313e-05 | 0.0001617 | 0.000601216 | -2.29147e-05 | 0.000104822 | 0.000456665 |
| D4-R2 / vy | 1.09782e-05 | 0.000202659 | 0.000739669 | 1.11121e-05 | 6.87393e-05 | 0.000209381 |
| D4-R2 / r | 0.00247372 | 0.00838995 | 0.0331036 | -8.27129e-05 | 0.00166967 | 0.0056971 |
| D4-R2 / e_psi | 2.43922e-05 | 0.000133645 | 0.000552532 | -2.33864e-05 | 5.729e-05 | 0.000172205 |
| D4-R2 / s_abs | -1.37036e-06 | 3.79091e-06 | 1.49349e-05 | -8.18621e-07 | 2.35669e-06 | 9.83222e-06 |
| D4-R2 / e_y | 2.24569e-06 | 1.2392e-05 | 5.0952e-05 | -2.18641e-06 | 5.40592e-06 | 1.5962e-05 |
| D4-R3 / vx | -5.83108e-05 | 0.000190163 | 0.000742797 | -2.33489e-05 | 0.000105641 | 0.000460278 |
| D4-R3 / vy | -0.000113236 | 0.000720665 | 0.00305049 | -1.3788e-05 | 0.00016442 | 0.000621968 |
| D4-R3 / r | 0.00276449 | 0.00871925 | 0.0346763 | -7.92055e-05 | 0.000941901 | 0.00326765 |
| D4-R3 / e_psi | 5.3649e-05 | 0.000315112 | 0.0013434 | -2.81376e-05 | 7.23196e-05 | 0.000163814 |
| D4-R3 / s_abs | -2.59541e-06 | 8.62664e-06 | 3.68565e-05 | -1.63358e-06 | 5.44049e-06 | 2.33661e-05 |
| D4-R3 / e_y | 3.88539e-06 | 3.34788e-05 | 0.000138089 | -4.93066e-06 | 1.20752e-05 | 2.5341e-05 |
| D4-R4 / vx | 0.000947568 | 0.00137954 | 0.00274628 | 0.000528321 | 0.000836281 | 0.00166821 |
| D4-R4 / vy | 0.000233215 | 0.00217149 | 0.00590519 | 4.69146e-05 | 0.000470134 | 0.00117943 |
| D4-R4 / r | 0.00403149 | 0.125324 | 0.155773 | 0.00298643 | 0.0865519 | 0.10821 |
| D4-R4 / e_psi | -2.83587e-05 | 0.00259894 | 0.00392075 | 2.33186e-06 | 0.00142307 | 0.00180231 |
| D4-R4 / s_abs | 3.57762e-05 | 4.81536e-05 | 0.000109771 | 1.87339e-05 | 2.71916e-05 | 6.06234e-05 |
| D4-R4 / e_y | -9.03336e-06 | 0.000244685 | 0.000397021 | -4.17117e-06 | 0.000128905 | 0.000181124 |

## First-release versus subsequent-release effect

The unchanged rolling estimator starts at 17 ms, uses the median of up to 10 observed readiness
delays and clips to [0,0.30] s. First runtime release is 0.100 s, target 0.117 s in every regime.
Readiness/accepted handoff is 0.135 s in R1/R2 (+18 ms relative to target), 0.160 s in R3/R4
(+43 ms). All subsequent estimates equal the imposed 35 or 60 ms and readiness/handoff minus
target is zero within event tolerance. The estimator was never reset or manipulated.
Every actual timestamp and processed/readiness distinction is retained in
[release_scores.csv](task007d/d4/release_scores.csv).

**After excluding only the first runtime release**, all six RMS improvements remain positive:

| Regime / host | vx reduction | vy | r | e_psi | s_abs | e_y |
|---|---:|---:|---:|---:|---:|---:|
| D4-R1_A | 99.54% | 84.05% | 97.09% | 83.30% | 18.36% | 82.77% |
| D4-R1_B | 99.62% | 83.69% | 97.68% | 86.28% | 38.45% | 85.83% |
| D4-R2_A | 24.03% | 47.44% | 80.37% | 57.45% | 33.94% | 56.26% |
| D4-R2_B | 26.86% | 29.89% | 84.01% | 64.25% | 36.82% | 62.93% |
| D4-R3_A | 38.03% | 77.11% | 92.84% | 77.28% | 36.24% | 63.94% |
| D4-R3_B | 42.98% | 80.86% | 94.88% | 82.39% | 40.73% | 71.18% |
| D4-R4_A | 39.26% | 78.29% | 30.92% | 45.24% | 43.54% | 47.32% |
| D4-R4_B | 38.80% | 77.96% | 29.51% | 44.02% | 43.19% | 46.03% |
| D3-ref_A | 27.50% | 16.38% | 46.98% | 69.13% | 57.49% | 69.50% |
| D3-ref_B | 26.62% | 16.79% | 47.10% | 69.11% | 57.26% | 69.48% |

That result alone overstates persistence in the low-latency cases. The per-release counts
showed a concentration of A squared error in release 2 (t=0.2s), so an **explicitly exploratory,
post hoc sensitivity check** also examines releases 3–19, without removing them from the
primary report or changing the predeclared endpoint. In the A-host histories, release 2 alone
accounts for 90.0%, 90.0%, 95.7% of total A heading squared error in R1/R2/R3; the first release
accounts for 8.5%, 2.3%, 0.4%. Thus the first 17 ms-estimate release is not the whole explanation,
but an early transition still dominates those aggregate heading RMS results. This is an
observed concentration, not proof of a particular numerical/physical cause.

| Exploratory releases 3–19, A-host | vx reduction | vy | r | e_psi | s_abs | e_y |
|---|---:|---:|---:|---:|---:|---:|
| D4-R1_A | 70.56% | 67.01% | 5.34% | -20.86% | 0.43% | -23.80% |
| D4-R2_A | -350.59% | 56.51% | -159.17% | -51.48% | 28.73% | -46.05% |
| D4-R3_A | -89.47% | -158.21% | -39.94% | -14.45% | 9.17% | -12.41% |
| D4-R4_A | 40.34% | 82.22% | 30.95% | 45.52% | 44.74% | 47.85% |
| D3-ref_A | 55.73% | 15.79% | 46.90% | 69.76% | 66.41% | 70.46% |

The B-host exploratory check agrees qualitatively: later heading/lateral RMS worsens at
0/5ms and improves at 15 ms. Those absolute errors are small; large percentages near a tiny
baseline are not evidence of physical instability. First-release progress is a clear
counterexample too: in R4 and retained D3, B's s_abs absolute error is 2.24827e-6 m versus
A's 2.04117e-7 m (about 11x), despite near-zero vx/vy/r error. Both values remain reported.

## Pending categories and codriver busy-tick sensitivity

| Regime | Per-run none / due_now / future | Codriver busy ticks per run | Planner busy ticks |
|---|---|---:|---:|
| R1 35/0ms | 0 / 19 / 0 | 0 | 0 |
| R2 35/5ms | 0 / 0 / 19 | 0 | 0 |
| R3 60/5ms | 0 / 0 / 19 | 0 | 0 |
| R4 60/15ms | 0 / 0 / 19 | 100 | 0 |
| D3 reference35/15ms | 0 / 0 / 19 | 100 | 0 |

Across the new matrix: 38 due-now and 114 future-pending contexts, zero naturally absent
pending commands. Zero latency still leaves a newly computed command pending at the
release phase; its physical application follows the existing same-time continuation.
The unchanged isolated no-pending fixture (`test_pending_and_no_pending[False]`) passed.
No scheduler change or artificial release was used to create coverage, and no extra urgent
experiment was needed. Existing urgent-release regression tests still pass.

RMS improvement without any skipped ticks (R1–R3) shows that skips are not a prerequisite.
However, later-release improvement is more consistent in the 15 ms regimes. This matrix
changes delay and skipped ticks together; it **cannot assign a causal percentage of benefit
to skipped ticks independently of latency or the changed closed-loop history**.

## Planner-delay sensitivity

At 5 ms driver delay, extending planner readiness from 35 to 60 ms retains aggregate RMS gains;
the A-host yaw reduction changes 80.10%→89.20% and heading 57.13%→77.05%. These are dominated
by early transitions and do not establish a generally better long-delay forecast. Absolute
A/B heading RMS both grow (0.000133645/0.0000572900 to 0.000315112/0.0000723196 rad).

At 15 ms driver delay, D3→R4 extends the forecast interval while retaining 100 busy ticks;
heading RMS reduction falls 69.12%→45.24% and lateral 69.50%→47.32%, while vy improves more.
A/B heading RMS rises 0.000468874/0.000144768 to 0.00259894/0.00142307 rad. B still approximates
all *future unknown* feedback computation latency as ideal after replaying the one known
pending command. No future duration/history enters either predictor. Longer propagation
exposes more of that existing approximation; attributing exact error components requires
another authorized causal investigation, not a silent change to the forecast model.

## Physical validity, smoothness and chronology

Each pair shares observed physical time 0–1.995 s (simulated end 2 s; the unchanged logger omits
the final endpoint), 400 common samples, identical release/estimate chronology, and identical
accepted packet IDs/timestamps. All 8 runs: 19 accepted handoffs, zero rejections, zero observed
boundary violations, solver/preparation/model failures, exhaustion or fallback. Maximum slack
is below 9.1e-11 m, well below 1e-6 m. Minimum reserve is 0.67 s for 35 ms planning and 0.645 s for 60 ms.

| Regime / active | Min center clearance (m) | Steering TV (rad) | Global heading TV (rad) | APEX ey RMS (m) | APEX e_psi RMS (rad) | Progress reached (m) |
|---|---:|---:|---:|---:|---:|---:|
| D4-R1_A | 0.4373138 | 0.1961563 | 0.2942497 | 0.0005419299 | 0.003698786 | 12.49532 |
| D4-R1_B | 0.4373138 | 0.2047517 | 0.2942512 | 0.0005467943 | 0.00380033 | 12.49525 |
| D4-R2_A | 0.4373138 | 0.2657637 | 0.3024385 | 0.0005617674 | 0.00440626 | 12.49721 |
| D4-R2_B | 0.4373138 | 0.2576134 | 0.3024391 | 0.0005830056 | 0.004430737 | 12.49718 |
| D4-R3_A | 0.4373138 | 0.2377572 | 0.3024791 | 0.0006915984 | 0.004686633 | 12.49436 |
| D4-R3_B | 0.4373138 | 0.2269206 | 0.3024794 | 0.0007256905 | 0.004704577 | 12.49433 |
| D4-R4_A | 0.2286613 | 0.9497829 | 2.069154 | 0.004377761 | 0.03790335 | 12.19164 |
| D4-R4_B | 0.1021847 | 0.9509112 | 2.071808 | 0.004143317 | 0.03617762 | 12.11434 |
| D3-ref_A | 0.2466621 | 0.943432 | 1.78859 | 0.003607407 | 0.03572488 | 12.20427 |
| D3-ref_B | 0.2479049 | 0.9320446 | 1.785702 | 0.003486185 | 0.03396975 | 12.20777 |

**R4-B clearance is a material adverse result:** 0.102185 m versus A's 0.228661 m, a 0.126477 m
reduction. Only 0.022185 m remains above the frozen 0.08 m tracking margin. B follows its active
APEX trajectory more closely in RMS yet reaches a less favorable physical clearance; these
are different metrics. No boundary gate triggered, but this rules out claiming an absence
of physical regressions. At zero latency B's steering TV and lateral/heading tracking RMS
also increase slightly. Small progress differences are not established racing gains.
Clearance concerns the recorded vehicle-center state, not a continuous swept body footprint.

## First A/B divergence and handoff distinction

First forecast divergence is at 0.1 s in all pairs. First changed applied command follows
acceptance and an eligible codriver update; states remain identical until propagation.

| Regime | First accepted runtime handoff | First changed applied command | First observed state split |
|---|---:|---:|---:|
| D4-R1 | 0.135 | 0.140 | 0.145 |
| D4-R2 | 0.135 | 0.145 | 0.150 |
| D4-R3 | 0.160 | 0.165 | 0.170 |
| D4-R4 | 0.160 | 0.175 | 0.180 |
| D3-ref | 0.135 | 0.155 | 0.160 |

There is no premature packet authority. The compact summary retains the preceding command
and handoff events, per-state same-time handoff continuity RMS/max, and all chronology audits.
Target errors remain distinct from nominal-to-actual error at accepted handoff: for example,
first acceptance occurs 18/43 ms later than the initial forecast target. The old readiness
`prediction_error` was not substituted for target-aligned scoring.

## Individual releases where B is worse

Counts below are **better/worse/tie** per state on A-host histories, using the declared
1e-12 absolute SI tie band. Full B-host and first/subsequent counts are in the CSV.

| Regime | vx | vy | r | e_psi | s_abs | e_y |
|---|---|---|---|---|---|---|
| D4-R1_A | 19/0/0 | 19/0/0 | 18/1/0 | 3/16/0 | 18/1/0 | 3/16/0 |
| D4-R2_A | 6/13/0 | 18/1/0 | 2/17/0 | 2/17/0 | 18/1/0 | 2/17/0 |
| D4-R3_A | 8/11/0 | 4/15/0 | 3/16/0 | 4/15/0 | 18/1/0 | 4/15/0 |
| D4-R4_A | 18/1/0 | 18/1/0 | 19/0/0 | 19/0/0 | 17/2/0 | 19/0/0 |
| D3-ref_A | 18/1/0 | 17/2/0 | 19/0/0 | 19/0/0 | 17/2/0 | 19/0/0 |

The largest **absolute-error increase for each state** across the new matrix is shown below;
this comparison never mixes units across states. These are observed regressions, not failures
invented from a scalar score. All raw outcomes are retained.

| State | Regime / host | Release (s) | A absolute error | B absolute error | Increase |
|---|---|---:|---:|---:|---:|
| vx | D4-R4_A | 0.2 | 0.000299773 | 0.00070815 | 0.000408377 |
| vy | D4-R4_B | 0.2 | 0.000521545 | 0.00117946 | 0.000657919 |
| r | D4-R2_A | 0.3 | 0.000645433 | 0.00293864 | 0.00229321 |
| e_psi | D4-R2_A | 0.3 | 3.1261e-05 | 0.000172205 | 0.000140944 |
| s_abs | D4-R4_A | 0.2 | 7.57255e-06 | 2.4595e-05 | 1.70224e-05 |
| e_y | D4-R2_B | 0.3 | 1.67869e-06 | 1.45767e-05 | 1.2898e-05 |

## Limits, verification and recommendation

This is one synthetic fixture/start, one deterministic run per active architecture/regime,
and a 2 s interval. No-pending releases, longer traversals, independently varied busy behavior,
measured delays and other starting positions remain untested physically. P95 is unavailable
at this sample size. Reconstruction reuses the approved independent plant and has zero full
bracket closure error in all 8 new runs; the largest partial/two-half-step difference in any
channel is 4.08489e-11 (r, rad/s), not a rigorous physical-error bound. The new campaign contains 152 paired contexts; the retained gamma2 D3 reference contains 38.
All physical histories and estimator observations are scoring-only after capture.

The primary aggregate result is favorable across timing, but a recommendation of universally
better application-state prediction would be unsupported. **Keep B as a candidate, not the
selected predictor for Architecture C.** Refinement review is justified by low-latency later
errors and R4-B clearance loss. Recommended next bounded assignment: an event-level causal
audit of release 2/3 in R1–R3 and the R4-B clearance deterioration, separating known-prefix
benefit, future ideal-latency approximation and NMPC/trajectory changes. Any refinement or
new runs require authorization; no controller tuning, predictor repair or C implementation
was performed in D4.

Verification: 133 focused tests passed in 7.94 s (17 new D4 cases plus 116 retained), including
exact Architecture A default fingerprints, capture/RK4 noninterference, D1 pending/no-pending,
zero/injected/measured timing contracts, causal shadow isolation, timestamp classification,
first/later stratification and explicit excluded-case accounting. Existing tolerances were
unchanged. Scoped Ruff check/format passed. Every worker configured Accelerate SINGLE before
numeric imports and observed one OS thread at preparation entry/exit; CPU/wall ratios range
0.9466–0.9972 (descriptive, not performance claims or proof of absence of transient threads).

Execution configuration is serialized per run, including the frozen MPC/plant/tire/cost
configuration, fixed timings, initial state, fixture/source/vehicle hashes and native policy.
IPOPT retains max_iter=100, tol=1e-7, acceptable_tol=1e-6, constr_viol_tol=1e-7, bound_relax_factor=0,
honor_original_bounds=yes, warm_start_init_point=yes, print_level=0/sb=yes, print_time=false,
error_on_fail=false; primal warm starts remain enabled, without dual initialization. Source
hashes retain exact model/solver implementations. No prior evidence was overwritten.

Raw evidence (~10MiB) is under `results/task007d/d4/`; the compact review bundle (~520KiB) is
under `docs/task007d/d4/`. D3 reference files are read-only inputs. The first export is retained
in a scratch directory; final export includes the explicitly post hoc transient audit.
All four final compact exports reproduce byte-for-byte in a fresh scratch directory.
Preservation check: 407 other preexisting Git files remain SHA-256-identical, including all
core source, D3 docs/evidence and original tests. Only the two authorized script files and
current handoff changed among existing files. All 10,873 preexisting result files retain their
sizes/mtime (metadata check, not a fresh bulk content-hash audit). New raw results were never
added to Git. The numerical model, predictor and physical scheduler were not edited.

## Reproduction

Use a fresh output root and confirm no MEASURED_ACTIVE campaign. Run commands **sequentially**,
inspect each `summary.json.stop_gate` and exit status before continuing. A failed branch is
preserved, not replaced. The existing1GiB floor and shared `results/task007d/D3_ACTIVE` lock
protect both D3 and D4 launchers. Original CLI defaults remain 35/15 ms.

```sh
.venv/bin/python scripts/run_task007d_pilot.py --architecture A --gamma 2 --planner-delay .035 --codriver-delay 0 --output results/task007d/d4_repro/R1_A
.venv/bin/python scripts/run_task007d_pilot.py --architecture B --gamma 2 --planner-delay .035 --codriver-delay 0 --output results/task007d/d4_repro/R1_B
.venv/bin/python scripts/run_task007d_pilot.py --architecture A --gamma 2 --planner-delay .035 --codriver-delay .005 --output results/task007d/d4_repro/R2_A
.venv/bin/python scripts/run_task007d_pilot.py --architecture B --gamma 2 --planner-delay .035 --codriver-delay .005 --output results/task007d/d4_repro/R2_B
.venv/bin/python scripts/run_task007d_pilot.py --architecture A --gamma 2 --planner-delay .060 --codriver-delay .005 --output results/task007d/d4_repro/R3_A
.venv/bin/python scripts/run_task007d_pilot.py --architecture B --gamma 2 --planner-delay .060 --codriver-delay .005 --output results/task007d/d4_repro/R3_B
.venv/bin/python scripts/run_task007d_pilot.py --architecture A --gamma 2 --planner-delay .060 --codriver-delay .015 --output results/task007d/d4_repro/R4_A
.venv/bin/python scripts/run_task007d_pilot.py --architecture B --gamma 2 --planner-delay .060 --codriver-delay .015 --output results/task007d/d4_repro/R4_B
VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/report_task007d_timing.py --input results/task007d/d4_repro --reference results/task007d/d3 --output results/task007d/d4_repro_compact
```

The last command analyzes saved evidence only, after all workers exit. Review files contain
full precision rather than the rounded document values. Focused verification command:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python - <<'PYTEST'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import pytest
raise SystemExit(pytest.main(['-q',
    'tests/unit/test_timing_sensitivity.py',
    'tests/unit/test_prediction_diagnostics.py',
    'tests/unit/test_committed_prefix.py',
    'tests/unit/test_committed_prefix_runtime.py',
    'tests/unit/test_async_chronology.py',
    'tests/unit/test_trajectory_tracker.py',
    'tests/unit/test_diagnostic_timing.py']))
PYTEST
.venv/bin/ruff check scripts/run_task007d_pilot.py scripts/task007d/worker.py scripts/task007d/sensitivity.py scripts/report_task007d_timing.py tests/unit/test_timing_sensitivity.py
.venv/bin/ruff format --check scripts/run_task007d_pilot.py scripts/task007d/worker.py scripts/task007d/sensitivity.py scripts/report_task007d_timing.py tests/unit/test_timing_sensitivity.py
```

**STOP AFTER D4.** Await Engineering Orchestrator review. Task007D remains incomplete.
