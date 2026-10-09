# Task007C resumed C1–C4 — final scientific review

2026-10-08. The original Task007C gate-stop reports remain historical evidence; Task007C-R
passed that gate and this report covers the resumed formulation study. All results concern
the configured synthetic vehicle and synthetic Grand Prix reference. Production defaults are
unchanged. Final audits passed:155 formulation configurations,160 asynchronous cases and all original
B/C/CR artifact hashes. The causal replay and final inventory are complete. Stop for review.

## 1. Task Completed

C1–C4 grids, retained-history comparisons, exact N6/N8 repeats, zero/injected checks, eight
sustained confirmations and twenty fresh measured repetitions are complete. The first crossing
starts at s_abs=1m; sustained cases request three crossings to obtain two subsequent full laps.
Finite histories are never padded. Failures and censored records remain in the evidence.

The decision order is physical validity, solver/domain validity, smoothness, outcome precision,
local tracking, then performance. The required four axes precede performance here:

| Axis | Baseline N4, gamma2 | N6, gamma2 | N8, gamma2 | N6, gamma2.2 upper stress |
|---|---|---|---|---|
| Reproducibility | Exact default parity with retained CR trajectory | Exact fresh fixed-history repeat across states, controls, handoffs and full NLP data | Same exact repeat result; horizon-specific decision layout checked | Five retained histories; exact N6 repeat checked at gamma2, no separate gamma2.2 exact pair |
| Accuracy | Fixed/smooth one-step ey RMS 1.43–1.45e-7m; realized accepted step4 ey RMS 0.0245–0.0265m | 1.35–1.38e-7m; step4 ey 0.02316–0.02318m | 1.31–1.34e-7m; step4 ey 0.01744–0.01999m | Worst measured heading-TV case: one-step ey RMS 1.58e-7m; step4 ey RMS 0.02563m |
| Precision | Five measured completions; heading TV 12.135–19.107rad; tracking ey RMS 1.553–2.137mm | Four completions and one retained trajectory-exhaustion failure; completed heading TV 8.732–9.976rad; all-record tracking RMS 1.319–1.970mm | Five completions; heading TV 8.179–8.417rad; tracking RMS 1.261–1.307mm | Five completions; heading TV 8.901–10.069rad; tracking RMS 1.431–1.916mm |
| Smoothness | Across five retained histories on common progress: epsi TV 10.278–28.651rad | Same interval: 8.214–8.495rad; sustained improvement is not uniform on every lap | Same interval: 6.916–7.496rad; lower steering variation/rate-limit duration, but feedback reversals remain | Retained-history common-prefix TV 8.748–9.274rad; third smooth full lap grows to11.530rad |

Accuracy here means internal synthetic consistency, not measured-vehicle accuracy. Realized
horizon errors include subsequent feedback/replanning. Precision ranges are descriptive, not
confidence bounds. The measured all-formulation common prefix ends at97.042m because N6
failed; its low whole-record TV cannot be compared with completed rolling segments. See
`TASK007C_MEASURED_RESULTS.md` for both common-progress and individual whole-record tables.

Only after the four axes, compare useful performance:

| Configuration | Measured completed rolling segments | Rolling time range s | Median s | Observed whole-record progress-rate range m/s |
|---|---|---|---|---|
|gamma2 N4|5/5|31.223–31.793|31.404|4.836–4.925|
|gamma2 N6|4/5|30.918–31.055 (completed only)|30.979 (completed only)|4.951–5.122 (includes shorter failure)|
|gamma2 N8|5/5|30.932–30.963|30.957|4.966–4.971|
|gamma2.2 N6|5/5|29.756–29.846|29.778|5.152–5.167|

N8's gamma2 median is0.447s faster than N4, after the higher-priority evidence is considered.
N6's failed shorter record must not be promoted because its partial-route progress rate is
higher. Progress rate is accumulated progress divided by observed physical duration, with
coverage shown separately. Planning speed shortfall is reported in section20. On the two full
sustained laps, gamma2 N8 times are31.185/31.173s fixed and31.152/31.123s smooth, versus N4
31.401/31.729s fixed and31.479/31.511s smooth.

## 2. Task 007B Anchor Reproduction

Task007C-R established exact original E/F replay under their original availability sequences,
exact fixed-timing repeatability and identical outputs for identical NLP inputs. Sampled warm
starts did not show competing solution branches. Fresh measured histories need not recreate
an old trajectory. This resumption retains exact baseline full-screen parity and all original
B/C/CR evidence. The prior B0 loader-source limitation remains documented in the CR report.

## 3. Fine Aggression Transition Map

All eight gamma values1.5–2.2 were screened with N4, baseline weights and lambda0 under fixed
and smooth histories; lambda2 was added at1.8/2.0/2.1. Fixed heading TV rises from10.204rad
at1.9 to11.993 at2.0 and24.807 at2.2. Smooth1.9 already gives14.770rad, worse than smooth2.0.
The transition is nonmonotonic. Exact beta, utilization, adaptation, slack and iteration data
are in `comparison.csv` and `TASK007C_C1_FIXED_SCREEN.md`.

## 4. Oscillation Metrics

Retained metrics include unwrapped Frenet epsi/ey/vy/r variation, steering variation, peak-to-peak
excursions, rate-limit time, reversal deadband sensitivity, accepted-packet variation over the
same first0.4s, rolling windows and separate sector/lap traversals. "Heading TV" means Frenet
epsi, not global yaw. Raw packet variation and stitched active-reference variation are distinct.
Phase portraits retain loops driven by changing corner demand; they are not autonomous
limit-cycle proofs.

## 5. Identified Transition Region

Sensitivity emerges around1.9–2.0 across beta, tire usage, rate-limit occupancy, variation and
timing-history spread. Baseline2.2 has a much sharper deterioration and a fixed-history
boundary crossing. No single beta, utilization or gamma threshold defines acceptance.

## 6. Baseline Dynamic-State Reference Formulation

Planning supplies geometric and speed intent. Control constructs vy_ref=0 and
r_ref=v_ref*kappa_ref. The canonical nonlinear states remain [vx,vy,r,e_psi,s_abs,e_y].
Baseline stage Q is diag(4,4,1,200,200) for [vx,vy,r,e_psi,e_y], R=diag(25,1),
W=diag(1,0.1). Plant, symbolic model, constraints, TVLQR and solver settings remain frozen.

## 7. vy Reference Ablation

The full approved grid and follow-ups are retained. Half-vy improves the initial gamma2
fixed/smooth screens but does not generalize to1.8, gamma2.1 smooth or gamma2/lambda2.
It fails pathological E in the fast sweeper:59 boundary samples, clearance−0.033446m.
Reject half-vy as a robust finalist; do not lower its weight globally.

## 8. Yaw-Rate Reference Ablation

Reducing yaw tracking generally worsens oscillation. Zero yaw weight at gamma2/smooth gives
62 boundary samples on the hairpin approach, minimum clearance−0.040392m. Keeping the yaw
state while removing its cost is not evidence that the resulting trajectory is preferable.
Retain alpha_r=1.

## 9. Combined vy/r Ablation

Combined(.25,.25) at gamma2/fixed gives159 boundary samples and max ey0.814420m near technical
entry. The zero/zero and all other approved combinations remain in the grid, including their
unfavorable smoothness results. No combined cost weakening is recommended.

## 10. Terminal-Cost Consistency

Independent nonnegative alpha_vy/alpha_r scale the stage costs and compatible terminal DARE
construction. Terminal design Q uses [ey,e_psi,vy,r] with diag(100,100,4*alpha_vy,alpha_r),
R=25 and unchanged100Hz design/speed-node interpolation. Full P coupling is retained.
Twenty-seven DARE solutions were checked; default weights reproduce the previous P exactly.

## 11. Sideslip Results

In measured gamma2 runs, max |beta| ranges0.309–0.318rad for N4,0.163–0.168 for N6 and
0.140–0.144 for N8. N6 gamma2.2 reaches0.187–0.226rad. Nonzero beta is physically expected;
it is judged with force usage, trajectory quality and tracking, not penalized by an invented
safety threshold. The phase portraits expose the large N4 hairpin excursion.

## 12. Hairpin Diagnosis

Baseline gamma2.2/fixed crosses the boundary at s21.097–21.345m, max ey0.569740m,
slack0.100121m. The solver succeeds and the physical vehicle follows an already unsafe APEX
nominal. Horizon benefits here are smaller and not uniformly monotonic: gamma2 N8 fixed
hairpin steering TV is slightly above N4. This sector cannot be summarized by whole-lap TV.

## 13. Technical-Section Diagnosis

This is the strongest consistent horizon benefit. At gamma2/fixed, planned epsi TV is
4.304→3.462→2.182rad for N4/6/8; under smooth timing3.783→2.690→1.947rad. Steering variation
and rate-limit time also fall. Actual small-correction reversal counts can rise despite that
improvement. The measured shared prefix ends before this section, so the matched-history
sector evidence and complete measured runs are reported separately.

## 14. Fast-Sweeper Diagnosis

The baseline-cost horizon candidates are comparatively smooth here. Half-vy pathological E
produces material predicted slack0.111458m and a nominal ey0.581448m; physical max ey is
0.583446m and local position error remains below0.010m. This is primarily unsafe upstream
trajectory generation, not evidence that TVLQR needs replacement.

## 15. Horizon Sensitivity

Keep dt0.1s and compare N4/6/8 without retuning Q/R/W. N6 is the smallest broadly promising
mathematical extension across the initial1.8/2.0/2.1 grid. N8 is smoother at2.0 but worse than
N6 at2.1; longer is not universally better. Eight sustained cases complete all crossings safely.
N6 slightly worsens gamma2 smooth lap3 heading TV versus N4 (9.992 versus9.855rad), while N8
improves both full gamma2 smooth laps. N6 gamma2.2 smooth lap3 grows to11.530rad.

## 16. Horizon Computational Cost

Fresh measured gamma2 planner timing and demand:

| N | Per-run mean preparation range ms | Per-run p95 range ms | Largest observed preparation ms | Planner CPU core-s/s range | Total planner+codriver CPU core-s/s range |
|---|---|---|---|---|---|
|4|28.63–31.01|32.90–36.82|136.98|0.286–0.301|0.370–0.389|
|6|42.01–47.39|51.11–55.75|593.02|0.420–0.432|0.502–0.516|
|8|55.52–56.47|68.15–69.57|184.05|0.554–0.560|0.638–0.647|

These are controller CPU demands per simulated physical second, not total simulator wall
throughput. N8 costs roughly0.26 additional planner cores versus N4 here. Backend audits
observed one native thread, with N6/N8 CPU/wall0.9970/0.9993. Polling may miss brief transients.
No new real-time guarantee follows from a mean or p95 below the100ms period.

## 17. Static Progress-Weight Feasibility Map

Thirty matched cases cover gamma1.9/2.0/2.1 and lambda0/.5/1/2/4. All initial grid cells stay
inside the track, yet responses are nonmonotonic. At1.9 positive lambda worsens fixed-history
variation while improving smooth-history baseline. Gamma2/lambda4 initially improves both
histories but fails pathological F:100 boundary samples, clearance−0.087804m, slack0.162558m.
Reject lambda4 as a robust finalist. Lambda remains0 for the near-limit recommendation.

## 18. Evidence for Future lambda Scheduling

The270 bounded sector traversals preserve tire/steering/rate utilization, slack, beta,
clearance, denominator and forecast residuals. Negligible slack can coexist with substantial
oscillation. No single signal or gamma-only schedule predicts benefit across histories.
These post-change signals are responses, not independently validated causal predictors.

## 19. Optional Diagnostic Gate Results

No adaptive gate was fitted: the evidence does not support a generalizable gate or final
scheduling function. Fitting one to these selected histories would exceed what they establish.

## 20. Planning → APEX Adaptation

In measured gamma2, node ey-adaptation RMS spans0.0307–0.0457m for N4 and0.0217–0.0243m for N8.
Mean speed adaptation is−0.356 to−0.282m/s for N4 and−0.242 to−0.239m/s for N8. This is
Control adapting the same Planning intent under constraints; Planning was not made easier.
Pseudo-reference dynamic channels remain explicitly distinguished from Planning requests.

## 21. APEX → Vehicle Tracking

Measured N8 ey RMS is1.261–1.307mm, with max absolute ey error8.03–9.67mm. N4 RMS is
1.553–2.137mm and maxima10.07–16.01mm. N6's failed run reaches19.39mm before exhaustion.
Position tracking remains local and useful, but transient yaw errors are larger; do not call
every state error negligible. These data do not justify changing the frozen100Hz TVLQR.

## 22. Tire Utilization

Measured gamma2 N8 max front utilization is0.856–0.858 and rear0.871–0.872, versus N4
front0.956–0.959 and rear0.975–0.978. Principal figures show slip/force clouds, a conditioned
smooth-grip law slice and both normalized friction planes with unit boundaries. Independent
NumPy/CasADi derivatives agree to about3e-14; force balance agrees at floating-point precision.
For the measured worst-heading N8 case, smooth-stencil ay finite-difference RMS discrepancy is
0.001108m/s². These are internal synthetic checks, not real-vehicle validation.

## 23. Steering Utilization

Measured gamma2 per-run max |delta| is0.364–0.373rad with N8 against the unchanged0.4rad limit.
N4 reaches0.360–0.377rad; N6 reaches0.370–0.381rad. Angle utilization alone does not explain
oscillation or establish a useful progress reward.

## 24. Steering-Rate Utilization

The1rad/s limit remains active. N8 measured rate-limit time is2.20–2.60s versus N4's4.41–7.56s.
N8 actual steering TV is7.259–7.793rad versus10.798–16.265rad for N4. However, at the0.001rad/s
deadband, N8 has408–422 reversals versus306–403 for N4. A post-hoc sensitivity check retains
that unfavorable fact: at0.05rad/s counts remain244–267 versus184–255; at0.25rad/s they are
100–122 versus119–134. These deadbands are descriptive, not acceptance thresholds.
Smaller variation is supported; elimination of feedback chatter is not. Review residual
reversals before adopting any production envelope.

## 25. Acceleration / Braking

Dynamic a_cmd is Fx/m, not dvx/dt. Measured gamma2 N4 uses the full−3 to2m/s² command range;
N8's observed range is−2.177 to1.943m/s². Allocation, normal loads and combined-grip law are
unchanged. The dashboards retain commanded acceleration separately from lateral acceleration.

## 26. Track Margin / Slack

All twenty measured records have zero observed boundary crossings and maximum predicted
slack around9.1e-11m (barrier-scale, not material relaxation). Measured N8 minimum clearance
is0.329019–0.329142m. N6 gamma2.2 clearance is0.309807–0.326609m. Retained grid/history failures
remain failures regardless of favorable later runs. Their slack peaks are material and
reported alongside nominal and physical excursions.

## 27. Solver Behavior

All twenty measured records have zero solver, planner or forecast/gain failures. Mean
iterations per preparation at gamma2 are about11.3–11.8 (N4),11.8–12.6 (N6),12.21–12.24 (N8).
Maximum observed iterations are17/18/18 respectively. The N6 exhaustion's pending solve
succeeded in13 iterations; labeling it an IPOPT failure would be incorrect.

## 28. Planner Computational Cost

The measured distribution report retains per-run mean/p95/p99/max, CPU demand and outcomes.
N8 per-run p99 preparation is70.60–75.01ms; max184.05ms. N6's593.02ms tail used118.65ms CPU,
with an unresolved wall-minus-CPU delay. No OS trace establishes its external cause. It is
retained as a failed availability outcome, never removed as an outlier.

## 29. Codriver Computational Cost

Gamma2 N8 per-run p95 total codriver time is1.175–1.202ms and CPU demand0.0840–0.0864core-s/s.
Observed max is32.24ms. The other horizons also show rare tails beyond10ms. Full interpolation,
feedback, validation, CPU and total timing are retained; kernel time alone is not the budget.

## 30. Physical-Time Deadline Behavior

Across five gamma2 runs, planner/codriver misses total2/10 for N4,5/6 for N6 and2/8 for N8.
The deterministic150ms planner/25ms driver checks count4 planner and53 codriver misses each
for N6/N8 over0.8s, with continued plant motion, continued tracking and application staleness.
Zero-delay checks have zero misses. Synchronous physics was never introduced or paused.
Measured delay thresholds are not exact CI pass/fail assertions.

## 31. Trajectory Reserve

N8 measured minimum reserve ranges0.570–0.652s. N6's failed record reaches0 at18.756621s;
the pending plan would be available at18.793021s. Physics advances about3.109m during the
observed pending interval. The existing baseline fallback rejects the state outside its
valid domain. No post-termination physical motion or unavailable driver tail is invented.
The measured failure history was then replayed without padding: N6 reproduces every physical
and NLP channel exactly and fails at the same instant. N8 stays valid until driver-trace
exhaustion at18.760s, with0.196621s reserve and no fallback. This is censored evidence: the
pending replacement has not completed before the retained driver history ends, so it is not
a completed recovery test or proof of tolerance of arbitrary593ms stalls. Exact parity is in
`measured_n6_failure_replay_parity.json`; raw transferred history and both outcomes are retained.

## 32. Failure-Source Classification

| Important case | Classification | Supporting evidence |
|---|---|---|
|Baseline2.2 fixed|Planning demand + APEX formulation interaction|Nominal softened track excursion, material slack, valid solver; vehicle follows upstream trajectory|
|Combined(.25,.25), zero-yaw|APEX formulation limitation|Changing only cost importance worsens oscillation and produces retained boundary failures|
|Half-vy E, lambda4 F|APEX formulation/chronology interaction|Nominal already unsafe; local ey error below0.010m; no solver/deadline failure|
|N6 measured repetition00|Availability/trajectory-reserve limitation; external delay cause unresolved|Successful13-iteration solve,593ms wall/119ms CPU, pending completion after trajectory end|
|Residual rapid steering corrections|Mixed/unresolved amplitude/frequency issue|Lower TV and small ey errors coexist with many sign changes; not sufficient evidence for adaptive codriver|

## 33. Required Telemetry Dashboards

`TASK007C_ARTIFACT_INDEX.md` gives verified absolute links to all principal measured dashboards,
physics panels, sector zooms and comparison figures. Selection is the largest completed
heading-TV run in each measured group, plus every failed measured record; it is not a
favorable-run selection. The24-panel dashboards include sector shading and pending preparation
events at their source progress, even when those plans never become active.

## 34. Zoomed Hairpin Dashboard

Primary recommended-point case: `results/task007c_resume/g2_w0_vy1_r1_n8_measured_l1_rep04/dashboard_hairpin.png`.
Baseline, N6 and upper-stress counterparts are linked in the artifact index. Existing failed
baseline2.2 and zero-yaw evidence remains available for comparison.

## 35. Zoomed Technical-Section Dashboard

`results/task007c_resume/g2_w0_vy1_r1_n8_measured_l1_rep04/dashboard_technical_section.png`.
The failed measured N6 record does not reach this section; no technical zoom is fabricated for it.

## 36. Zoomed Fast-Sweeper Dashboard

`results/task007c_resume/g2_w0_vy1_r1_n8_measured_l1_rep04/dashboard_fast_sweeper.png`.
The retained half-vy E boundary-failure dashboard and physics checks remain separate evidence.

## 37. Transition Map

`results/task007c_resume/c1_transition_map.png` and `c1_phase_portraits.png`, supported by the
full C1 tables. Beta, utilization, variation, rate activity, margin and chronology are read together.

## 38. Dynamic-Reference Ablation Image

The C2 comparison figure and exact36-cell initial grid plus four follow-ups are linked in the
artifact index and `TASK007C_C2_GRID_RESULTS.md`. Terminal consistency and later E rejection
are required context; the initially favorable half-vy screen is not the final verdict.

## 39. Horizon Comparison Image

`c3_formulation_comparison.png`, `c3_gamma2_phase_portraits.png`, `measured_gamma2_comparison.png`
and `measured_worst_phase_portraits.png` under the result root. The latter labels gamma2.2
separately and retains repeated sector loops. The measured comparison includes the failed N6
record and the common-prefix coverage limitation.

## 40. Regression Tests

The full533-test suite passed before later diagnostic-only additions. Thirteen ablation tests
and27 DARE checks validate implemented cost mathematics; the three current physics/extraction
tests passed, including the common-prefix endpoint interval. Subsequent changes are report,
audit and plotting scripts; Ruff passes. No runtime mathematics changed after the established
suite result. Exact timing comparisons are physical diagnostic checks, not wall-clock CI tests.

## 41. Generated Artifacts

Raw states, controls, events, trajectory packets, predictions, exact NLP inputs/solutions,
per-cell configurations and fixture/source hashes are retained. Derived products include
comparison/per-lap/sector tables, measured per-run distributions, common-progress tables,
physics validations, dashboards, failure reviews, replay parity and final provenance. The
artifact index provides navigable paths; reproduction commands have a separate complete guide.

## 42. Known Limitations

One synthetic vehicle/track, perfect state, selected timing histories and five measured runs
per point do not establish population failure probability or physical-vehicle safety. The
measured repetitions close rolling segments, while later full laps are controlled-history
confirmations. No confidence bounds or continuous-gamma guarantee are claimed. Desktop OS
background load is uncontrolled. Native-thread sampling is finite. Prediction residuals mix
future replans/feedback with model approximation. Reversal counts and high-demand sustained
smoothness remain review items. No disturbance/opponent/SI generalization is established.

## 43. Architecture Deviations

No plant, tire law, canonical state order, TVLQR rate, constraints, solver algorithm or timing
architecture was redesigned. Runtime additions are approved independent cost multipliers and
compatible DARE construction, both defaulting to1. Candidate horizon/weight settings are
experiment-local. New guards, reports and diagnostics do not alter physical simulation timing.

## 44. Evidence For / Against Adaptive Codriver

Position tracking follows APEX closely even when APEX requests an unsafe path. The primary
formulation failures therefore argue for upstream improvement first. The measured exhaustion
is a delayed-availability problem. Residual yaw transients/steering chatter deserve later
review, but these results do not justify implementing an adaptive codriver now.

## 45. Recommended APEX Formulation Change

Recommend horizon extension only, retaining alpha_vy=alpha_r=1, lambda0 and dt0.1s. For the
current end-to-end review candidate, N8 at gamma2 has the stronger combined evidence: stable
five-run measured behavior, broad retained-history smoothness and sustained full-lap support,
at higher but measured computational cost. N6 is the smaller mathematical extension and
remains promising, but its retained availability failure prevents an unqualified robustness
recommendation. Do not weaken yaw/vy costs or adopt static positive progress weight globally.
No production default has been changed.

The provisional demonstrated operating point is the N8/gamma2 synthetic configuration.
Controlled N8 points1.8/1.9 provide adjacent evidence, not a proof of every intermediate or
lower gamma. Do not declare a continuous robust interval or extend this envelope to2.1/2.2:
N8 lacks fresh measurements there, and N6's faster2.2 runs do not erase its gamma2 failure or
sustained smoothness caveat. Residual reversals and unbounded desktop timing tails make this
a review candidate, not a certified smooth or hard-real-time envelope.

## 46. Readiness for Task 007D

C1–C4 evidence is ready for formulation review: final audits and the causal-replay checks
passed within their explicitly stated coverage. Advancement to adaptive codriver, LMPC, SI, energy or opponents is not
automatic. No such implementation has begun.

## 47. Recommended Next Step

Stop for review of the single horizon change and its bounded operating-point evidence.
After that review, the documented timing study compares current variable availability,
committed-control-prefix MPC and fixed future30/40/50ms handoffs aligned to the10ms codriver
grid. It remains unimplemented. After online SI is implemented AND accepted, the mandatory
workbench/real-time identification checkpoints in `PROJECT_ROADMAP.md` remain required.

## 48. Reproduction Commands

Use `TASK007C_RESUMED_REPRODUCTION.md`. It contains the exact grid, retained-history, sustained,
thread-audit, measured, analysis, plotting and final-audit commands. Existing completed identities
are reused, not overwritten or silently counted as fresh repetitions. New failures stop for
review and finite traces stop at their recorded end.
