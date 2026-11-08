# NMPC Lab V1 — bounded WORK

**WORK_COMPLETE_PENDING_REVIEW.** 8 November 2026. Branch `codex/nmpc-lab-v1`, starting
commit `4f398cfa68bbad3f5d66068888aec70d948e1bb9`; scientific source remains
`48adbdf64d492592d15e23c917aca71fa58aa8a5`. The containing candidate supplies the exact
implementation for one independent-context Engineering Review. No genuine Scratch experiment
has run. [Machine record](work_record.json).

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

After independent PASS, this assignment conditionally permits exactly three2.0s attempts:

1. Accepted Performance cost defaults.
2. Same scenario, only lateral2.0→1.0.
3. Accepted costs with the existing native state perturbation: +0.08m e_y, −0.04rad heading,
   configured0.5s. These magnitudes are existing AsyncConfig defaults. Native geometry/domain
   configuration is checked before execution; actual trigger time and applied configuration persist.

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

Final focused pre-review invocation: **96 passed,0 failures/errors/skips,31 deselected,59.90s**.
No genuine controller/closed-loop run, optimizer solve or Plant.step occurred. Source-isolated
configuration/MPCProblem construction and component algebra were permitted. Tests independently
check all eight overrides reaching native problem/constructor semantics, literal cost expressions,
canonical geometry/reference conversion on original retained data, finite-difference Jacobian/order
and native feedback sign, noncommuting time-varying matrices, actual-time metrics/insufficient tails,
small-editor UI, replay, same-size/restored-mtime corruption withdrawal, lifecycle/budget/failure,
and original M5-A/P/C0 behavior. Scientific launches were audit-blocked in the pytest parent.

Earlier32-pass/4-setup-error attempts exposed missing runtime-parent/root coupling. The final design
uses the existing verified cache read-only and leaves both original M5-A modules byte-identical.
Earlier36/37-pass checks remain separate. A selection including a legacy plotting/simulation node
was interrupted before that node:24 passes, incomplete selection, zero numerical launches. Its
interruption, sandboxed process-inspection denial and successful scoped interruption remain recorded.
Initial lint failures and all corrected attempts/logs/JUnit remain in the ignored WORK directory.
No historical counts are added to96. Broad scientific/qualified/frozen suites were not run.

Pre-review audit:6,329 original M5-A regular files and324 links unchanged, no added historical files;
333 frozen runtime members match exact Git bytes; no src/scripts/configs/dependency changes. Primary
56 scientific /345 qualification /25 P /4 oval groups and original C0 bytes match; G1 stays OPEN.
This preserves independently verified PRE-INT-W1 and all historical research. Raw evidence remains
local/ignored; committed hashes do not establish off-host retrieval. No formal Verification or
scientific qualification is claimed.

Next: one consolidated independent review of the exact candidate. Only after PASS may the three
predeclared attempts run, sequentially under unchanged caps, followed by retained-result/UI audit.
No change to controller mathematics, physical assumptions, accepted architecture, Safety policy,
frozen source or numerical budget is delegated. Stop after delivery at
`NMPC_LAB_V1_WORK_COMPLETE_PENDING_PRIMARY_ACCEPTANCE` if the authorized work succeeds.
