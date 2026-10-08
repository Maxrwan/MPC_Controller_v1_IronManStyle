# Task007C results — reproduction gate not passed

Task007C is **incomplete and stopped before C1–C4**. All six anchor runs and one additional
unchanged measured repeat each of E/F completed. The original rejected behaviors did not
reproduce. The brief explicitly requires stopping here. No formulation change is recommended.

## Anchor reproduction

A–D values below are means of the two complete comparable laps after the startup lap.
E/F values are single rolling-start lap screens, not three-lap confirmations.

| Anchor | gamma | lambda | Original lap [s] | New lap [s] | Change [%] |
|---|---:|---:|---:|---:|---:|
| A | 1 | 0 | 59.012767 | 59.013907 | +0.0019 |
| B | 1 | 2 | 58.798913 | 58.798331 | -0.0010 |
| C | 2 | 0 | 31.495342 | 31.470341 | -0.0794 |
| D | 2 | 2 | 31.581479 | 31.609934 | +0.0901 |
| E | 2.5 | 1 | 32.206657 | 30.287582 | -5.9586 |
| F | 2.5 | 2 | 31.576227 | 30.659326 | -2.9038 |
| E_REPEAT | 2.5 | 1 | 32.206657 | 30.919824 | -3.9956 |
| F_REPEAT | 2.5 | 2 | 31.576227 | 31.008320 | -1.7985 |

Conservative progress benefit reproduces: B improves over A by approximately 0.365%.
At gamma=2, positive progress remains slower: D is approximately 0.444% slower than C.
These checks do not rescue the failed rejected-case prerequisite.

| Critical metric | Task007B original | First repetition | Additional repetition |
|---|---:|---:|---:|
| E sweeper planned-heading TV [rad] | 6.328775 | 0.280870 | 0.282400 |
| E sweeper rate-limit time [s] | 2.35 | 0.00 | 0.00 |
| F maximum predicted slack [m] | 0.0274713 | 9.092e-11 | 9.093e-11 |
| F minimum physical clearance [m] | 0.0600955 | 0.109151 | 0.095736 |

F also varies across runs: original/first/repeat sweeper heading TV is 0.278812/1.834608/
0.280390 rad. The first repeat has 0.79 s at the rate limit there; the additional repeat has
0.01 s. Retain all outcomes. A smoother repeat does not establish safety or invalidate Task007B.

## Provenance and chronology

Before work, 259 Task007B source hashes and 675 artifact hashes were verified. The final
`anchor_provenance.json` verifies all 79 unchanged current runtime Python files, all 675 prior artifacts,
all eight fixture copies, configurations, native settings and startup states/controls.
B–F and both repeats match their original runtime source hashes exactly. A is the documented
exception: early Task007B B0 predates additive capped-polynomial loader support in
`planning_reference/reference.py` and `planning_reference/speed_polynomial.py`. No new
Task007C runtime changes exist. That inherited difference is disclosed rather than hidden.

All eight physical-time audits pass: physics advances between releases/applications, commands
remain held until application, rate/angle/force bounds hold, solver jobs do not overlap,
trajectory samples match the active packet, and skipped releases are accounted for.
Measured traces are not equal. Timing-dependent trajectory sensitivity remains a hypothesis;
neither source equality nor different timings alone establish a causal explanation.

## Implemented offline diagnostics

Five arithmetic tests cover beta, variation/heading unwrapping, steering reversals/rate-limit
time, numerical-chatter deadband, prediction progress and a common 0.4 s comparison window.
For every logged prediction, exports retain individual steering/heading/ey/vy/r TV and span,
reversals, beta statistics, progress and normalized variation. Packet preparation and accepted
handoff flags distinguish optimizer output from active packets. Sector/lap exports and rolling
one-second variation cover active plans and vehicle motion independently.

No scalar oscillation score is used. Reversal deadbands 1e-5/1e-4/1e-3 rad/s expose sensitivity.
Within-prediction steering excludes the unavailable prior-command-to-u0 increment; N controls
span (N−1)dt. Nominal packet input jumps are not continuous actuator-rate violations.
Sideslip is atan2(vy,vx), in radians. Nonzero sideslip alone is not classified as failure.

## Anchor physical and computational evidence

| Case | max abs beta [rad] | lateral RMS [m] | front/rear max | clearance [m] | planner mean/p95 [ms] | codriver mean/p95 [ms] | planner/codriver misses | reserve min [s] |
|---|---:|---:|---|---:|---|---|---|---:|
| anchor_a | 0.1294 | 0.000410 | 0.3844/0.3057 | 0.334927 | 24.054/30.759 | 0.850/1.175 | 3/7 | 0.200000 |
| anchor_b | 0.1285 | 0.000421 | 0.3908/0.3099 | 0.335025 | 24.101/30.698 | 0.861/1.194 | 3/1 | 0.179033 |
| anchor_c | 0.3149 | 0.001505 | 0.9585/0.9778 | 0.320557 | 28.637/32.916 | 0.844/1.106 | 1/0 | 0.200000 |
| anchor_d | 0.3139 | 0.001543 | 0.9525/0.9791 | 0.315437 | 28.445/32.975 | 0.840/1.115 | 0/0 | 0.273154 |
| anchor_e | 0.3458 | 0.002438 | 0.9068/0.9603 | 0.127485 | 30.057/34.549 | 0.831/1.068 | 0/0 | 0.263942 |
| anchor_e_repeat | 0.3961 | 0.002523 | 0.9232/0.9765 | 0.131914 | 30.267/34.270 | 0.842/1.084 | 1/0 | 0.199801 |
| anchor_f | 0.4290 | 0.002587 | 0.9392/0.9818 | 0.109151 | 30.728/35.303 | 0.842/1.070 | 1/1 | 0.199417 |
| anchor_f_repeat | 0.4202 | 0.002548 | 0.9350/0.9807 | 0.095736 | 29.968/34.044 | 0.834/1.072 | 0/0 | 0.267648 |

All eight runs complete without solver failures, planner failures, global fallback or boundary
crossings. Higher-demand cases use the retained acceleration/braking bounds −3/+2 m/s²
(dynamic a_cmd=Fx/m). Steering stays within ±0.4 rad and applied rate within ±1 rad/s.
F repeat reaches the steering-angle limit. These are observations, not proof of robust safety.
Timing p50/p95/p99/max, preview/solve/gain/preparation components, CPU demand and RSS remain
in each `summary.json`. Total measured CPU demand is 0.322–0.387 core-seconds/s and
peak worker RSS is approximately 188–291 MiB across anchors. Measured timing is not an
exact regression pass/fail requirement.

## Region-specific reproduction review

**Hairpin:** E/F planned heading TV stays roughly 1.83–1.93 rad in the new runs, with
0.89–1.04 s at the applied rate limit and local lateral RMS 2.44–2.69 mm. Activity persists,
but alpha/horizon experiments were not run; its cause cannot be assigned to either hypothesis.

**Technical section:** E new heading TV 5.424/5.618 rad; F 3.960/4.825 rad. Rate-limit times
are 1.91/1.97 s and 1.92/1.98 s respectively, with local lateral RMS about 2.45–2.86 mm.
This region remains active even when the sweeper is smooth. Direction-change activity and
sector TV alone do not establish pathological oscillation. No pseudo-reference causal claim.

**Fast sweeper:** visually inspected common-axis E overlays show the original repeated
heading/vy/r/steering oscillation and speed loss absent from both new E runs. Actual vehicle
motion follows the original oscillatory plan closely. F varies by repeat and does not reproduce
its original material-slack failure. The accepted gate therefore fails both numerically and visually.

## Failure-source classification and limits

The original E pathology is evidence of undesirable APEX planned motion with close local
tracking, rather than evidence that TVLQR caused it. Its mathematical cause remains unresolved.
Original F margin/slack behavior likewise is not reproduced. Its maximum active-packet slack
appears around progress 13.584 m in the long-straight sector before the hairpin, not in the
sweeper. An additional F long-straight overlay exposes that difference. Classification for the changed
reproduction outcome is **mixed / unresolved**. Planning feasibility demand, pseudo-reference
cost, preview and progress-pressure hypotheses remain unseparated. No new evidence supports
changing the codriver. Synthetic tire parameters are not measured APEX vehicle data.

## Deferred experiments and figures

C1 fine transition map, C2 vy/r and consistent terminal-DARE ablations, C3 N4/N6/N8 study,
C4 static-lambda map and optional diagnostic scheduling gate were not run because the
mandatory anchor prerequisite failed. No alpha parameters or DARE changes were implemented.
No transition region, best alpha, preferred horizon or lambda scheduler can be inferred here.
Task007D is not ready on Task007C evidence.

Anchor full-trend review images and E/F sector overlays are provided below. They are
**reproduction-review artifacts**, not substitutes for the unexecuted C1–C4 dashboards/maps.
The required transition, dynamic-reference ablation and horizon-comparison images were not
fabricated. The full 22-panel experimental dashboards await an authorized study past the gate.

## Artifact locations

- `results/task007c/anchor_comparison.json`: original/first/repeated comparison and gate checks.
- `results/task007c/anchor_provenance.json`: runtime/fixture/configuration/startup verification.
- `results/task007c/verification.json`: eight chronology audits.
- `results/task007c/anchor_{a,b,c,d,e,f,e_repeat,f_repeat}/`: raw events, states, controls,
  predictions, packets, summaries, analysis, telemetry and oscillation exports.
- `results/task007c/task007c_anchor_review_anchor_<case>.png`: eight full-trend anchor images.
- `results/task007c/task007c_anchor_comparison.png`: anchor comparison.
- `results/task007c/task007c_anchor_{e,f}_{hairpin,technical_section,fast_sweeper}_zoom.png`:
  six common-axis overlays of original/first/repeated runs.
- `results/task007c/task007c_anchor_f_long_straight_zoom.png`: the original F slack episode.
- `results/task007c/regression.log`: full project regression results.
- `results/task007c/sideslip_<case>.png`: eight anchor sideslip relationship plots.
- `results/task007c/ARTIFACT_INDEX.md`: exact absolute image and evidence paths.

## Validation

Full project regression: **505 passed in 653.71 s (10 min 53 s)**, including the five new
arithmetic diagnostic tests. Whole-repository Ruff lint passes; all nine new/updated Task007C
Python/test files are formatted. Eight chronology audits and eight export-completeness checks
pass. All 24 PNGs decode successfully; original E sweeper, original F slack episode, F technical
section and the anchor comparison were visually reviewed. No runtime alpha/DARE tests were
added because those formulation changes were intentionally not implemented past the failed gate.

Current source hashes, archived source snapshot and result hashes are in
`results/task007c/provenance.json` and `source_snapshot.zip`. Existing git changes from previous
tasks are not Task007C runtime changes; preservation is checked against the accepted Task007B
hashes, not a clean-git assumption.

## Next recommendation

Agree on a controlled reproducibility investigation before resuming C1–C4. Recorded-latency
replay alongside fresh measured repeats could separate chronology sensitivity from formulation
sensitivity while preserving physical motion during computation. This is a recommendation,
not an implemented replay mechanism or proof that timing caused the mismatch. Do not
retune anchors into agreement or relax the gate retrospectively. See reproduction commands
in `docs/TASK007C_REPRODUCTION.md`.
