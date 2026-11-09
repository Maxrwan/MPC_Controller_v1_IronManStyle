# NMPC Lab V1 — bounded WORK

**WORK_COMPLETE_PENDING_FINAL_REVIEW.** 9 November 2026. Branch `codex/nmpc-lab-v1`, starting
commit `4f398cfa68bbad3f5d66068888aec70d948e1bb9`; scientific source remains
`48adbdf64d492592d15e23c917aca71fa58aa8a5`. Independently reviewed execution source
`af3956fc2dc8c1a88051e87e2eae66010490a2fb` produced all three authorized attempts, once each.
The containing candidate adds only retained-data presentation/tests and documentation after Primary's
Bench reference addendum; no additional numerical execution is permitted. The same independent
context is completing consolidated final review. [Machine record](work_record.json).

## Small configuration contract

The sole profile is [nmpc_scratch_profile.json](../../tools/apex_workbench/nmpc_scratch_profile.json).
It references the original vehicle, Planning, Performance, configuration and availability sources.
The GUI exposes only native CostScales `lateral`, `dynamic`, `speed`, `control`, `rate`, `terminal`,
`alpha_vy`, `alpha_r`, reset-to-baseline, and a fixed native disturbance selector. No vehicle, tire,
actuator/constraint, horizon/timestep/substep, solver, TVLQR-structure or geometry/reference editor
is added. Broader source-controlled experimental changes require a revised profile/scientific review;
the accepted frozen Performance configuration is never overwritten. Native dataclasses construct
the actual MPCConfig/CostScales. Alpha factors retain their stage/terminal-DARE meanings; increment
penalties are not derivative penalties.

Versioned documents contain configuration ID/version, profile ID/hash, scientific SHA, the eight
costs and named disturbance. Strict JSON round-trips reject unknown fields, duplicates, nonfinite,
Boolean and invalid native positivity values. Drafts save exclusively under the Scratch output root.
They remain unreviewed. A future exporter must explicitly select an exact version/hash and its
review record, then reuse the canonical factory; last editor values are not deployment approval.
No exporter, ROS 2, Docker or hardware packaging is implemented.

## Execution and recording

`nmpc_scratch` uses the original source-isolated imports, NMPC/IPOPT/TVLQR, Architecture A,
GP gamma2 and asynchronous runner. The verified333-file frozen runtime is mounted read-only from
M5-A; output/configuration/probes and the initial flat WORK budget live only under
`results/apex_workbench_nmpc_lab_v1/`. Existing M5-A gate/claims and all historical evidence remain
unchanged. All adapters share the existing lease, cancellation, owner-birth checks and resource
safeguards:60s wall /30s CPU /512MiB sampled RSS /64MiB sampled output /16MiB single file.

After exact-source independent PASS, the three authorized2.0s attempts completed with valid evidence:

1. Accepted Performance cost defaults.
2. Same scenario, only lateral2.0→1.0.
3. Accepted costs with the existing native state perturbation: +0.08m e_y, −0.04rad heading,
   configured0.5s. These magnitudes are existing AsyncConfig defaults. Native geometry/domain
   configuration is checked before execution; actual trigger time and applied configuration persist.

All ran on8 November UTC (8/9 November Cairo). Native windows contain400 states /200 applied commands,
0–1.995s samples and end1.9999999999999787s. Supervisor wall times18.039/18.141/17.943s and peak RSS
242,204,672/229,212,160/240,336,896bytes stayed within unchanged caps. Output was3.55/3.55/3.64MB,
largest file1.12MB. All three slots are consumed, with no retry, censoring or acceptance enabled.
Native Accelerate SINGLE controls were verified; four total process threads were sampled. That does
not establish a single-thread process, parallel execution or a hard real-time guarantee.

One mutable access/budget document binds the reviewed source and records consumption under the
existing lease; there is no per-experiment immutable authorization chain. No retry/search or extra
experiment is allowed. After Primary acceptance, a separate explicit acceptance record can enable
interactive user-triggered runs within this fixed profile/caps; it is not enabled by WORK or review.
Native failures, partial journals and administrative censoring remain retained and distinguishable.

## Observation and analysis

New Run/Inspect/Compare routes and a dedicated Analyze view preserve the old workspace paths.
Recorded replay steps actual samples only, with canonical global conversion, true track boundaries,
selected nominal packet predictions/reference nodes and separate optimized/requested/applied command
clocks. Packet observer capture occurs before scheduler completion stamping; actual scheduling is
read from original raw packet/plan/handoff records. No missing sample, prediction or command is filled.

Read-only design reference: [APEX Development Bench35f6fa5](https://github.com/Maxrwan/apex-development-bench/tree/35f6fa579adc574d73ea834786e53667eddcb585),
especially `web/app.mjs`25–30 and README value classifications. The small extension exposes actual
N=8 node selection (nine states/eight commands; no terminal command), objective-component bars,
native residual/slack/timing and packet completion/validity/handoff records. Plant/SOLVER/DERIVED
classes remain explicit. Native completion prediction_error keeps its original semantics and both
target/comparison times; no interpolated prediction-error curve is manufactured. No Bench N=4
assumption, interpolation, vendor scientific implementation or standalone runtime was copied.

Racing-reference errors subtract original Planning e_y/e_psi at each actual s_abs (heading wrapped
canonically). Raw Frenet coordinates and active-TVlQR-packet errors stay distinct. Metrics use native
sample windows: peak/RMS/heading error, zero crossings, actual application-time command variation,
solver/preparation durations/iterations, native slack, grip utilization and model/domain outcomes.
Different cost-objective totals are not ranked. Two-run comparisons show all configuration differences;
different source/scenario/environment/coverage are illustrative and recovery requires compatible
actual disturbance definitions.

Observed settling means the first native sample whose entire observed remaining tail stays within
an analysis-only error band (default0.01m, minimum tail0.25s). These descriptive settings do not change
scientific tolerances or constitute acceptance criteria. A short or nonsettled window is reported.
No reference step occurs here, so step overshoot is unavailable. A two-second observation is not a
stability or physical-validity qualification.

Local indicators use the actual frozen TVLQR Jacobian and recorded gain at identical nominal
packet operating points:10ms discretization /RK4×2, order[e_y,e_psi,vy,r], steering input, negative
feedback. F=A−BK, eigenvalues, spectral radius, gain variation and chronological finite-horizon
products are read-only diagnostics within one nominal packet. Mixed-SI Euclidean amplification is
coordinate-dependent; clamps, handoffs, longitudinal coupling and nonlinear/hybrid guarantees are
excluded. Instantaneous eigenvalues inside the unit circle do not prove time-varying stability.
Observer overhead is separately recorded; it never changes imposed simulated availability.

## Focused software evidence and preservation

Pre-SVG focused presentation invocation on132a8e3: **98 passed,0 failures/errors/skips,31 deselected,66.59s**.
No genuine controller/closed-loop run, optimizer solve or Plant.step occurred. Source-isolated
configuration/MPCProblem construction and component algebra were permitted. Tests independently
check all eight overrides reaching native problem/constructor semantics, literal cost expressions,
canonical geometry/reference conversion on original retained data, finite-difference Jacobian/order
and native feedback sign, noncommuting time-varying matrices, actual-time metrics/insufficient tails,
small-editor UI, N=8 terminal-node handling, replay, same-size/restored-mtime corruption withdrawal, lifecycle/budget/failure,
and original M5-A/P/C0 behavior. Scientific launches were audit-blocked in the pytest parent.

Earlier32-pass/4-setup-error attempts exposed missing runtime-parent/root coupling. The final design
uses the existing verified cache read-only and leaves both original M5-A modules byte-identical.
Earlier36/37-pass checks remain separate. A selection including a legacy plotting/simulation node
was interrupted before that node:24 passes, incomplete selection, zero numerical launches. Its
interruption, sandboxed process-inspection denial and successful scoped interruption remain recorded.
Initial lint failures and all corrected attempts/logs/JUnit remain in the ignored WORK directory.
The earlier corrected97-pass gate remains separate. A later harness invocation failed before
collection because its PYTHONPATH omitted the repository root; log retained, then corrected without
changing implementation. No historical counts are added to98. Broad scientific/qualified/frozen suites were not run.

Additional actual-retained-data AppTest: **4passed,5.92s** before the renderer correction;
final SVG invocation **4passed,6.05s** (separate counts), no scientific imports or launches. It
exercised replay steps/seek/play/pause, terminal node8, disturbance/local analysis, insufficient
recovery windows, controlled/illustrative comparison and original M5-A/P/C0 workspace routes.
The real embedded browser exposed blank WebGL traces despite passing AppTest. Original screenshots
are retained; replacing the four Scattergl constructors with SVG Scatter preserves every data array
and removes that renderer dependency. A fresh owned server rendered15 SVG trace paths/2723 points
with no GL canvases; the disturbance response is visibly present. No general browser/GPU guarantee
is inferred. Hot module reload did not replace the old server imports; clean owned restart was
required, as already documented. Native segment boundaries independently confirm the only jump is exactly the declared state kick
at0.5s. RMS racing-reference lateral errors were0.008359/0.010243/0.021431m; these three individual
synthetic observations establish no performance superiority. Baseline/lateral physical-state and
requested/applied-control fields exactly match their original M5-A records (400/200 rows each);
host timing/observer records are excluded from this retained-data comparison. Disturbance observed-window settling
was0.465s after application at the descriptive0.01m band/0.25s tail, observed only through1.995s.

Pre-review audit:6,329 original M5-A regular files and324 links unchanged, no added historical files;
333 frozen runtime members match exact Git bytes; no src/scripts/configs/dependency changes. Primary
56 scientific /345 qualification /25 P /4 oval groups and original C0 bytes match; G1 stays OPEN.
This preserves independently verified PRE-INT-W1 and all historical research. Raw evidence remains
local/ignored; committed hashes do not establish off-host retrieval. No formal Verification or
scientific qualification is claimed.

The initial exact candidate01ace08d independently failed V1-ER1-P1: a replacement between data
ingestion and fresh anchor hashing could be adopted as the new anchor. The failed reproduction,
BLOCKED record (`f748b788cbf65a48518209b95779b16d889aaca6e68ff4ea791531fe653e5d38`) and original
96-pass WORK result remain preserved separately. The correction captures status/manifest bytes before
ingestion, decodes only artifacts verified against that captured manifest, anchors their expected
hashes and checks that binding before return/render. A deterministic interleaving regression and
post-render same-size/restored-mtime replacement checks pass. Correctedaf3956 received independent
PASS (`6a6196f99aa4171feaaca9a50e9643697cd8bb018a8b7ad6b241c4539af95557`) before execution.
The fixed pre-execution review/budget binding stays unchanged. Independent post-execution audits
verified the actual optimizer/packet/control/plant associations,4880 Jacobian/gain rows, identities,
once-each budget and historical preservation without rerunning models or experiments.

Next: exact final presentation review and final documentation delivery; numerical budget exhausted.
No change to controller mathematics, physical assumptions, accepted architecture, Safety policy,
frozen source or numerical budget is delegated. Stop after delivery at
`NMPC_LAB_V1_WORK_COMPLETE_PENDING_PRIMARY_ACCEPTANCE` if the authorized work succeeds.
