# Task007C C1 fixed-timing screen — interim evidence

This is an interim screen, not the final C1–C4 recommendation. All eight baseline cases use
Candidate C, N4/dt0.1, lambda0, alpha_vy=alpha_r=1, fixed35ms planner/1ms codriver physical
availability, frozen TVLQR, and one rolling-start lap. No second-lap or measured-repeat
acceptance is implied. The exact baseline gamma2 trajectory matches the archived CR case.

| Gamma | p95 abs beta rad | max abs beta rad | rear utilization max | rate-limit s | heading TV rad | nominal steering TV rad | min clearance m | max predicted slack m |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1.50|0.0486|0.0870|0.8089|5.76|9.691|6.693|0.3109|~0|
|1.60|0.0600|0.0854|0.8640|4.14|8.266|5.132|0.2963|~0|
|1.70|0.0764|0.1361|0.9060|5.39|9.679|5.885|0.3034|~0|
|1.80|0.0939|0.1801|0.9378|5.49|9.647|6.085|0.3264|~0|
|1.90|0.1164|0.2530|0.9643|5.81|10.204|6.226|0.3177|~0|
|2.00|0.1459|0.3183|0.9759|8.56|11.993|8.001|0.3206|~0|
|2.10|0.1510|0.3318|0.9799|7.72|11.594|7.267|0.3196|~0|
|2.20|0.1967|0.4325|0.9839|16.69|24.807|15.267|-0.01974|0.10012|

Machine-readable exact values: `results/task007c_resume/comparison.csv` (growing table;
filter fixed/lambda0/alphas1/N4/laps1). The 2.10 rear utilization above is rounded;
consult the machine-readable table for the exact value.

Multiple indicators change around1.9–2.0, with a much sharper deterioration at2.2. This is a
candidate transition region, not a universal threshold. Tire utilization and beta alone are
not an oscillation classifier. The smooth-history grid has now completed; see the comparison below. C2 uses the original
approved1.8/2.0 points, C3 uses1.8/2.0/2.1, and C4 isolates static progress weights at1.9/2.0/2.1
with baseline costs/horizon. The1.8 lambda2 screen remains a lower-demand comparison.

## Boundary review

Gamma2.2 completes a31.3064s lap, but44 physical samples violate the boundary over
3.870–4.011s, s=21.0968–21.3447m, at entry to the hairpin. Max ey=0.569740m. All solver
returns remain valid and there are no planner/codriver deadline misses or fallbacks.
Gamma2.2 is rejected as an operating-envelope candidate and retained as a stress case.
A single matched smooth-history diagnostic is retained after this review to measure chronology
sensitivity. A favorable replay cannot erase the fixed-history physical failure.

The independently transcribed model derivatives agree to machine precision. One-step body
state residual maxima are vx0, vy2.22e-16m/s, r4.44e-16rad/s. Frenet residuals include the
explicitly disclosed frozen-curvature diagnostic approximation; max epsi2.69e-4rad and
ey1.62e-6m. Force-balance lateral acceleration agrees to8.89e-16m/s²; smooth-stencil finite-
difference ay RMS discrepancy is0.00277m/s². Realized horizon errors grow substantially
(e.g. step4 yaw RMS0.860rad/s), but these include later replans, feedback, forecasts and
interpolation, and must not be described as pure tire-model error.

These checks support a controller/demand limitation within the synthetic model, not a
NumPy/CasADi derivative mismatch. The remaining C2–C4 experiments must distinguish
pseudo-reference, short-horizon and progress-pressure effects. They do not validate a real car.

## Review artifacts

- `results/task007c_resume/c1_transition_map.png`
- `results/task007c_resume/c1_phase_portraits.png`
- `results/task007c_resume/g2p2_w0_vy1_r1_n4_fixed_l1/primary_dashboard.png`
- `results/task007c_resume/g2p2_w0_vy1_r1_n4_fixed_l1/dashboard_hairpin.png`
- `results/task007c_resume/g2p2_w0_vy1_r1_n4_fixed_l1/physics_review.png`
- `results/task007c_resume/g2p2_w0_vy1_r1_n4_fixed_l1/physics_validation.json`
- `results/task007c_resume/c1_boundary_review.json`

All533 regression tests passed. The current controlled cases can overlap offline analysis,
so their recorded preparation wall times are not the isolated measured benchmark. Fresh
measured shortlisted repetitions remain pending and will run without competing numerical work.

## Completed baseline replay comparison

All eight smooth-history runs completed without physical boundary or solver failures.
Gamma2.2 nevertheless remains rejected because of its fixed-history crossing. These are two
controlled histories, not a measured outcome distribution or a robustness certificate.

| Gamma | Fixed heading TV | Smooth heading TV | Fixed nominal steering TV | Smooth nominal steering TV | Fixed rate-limit s | Smooth rate-limit s |
|---|---:|---:|---:|---:|---:|---:|
|1.50|9.691|7.734|6.693|5.235|5.760|1.900|
|1.60|8.266|8.901|5.132|5.811|4.140|2.390|
|1.70|9.679|10.851|5.885|7.376|5.390|3.600|
|1.80|9.647|11.112|6.085|7.480|5.490|3.360|
|1.90|10.204|14.770|6.226|10.851|5.810|5.620|
|2.00|11.993|11.214|8.001|7.342|8.560|3.746|
|2.10|11.594|10.899|7.267|6.894|7.720|3.296|
|2.20|24.807|21.917|15.267|14.848|16.690|7.816|

The onset is not monotonic: gamma1.9 smooth heading TV14.770 exceeds both its fixed value10.204
and the gamma2.0 smooth value11.214. Near-limit sensitivity is already observable before the
first physical crossing. At2.2, smooth-history min clearance is0.099964m and heading TV21.917rad;
a favorable boundary result still accompanies a large smoothness deterioration.

The six lambda2 follow-ups at1.8/2.0/2.1 completed without boundary or solver failures.
C2–C4 and the three-layer shortlist validation remain incomplete.

## Informative lambda2 follow-up

Changes below are lambda2 minus lambda0 under the identical history; negative TV or lap-time
change denotes a reduction. Every row is a one-lap screen, not an accepted operating point.

| Gamma | History | Lap change s | Heading TV change rad | Nominal steering TV change rad | Rate-limit change s |
|---|---|---:|---:|---:|---:|
|1.80|fixed|+0.177|+1.545|+1.689|+2.000|
|1.80|smooth|-0.127|-0.603|-0.519|-0.280|
|2.00|fixed|+0.707|+3.428|+1.675|+1.980|
|2.00|smooth|+0.068|+0.254|+0.016|-0.016|
|2.10|fixed|-0.158|+0.359|+0.071|+0.091|
|2.10|smooth|-0.340|-1.899|-1.081|-0.716|

Lambda2 is not uniformly useful. At gamma2 fixed timing it increases lap time by0.707s,
heading TV by3.428rad and rate-limit time by1.98s. At gamma2.1 smooth timing it reduces lap time
by0.340s and heading TV by1.899rad; the fixed-history smoothness benefit does not accompany it.
The same static reward can help or hurt depending on operating point and chronology. No final
lambda schedule or production default change follows from these screens.

Fresh backend audit observed a maximum of one sampled process thread and CPU/wall0.994886
for100 exact NLP solves. The frozen native SINGLE control was configured before numerical
initialization. The audit sampling can miss very brief transients, as documented in its JSON.
All prior B/C/CR result hashes were reverified:675/293/1907 archived files respectively.
