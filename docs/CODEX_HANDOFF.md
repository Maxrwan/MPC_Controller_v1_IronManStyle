# APEX handoff — Task007C C1–C4 robustness validation

Updated2026-10-08. Task remains in progress. User repeatedly authorizes continuation.
Current brief: `/Users/marwansaber/.codex/attachments/6fa32293-b32a-4ccb-9110-ac5a34e1787d/Pasted text.txt`.
Original detailed request: attachment `f3aef931-588b-4af1-be06-3450fc5a54cf/Pasted text.txt`;
protocol: `TASK007C_NEAR_LIMIT_APEX_DIAGNOSIS.md`, superseded gate status clarified in
`TASK007C_RESUMPTION.md`. Original end-of-task response requires48 numbered sections.
Prior completed reproducibility-gate handoff: `TASK007C_R_HANDOFF.md`.

## Active work and immediate continuation

The controlled queue finished (`upper_region_campaign_after_review.log`, former session2722).
No numerical project jobs remained when inspected before backend benchmarking. N6/N8 backend
thread audits passed: each sampled max1 thread, CPU/wall0.9970/0.9993. Measured repetitions
are active in session54522 after reviewing the first N6 failure. The same immutable plan
resumes by reusing completed cases, never replacing a failed run. Tail `measured_g2_campaign.log`.
The completed follow-up includes all gamma2.1 histories, gamma2.2 N6 median/E/F, both exact
fixed-history repeats, four zero/injected latency checks, and eight sustained confirmations.

Both N6/N8 repeat checks PASS with zero numerical differences across physical state/control,
availability, references, predictions and NLP inputs/solutions. The horizon-specific control
offset is explicitly corrected in `confirmation_report.py` without changing the archived CR
helper. Artifacts: `n6_fixed_repeat_parity.json`, `n8_fixed_repeat_parity.json`.

All eight sustained cases completed three crossings with no boundary, solver, forecast,
fallback or deadline failures: gamma2 N4/N6/N8 and gamma2.2 N6 under fixed/smooth histories.
The first crossing starts at s_abs=1m; only the next TWO laps are full geometric laps.
`TASK007C_SUSTAINED_CONFIRMATION.md` and `sustained_per_lap.csv` report each separately.
N6 is not uniformly smoother on every sustained lap: gamma2 smooth lap3 heading TV is
9.992 versus baseline9.855rad; at gamma2.2 smooth lap3 it grows to11.530rad versus8.957 on lap2.
These caveats must enter the envelope decision. N8 improves both full gamma2 smooth laps.

Zero/injected diagnostic checks passed for N6/N8 (`candidate_latency_checks.json`). With
150ms planner/25ms driver injection, physics advances0.841/0.848m during solves, application
progress staleness reaches0.140/0.142m, codriver executes during preparation, and4 planner/53
codriver misses are counted separately in each0.8s record. Zero-delay checks have no misses.

Next measured plan: gamma2 N4/N6/N8, five repetitions each in rotated order, then five N6
repetitions at the upper gamma2.2 point. Do not run analysis/rendering/tests concurrently.
Review every new failure before resuming. No formulation or envelope is accepted yet.

## Completed scientific work

C1:16 baseline cells gamma1.5–2.2 plus6 informative lambda2 cells. Transition sensitivity starts
around1.9–2.0, is nonmonotonic across histories, and worsens sharply at baseline2.2. Fixed2.2
crosses the boundary; smooth2.2 is highly oscillatory. See `TASK007C_C1_FIXED_SCREEN.md`.

C2:36 initial grid cells (four reused C1 baselines), plus4 follow-ups, all analyzed. Weakening
yaw tracking is poor. Half-vy improves only gamma2 in the initial two histories, then FAILS
pathological E; it is rejected as a robust finalist. See `TASK007C_C2_GRID_RESULTS.md`.

C3:all18 primary horizon cells complete and analyzed, baseline weights/lambda0. N6 improves
heading variation and rate-limit activity at1.8/2.0/2.1 under fixed and smooth histories. N8
improves2.0 further but is worse than N6 at2.1 in these two histories. Supplemental1.9 N6/N8
fixed/smooth all safe and smoother than baseline. N6 gamma2.2 fixed/smooth both safe with
negligible slack; fixed heading TV24.807→9.278rad and clearance−0.01974→0.31563m. This is not
an accepted envelope. See `TASK007C_C3_GRID_RESULTS.md`, `TASK007C_GRID_INTERPRETATION.md`.

C4:all30 static-weight cells complete and analyzed at1.9/2.0/2.1. Responses are nonmonotonic
and history-dependent. N4/lambda4 improves initial gamma2 smoothness but FAILS pathological F;
reject it as a robust finalist. No adaptive gate or schedule is justified. Exact table:
`TASK007C_C4_GRID_RESULTS.md`;270 bounded sector traversals in `c4_paired_sector_feasibility.csv`.

Gamma2 retained-history matrix is complete: five formulations ×five histories. Half-vy and
lambda4 are rejected; N6/N8 remain. On the same approximately1–145.94m progress interval:
baseline heading TV10.278–28.651rad, N6 8.214–8.495rad, N8 6.916–7.496rad. Median trace ends
at30.45s before the gamma2 lap end for every formulation; each retains two codriver misses.
N6/N8 reach their requested E/F lap ends safely. These screens start at s_abs=1m, not a complete
geometric lap. Gamma2.1 retained-history matrix is also complete:15 records, no boundary/solver failure;
see `TASK007C_G2P1_HISTORY_RESULTS.md`. Gamma2.2 N6 completes all five histories safely;
`TASK007C_G2P2_HISTORY_RESULTS.md` reports seven records including the rejected N4 fixed stress case. Exact gamma2 coverage/ranges: `TASK007C_G2_HISTORY_RESULTS.md` and
`TASK007C_REPRESENTATIVE_HISTORY_REVIEW.md`; native-progress JSONs remain in the result root.

## Rejections and evidence preservation

`results/task007c_resume/reviewed_failures.json` binds each review to the exact summary hash.
Never discard unfavorable runs or waive an unreviewed new failure.
- Baseline gamma2.2 fixed:44 boundary samples, max ey0.569740m.
- Gamma2 alpha(.25,.25) fixed:159 samples, max ey0.814420m, technical entry.
- Gamma2 alpha(1,0) smooth:62 samples, max ey0.590392m, hairpin approach.
- Half-vy gamma2 pathological E:59 samples, max ey0.583446m, clearance−0.033446m, fast sweeper.
  Slack0.111458m, active nominal ey0.581448m, local ey error below0.010m; no solver/deadline
  failure. `c2_pathological_e_boundary_review.json`. F was retained and did not add a crossing.
- N4/lambda4 gamma2 pathological F:100 samples, max abs ey0.637804m, clearance−0.087804m,
  return complex. Slack0.162558m, active nominal abs ey0.631948m, local ey error below0.010m;
  no solver/deadline failure. `c4_pathological_f_boundary_review.json`.
Do NOT run measured finalist repetitions for half-vy or lambda4. Their physics and failure
sector dashboards are exported. Half-vy fast-sweeper and lambda4 return-complex dashboards were both visually inspected
(`c2_pathological_e_failure_render.log`, `c4_pathological_f_failure_render.log`).

## Validation and artifacts

Runtime changes relative to resumption are only independent nonnegative alpha_vy/alpha_r
(default1) and compatible DARE construction in cost.py/controller.py. Nonlinear states,
constraints, TVLQR, plant, solver and timing architecture remain unchanged. Defaults retain
exact full rolling-screen parity with the archived CR case: `full_lap_default_parity.json`.
27 DARE checks and533 full regression tests passed before diagnostic-only additions. The three
current physics/extraction tests passed, including shared-prefix endpoint handling. Ruff passes.

Principal baseline/N6/N8 and former alpha/lambda candidates have schema2 physics exports,
large dashboards and hairpin/technical/sweeper zooms. Primary horizon errors use accepted
packets only; tagged rejected/pending/all-prepared evidence remains. No state extrapolation.
`TASK007C_PHYSICS_REVIEW.md` documents derivative, force-balance, finite-difference and realized
horizon errors. These are internal synthetic checks, never physical-vehicle validation.
`TASK007C_SECTOR_DIAGNOSIS.md` preserves increased actual reversal counts where planned TV falls;
interpret counts with their magnitude/deadband and sector context. Heading TV here is Frenet
unwrapped epsi. C3 phase portraits and comparison figures were visually checked.

Original B/C/CR artifact hashes are preserved:675/293/1907 files verified at the90-cell audit.
Chronology passed91 cases including baseline parity. Rerun final audits after all new cases.
Disk was previously exhausted during a derived export; user freed space, raw evidence verified,
exports regenerated. Current free space about5.1GiB. Launch/analysis stop below1GiB. Do not
remove prior evidence. `disk_capacity_pause_record.txt` preserves that interruption record.

## Measured phase — first failure reviewed, repetitions active

`measured_campaign.py --gamma 2 --horizons 4 6 8 --repeats 5` prepares immutable rotated-order
plans and runs sequential fresh measured workers, preserving every outcome and UTC journal.
The MEASURED_ACTIVE guard blocks new analysis/rendering/bulk audits/backend benchmarks and
admits only that harness's workers. It does NOT stop preexisting jobs: verify no preexisting
analysis/render/test workers before starting measurements; the controlled queue has finished.

First run isolated `backend_audit.py --case` for N6/N8 to verify actual threads and CPU/wall,
then measured repetitions. Baseline audit observed one thread and CPU/wall0.9949. Environment
variables alone are not evidence. Decide upper-point N6 measured repeats from completed histories
and sustained confirmations; do not claim an envelope from the largest completed screen alone.
Five repeats support descriptive distributions, not population guarantees or exact timing CI.
No bulk analysis, plots or tests may compete with measured workers. The guard/harness worked: the first measured N6
failed at18.756621s, trajectory exhaustion outside fallback domain, no boundary or solver
failure. Pending plan182 used593.021ms wall versus118.649ms CPU,13 successful iterations.
Physics advanced3.1085m during the observed pending interval.5 planner/6 driver misses.
Cause of the large wall/CPU gap is unresolved; do not discard the result as an OS outlier.
`measured_n6_rep00_exhaustion_review.json` and hash-bound review retain the failure. Complete
the predeclared five repetitions to characterize outcome spread; no acceptance yet. No production defaults are changed.

## Remaining deliverables and stop condition

Controlled histories, exact fixed repeats, latency checks and sustained confirmation are done.
Complete isolated backend/measurement work, per-run
outcome/compute distributions and principal finalist/worst-case visuals. Assemble four-axis
reproducibility/accuracy/precision/smoothness table BEFORE performance, provisional envelope,
final preservation/config/chronology audits and source/result manifest. Complete the original
48-section response plus updated brief products. Stop for review; no final selection yet.

After C1–C4 formulation review, document-only timing comparison remains current variable
availability versus committed prefix versus fixed future30/40/50ms on the10ms codriver grid.
After online SI is implemented AND accepted, mandatory workbench updates must show identified
parameters, spatial maps, uncertainty, residuals, nominal/identified predictions, grip trends
and lap comparisons. Then study estimator cost/scheduling/update rate, async adoption/delay,
HIL/bench work where available, sensor/actuator latency, missed updates and uncertainty response.
See `PROJECT_ROADMAP.md`. Do not implement these, adaptive codriver, LMPC, energy or opponents now.
