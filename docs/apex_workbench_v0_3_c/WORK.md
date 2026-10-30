# V0.3-C — engineering usability, recorded replay and pairwise comparison

**ENGINEERING REVIEW: PASS WITH CONDITIONS.** Finalized 30 October 2026; tests executed 29 October.
Reviewed implementation `8cff10bca8475f0992221d2cebf8862414210056`, branch `codex/apex-workbench-v0-3-c`,
from B Verification delivery `ccd19549a9b3e25d1a5bd2c037a27090eda8dccf`.
The authoritative B handoff still says `V0.3_B_VERIFIED_PENDING_USER_ACCEPTANCE`; hands-on feedback
is not recorded as formal acceptance. This task explicitly authorizes C engineering independently.
The containing delivery changes documentation only after the exact-revision independent review.
Formal full-suite Verification is not authorized here.

## Implementation

The same primary `workspace.py` now uses compact status columns, plot columns and a native-time
control strip. Run/Inspect/Compare remain directly reachable in the sidebar. Configuration, paths,
source/qualification detail, raw exports and notes are on demand. Warnings and eligibility remain
visible. Existing execution, validators/defaults, workers, ownership, limits, scientific readers and
launcher are unchanged. Lab case selection is outside the submission form so its description and
resolved snapshot update before launch; submission still uses the same finite nominal request.

Three small additive modules:

- `experiment_catalog.py`: descriptions for exactly the three existing adapters and five finite lab
  cases, including purpose, inputs, observations, composition and synthetic/qualification limits.
  Proposed racing scenarios are not registered as executable experiments.
- `recorded_view.py`: verified snapshots tied to committed status/manifest identities, exact native
  timestamp lookup, literal source/sample identity and bounded deterministic viewer clock. Known
  version-2 Workbench SI contracts admit replay; unsupported profiles retain verified static/raw access.
- `workspace_panels.py`: common-time inspection, play/pause/seek/step, stored-XY cursor, compact native
  values and source panels, and two-to-four-run presentation. The prior inspect_channels warning is
  removed by using session-state initialization without a competing widget default.

No dynamics, integrator, controller, new scientific metric, reference reconstruction or command path
is added. Replay reads software evidence. Its one-second viewer tick advances a selected number of
stored samples once per render tick, without wall-time catch-up; it is not model time or a real-time
promise. Leaving the page, changing run/timebase/qualification or seeking pauses/resets as appropriate.
Evidence/qualification changes withdraw the scientific view and stop playback. A fragment's mounted
epoch is checked before reads; source/profile metadata must match the verified request.

The selected clock is an explicitly named run's native state timebase. Each other source/run joins
only an exactly equal retained timestamp. Off-grid numeric input is rejected without snapping;
missing, multirate and out-of-coverage samples stay unavailable. No previous command is inferred.
For the declared VDL ZOH profile, applied controls describe the recorded next interval only when a
next state exists. Terminal diagnostics are informational; partial last/attempted rows do not prove
interval completion. Input traces use held-step styling only for the producer's explicit VDL contract;
original data/timestamps are not resampled or extended. Position uses stored XY only; XY/state native
timebases must agree. There is no event reconstruction, physical telemetry or generic archive importer.

Multi-run overlays retain native timestamps and units. Every pair calls the unchanged production
comparison/qualification reader. BASE/IZ and BASE/CF can qualify with exact applicable Q; IZ/CF is
illustrative. There is no group-qualified label or causal three-way ranking. Four runs is a UI/resource
bound, not a scientific operating limit. Ambiguous/corrupt pairs withhold the shared scientific view.
The verified catalog/alias policy and append-only owned notes remain intact; archives never receive
reconciliation, cancel or annotation writes. Existing V0.1/V0.2 inputs/entrypoints remain unchanged.

## Evidence and practical scenarios

Local evidence: `results/apex_workbench_v03c_work_20261029/`; commands/logs/JUnit and hashes are in
[work_record.json](work_record.json). Fresh/disposable outputs only. Tests are software acceptance,
not new numerical qualification. No newly designed scenario, 17-trajectory campaign, parameter sweep,
CT/Performance/Efficiency/Safety campaign or hardware activity ran.

| Scenario | Evidence |
|---|---|
| A — compact inspection | Primary action/status/cursor strip, side-by-side native signals/stored XY, collapsed provenance/raw details and directly accessible diagnostic/evidence/notes tabs; AppTest plus live desktop/narrow browser inspection |
| B — transient at 0.125 s | Actual BASE/IZ retained CSV lookup and UI readouts at native state/control sample 25; r differs and actual delta=0.02 rad for both, without interpolated samples |
| C — three-run comparison | Actual BASE/IZ/CF source paths and Q; two BASE edges qualify, treatment/treatment remains illustrative; original source/profile/units and native coverage retained |
| D — replay | Deterministic injected viewer-clock checks and real browser automatic playback from sample 19 at 0.095 s across onset to sample 35 at 0.17500000000000002 s, then pause; no execution APIs invoked |
| E — invalid/partial | Copied checksum/missing/XY mismatch and literal partial fixtures quarantine or retain explicit partial coverage; invalid comparison cannot be promoted |
| F — preservation | Focused Workbench suite includes original V0.1 byte/worker parity, V0.2 independent canonical-runner parity, locks/SIGKILL/cancellation/integrity and legacy UI; actual unchanged launcher start/reuse/owned shutdown |

All 56 scientific dependencies remain byte-identical to accepted V0.2
`4897686e79c13757d5ef5b4373b44d4cab99b5bf`, including app.py/plots.py. New presentation modules
enter unchanged full provenance. The original 17-run qualification is consumed read-only and its
four accepted conditional pair labels remain applicable. Exact before/after preservation and
current test outcomes are in the machine record (one 276-pass directory run, then final 38-pass affected-file run); counts from different runs are never summed.

Retained failed attempts are explicit: an AppTest `.expanded` attribute error was a harness error
(corrected to protobuf state), and an old two-plot comparison assertion needed to account for the
new stored-XY pane. Its replacement verifies that XY axis as well as the plot count. No scientific
assertion, threshold or failed original evidence was modified to obtain a pass. Earlier logs remain.

The live launcher smoke used the actual executable from a different cwd, loopback 8501, the exact
owned listener and a second invocation reusing it. Both smoke servers stopped cleanly. The second
server restart loaded the final imported presentation modules after layout edits; no user server
was stopped. A 1440x1000 desktop layout and default narrow browser layout were inspected; the
temporary viewport override was reset. Native UI observations and screenshot are retained under
`interactive-ui-final/`. These checks are functional/visual observations, not final user acceptance.

## Bounded correction R1 — independently closed

The independent [iteration-1 FAIL](../reviews/apex_workbench_v0_3_c/iteration_1/REVIEW.md)
is preserved against exact initial candidate `c57603ea0e80b7b2121648ae687ac2afa03cb33d`.
Six copied optional-metadata cases were contained by B but raised uncaught C exceptions;
the separate reviewer also freshly passed the affected 38 tests and 15 adversarial core checks.
These invocations are distinct and do not replace or erase the failures.

The correction validates the optional object/list/text shapes consumed by the additive snapshot
and contains expected malformed-data exceptions in its UI boundary. Invalid metadata withholds
plots/replay with a clear error; native raw records/provenance remain available and no field is
normalized, repaired or resealed in production. Nine copied genuine legacy-record regressions
cover the reported top-level/nested cases plus environment/contract/units shapes, requiring the
frozen reader precondition, no application exception, no scientific plots/cursor, raw access and
byte-identical retained fixture contents. Valid legacy and VDL paths remain in the affected tests.
Fresh correction selection: **47 passed**, zero failures/errors/skips, 261.78 s; separate from the
earlier 276-pass run and initial 38-pass final-view run. No pytest retry. Imported-fixture lint
suppression was adjusted after formatting; all changed-file Ruff lint/format and diff checks pass.
No accepted reader/backend/scientific source is changed. This is one substantive correction
iteration of the authorized maximum three, independently closed by the
[final review](../reviews/apex_workbench_v0_3_c/iteration_2/REVIEW.md) at `8cff10bca8475f0992221d2cebf8862414210056`.

## Independent review outcome and retained condition

Separate-context Engineering Review is **PASS WITH CONDITIONS**. R1 is closed with fresh fault
reproductions and literal-byte/raw/export preservation. The initial FAIL report remains verbatim.
The final [review record](../reviews/apex_workbench_v0_3_c/iteration_2/review_record.json) retains
all exact commands, evidence hashes and distinct outcomes:

| Final independent invocation | Outcome |
|---|---|
| Correction/actual-Q/native-sample probe | 26 passed |
| Exact candidate affected two-file selection | 45 passed, 2 AppTest timeout failures; exit 1 |
| One authorized supplemental check of those same two original assertion bodies | 2 passed separately; 120 s/render, 420 s aggregate cap not hit |

The failed 47-test invocation stays failed. The supplemental result changes no committed source,
test or assertion; it demonstrates semantic completion, not the original 45/60 s deadlines. One
Q-selection render took **89.886 s**, a material practical limitation with unresolved cause. N1 is
nonblocking for this bounded Engineering Review; formal Verification must retain/reconcile the
failure evidence, declare a bounded UI harness/deadline policy and assess the long render. No
responsiveness guarantee or new scientific/latency acceptance criterion is installed by this task.
The prior 15-pass independent core is inherited only where exact AST/dependency identity is recorded;
it is not newly executed or added to current counts.

Independent final preservation checks all 56 scientific files, 985 preexisting tracked files,
345 original qualification files and 741 prior-iteration files by SHA-256; 42,566 historical result
files by size/mtime and 1,293 symlink targets. All remain unchanged before review-doc delivery.
Current Python/package versions also match the tested environment on 30 October. No test reran
after the interrupted reviewer turn resumed; only audit/completion documentation was finalized.

## Scientific preparation and remaining gates

[RACING_SCENARIO_PROPOSALS.md](RACING_SCENARIO_PROPOSALS.md) audits all five requested families and
recommends three complementary priorities: existing oval LQR/PI use, source-bound retained GP-sector
investigation, and a separately contracted rolling straight/turn-in open-loop family. Historical
Task007A conservative G and accepted Performance P identities remain distinct. No proposed scenario
was added to the execution catalog or run.

[SCIENTIFIC_DECISIONS.md](SCIENTIFIC_DECISIONS.md) asks Primary for three consequential dispositions:
minimal expansion/interpretation, exact future racing profile/provenance, and the new response
family's geometry/excitation/domain/qualification contract. Unknown straight geometry or physical
assumptions are not invented. Source migration is required if a future indispensable change touches
one of the 56 dependencies; this task needs none.

Next: separately authorized formal Verification, including N1 disposition, and Primary scenario
contract approval. Engineering Review is complete with conditions after one bounded correction.
No automatic next MVP stage or new racing execution.

**Stop: V0.3_C_ENGINEERING_REVIEW_COMPLETE_PENDING_VERIFICATION_AND_SCENARIO_APPROVAL.**
