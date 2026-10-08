# Task007C C2 complete initial grid

The36-cell initial grid is complete: nine alpha pairs, gamma1.8/2.0, fixed and stable-C
histories. Four baseline cells are reused from C1. This completes the initial ablation grid,
not the full C1–C4 task or candidate acceptance. Four targeted follow-ups are also complete (see below);
representative-history/fresh-measured acceptance remains pending.

The synthetic plant, full nonlinear state vector, TVLQR, dt0.1/N4, lambda0, bounds, solver and
availability histories were frozen. Each terminal DARE was regenerated from the compatible Q;
all27 pair/speed-node solutions passed residual, symmetry, PSD and closed-loop pole checks.
Default alpha1 behavior retains exact full-lap parity with the archived CR baseline.

## Findings

At gamma1.8, weakening either individual pseudo-reference does not improve heading and steering
variation under either history. Removing yaw tracking is particularly poor: smooth-history
heading TV rises11.112→34.872rad. Larger sideslip accompanies, but is not itself the criterion
for rejecting, the increasingly oscillatory plans.

At gamma2, half-vy with full yaw tracking is the only tested ablation that improves heading,
steering and rate-limit activity under both histories:

| Metric | Baseline fixed | Half-vy fixed | Baseline smooth | Half-vy smooth |
|---|---:|---:|---:|---:|
| Planned epsi TV rad |11.993|10.893|11.214|10.692|
| Nominal steering TV rad |8.001|7.046|7.342|6.519|
| Physical rate-limit s |8.560|7.260|3.746|3.260|
| p95 abs beta rad |0.1459|0.1414|0.1361|0.1404|
| Min physical clearance m |0.3206|0.3210|0.3206|0.3210|
| Lap s |31.267|31.044|31.202|31.166|

The beta response is not uniformly lower despite the smoothness improvement. This supports
interpreting dynamic-state freedom jointly with trajectory quality and feasibility. It does
not establish a globally better weight: the same change worsens gamma1.8 smoothness.

Quarter-vy and zero-vy improve some gamma2 smooth-replay metrics but worsen the fixed-history
oscillation measures. Neither provides the same two-history support as half-vy. Weakening yaw
tracking, alone or jointly, causes large oscillations. Gamma2 smooth heading TV is49.562rad
for(1,.25),42.306rad for(1,0),41.578rad for(.25,.25), and50.107rad for(0,0), versus11.214rad
for baseline. Lack of a crossing in an individual run does not make these acceptable.

## Retained failures

- Gamma2(.25,.25), fixed:159 boundary samples, max ey0.814420m, minimum clearance−0.264420m,
  predicted slack max0.3406m, technical-section entrance. No solver/fallback/deadline failures.
- Gamma2(1,0), smooth:62 boundary samples, max ey0.590392m, minimum clearance−0.040392m,
  predicted slack max0.1141m, hairpin approach. No solver/fallback/deadline failures.

The failures are upstream trajectory problems within the tested formulation/chronology, with
small local position-tracking error. Track slack is penalized rather than a hard physical
boundary guarantee. They remain rejected even though their alternative histories stay inside
the boundary. Exact case-summary hashes and continuation reviews are in reviewed_failures.json.

## Candidate scope, not a production selection

Keep half-vy/full-yaw as a provisional candidate at gamma2. Its completed high-demand and
progress follow-ups at gamma2.1/lambda0 and gamma2/lambda2 under both histories retained N4.
C3 and C4 retain baseline alpha1 to isolate horizon and progress effects. Important candidates
must then pass representative retained-history comparisons and fresh measured repetitions.
No adaptive policy, TVLQR change, new timing architecture or production default is introduced.

## Evidence

Exact metrics and all cases: `results/task007c_resume/comparison.csv`, per-case analysis.json,
oscillation.json, diagnostic_telemetry.csv, prediction_oscillation.csv and sector_oscillation.csv.
Comparison image: `results/task007c_resume/c2_formulation_comparison.png`.
Cost construction: `src/apex/control/mpc/cost.py`; DARE audit: `terminal_audit.json` in the result root.
The term "heading TV" in these inherited metrics denotes unwrapped Frenet epsi variation;
raw within-prediction and stitched active-trajectory measurements are kept separate.
All results are internal synthetic-model evidence, not real-vehicle validation.

## Completed C2 follow-ups

All four follow-ups completed without boundary or solver failures, but the half-vy benefit
is narrow. At gamma2.1, fixed heading TV falls11.594→11.295rad, while smooth-history heading
TV rises10.899→12.557rad and steering TV6.894→8.976rad. It therefore does not demonstrate a
uniform extension of the robust region beyond gamma2.

Adding lambda2 to the half-vy gamma2 case raises fixed heading TV10.893→18.343rad, steering
TV7.046→12.242rad and rate-limit activity7.26→13.086s. Smooth-history heading TV also rises
10.692→11.677rad. This does not justify combining the ablation with positive progress reward.
The provisional alpha(.5,1) candidate remains gamma2/lambda0 only, pending broader timing
histories and measured repetitions. Production defaults remain unchanged.

## Representative-history rejection

Half-vy N4 gamma2/lambda0 is now rejected as a robust finalist. Under original pathological E,
it crossed the boundary for59 samples at12.3657–12.55s, progress59.0012–59.6474m in the fast
sweeper. Max ey0.583446m means minimum clearance−0.033446m. Peak predicted slack0.111458m
and active nominal ey0.581448m show that the upstream trajectory itself used the softened
track limit. Local ey RMS in12.3–12.7s is0.006482m (max0.009493m), with no solver, planner,
forecast/gain, fallback or deadline failures. This supports a formulation/chronology limitation,
not a new TVLQR redesign. The finite replay later exhausted before completing a lap.

The matched baseline E run did not cross the boundary in its retained coverage. The favorable
fixed/smooth/median half-vy results cannot erase this failure. Preserve F as a predeclared stress
diagnostic, but do not spend measured-finalist repetitions on this rejected variant. Exact
summary hash, samples and continuation decision: `c2_pathological_e_boundary_review.json` and
`reviewed_failures.json` in `results/task007c_resume/`.
