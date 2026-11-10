# APEX Engineering Workspace / NMPC Lab V1

Primary accepted NMPC Lab V1 for bounded synthetic experimentation. The configured accepted
checkout uses `accepted-interactive` admission; [acceptance and operations](../../docs/nmpc_lab_v1/OPERATIONS.md)
record source/review identities and restrictions. The V0.3-C verification history below is retained.

The primary local workspace provides **Home / Run / Inspect / Compare** over the accepted
Workbench engine. Inspect actual native samples, use read-only replay, compare two to four retained
runs with pairwise eligibility, and open detailed configuration/provenance on demand.

Corrected source `34f98a4894e457900d2fae3b2fd09ead4f5ba5a0` passed independent Engineering Review and formal
functional Verification: **1,069 passed, 17 separately gated G2 skips**, zero failures/errors in one
complete invocation. Original 45/60 s UI deadlines remain unchanged. N1 is closed within the bounded
reference checks; original failures and the unexplained historical 89.886 s observation are preserved.
See [correction/Verification report](../../docs/reviews/apex_workbench_v0_3_c/RESPONSIVENESS.md),
[independent PASS](../../docs/reviews/apex_workbench_v0_3_c/responsiveness/iteration_1/REVIEW.md)
and [original WORK](../../docs/apex_workbench_v0_3_c/WORK.md). Final user acceptance and Primary
scenario decisions remain pending. Timings are observations; no general latency guarantee follows.

The five finite synthetic V0.2 cases and four baseline/treatment comparisons were qualified and
functionally verified before this task. Primary accepted that finite scope in V0.3-A. See the
[qualification report](../../docs/apex_workbench_v0_2_d/QUALIFICATION.md) and
[V0.2 Verification](../../docs/reviews/apex_workbench_v0_2_e/VERIFICATION.md).
This presentation preserves all 56 accepted scientific dependency hashes, including the original
`app.py` and `plots.py`. It changes no numerical criteria, canonical model or historical evidence.
Qualification does not establish physical validity, actuator feasibility or hard real-time behavior.

Historical implementation/review evidence remains in [V0.2-B WORK](../../docs/apex_workbench_v0_2_b/WORK.md),
[V0.2-C closure](../../docs/apex_workbench_v0_2_c/WORK.md), [R1–R6 corrections](CORRECTIONS.md),
[original failed review](../../docs/reviews/apex_workbench_v0_1/REVIEW.md) and
[V0.1 stabilization](STABILIZATION.md).

## Setup and launch

On this configured Mac, double-click
[Launch_APEX_Workbench.command](../../Launch_APEX_Workbench.command) in the repository root.
It starts the local server and opens your default browser when ready. When starting a new server,
keep that Terminal window open; press **Control-C** there to stop it. The launcher works regardless
of Terminal's current folder and does not run an experiment automatically. A second double-click
reopens this project's already-running Workbench without starting another server. A listener
belonging to another application or checkout produces a clear port-conflict message. After updating
the checkout, stop its old owned server and relaunch to load all changed presentation modules.

From the repository root, using Python 3.12 and the existing core environment:

```sh
.venv/bin/python -m venv tools/apex_workbench/.venv
uv pip freeze --python .venv/bin/python | rg -v '^-e ' > /tmp/apex-workbench-pins.txt
uv pip install --python tools/apex_workbench/.venv/bin/python -e . \
  -r tools/apex_workbench/requirements.txt --constraint /tmp/apex-workbench-pins.txt
tools/apex_workbench/.venv/bin/python -m streamlit run tools/apex_workbench/workspace.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true \
  --browser.gatherUsageStats false
```

Open <http://127.0.0.1:8501>. The pins preserve the installed scientific dependency versions;
Workbench dependencies live in its ignored `.venv`, outside the core environment. If dependencies
are already installed, only the last command is needed. `uv` cache/network access must be available.
Install pytest in this tool environment to run the focused tests. See [validation](VALIDATION.md)
for the exact checked environment and evidence. No cloud deployment or authentication is included;
keep the server bound to loopback.

The one-click launcher opens `workspace.py`. Direct compatibility access to the original accepted
application is retained. To run it alongside the primary workspace, use a separate port:

```sh
tools/apex_workbench/.venv/bin/python -m streamlit run tools/apex_workbench/app.py \
  --server.address 127.0.0.1 --server.port 8502 --server.headless true \
  --browser.gatherUsageStats false
```

A legacy app occupying port 8501 is not reused or stopped by the new launcher. Stop it in its own
Terminal or use the separate port above. The launcher reports a conflict and preserves its owner.

## NMPC Scratch / Control Analysis (V1)

Open **NMPC Scratch / Control Analysis** on Home. Run exposes the eight native cost multipliers,
reset-to-accepted-costs, and one fixed native disturbance selector. It adds no vehicle/tire/constraint,
horizon/timestep, solver, TVLQR-structure or geometry editor. The single source-controlled
[nmpc_scratch_profile.json](nmpc_scratch_profile.json) references the existing scientific sources.
Broader configuration/domain changes require scientific review and a revised profile; frozen
Performance files are never overwritten. **Inspect effective frozen configuration** is a no-solve
source/dependency/dataclass check. Saved ID/version drafts live under
`results/apex_workbench_nmpc_lab_v1/configurations/`; they are unreviewed, not deployment input by default.

Primary accepted repeatable, explicitly user-triggered Scratch within this fixed profile and unchanged
worker caps. The original three WORK runs remain consumed and preserved: baseline, lateral1.0 and
baseline with native+.08m/−.04rad kick at.5s. Acceptance does not reset them or the historical M5-A
budget. No automated sweep, background experiment, new scenario or frozen Performance overwrite.

Inspect offers elapsed-time browser playback at0.25×/0.5×/1×/2×, pause/restart, native sample
steps/seeking, canonical track/position and active or explicitly historical prediction/reference
nodes. Only the displayed XY marker interpolates; known kicks are not smoothed across. Native
readouts, controls, packet identity and scientific metrics are never interpolated. Tracking/control
plots and detailed diagnostics open on demand. Analyze displays racing-reference error (not raw e_y), control effort,
solver/constraint/grip diagnostics, observed-window recovery and local linear indicators. Compare
shows exact parameter differences/common physical metrics and labels incompatible cases illustrative.
Everything is synthetic/experimental/unqualified. Local eigenvalues are not complete stability proof;
insufficient windows do not become successful recovery. [WORK/evidence](../../docs/nmpc_lab_v1/WORK.md).

The N=8 prediction-node explorer shows nine genuine predicted states/eight nominal controls,
recorded objective components and completion/validity/handoff diagnostics on demand. Terminal state8 has no
invented command. Requested/applied clocks and simulated/solver/derived classifications remain
explicit. Replay uses Canvas2D; Analyze retains SVG plots. Original blank-WebGL findings remain preserved.
This reuses presentation concepts from the read-only Development Bench, without its older
N=4 controller assumptions, scientific interpolation semantics or standalone runtime.

Ordinary Scratch pages show `Synthetic research mode · Not physically qualified`. Evidence hashes
are rechecked every second; a change clears and quarantines replay. A missed browser validation
lease clears the local payload after4.5s. Reopen explicitly after an evidence failure; refresh/reopen
never qualifies a result. See [UX correction](../../docs/nmpc_lab_v1/UX_CORRECTION.md).

From the accepted `codex/nmpc-lab-v1` checkout, double-click the normal launcher or run:

```sh
./Launch_APEX_Workbench.command
```

Open <http://127.0.0.1:8501>. This Mac is configured with the approved existing environment; no
new dependencies are needed. For another Git worktree sharing an already configured primary checkout,
the minimal one-time environment link (only when the local tool environment is absent) is:

```sh
apex_shared_checkout="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
ln -s "$apex_shared_checkout/tools/apex_workbench/.venv" tools/apex_workbench/.venv
```

The target must already be the supported approved environment. For an independent installation,
follow the existing setup section and the per-checkout acceptance/runtime requirements in Operations.
The launcher never installs dependencies or changes scientific configuration automatically.

Future export must explicitly select a versioned configuration and its exact review/hash. No ROS2,
production exporter or hardware packaging is included. Existing launch and compatibility paths remain.

## Supported experiments

- **Vehicle Dynamics Laboratory / prescribed open loop:** canonical `DynamicBicycle` with default
  linear axle tires/quasi-static loads, fixed existing track and canonical `SimulationRunner`.
  Select `VDL1_BASE`, `VDL1_IZ_HIGH`, `VDL1_STEER_HIGH`, `VDL1_CF_HIGH` or `VDL1_CR_HIGH`.
  Every case shows its full SI parameter snapshot, initial state and held-input schedule. All use
  [2,0,0,0,0,0], a_cmd=0, a steering step at 0.100 s, duration 0.500 s and plant/input period 0.005 s.
  The four treatments independently change Iz, steering amplitude, Cf or Cr. See
  [exact values/origins](../../docs/apex_workbench_v0_2_a/PROPOSED_CASES.md). There is no arbitrary
  parameter editor or mass family. The UI admits the nominal grid. The backend admits the accepted
  refinements only with explicit qualification purpose; software-test profiles are ineligible for
  scientific qualification evidence.
- **Dynamic bicycle / open loop:** the unmodified Task004 CLI `main()`; duration and RK4 timestep.
  The original synthetic vehicle, track, initial state, steering and acceleration schedule remain fixed.
- **LQR/PI / tracking:** the unmodified Task005 `run_case()`; duration, circle/oval track,
  initial/reference speed, initial lateral error and heading error. Duration-only termination,
  fixed 200 Hz plant / 100 Hz control, original weights/gains and PI constants.

The [capability matrix](CAPABILITY_MATRIX.md) records sources, SI units, bounds, validation,
provenance and deferred features. Every bound beyond an existing mathematical contract is labeled
as a conservative UI/resource safeguard. These ranges are not certified physical validity domains.
Parameters are synthetic, never measured or identified APEX data. Linear tires remain unsaturated;
`mu` is diagnostic. Dynamic `a_cmd` means `Fx/m`, not generally `dvx/dt`.

## Use

**M0 status: formal Verification BLOCKED at retained-evidence admission.**
Exact implementation `96be0969703f0675060208843c9920bca2187e3e`. R1/R2 corrections passed independent
review before one new nominal and one exploratory native 2.0 s attempt; both completed with valid
retained evidence and passed final independent assessment. These are synthetic, experimental and
unqualified results. Both successor attempts are consumed; further execution requires a new Primary
authorization. The subsequent formal check found an exploratory software-probe hash mismatch and
correctly stopped before regression. Its decoded values are unchanged, but exact authority bytes
do not match. [Verification report](../../docs/reviews/apex_workbench_nmpc_weight_m0/VERIFICATION.md).
Original failed attempt, claim/gate/BLOCKED, negative reviews and logs are preserved. No evidence
was repaired/resealed. Formal Verification is incomplete and acceptance has not occurred.
See the linked WORK/record for exact gate, source, environment, native outcomes and limitations.

**Experimental NMPC Weight Lab M0:** Home → **Open experimental NMPC Weight Lab M0**, or Run →
**NMPC Weight Lab M0**. Exactly two presets use the genuine frozen Architecture-A NMPC/TVLQR
controller on the same synthetic GP gamma2 / N8 / dt0.1 / RK4×4 / 2.0 s scenario. Nominal uses
stage lateral/heading scale2; exploratory uses scale1. Terminal, plant, tires, constraints,
TVLQR, reference and solver/warm-start configuration stay unchanged. Complete actual configuration,
frozen source/module/dependency identities and the software gate precede admission. Each preset
has one append-only authorized attempt; consumed/failed attempts cannot be retried automatically.
All new M0 outputs, runtime copies and the checkout's shared execution lease live under
`results/apex_workbench_nmpc_weights/`. The existing worker/ownership/resource guards are reused;
restart older Workbench processes before using this changed checkout. Original output paths for
other modes stay unchanged. Managed worktrees read accepted archives from the primary checkout
read-only; that directory is never a scientific import root for M0.

Inspect retains native state/command histories, separate requested/application clocks, optimizer
events and controller-native post-solve objective components. It shows failed/partial coverage and
retained callback journals without reconstructing missing results. Compare → **NMPC Weight Lab M0
(unqualified)** offers only the nominal/exploratory pair with identical non-treatment snapshots;
differently weighted objective totals are not compared as a performance score. All outputs remain
**EXPERIMENTAL / UNQUALIFIED — synthetic**. This is not physical or controller-performance
qualification. See the [bounded contract](../../docs/apex_workbench_nmpc_weight_m0/EXPERIMENT_CONTRACT.md)
and [WORK record](../../docs/apex_workbench_nmpc_weight_m0/WORK.md). No M5-B, SID or hardware capability.

**C0 descriptive-only historical inspection:** choose **Inspect retained C0 descriptive-only
archive** on Home, or **Inspect → Inspection source → C0 descriptive-only record**. This separate
read-only view accepts only the original 152,600-byte, SHA-pinned `original155.json`. It is not a
run or comparison candidate. G1 capture-time producer provenance remains OPEN: the persistent
DESCRIPTIVE ONLY / SOURCE UNVERIFIED banner applies to every view and HTML export. Inspect exact
numeric tokens and JSON pointers, independent collection chronology, null/absent fields and the
original JSON. Plots are recorded markers with undeclared units; optional reference explanations
are capture-unverified. No geometry, terminal state, held controls or missing events are inferred.
**Prepare C0 descriptive HTML inspection** offers self-contained local HTML with original JSON,
tokens, missingness and the same limitations. Changed evidence or contract/review identities
quarantine the view and withhold export. This software WORK passed independent Engineering Review
at `d246f1e9639737e4ecbbd12f8bd0c9b2f1574712`; formal Verification remains separately gated.
It does not establish authenticated controller evidence, scientific qualification or physical data.
The C0 view uses static tables/plain text and disables Plotly's native export controls in both
live and HTML plots. Its only offered output action is the explicitly prepared HTML download.

1. **Home** shows the three supported modes, explicit unavailable capabilities, adapter/outcome
   filters and unverified discovery metadata. Inspect a record to establish evidence trust.
2. **Run** submits the same allowlisted defaults/inputs through the original leased worker. A run
   note is optional. The laboratory remains nominal-only. Start, leave the page and reopen the run
   in **Inspect**; active owned runs have explicit refresh/cancel controls.
3. **Inspect** selects a run from its original path. Primary status and signals come first; diagnostics,
   raw rows, evidence/provenance and notes are in compact tabs/expanders. Read its outcome/evidence status, configuration,
   effective parameters, source and numerical provenance, actual summary fields and telemetry contract.
   Choose state/control/diagnostic channels; actual recorded reference channels are overlaid only
   when present. Each channel has its own declared unit axis. Native rows and XY/track are available.
4. **Compare** selects two to four runs. Each pair has its own classification; an overlay is never
   a single qualified multi-way experiment. The accepted readers determine candidate, qualified synthetic,
   illustrative or invalid status and show actual differences and retained summaries. Select the
   accepted qualification explicitly in the sidebar; discovery alone confers no qualification.
   Plots use raw timestamps without interpolation or time alignment. Status/manifest and selected-Q
   identities bind classification to display; changed identities clear labels and overlays. Invalid
   pairs have no overlays.
5. **Raw records and failure logs** remain available for corrupt/incomplete records with explicit
   unverified labels. Verified records offer a ZIP of original manifest-listed bytes plus their
   status/manifest; moving anchors abort export. This is retained evidence, not a new execution.
6. **Engineering notes** preserve original prediction/observation/explanation records and append-only
   versions. Only owned runs offer note writes. Qualification archives are read-only.

**Common time and recorded replay:** use the native-time slider, exact numeric entry, previous/next
sample and play/pause. The cursor follows the named run's retained state clock. Other panels join
only exact timestamps; missing or out-of-coverage state/control/diagnostic/XY samples stay unavailable.
No interpolation, clock shift, previous-command inference or XY reconstruction is performed. Applied
control rows remain separate from state-row input aliases. At the terminal lab sample there is no
new applied interval; diagnostics are informational. Partial last/attempted rows do not establish
completion. Input plots use held-step styling only for the declared VDL ZOH profile, without adding rows.

Replay reads existing software samples only. Its one-second, render-dependent viewer tick advances
1/5/10 samples; it never runs dynamics, emits commands or promises real-time speed. Run/timebase/Q
changes and navigation stop/reset playback; evidence changes withdraw stale plots/labels. Known
version-2 Workbench SI profiles are supported. Unknown profiles retain verified static/raw access;
external imports, general controller event archives and physical telemetry are not supported. The
single fixed C0 descriptive profile above is separate from these verified replay profiles. Native raw rows
remain available on demand. Narrow browser views stack columns; a desktop viewport shows parallel panels.

The [racing-scenario proposals](../../docs/apex_workbench_v0_3_c/RACING_SCENARIO_PROPOSALS.md) and
[Primary decisions](../../docs/apex_workbench_v0_3_c/SCIENTIFIC_DECISIONS.md) are design-only. They do
not add executable experiments or authorize new tracks, controllers, thresholds or scientific runs.

Discovery is restricted to direct directories in `results/apex_workbench/` and the original source
runs referenced by `results/apex_workbench_qualifications/v0_2_reviewed_20261029/qualification/`.
No arbitrary path importer is provided. Paths sharing captured run/worker/manifest identity are
shown once with aliases; a copied folder never counts as another execution. Original archives anchor
discovery; conflicting alias hints cannot merge distinct originals. Metadata symlink loops are
quarantined without blocking the catalog. Conflicting aliases
are disclosed. The original qualification source can still be independently verified; ambiguous
owned aliases are quarantined and offer no lifecycle controls. Archived/nonterminal records never
invoke reconciliation or cancellation. Nothing is copied, resealed or migrated for discovery.


Lab comparisons allow BASE against one of the four treatments in either order. They show a
**Controlled candidate** only after checking full resolved snapshots, actual applied controls,
initial state, schemas/units, source identity, environment, geometry and evidence. Other verified
pairs are illustrative; corrupt/incomplete records are invalid. Without an explicitly selected valid
qualification record, completed runs remain unqualified. Observed yaw separation alone cannot confer
qualification, even when it exceeds the provisional minimum signal floor.
The retained accepted qualification record can be explicitly selected. It is
revalidated against all referenced runs, source/environment and exact finite-case exports before
showing numerical case status and pair eligibility. Sampled interpretation, excitation and physical
validity stay separate; records are never silently attached to or written into old run evidence.

Lab state/control and canonical sample-diagnostic plots show actual retained yaw/lateral/longitudinal
response, steering/a_cmd, slip, lateral forces, axle loads, nominal/effective stiffness, utilization,
Frenet denominator, XY and sampled CG corridor flags. Terminal input/diagnostics are informational.
Configuration, execution, evidence, numerical qualification, model window, excitation and comparison
remain distinct. Missing observations are unavailable, never fabricated. The lab does not hold vx
constant when a_cmd=0 and introduces no steering actuator or feedback law.

Failed, timed-out and cancelled runs stay visible. A `completed` execution means the original
entry point returned successfully; review boundary violations, model failures and summary criteria
separately. Short runs may have null settled metrics. The dynamic demo does not export boundary
violation flags or reference states. Solver status/computation times, application staleness,
latency/deadlines and optimizer constraints are unavailable here and are explicitly labeled so.
Host wall runtime is process overhead plus computation, not modeled control delay.

## Execution and evidence

Every run exclusively reserves `results/apex_workbench/<UTC timestamp>_<random id>/` before launch.
Original experiment outputs live in `experiment/`; preexisting output directories are rejected.
The request records source/effective configuration, notes, adapter/version/entry point, model,
controller, full synthetic vehicle YAML, timing mode, Git revision/branch/status/diff hash,
source hashes, Python and package versions. Worker environment controls and loaded native pool
inspection are retained separately. The immutable execution receipt records the scientific outcome.
Status records evidence validity separately and commits the manifest hash only after all stable
artifacts have been hashed. A hash/finalization failure is visible as `evidence_failed`, even
when scientific execution completed. Interrupted finalization is reconciled conservatively.
Observations/explanations are append-only note versions; the original prediction is preserved.
Do not manually edit run evidence or delete the execution lock file while workers are running.

The supervisor persists independently of browser reruns/closure. The scientific worker also
inherits the checkout execution lock and runs its own guard. Supervisor loss, cancellation,
wall/RSS/output limits and monitoring faults are checked by that guard; it stops its own process
without signalling a stored PID. Supervisor termination actions verify worker birth time, full
command, role and run path through psutil. A second worker cannot start while the first retains
the lease, including when the supervisor has been killed. Stale corrected records are reconciled
under the same lock; interrupted/uncertain outcomes are never promoted to success.

Initial request/status publish together through a hidden staging directory. Notes publish complete
exclusive versions; malformed historical notes are retained and skipped with a warning. Required
artifact hashes are checked before plots or comparison. Only selected files are read, using a
bounded cache keyed by expected hash, inode, size, mtime and ctime; changed data is quarantined.
Historical records are not repaired in place. Legacy runs need their original valid artifact hashes
for individual plots and lack the new comparison contract, so cannot claim a controlled comparison.
Malformed request/status records are preserved and excluded with a warning. Selected completed records
are revalidated before metadata or plots appear. Missing manifest-listed files are integrity failures;
successful corrected runs also require their expected exports. Optional channels never produced by
an adapter remain unavailable. A failed run with no exports keeps its failure/error visible.
Unreadable lifecycle records block new admission until inspected; exclusion from UI selection does
not authorize another worker. No historical record is automatically repaired or deleted.

Repository `MEASURED_ACTIVE` / `D3_ACTIVE` guards and a 1 GiB disk floor are checked before launch.
The Workbench lease cannot serialize unrelated direct experiment launches: do not start external
measurements while Workbench runs. These are functional simulations, not timing benchmarks.

Limits: 60 s wall supervision, 30 s soft / 31 s hard kernel CPU, 16 MiB kernel per-file limit,
512 MiB sampled worker RSS and 64 MiB sampled output budget. RSS/output/thread observations at
100 ms (supervisor) / 50 ms (worker guard) are soft samples, not exact peak bounds. Single native thread controls are configured
before numerical imports; macOS uses the existing Accelerate API. Loaded pools and sampled
process thread counts are recorded; environment values or thread counts do not prove parallel
numerical execution. The worker guard depends on Python/OS scheduling: SIGSTOP pauses it too, while the inherited
lock still prevents overlapping runs. Host/OS failure is not hardware watchdog protection.
No standstill braking, collision safety or real-time certification is implied.

## Engineering Understanding Notes

`app.py` submits only the selected adapter's allowlisted values. `configuration.py` rejects
unknown, nonfinite or out-of-range values and invalid LQR step multiples. `jobs.py` reserves an
exclusive run directory, captures source identity, holds the execution lock, and starts a fresh
supervisor/worker with explicit argument arrays and no shell interpolation. `worker.py` applies
resource/native controls and calls the original Task004 CLI or Task005 function.
For `dynamic_lab`, the worker checks source/captured composition before and after execution, constructs
immutable canonical parameters and calls the canonical runner. Its raw CSVs precede diagnostic export;
`resolved_lab.json`, controls, diagnostics, telemetry units and summaries join the existing manifest.
Every required lab artifact is verified before scientific display, including a state-only plot.

The original experiment composes the actual `DynamicBicycle`, original tire/load components,
canonical RK4 integration, track geometry and (for Task005) scheduled LQR/PI plus
`SimulationRunner`. The controller's linear design stays separate from the nonlinear plant.
`lifecycle.py` owns the worker lease/identity checks; `storage.py` publishes records and verifies
selected artifacts; `comparison.py` classifies compatibility. Lab modules add the accepted finite
composition and sampled reporting, with no new simulation or analysis framework. The Workbench
contains no vehicle/tire/controller/integration/solver equations. Derived display
coordinates call the canonical Frenet API after execution. `plots.py` reads the retained CSVs;
no missing telemetry is invented. Learning notes then close the experiment loop without supplying
an AI explanation.

## Historical GP evidence and oval shortcut (V0.3-D)

Use **Inspect retained Performance P GP archive** on Home for the one read-only P/VIS-1R
profile. It reads only `results/task007d/vis/vis1r_c699057/controlled_A` (`apex-run/0.1.0`),
verifying all25 files against externally pinned historical evidence on each operation and before
publication. No controller, worker, repair/exporter or Safety command path is invoked. Missing or
corrupt files quarantine the view. G and incomplete C70 archives remain unsupported. This successful
P case contains no fallback/failure episode; broader M4 failure inspection remains incomplete.

Select full run or an original named sector, vehicle/reference, tracking, controls, diagnostics
or planner/solver events. Sector filters use native state/Planning progress and retain whole-run
identity; controls/events/cycles remain full-run. Separate visits use markers. Applied controls use
`application_time`, requests use computation `time`; both are SI seconds. Event payloads retain
actual solver status and unspecified same-time ordering. Stored XY/reference sampling are labeled
producer reconstructions. No new samples, events, scores or cross-profile qualification are produced.
**Prepare source-linked HTML inspection** exports the displayed verified view, provenance and
inventory as a derived inspection document, never a new execution/evidence package. Downloaded
HTML works offline.

**Prepare 2 m/s oval LQR/PI** opens the existing form with oval, 12 s, 2 m/s and zero initial
tracking errors. **Start run** remains explicit and uses unchanged safeguards. Owned results reopen
through Inspect. Older `results/lqr_baseline/oval_2mps` bytes remain untouched and lack a source-bound
Workbench artifact contract; their historical verification JSON is not promoted to current verified
evidence. Original launcher and `app.py` paths remain available.

See [archive contract](../../docs/apex_workbench_v0_3_d/ARCHIVE_CONTRACT.md),
[WORK report](../../docs/apex_workbench_v0_3_d/WORK.md) and
[unimplemented RBT-0.1 proposal](../../docs/apex_workbench_v0_3_d/ROLLING_RESPONSE_PROPOSAL.md).
New racing execution, RBT implementation/qualification and full formal Verification require separate gates.

## Later work, requiring bounded review

- Exact-revision formal Verification of the new workspace after independent Engineering Review.
  Existing numerical qualification is consumed read-only; no auto-qualification from WORK smokes.
- Further finite synthetic mass/initial/input cases after reviewed numerical contracts; no
  unrestricted slider ranges or invented parameter coupling.
- Explicit selection of existing kinematic and smooth combined-grip compositions; no hidden swap.
- Separately bounded NMPC/async adapters after their prerequisite gates, with zero/injected/measured
  latency, continuing plant motion, application staleness, fixed deadlines and failure retention.
- Pairwise multi-run/common-time inspection, recorded replay, explicit legacy archive profiles and
  useful presentation exports, under the accepted roadmap and separate stage authorization.
- Review/Verification of later implementation revisions. VIS package ingestion, VIS-2 unseen tracks,
  frozen Performance changes, Efficiency execution and physical vehicle identification remain separate.

## V2 engineering workspace

Use `./Launch_APEX_Workbench_V2.command` (or double-click its Finder icon) in the intended
checkout with the existing Workbench environment. Loopback: `http://127.0.0.1:8503`.
Configure → Run → Replay → Analyze → Compare exposes the existing eight cost multipliers,
finite recording modes, retained native Canvas playback, applied-front-steering instrument,
Control Analysis and same-family comparison. Stop the owned server with Control-C in its Terminal.

UI acceptance does not unlock V2 execution: source/review/Primary bindings and the full-lap
resource preflight still apply. The accepted V1 launcher and its execution policy remain unchanged.
See [UI scope and evidence](../../docs/workbench_v2_ui/WORK.md) for display clocks, units, native
window limits, missingness and current resource limitations. No new installation dependency.
