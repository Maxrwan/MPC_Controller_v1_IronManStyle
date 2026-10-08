# Task007C C1–C4 resumption — robustness first

Authorized 2026-10-07 by the new user brief in attachment
`6fa32293-b32a-4ccb-9110-ac5a34e1787d/Pasted text.txt`.
The original C1–C4 intent and approved alpha pairs in
`TASK007C_NEAR_LIMIT_APEX_DIAGNOSIS.md` remain controlling; Task007C-R passed its gate.
Original B/C/CR results are immutable inputs. New outputs use `results/task007c_resume/`.

## Evidence layers and ordering

1. Matched fixed planner35 ms/codriver1 ms and retained stable-C recorded history for the full
   C1 lambda0 grid (gamma1.50–2.20 in0.10 increments). The stable C history has about94 s of
   recorded entries, providing longer coverage than E/F's one-lap histories.
2. Important transition/ablation/horizon/progress candidates receive the original pathological
   E/F histories and an E measured history closest to median whole-run planned heading TV.
   Selection is fixed from Task007C-R data before new formulation outcomes. These are physical
   availability histories, not guaranteed transferable outcome labels. Finite traces stop
   explicitly on exhaustion; no padding/cycling. Compare covered sectors/common prefixes and
   never treat a censored run as a completed lap or as a safety success.
3. Shortlisted candidates receive sequential fresh measured repetitions and useful comparisons
   receive two-lap confirmation. No concurrent tests, plots, analysis or benchmarks during these
   measurements. SINGLE is configured before backend imports in each new worker.

Rank physical validity/boundary safety, solver/domain validity, smoothness, timing-history
robustness/spread, local tracking, then racing performance. Use separate metrics, no scalar score.
Physical/domain/solver failure pauses automated extension of that region for evidence review.
No production defaults are selected before all required comparison layers are evaluated.

## Formulation controls

Only explicit independent alpha_vy/alpha_r multipliers are added, both default1. Stage weights
and matching terminal DARE follow the original approved specification. Zero multipliers retain
all nonlinear states, dynamics, constraints and pseudo-reference construction; only tracking
importance changes. TVLQR is untouched. C3 changes only N4/6/8 with dt0.1 s. C4 initially retains
baseline Q/R/W/horizon and tests static lambda0/.5/1/2/4 at informative transition points.
No adaptive lambda policy, adaptive codriver or fixed-handoff architecture is implemented.

## Internal synthetic physics and review products

Principal cases will export slip/force curves, normalized axle friction planes with unit bounds,
independent lateral-acceleration reconstruction, low/high-slip yaw-reference comparison,
beta versus normalized lateral demand, one-step model residuals and horizon-step prediction
errors. Distinguish same-input model consistency from closed-loop prediction error caused by
changed controls/forecast timing. Numerical derivatives need explicit stencil/time-step limits.
These are synthetic-model checks, never real-vehicle validation.

Hairpin, sweeper and technical phase portraits beta–r and ey–epsi accompany direct heading,
steering/rate TV and reversal measures. Large sector-shaded dashboards and the four-axis
reproducibility/accuracy/precision/smoothness table precede performance comparisons.

## Future timing architecture — document only

After C1–C4 selects a better formulation, compare current variable predicted availability,
committed-control-prefix MPC, and quantized fixed future handoffs30/40/50 ms aligned to the
10 ms codriver grid. Assess handoff prediction error, deadlines, responsiveness, timing-history
sensitivity, smoothness, slack, clearance and performance. Do not confound this with formulation
changes now.

## C2 and measurement counts

The initial C2 grid retains the original nine alpha pairs at gamma1.8 and2.0, N4/lambda0,
under the same fixed and stable-C histories; baseline cells are reused. High-demand/progress
follow-ups depend on physical-validity review. Initial C3 and C4 retain baseline weights rather
than silently combining a successful C2 change with horizon/progress changes. Any combined
confirmation is separately labeled after the isolated effects are understood.

For each final shortlist formulation and its matched baseline, plan five sequential measured
repetitions at the selected operating point(s), with two-lap confirmation for useful comparisons.
Five repeats support descriptive quantiles only, not a population robustness guarantee. Add
repetitions only for a documented unresolved question, preserving every run. Controlled-run
wall times may overlap offline analysis and are not the primary computational benchmark;
measured finalist comparisons must be uncontended. Fixed35ms availability is the existing
007C-R diagnostic mode, not the deferred quantized/committed future-handoff architecture.

## C1 review and informative progress points

All eight fixed and eight stable-C baseline replays completed. The fixed gamma2.2 case crossed
the physical boundary; the stable-C gamma2.2 replay did not. It remains rejected. See
`TASK007C_C1_FIXED_SCREEN.md` and the retained boundary review for the evidence and limitations.
The lambda2 follow-up uses gamma1.8 (lower-demand comparison),2.0 (multiple indicators rise),
and2.1 (near the observed safety transition), under both identical histories. It does not
repeat the rejected2.2 region. These cells are reused by the later static progress map.

The shared-progress export `scripts/task007c_resume/common_coverage.py` keeps each retained
history's actual samples and limits comparisons to intersecting observed progress ranges.
It never fills a censored tail. Complete-lap outcomes and partial-prefix diagnostics must be
reported separately. Plot phase portraits by sector/lap, not across disjoint traversals.

The completed two-history baseline map additionally exposes a nonmonotonic gamma1.9 sensitivity:
heading TV10.204 fixed versus14.770 smooth, while gamma2.0 is11.993 versus11.214. Therefore the
full C4 static-weight grid will use1.9/2.0/2.1, reusing the C1 lambda2 cells and retaining1.8's
lambda2 comparison as a lower-demand control. This selects informative transition points from
the completed C1 observations; it does not alter the approved weight set or control mathematics.

C2's original high-demand/progress follow-up is restricted to alpha_vy0.5/alpha_r1, the only
vy reduction that improved gamma2 smoothness under both fixed and stable-C histories. Test
(1) gamma2.1/lambda0 and (2) gamma2/lambda2, under both histories, keeping N4 and all other
terms fixed. The corresponding alpha1 baselines are already retained. This is a diagnostic
candidate selection, not a production default change or adaptive cost policy.

Physics export schema2 labels each retained packet as accepted, rejected or pending. Primary
horizon-error curves use accepted packets; the CSV and all-prepared companion summary retain
the others. Packet-node forecasts still include later replans/feedback and availability error;
they are not pure model-transcription residuals. Regenerate schema1 principal exports through
`analyze.py --physics` before final rendering. Runtime dynamics and chronology are unchanged.

## Follow-up selection after completed C3/C4 simulations

All18 C3 and30 C4 cells completed without boundary or solver failures. C3 N6 reduces heading
variation and rate-limit time at all three gamma points under both initial histories. N8 is
better at gamma1.8/2.0, but gamma2.1 fixed is worse than N6. These are promising candidates,
not production choices; computational viability still requires isolated measured repetitions.

The next controlled coverage checks use N6/N8 at gamma1.9, where C1 showed a nonmonotonic
history-sensitive pocket, rather than interpolate between1.8 and2.0. The original requested
known-oscillatory stress follow-up uses only N6, the smallest promising extension, at gamma2.2
under fixed/smooth histories. Baseline2.2 fixed remains rejected and retained. A successful
new2.2 lap is not sufficient to expand the robust envelope.

Representative histories first compare gamma2/lambda0 baseline N4, half-vy/full-yaw N4,
baseline-weight N6 and baseline-weight N8 on median/E/F. Gamma2.1 histories compare baseline
N4 and both horizon candidates; half-vy's benefit did not generalize there. Each cell uses
an immutable manifest and a fresh SINGLE worker. No combined alpha/horizon change is introduced.
Review any new failure before continuing. Finite traces retain their actual stopping point.

`validation_campaign.py` provides these explicit phases plus deterministic fixed-history
repeats for N6/N8 at gamma2. The measured shortlist remains contingent on these histories,
C4 analysis and isolated backend/compute observation. No adaptive progress gate is justified yet.

C4's completed analysis identifies one additional narrow candidate: gamma2/lambda4/N4 improves
heading TV, steering TV and rate-limit time under both initial histories. Fixed lap time improves
0.200s; smooth lap time is essentially unchanged (+0.007s), with slightly lower minimum clearance.
The same lambda4 strongly worsens gamma2.1 fixed oscillation. Therefore add gamma2/lambda4/N4,
with baseline alpha1, to each representative median/E/F history before accepting or rejecting
it as a static candidate. Do not generalize it to a global default or combine it with N6/N8.

N6 gamma2.2 completed both controlled stress histories with no boundary/solver failure and
negligible predicted slack. Fixed heading TV24.807→9.278rad, rate-limit time16.69→5.706s and
clearance−0.01974→0.31563m; smooth heading TV21.917→8.760rad and clearance0.09996→0.31562m.
This warrants candidate-only gamma2.2 N6 sensitivity checks on median/E/F, appended after the
representative-g2p1 phase. The matched2.2 N4 comparison is fixed/smooth only; do not claim a
matched N4 improvement under E/F without that comparison. Gamma2.2 remains outside any accepted
envelope until representative histories and fresh measured repetitions are assessed. Do not
extend the aggression grid beyond the originally requested2.2.

After fixed N6/N8 repeats, the queue runs short0.8s zero-latency and injected chronology checks
at gamma2/lambda0. The injected case uses the existing diagnostic timing interface for150ms
planner delay and25ms codriver/actuator availability, exceeding their100ms/10ms deadlines.
Verify physical progress during preparation, ongoing codriver work, command-application state
staleness, and separately counted planner/codriver skipped deadlines. Preserve raw outputs.
These tests make deterministic physical-time assertions only; measured wall times are never
exact CI thresholds. Full fresh-measured finalist repetitions remain a separate later phase.

Sustained confirmation keeps the existing initial s_abs=1m unchanged. Because the first lap-end
crossing is a rolling segment, request THREE counted crossings to obtain TWO subsequent complete
geometric laps. After fixed repeats/latency checks, run gamma2 N4/N6/N8 and gamma2.2 N6 with
baseline weights/lambda0 under fixed and smooth histories, laps=3 and duration120s. The smooth
history remains finite; if it exhausts before two full laps, report that censoring rather than
extend it. Per-lap metrics and individual lap times distinguish the rolling segment from the
second/third complete laps. Never compare summed three-crossing TV with a one-screen total.

The prepared measured harness rotates configuration order across repetitions, dispatches one
fresh worker at a time, journals UTC events, preserves per-cell outputs and stops on new failures
for review. `MEASURED_ACTIVE` blocks new analysis/rendering/bulk preservation audits/backend
benchmarks and admits only measured workers carrying that harness's owner token. This guard does
not stop preexisting jobs: verify those have finished before starting measurements. The gamma2 measured campaign is active. The first N6
repetition exhausted its trajectory during a593ms preparation interval (119ms CPU), despite
a successful13-iteration solve; its failed outcome is retained. See
`measured_n6_rep00_exhaustion_review.json`. Reviewing this failure authorizes completion of
the predeclared repetitions for outcome precision, not acceptance or replacement of the run. Do not overlap numerical tests or other projects'
benchmarks with it. The guard is orchestration only; controller/plant mathematics are unchanged.
