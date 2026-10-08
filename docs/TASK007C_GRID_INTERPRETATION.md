# Task007C controlled-grid interpretation

Initial C1–C4 grids are complete. Representative-history and fresh-measured acceptance is
still in progress. This document is not the final selection or robust operating envelope.
All statements concern synthetic data and unchanged TVLQR/physical plant/timing architecture.

## C3: N6 is the smallest consistently promising horizon extension

With baseline costs and lambda0, N6 reduces heading variation and rate-limit activity at all
three primary gamma points1.8/2.0/2.1 under both initial histories. At gamma2, fixed heading TV
falls11.993→9.371rad and smooth11.214→9.128rad; fixed steering TV8.001→5.660rad and smooth
7.342→5.666rad. Minimum clearance slightly improves. Local tracking remains small.

N8 improves gamma2 smoothness further: heading TV8.009 fixed/7.754 smooth and steering TV
4.960/4.740rad. But at gamma2.1 N8 is worse than N6 under both histories. Smooth rate-limit
time is3.646s with N8, exceeding baseline N4's3.296s, whereas N6 gives2.401s. A longer horizon
therefore does not guarantee smoother behavior. Common first0.4s packet metrics agree with
this nonmonotonic gamma2.1 result; it is not simply an unequal-horizon TV artifact.

The observed gamma2 one-step residuals remain tiny across horizons. Realized common-step4
errors improve with longer horizons, but include future feedback/replanning/forecast effects.
See `TASK007C_PHYSICS_REVIEW.md`. Isolated compute cost is still required; do not use contended
controlled-run wall times to select N6 or N8. Gamma1.9 supplemental coverage and the N6 gamma2.2
stress follow-up are separate from the original18-cell grid.

## C4: static progress reward has a conditional, nonmonotonic effect

All30 cases stayed within the track with no solver failure. Their maximum predicted slack is
about9.1e-11m, numerical barrier-scale slack rather than material track relaxation. This does
not make every trajectory acceptable: oscillation and timing sensitivity still differentiate them.

At gamma1.9 all positive weights worsen fixed-history heading/steering variation, while all
improve the smooth-history baseline. Lambda4 changes heading TV10.204→11.462rad fixed but
14.770→9.231rad smooth. A favorable history cannot establish a globally useful progress weight.

At gamma2, lambda4 is a narrow candidate: heading TV11.993→10.490rad fixed and11.214→10.578rad
smooth; steering TV8.001→6.289 and7.342→6.510rad. Fixed lap time improves0.200s; smooth changes
by+0.007s, essentially neutral at this scale. Clearance decreases slightly. Lambda0.5 improves
fixed smoothness but worsens smooth-history behavior; lambda1 does the reverse. Lambda2 slows
both histories and notably worsens fixed oscillation. There is no monotonic weight-response law.

At gamma2.1, lambda2 improves smooth-history behavior/performance but slightly worsens fixed
smoothness. Lambda4 gives fixed heading TV21.374rad versus11.594 baseline, rate-limit time
15.37s versus7.72, and lap31.807s versus30.819, despite a faster smooth-history lap. This
rejects a global lambda4 choice even though gamma2 remains worth representative-history testing.

## Feasibility signals and scheduling limits

`results/task007c_resume/c4_paired_sector_feasibility.csv` provides270 bounded sector traversals
from30 cells, with paired lambda0 deltas. It retains tire/steering/rate utilization, clearance,
slack, beta, Frenet denominator and held handoff-forecast residuals alongside oscillation metrics.
Sample quantiles and interval-weighted RMS are distinguished in its method JSON.

In this grid, slack alone cannot identify oscillation: it remains negligible in the bad cases.
Boundary crossing alone also fails to identify the poor trajectories. Rate-limit occupancy,
reversals and direct heading/steering variation reveal deterioration that lap completion hides.
Tire usage, beta and margin reserve must be interpreted jointly with chronology and sector.
The same gamma/weight can improve one retained history and degrade another, so a gamma-only
or lambda-only schedule is unsupported. The post-change signals are responses, not independently
validated predictors. Forecast residual includes chronology and must not be relabeled physical
model mismatch. No adaptive gate or final scheduling function is fitted from this small grid.

## Current candidates and pending decision

At gamma2 compare baseline N4/lambda0 with half-vy N4/lambda0, baseline-weight N6/lambda0,
N8/lambda0 and N4/lambda4 on median/E/F. At gamma2.1 compare baseline N4 and N6/N8 with lambda0.
Keep each formulation effect isolated. The first two histories favor the N6 extension most
consistently, but acceptance still depends on representative histories, outcome precision and
isolated measured computational viability. Production defaults remain unchanged.

Exact controlled tables: `TASK007C_C3_GRID_RESULTS.md`, `TASK007C_C4_GRID_RESULTS.md`.
Here, inherited "heading TV" is unwrapped Frenet epsi variation; stitched active trajectories
and individual packet predictions are reported separately. No scalar score is used.

## Subsequent representative-history verdict

The gamma2 median/E/F comparisons are now complete. Half-vy fails the E fast-sweeper boundary;
N4/lambda4 fails the F return-complex boundary. Both initial narrow candidates are rejected from
measured finalist testing. N6/N8 remain for higher-demand and isolated measured validation.
See `TASK007C_REPRESENTATIVE_HISTORY_REVIEW.md`; initial controlled improvements above remain
retained evidence rather than acceptance claims.
