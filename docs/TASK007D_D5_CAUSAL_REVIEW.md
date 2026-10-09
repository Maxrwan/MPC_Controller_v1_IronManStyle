# Task007D-D5 — Architecture B clearance and prediction regression forensics

## Executive findings and scope

D5 is complete as an **offline investigation**, subject to Engineering Orchestrator review.
Starting main: `feb7c706f3f4b16d2a50240f151070b57e9cf50e`. No new forecast, solver call,
plant propagation, D3/D4 rerun or timing campaign was executed. Production Architecture A,
experimental Architecture B, all controller mathematics and runtime scheduling are unchanged.

**R4-B's clearance loss is a real lateral-position difference in this recorded synthetic
interval, not a narrower track or mainly a progress-alignment artifact.** At B's minimum,
the same-time clearance difference is −0.129530 m. The active nominal lateral positions
account algebraically for −0.129652 m, while the difference in physical tracking error
contributes +0.000122 m. At matched progress the clearance difference is still approximately
−0.127621 m. This identifies where the loss appears; it does **not** prove that a single
NMPC decision caused the entire downstream excursion or that B is safe.

The first steering-command separation is only at **0.715 s**, later than the first changed
acceleration at 0.175 s and first changed state at 0.180 s. A sustained steering offset and
subsequent heading/lateral separation precede the large clearance gap. By acceptance of
plan 18 at 1.860 s, the physical lateral positions already differ by −0.122179 m. Thus the
minimum is not a sudden tracking failure caused by accepting plan 18.

Low-latency late-release heading/lateral regressions are reproducible, above roundoff, but
small in absolute units. Across both host histories, the largest later absolute-error
increase is 0.00229321 rad/s in yaw rate, 0.000140944 rad in heading and 0.0000128980 m in
lateral position. These do not by themselves justify changing predictor mathematics.
The substantial R4 physical-clearance loss remains a separate unresolved control-sensitivity
risk and cannot be dismissed using those small forecast-error numbers.

## Evidence and analytical contract

Read-only inputs are the eight original `results/task007d/d4/R*_*/` directories and the
committed D4 compact evidence. Every raw/scores/context/summary file is checked against its
D4 SHA-256 before analysis; fixture and core-source hashes must also match D4. The fixture remains Task007C N8/gamma2, dt=0.1 s,
H=0.8 s, original Q/R/W, lambda_s=0, alpha_vy=alpha_r=1, the same synthetic vehicle,
combined-grip model, TVLQR, warm starts, estimator and variable-availability handoff.
R4 has imposed planner/codriver delay 60/15 ms. R1/R2/R3 are 35/0, 35/5 and 60/5 ms.

Canonical state: `[vx, vy, r, e_psi, s_abs, e_y]`, SI units. Positive e_y is left.
Left clearance = left_width − e_y; right clearance = right_width + e_y;
center clearance is their minimum. There is no vehicle-footprint or continuous-time
boundary certification. All observed positions remain in the named `long_straight` sector;
this sector name does not imply zero spline curvature.

**Recorded:** physical states, held applied commands, tire-utilization diagnostics, packet
IDs, requested commands and sample/application times, solver diagnostics, optimized packet
nodes and accepted handoffs. **Reconstructed from recorded packets:** active nominal states
and controls at physical timestamps, using the original `TrajectoryPacket.trim(accept_time)`
and `sample(time)` methods. No new feedback, optimization or dynamics are evaluated.
**Derived:** geometry at actual progress, signed clearances, actual-minus-nominal tracking,
application-interval steering rates and the comparison identities below.

Acceptance, rather than readiness alone, selects packet authority. A command's reference is
selected at its computation/sample time even if its application follows another handoff.
The reconstructed samples and residuals exactly reproduce all **1,400 recorded codriver
references and 152 accepted handoff residuals** across eight runs; maximum difference is 0.
All 152 saved active forecasts still exactly match the logged NMPC predicted x0 and previous
input. Original chronology checks return no issues. This rechecks retained values; it does
not rerun forecasts or claim access to unavailable NLP iterations or initial guesses.

Target prediction residual remains **forecast − physical state at the estimated target**,
with wrapped heading. Handoff continuity remains **physical − candidate nominal at actual
acceptance**. The first target is 0.117 s; R4 readiness/acceptance is 0.160 s (+43 ms),
R1/R2 is 0.135 s (+18 ms), R3 is 0.160 s (+43 ms). Subsequent target/readiness/acceptance
timestamps coincide within existing event tolerance. D5 reuses D3/D4's labelled first-target
RK4 reconstruction and subsequent recorded target samples; it creates no new target truth.

## Exact recorded minimum-clearance events

Displayed times are rounded to milliseconds; full binary-float timestamps and values are
in [summary.json](task007d/d5/summary.json). These are two separate minima, not a same-time pair.

| Quantity | R4-A | R4-B |
|---|---:|---:|
| Physical time (s) | 1.865 | 1.89 |
| Absolute progress (m) | 11.4544547943 | 11.5378802512 |
| Curvature (1/m) | -0.00521213005655 | -0.00500682641749 |
| Left width (m) | 0.55 | 0.55 |
| Right width (m) | 0.55 | 0.55 |
| Physical e_y (m) | -0.321338708716 | -0.447815295398 |
| Minimum center clearance (m) | 0.228661291284 | 0.102184704602 |
| vx (m/s) | 5.57549297158 | 5.37404132076 |
| vy (m/s) | -1.15255423617 | -1.13884744804 |
| r (rad/s) | 2.10520712881 | 2.02033315106 |
| e_psi (rad) | 0.206539859277 | 0.205519989533 |
| Applied delta (rad) | 0.119954542112 | 0.107178900183 |
| Applied a_cmd (m/s²) | 2 | 2 |
| Active packet ID | 18 | 18 |
| Active nominal e_y (m) | -0.319645859576 | -0.44051918741 |
| Physical minus nominal e_y (m) | -0.00169284913991 | -0.0072961079887 |
| Front utilization | 0.857784937255 | 0.848354040468 |
| Rear utilization | 0.843117809544 | 0.849219312623 |

Both limiting boundaries are **right**. Clearances reproduce D4 exactly:
A = **0.22866129128417373 m** at **1.8649999999999816 s**;
B = **0.10218470460178081 m** at **1.889999999999981 s**.
Their difference is −0.12647658668239292 m. Subtracting the unchanged 0.08 m synthetic
tracking margin leaves **0.1486612912841737 m** and **0.022184704601780805 m**.
The 0.08 m margin is not a body dimension, and this subtraction is not a safety proof.

Over the preceding 100 ms, A's heading error rises from −0.0229631 to +0.206540 rad,
while vy changes −0.655109→−1.152554 m/s. B's corresponding own-minimum window rises
from −0.0195696 to +0.205520 rad, with vy −0.715426→−1.138847 m/s.
These histories locate the lateral turning point, with positive body heading coexisting
with substantial negative lateral velocity. They are not identical-time windows.

Both use plan 18, accepted at 1.860 s after plan 17 at 1.760 s. A's minimum precedes the
first plan-18 command application: its held steering came from plan 17, sampled at 1.840 s
and applied at 1.855 s. B's minimum follows its plan-18 request at 1.860 s and application
at 1.875 s. The next requested command at 1.880 s remains unapplied until 1.895 s.
There is no stale-authority violation: pending old-packet commands legitimately survive
handoff. The recent event windows are preserved in the summary; all application rows are
in [applications.csv](task007d/d5/applications.csv).

At the minima the nominal steering is −0.0000454569 rad (A) and +0.00217891 rad (B),
substantially different from the held physical steering. The existing tracker limits each
request by 0.01 rad per nominal 10 ms tick; with 15 ms latency, successful computations
are spaced 20 ms apart. Measured from retained applications, maximum steering change per
elapsed application interval is 0.5000000000000111 rad/s in both runs, below the unchanged
1 rad/s physical limit. **No application-time clamp changes a requested steering value**
in either retained R4 run. This does not imply the tracker request limiter was inactive.

Plan-18 predicted max slack is 9.09090909647e−11 m (A), 9.09154624922e−11 m (B).
Full-interval peak front/rear utilizations are 0.868992/0.871465 and 0.851145/0.861592.
These recorded synthetic diagnostics show neither a tire-utilization peak nor material
predicted slack unique to B's minimum; they do not validate physical tires.

## Same physical time

The common observed interval is **0–1.9949999999999788 s**, 400 matched event timestamps.
Both simulations ended near 2 s, but the terminal endpoint was not recorded and is excluded.
No interpolation of physical states is used here. Widths remain 0.55 m on both sides
throughout both recorded histories: width variation contributes exactly zero.

For each boundary separately, the algebraic difference B−A is
`width difference + sign*(nominal e_y difference + tracking-error difference)`, with sign
+1 for the right boundary and −1 for the left. This is a decomposition of contemporaneous
positions, **not a causal attribution**. When A and B have different limiting sides, the
right-boundary identity must not be relabelled as the minimum-clearance identity.

| Common time (s) | A clearance (m) | B clearance (m) | B−A (m) | Right nominal contribution (m) | Right tracking contribution (m) |
|---|---:|---:|---:|---:|---:|
| 0.885 | 0.482581781 | 0.48155577 | -0.00102601133 | -0.000758633101 | -0.000267378225 |
| 1.260 | 0.35316561 | 0.376033127 | 0.0228675173 | -0.0229593619 | 9.18445853e-05 |
| 1.530 | 0.530457935 | 0.511891659 | -0.018566276 | -0.0588477335 | 0.00119732724 |
| 1.545 | 0.54881907 | 0.488860302 | -0.059958768 | -0.0613005511 | 0.00134178308 |
| 1.765 | 0.268125787 | 0.167830123 | -0.100295664 | -0.100424239 | 0.000128574919 |
| 1.865 | 0.228661291 | 0.105268471 | -0.12339282 | -0.12339474 | 1.91993813e-06 |
| 1.890 | 0.231714645 | 0.102184705 | -0.129529941 | -0.129652013 | 0.000122072104 |
| 1.995 | 0.303148871 | 0.14703422 | -0.156114651 | -0.156245637 | 0.000130986491 |

At 1.260 s both limiting sides are left, so B's more rightward position **improves** minimum
clearance there. At 1.530 s A is left-limited and B right-limited; the displayed right-side
contributions do not sum to the minimum-clearance gap. From 1.545 s onward in these listed
checkpoints both are right-limited. The gap is oscillatory, not a monotonic safety regression
from the first differing forecast.

The first tiny unfavorable clearance difference is at 0.325 s (6.34e−9 m); it exceeds 1 mm
at 0.885 s, 1 cm at 1.530 s, 5 cm at 1.545 s and 10 cm at 1.765 s. These are descriptive
first-observation thresholds, not additional safety gates. Earlier differences precede them:
steering first separates at 0.715 s; at 0.800 s B−A heading is −0.00171952 rad and lateral
position is −0.000204510 m. At 1.400 s heading differs by −0.0300971 rad and lateral position
by −0.0391584 m. The complete recorded state/nominal table is retained separately.

At **B's minimum time**, A is at s=11.5970620 m and B at s=11.5378803 m, a −0.0591818 m
progress shift. A clearance is 0.231714645 m, B 0.102184705 m. Nearly the entire −0.129529941 m
gap is the active nominal e_y separation (−0.129652013 m); tracking contributes **+0.000122072 m**,
slightly mitigating the gap. At A's minimum time the analogous gap is −0.123392820 m.

## Same observed progress

Shared progress is **[1.0, 12.114336757641519] m**. The union of observed progress knots
inside this interval gives 761 comparison points; A's later-only tail is excluded.
Strictly increasing time and progress are checked. At off-knot progress, only continuous
physical e_y and time are linearly interpolated between adjacent recorded samples.
Commands and packet IDs are never interpolated. Nominal states are sampled from the
packet accepted at that interpolated time; packet authority is selected before sampling.

Every row includes exact/interpolated labels and bracket times in
[same_progress.csv](task007d/d5/same_progress.csv). Brackets span at most 5 ms; corresponding
progress brackets are about 0.03 m or smaller. These are chord estimates, not new RK4
states or independently sampled truth; no rigorous interpolation-error bound is claimed.
No extrapolation or new plant execution is performed.

| Shared progress (m) | A time (s) | B time (s) | A clearance (m) | B clearance (m) | B−A (m) |
|---|---:|---:|---:|---:|---:|
| 11.4544547943 (A minimum knot) | 1.865000 | 1.874840 interpolated | 0.228661291 | 0.103432797 | −0.125228494 |
| 11.5378802512 (B minimum knot) | 1.879625 interpolated | 1.890000 | 0.229805734 | 0.102184705 | −0.127621029 |
| 12.1143367576 (common endpoint) | 1.981212 interpolated | 1.995000 | 0.288428239 | 0.147034220 | −0.141394019 |

At B's minimum progress, the nominal contribution is −0.126008963 m and the tracking
contribution −0.001612066 m. At its minimum **time**, the gap is −0.129529941 m. Replacing
the same-time A comparator with the same-progress comparator changes the gap by only
0.001908912 m in this local comparison. Thus most of this observed loss remains after
progress alignment; it is an actual lateral-position separation at comparable progress.
This number is not a globally applicable causal percentage.

## Nominal trajectories versus physical tracking

At their separate minima, nominal e_y differs by −0.120873328 m and tracking error by
−0.005603259 m, summing to the −0.126476587 m minimum difference because widths and limiting
side coincide. Since times differ, the common-time and common-progress results above are
the stronger comparisons. At matched minimum time the tracking difference is much smaller.

The nominal path cannot be regarded as an independent prescribed global path: each optimized
packet starts from that run's forecast of its already evolving physical state. At handoff,
new nominal and actual position nearly coincide. Accepted positions show gradual separation:

| Acceptance (s) / packet | Physical e_y A / B (m) | Nominal e_y A / B (m) |
|---|---|---|
| 0.760 / 7 | −0.0822974 / −0.0823500 | −0.0826944 / −0.0825177 |
| 0.960 / 9 | −0.0230980 / −0.0257280 | −0.0233703 / −0.0258785 |
| 1.160 / 11 | 0.150032 / 0.136437 | 0.149791 / 0.136314 |
| 1.560 / 15 | −0.0224467 / −0.0847672 | −0.0221781 / −0.0846226 |
| 1.860 / 18 | −0.321309 / −0.443489 | −0.321402 / −0.443545 |

See [handoff_positions.csv](task007d/d5/handoff_positions.csv) for every acceptance.
The small same-time continuity errors do not remove the accumulated physical separation.
D4 codriver-sample lateral tracking RMS improves from 0.00437776 to 0.00414332 m, yet boundary
clearance decreases materially. Tracking a different evolving nominal path more closely
is entirely compatible with moving closer to a boundary.

## First-divergence chain, R4

All values below are retained or sampled from retained accepted packets; no new NLP solve.

1. **Release 0.100 s:** identical physical state, active packet 0, applied command
   `[0.04913086757455902, 0.8131301658927691]`, last application 0.095 s, and pending request
   `[0.03913086757455902, 0.8843219200958784]` due 0.115 s. Both estimates are 17 ms.
   A holds/forecasts using the legacy path; B replays this known commitment and suppresses
   its known-busy 0.110 s tick. Neither forecast sees future readiness or truth.
2. **Predicted NLP initial state at 0.117 s:** canonical B−A is approximately
   `[-0.000381444, +0.000676894, +0.011504649, +0.000053359,
   -0.00000204415, +0.00000419025]`.
   Predicted preceding steering is identical; preceding acceleration is 0.886235761 (A)
   versus 0.884321920 (B). The logged prepared inputs and stored packet initial states
   verify this interface. Full NLP parameter vectors, warm-start guesses, active constraints
   and optimizer iteration trajectories were not exported; they are not reconstructed here.
3. **Solver output:** both return `Solve_Succeeded`, 12 iterations, negligible slack.
   Packet-1 first nominal control is `[-0.0186601453, 0.929453900]` (A),
   `[-0.0192465940, 0.930013156]` (B); its second nominal e_y node is −0.0655736843
   versus −0.0655145520 m. Objectives differ but concern different initial states,
   so their numerical ordering is not an independent performance comparison.
4. **Accepted at 0.160 s:** both physical states are still identical. Late acceptance
   trims the packet from its original 0.117 s origin. Active nominal e_y is −0.0799630583
   (A), −0.0799352429 (B); physical e_y is −0.0791901452 m.
   This nominal difference is already identifiable, but far too small and too upstream
   to identify the eventual 0.126 m loss by itself.
5. **TVLQR samples at 0.160 s, applies at 0.175 s:** rate-limited requested/applied steering
   is identical, +0.00913086757 rad. Requested/applied acceleration is 0.9388386993 versus
   0.9390163454 m/s², a B−A difference of +0.000177646132. First recorded state divergence
   is at 0.180 s. No command uses new packet authority before acceptance.
6. **First steering split:** under packet 6 (accepted at 0.660 s), the 0.700 s computations
   request 0.0899545421 (A), 0.0871789002 (B) rad, applied at 0.715 s.
   At that computation the nominal steering/correction pairs are
   `0.0659507328 + 0.0240038093` and `0.0693208094 + 0.0178580908` rad.
   These sum to the requests; both are within the per-request rate bound on this tick.
   B's net steering is lower even though its nominal steering is higher: feedback matters.
   Subsequent requests mostly walk along their rate bounds with the approximately
   −0.002775642 rad offset, followed by the growing heading/lateral separation described above.

This traces verified signal flow and a concrete later steering separation. It does not
establish whether the first release, repeated prediction changes, elapsed-limiter forecast
assumptions, NMPC sensitivity, or their interaction dominates the accumulated clearance loss.
Later A/B releases no longer have identical states or active trajectories. Within **each**
host release, the retained shadow A/B forecasts still share one identical causal context.
No single accepted packet can be assigned the full downstream loss from these logs.

## Low-latency release analysis

All 114 contexts (19 × three regimes × two host histories) are comparable, with zero
forecast failures/censored targets. Host histories stay separate. Each row in
[low_latency_releases.csv](task007d/d5/low_latency_releases.csv) contains signed and absolute
A/B error, their absolute-error difference and better/worse/tie outcome for r, e_psi and e_y.
[low_latency_phases.csv](task007d/d5/low_latency_phases.csv) separates release 1, release 2,
and releases 3–19, with RMS, counts and shares of **both** predictors' total squared error.
The unchanged 1e−12 SI absolute-error tie band is numerical only, not a practical threshold.
P95/confidence intervals are not meaningful for these small dependent strata.

The following compact tables show the A-controlled physical history; the complete B-host
results are retained in the linked tables. Within each entry below A/B are the two forecasts
on that same history, not forecasts from different physical trajectories.

| Regime / state | Release 1 signed A / B | Release 2 signed A / B | A squared-error share release 1 / 2 (%) |
|---|---|---|---|
| R1 / r | 0.03690173 / 1.110223e-16 | -0.04629592 / 0.0003063278 | 38.829 / 61.116 |
| R1 / e_psi | 0.0003031806 / -2.474028e-05 | -0.000989255 / -5.984357e-05 | 8.456 / 90.023 |
| R1 / e_y | 2.590913e-05 / -1.085213e-06 | -9.27419e-05 / -5.362732e-06 | 7.124 / 91.275 |
| R2 / r | 0.01549592 / -0.00326765 | 0.03310359 / 0.005697096 | 17.954 / 81.937 |
| R2 / e_psi | 8.910393e-05 / -4.854901e-05 | 0.0005525315 / 7.473158e-06 | 2.340 / 89.962 |
| R2 / e_y | 8.108134e-06 / -3.089488e-06 | 5.095196e-05 / 1.554881e-07 | 2.253 / 88.979 |
| R3 / r | 0.01549592 / -0.00326765 | 0.03467634 / -0.001563173 | 16.624 / 83.244 |
| R3 / e_psi | 8.910393e-05 / -4.854901e-05 | 0.001343397 / 1.136474e-05 | 0.421 / 95.659 |
| R3 / e_y | 8.108134e-06 / -3.089488e-06 | 0.0001380891 / -5.432413e-06 | 0.309 / 89.542 |

For single-release strata RMS equals the absolute value of the signed entry. Release 1
uses the 17 ms initial estimate; release 2 already uses the observed 35/60 ms estimate.
Thus exclusion of release 1 alone does not remove the dominant early transition.
For example R1-A heading squared error is 8.456% release 1 and 90.023% release 2; only
1.522% remains in releases 3–19. R2/R3 heading release-2 shares are 89.962%/95.659%.

| Regime / state, releases 3–19 | A RMS | B RMS | B better / worse / tie | Maximum increase in absolute error |
|---|---:|---:|---|---:|
| R1 / r | 0.00033585378 | 0.00031792497 | 16 / 1 / 0 | 1.1358677e-05 |
| R1 / e_psi | 3.1192778e-05 | 3.7700706e-05 | 1 / 16 / 0 | 2.1289146e-05 |
| R1 / e_y | 2.9788959e-06 | 3.6877777e-06 | 1 / 16 / 0 | 2.214657e-06 |
| R2 / r | 0.00029346386 | 0.00076056588 | 0 / 17 / 0 | 0.0022932067 |
| R2 / e_psi | 3.9202688e-05 | 5.9383025e-05 | 0 / 17 / 0 | 0.00014094387 |
| R2 / e_y | 3.8792011e-06 | 5.6656168e-06 | 0 / 17 / 0 | 1.1903527e-05 |
| R3 / r | 0.00033495898 | 0.00046874799 | 1 / 16 / 0 | 0.00062870461 |
| R3 / e_psi | 6.5960054e-05 | 7.5492969e-05 | 2 / 15 / 0 | 5.4755263e-05 |
| R3 / e_y | 1.1275658e-05 | 1.2675415e-05 | 2 / 15 / 0 | 8.3165859e-06 |

Units: r rad/s, e_psi rad, e_y m. The B-host later heading/lateral counts are 0/17 better/worse
in R1, 0/17 in R2 and 2/15 in R3, with the same qualitative RMS deterioration. Later yaw
improves 17/17 times in R1-B, worsens 17/17 in R2-B and worsens 16/17 in R3-B. No averaging
across host trajectories conceals these differences.

Worst absolute-error increases across **both** hosts are:

| Regime | r (rad/s) | e_psi (rad) | e_y (m) |
|---|---:|---:|---:|
| R1 | 0.0000113587 | 0.0000212891 | 0.00000221466 |
| R2 | 0.00229321 | 0.000140944 | 0.0000128980 |
| R3 | 0.000628705 | 0.0000547553 | 0.00000831659 |

R1's worst heading/lateral increases occur at release 7; the other listed worst increases
occur at release 3. R2's worst lateral increase is on the B-host history; all other listed
maxima are on A-host history. The global worst heading increase is about 0.00808 degrees,
lateral about 12.9 micrometers, yaw about 0.1314 degrees/s. The errors are many orders above
the tie band, so they are not roundoff ties; their large percentage deteriorations mostly
reflect very small baselines. A sensor/noise/physical-acceptability model is absent, so no
new practical equivalence threshold or safety claim is assigned.

## Verified mechanisms, supported hypotheses and unresolved attribution

| Explanation | Evidence status | Interpretation and limit |
|---|---|---|
| Pending command at release | **Verified** | All R1 releases have a due-now commitment; all R2/R3 releases a future commitment. None is a no-pending example. B replays it; A omits it. |
| Early command transient | **Verified inputs; supported explanation of early benefit** | R1-A release-2 applied/pending steering is −0.04948456/−0.04195923 rad, a 0.00752533 rad change; at release 3 the change is only 0.000109893 rad. R2/R3 release-2 pending change is −0.01 rad. Early squared-error dominance is verified; its full attribution is not. |
| Unknown future driver latency / ideal feedback timing | **Verified approximation; supported R2/R3 hypothesis** | After the known pending application B assumes zero future latency. Actual R2/R3 future requests apply 5 ms later. This can alter held inputs and steering clamping but cannot explain zero-latency R1 by itself. |
| Elapsed-application steering limiting | **Verified implementation difference; unresolved contribution** | B includes the physical elapsed-time clamp in addition to the per-tick request limit. At release+10 ms after a release+5 ms commitment, ideal B feedback has 5 ms since application; the real next request applies later. No internal forecast event traces were retained to allocate the resulting error. R4 actual application clamping is inactive, distinct from forecast clamping. |
| Curvature / integration approximation | **Verified approximation; supported R1 residual hypothesis** | Predictor holds curvature within each RK4 step; plant refreshes it at derivative stages. Forecast and actual partitions need not coincide. Residual heading/lateral errors remain even with actual zero future latency. Shared approximations and partial error cancellation in A are plausible; no attribution percentage is established. |
| Skipped ticks | **Verified absence in R1–R3** | None has codriver busy misses. Skips cannot be the sole explanation of their regression or early improvement. R4 has 100 busy ticks per run. |
| Nominal path versus tracking | **Verified algebra, unresolved upstream cause** | R4's same-time clearance loss near the minimum lies overwhelmingly in the active nominal-position difference. Nominal starts inherit the already diverging physical states; this is not proof that an independently selected bad nominal path originated the loss. |
| Chronology, authority or future-truth leakage | **No violation found** | Retained authority checks and input/reference matches pass; D5 never calls a predictor or feeds scoring truth into control. A source-level timing approximation is not an observed scheduler violation. |

No semantic defect requiring a predictor/scheduler repair is demonstrated. No such repair,
new forecast equation, gain tuning or estimator manipulation is made.

## Remaining risks and decision gate

**Question A — identifiable explanation, incomplete cause.** Width and mainly-progress
explanations are rejected for this interval. A real rightward physical and nominal excursion,
preceded by changed accepted predictions/controls and the 0.715 s steering split, accounts
for the gap. A unique upstream cause and the counterfactual necessity of any single release
remain unresolved. There is no evidence that accepting plan 18 suddenly creates the gap.

**Question B — no predictor modification justified solely by these small late errors.**
They are genuine systematic numerical differences, not ties, but small absolute heading/
lateral errors amplified by percentage ratios. They warrant a targeted approximation audit,
not a silent mathematical change. R4's 12.65 cm minimum-clearance loss deserves greater
physical-control scrutiny than aggregate RMS or percentage improvements.

**Question C — sufficient for a separately authorized bounded fixed-handoff investigation,
not for adoption or safety acceptance.** Keep A as the production default. Keep B eligible
as an experimental C predictor, with explicit adverse-clearance evidence. Testing C with
legacy A is scientifically reasonable and valuable: holding the predictor fixed separates
the effect of fixed handoff scheduling from the effect of B. A future comparison should
separate variable/fixed handoff and legacy/prefix predictor factors, rather than changing
both and attributing the outcome to one. This is a recommendation, not approval to implement C.

R4 retains zero recorded boundary crossings, solver/model failures, handoff rejections,
exhaustion or fallback. Both have 19 accepted handoffs, reserve ≥0.645 s, zero planner misses,
100 imposed codriver busy ticks and max slack <9.1e−11 m, below the 1e−6 m gate. Steering TV
is 0.949783/0.950911 rad; global heading TV is 2.069154/2.071808 rad. This short high-variation
synthetic interval, just 22.185 mm beyond the frozen margin at B's closest recorded event,
is not robust safety evidence. No independent physical vehicle or hardware timing validation,
full-lap stability, vehicle footprint, measurement-noise tolerance or hard-real-time result
is available. End-of-interval clearance differences are still growing even though each
individual run has passed its own minimum. A later loss cannot be excluded.

## Minimum future diagnostic, recommendation only

To isolate R4 control sensitivity, authorize a short checkpoint comparison from **one common
release context** around the first steering split (plan 6), capturing the complete NLP inputs,
warm-start vector, optimized nodes/gains and tracker values before/after request and application
limits. Fork only the A/B forecast/preparation choice, retaining identical preceding state,
active packet, committed request, imposed timing and all mathematics. Examine the first
resulting commands and a bounded common continuation. Restoring optimizer state is essential;
it was not fully retained, so current files cannot support that counterfactual faithfully.
Obtaining that checkpoint may require a separately authorized short replay; none ran in D5.

For low-latency attribution, a smaller offline diagnostic would trace one retained R1 release
7 and one R2 release 3, recording forecast application times, limiter activity and sampled
curvature. Only after reviewing those traces should an explicitly authorized one-factor
approximation comparison be considered. Do not fit/tune weights or select a predictor using
the same unfavorable cases without retaining the originals.

## Verification, preservation and reproduction

**15 focused offline tests passed in 0.03 s.** Scoped Ruff lint and format checks pass.
Tests cover analytic signed boundaries, side-switch decomposition, exact spatial knots,
bracket interpolation, rejected extrapolation/nonmonotonic/invalid history, unequal coverage,
acceptance-time packet selection/trimming, sample versus application authority, retained-reference
audit failures, immutable input records, phase shares/signs/counts/ties, censored releases and
readiness versus accepted-handoff distinction. No tests invoke solver or physical simulation.
New algebra/interpolation assertions use absolute 1e−12 with zero relative tolerance solely
for arithmetic roundoff. Existing tolerances and tests are unchanged.

Offline report execution revalidates all eight original input hashes, 152 runtime forecast
inputs, 1,400 driver references, 152 handoff errors, zero chronology issues and both exact D4
minima. A second fresh export reproduces the compact bundle byte-for-byte. All 40 retained
D4 files retain their SHA-256; all 10,913 prior result files retain size and mtime; all 417
other previously tracked files remain SHA-256 identical (handoff is the sole edited old file).
No D3/D4 or historical Task007 evidence is overwritten. No measurement process/guard was
active; free disk exceeded the existing 1 GiB floor. Numeric analysis/tests use fresh
Accelerate SINGLE processes and do not overlap measurements.

From the repository root, reproduce **analysis only** into a fresh directory:

```sh
VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/report_task007d_forensics.py --input results/task007d/d4 --output /tmp/apex-d5-review
```

The output directory must not already exist. The command reads retained raw evidence and
committed D4 hashes; it never invokes the pilot worker, solver, predictor or plant.

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts .venv/bin/python - <<'PYTEST'
from threading_study.config import configure_accelerate
configure_accelerate(1)
import pytest
raise SystemExit(pytest.main(['-q', 'tests/unit/test_prediction_forensics.py']))
PYTEST
.venv/bin/ruff check scripts/task007d/forensics.py scripts/report_task007d_forensics.py tests/unit/test_prediction_forensics.py
.venv/bin/ruff format --check scripts/task007d/forensics.py scripts/report_task007d_forensics.py tests/unit/test_prediction_forensics.py
```

Review bundle: summary/provenance JSON; same-time and same-progress tables; recorded-state,
application and handoff-position tables; low-latency per-release and per-phase tables under
`docs/task007d/d5/`. Sources: the new offline helper and report CLI, plus their focused test.
No architectural decision was implemented, so no ADR is added. The handoff is updated.

**STOP AFTER D5. Task007D is not complete. Await Engineering Orchestrator review; no
Architecture C implementation, production-default change or further experiment is authorized.**
