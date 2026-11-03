# PRE-INT-P0 — consolidated Control pre-integration plan

**Status: PLAN_COMPLETE_PENDING_PRIMARY_REVIEW**
**Prepared: 2 November 2026. Authority: Primary APEX.**
**P0 is planning and read-only source audit. PRE-INT-W1 is proposed, not authorized.**

## 1. Recommendation and claim boundary

Approve one bounded PRE-INT-W1 WORK assignment to expose the frozen Performance controller
through a small local Python interface, add simulation-only input/output supervision, and
produce source-bound tests and one short measured genuine-controller smoke result. Reuse
NMPC, TVLQR, packets, reference loading, the event simulator and existing timing facilities.
Do not merge Safety, Efficiency, R0 or Workbench branches. Do not build another dashboard.

The minimum product is a **nominal Performance controller with an explicit no-valid-output
result**, suitable for the next Simulation integration engineering task. It is not the S1
permission protocol, an actuator endpoint, a recovery controller or physical Safety acceptance.
No missing physical response is replaced by zero steering, zero acceleration or braking.

The existing restricted baseline fallback remains available in the untouched historical
simulator. The new public nominal-control interface does not export that fallback as an
independently qualified Safety policy. Failure of a new plan may leave the old valid nominal
packet usable; exhaustion without eligible nominal authority returns inhibited output.
This narrower interface scope must be explicitly approved with this plan. It does not change
frozen controller mathematics or relabel the historical fallback as invalid research.

All Category A work below belongs to one assignment, including routine internal corrections,
focused tests and the bounded experiment after its software gates. There is one final
Engineering Review, then separately authorized Verification. Routine implementation steps do
not create additional authorization gates. Genuine scientific, physical-policy, source-identity
or out-of-scope failures remain stop conditions.

## 2. Audit method and exact evidence ledger

Findings below come from static Git objects, source text, retained JSON and existing reports.
P0 performed no project/numerical imports, test collection/execution, controller construction,
solver call, simulation, benchmark, dependency installation, evidence regeneration or merge.
Historical test counts and run results are inherited evidence, not P0 observations of behavior.
Local refs establish inspected identities, not independent authorship or runtime qualification.

| ID | Exact inspected revision / record | Authority and meaning |
|---|---|---|
| P | `48adbdf64d492592d15e23c917aca71fa58aa8a5`, tree `63c9165d7b5286240ee5d9e020978cfe0090a1b7` | Frozen E4 acceptance/source and sole root of this planning branch. [Primary acceptance](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/docs/task007e/e4/primary_acceptance.json). |
| V | `e603672b209985f11ed26b6f44d3949ffd5675c5`; delivery `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9` | Exact E3 tested source and [verification record](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9/docs/task007e/e3/verification.json): historical 750 passes, not rerun here. |
| X | `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae` | Original scientific VIS worker; distinct from E3, E4, this plan and future W1 execution. |
| R | `b72c9f4d1b393d3071eb14ddbab8653fa15d1a98` on `codex/pre-sid-r0-w1-recovery` | [R0 correction WORK](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/b72c9f4d1b393d3071eb14ddbab8653fa15d1a98/docs/pre_sid/r0/WORK.md) and [recovery instructions](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/b72c9f4d1b393d3071eb14ddbab8653fa15d1a98/docs/pre_sid/r0/recovery_instructions.md). `RECOVERY_INCOMPLETE`, `PROPOSED_NOT_ACCEPTED`; correction review/verification independently owned. |
| S0 | `3747e0d9a7e834a5df34c4b089a5292c0a749fa4`; acceptance overlay at `9f0cbe0f0f48a1e2a62716957bbab79fe2b5b1b4` | [S0 specification](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/3747e0d9a7e834a5df34c4b089a5292c0a749fa4/docs/S0_SHARED_SAFETY_SPEC.md), [architecture acceptance](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/9f0cbe0f0f48a1e2a62716957bbab79fe2b5b1b4/docs/safety/s0/primary_acceptance.json). Architecture acceptance only. |
| S1 | `9f0cbe0f0f48a1e2a62716957bbab79fe2b5b1b4`; preparation `fa4615ac11a1cf79c14d12eedb9360e33291c182` | [S1 gates](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/9f0cbe0f0f48a1e2a62716957bbab79fe2b5b1b4/docs/safety/s1/review_gates.json); [later provenance](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/fa4615ac11a1cf79c14d12eedb9360e33291c182/docs/safety/s1a/provenance.json) records owner-supplied S1 acceptance with conditions. Earlier pending flags are historical, not erased. |
| S | `24cd70ca18b3efa56a9412d7cef9a86466091721` on `research/safety-s0` | Current committed S1-A lineage inspected: seven source modules, fixtures and comparator. [Implementation evidence](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/24cd70ca18b3efa56a9412d7cef9a86466091721/docs/safety/s1a/implementation_work_evidence.json), [oracle authorship review](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/24cd70ca18b3efa56a9412d7cef9a86466091721/docs/safety/s1a/oracle_completion_review.md). Unverified research candidate. |
| F | `37b3f19a5d58f9a76cfd9dee5cb5bf4352edc980` on `research/efficiency`; clock executable `c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a` | [Clock-only report](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/37b3f19a5d58f9a76cfd9dee5cb5bf4352edc980/docs/task007f/profile1/clock_only_execution_report.md). Observer validity incomplete and allowance unresolved; no controlled profiling qualification follows. |
| W | `52c5f55c253ef88bc0bc66fb9504eef5af21d2b5` on `codex/m5a-nmpc-weight-m0` | [M5-A WORK](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/52c5f55c253ef88bc0bc66fb9504eef5af21d2b5/docs/apex_workbench_nmpc_weight_m0/WORK.md). Committed checkpoint is blocked; active worktree has concurrent edits, excluded from this audit. No statement about their eventual outcome. |
| W0 | Accepted implementation `c5f3db6852af8f8ffccf4e5e9e6f11d01fa861b4`, recorded in W | [Workbench V0.3-D acceptance](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/52c5f55c253ef88bc0bc66fb9504eef5af21d2b5/docs/reviews/apex_workbench_v0_3_d/PRIMARY_ACCEPTANCE.md): bounded archive inspection and existing workspace capabilities; no new controller qualification. |

The M5-A table entry is an inspection checkpoint, not a frozen workstream head. During P0,
its independently owned branch advanced to `e1fe6666daaa7e85eb0dc29a80e969291a1afa48`.
That concurrent revision is not reviewed or changed by P0, and the pinned W findings are not
presented as its current outcome. R0 and the frozen Performance/Safety/Efficiency refs stayed
at the identities above.

P0 statically recomputed the 294 original `/source_sha256` entries in
`docs/task007d/vis/vis1l/evidence/controlled_A/summary.json` against P: zero mismatches.
All five gamma2 Planning file hashes match the immutable Performance manifest.
These are byte-preservation checks, not tests of mathematics or capture provenance.

| Protected input | SHA-256 at P |
|---|---|
| `configs/performance/apex_performance_synthetic_v1.json` | `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf` |
| `uv.lock` | `8cf85868a456415a898643dbb226d146b0b90e5c98982136cf2abf2465fa16ec` |
| `pyproject.toml` | `c8ea69a3a486c9794b6cf88ac26566211c6f1bb7b7286d86dbaa36a191353d41` |

P0's branch is `codex/pre-int-p0-plan`, created in an isolated managed worktree directly at P.
Only this document is written. Its containing commit is the planning delivery identity, supplied
in the final handoff without a circular self-hash. The explicit one-file P0 allowlist overrides
the general `CODEX_HANDOFF.md`/`DECISIONS.md` update rule for P0; this document is its handoff.
The original Workbench checkout, R0, Safety, Efficiency, CT and M5-A paths are read-only inputs.

## 3. What exists and what is missing

### 3.1 Execution, configuration and lifecycle

At P, `src/apex/control/mpc/controller.py` separates `MPCController` from the injected
solver and prediction problem. It has reset, retained primal warm starts, diagnostics,
independent optimized-vector/constraint checks and invalid-result rejection. A failed solve
clears the retained solution. Its returned previous-command placeholder is not an eligible
nominal packet. `finalize_control` covers the synchronous path; it is not the asynchronous
actuator application's universal Safety gate.

`src/apex/control/trajectory/planner.py` composes the original actuation predictor, genuine
NMPC solution, packet and TVLQR gains. Invalid prediction/gains yield no packet. Packet and
buffer code own copied read-only arrays, finite/shape/time checks, interpolation, newer-plan
admission, availability and reserve. Buffer sampling rejects an exhausted horizon. The tracker
clips to the configured box, then limits steering change; the runner separately limits actual
application by elapsed time. These are existing mechanisms, not work to reinvent.

The accepted configuration is **not the generic constructor default**: N8, dt=0.1 s, H=0.8 s,
four RK4 substeps, `CostScales(lateral=2)`, combined grip/normal-load allocation, 0.08 m tracker
margin, racing reference enabled, progress weight zero. TVLQR is 100 Hz, speed gain 1,
steering-rate 1 rad/s, with the original gain construction and terminal design. Explicit IPOPT
options, warm starts and gamma2 Planning must remain identical. The frozen manifest and
`scripts/task007dcx/worker.py::{geometry,frozen_config}` establish this composition;
`scripts/task007dvis/worker.py` establishes its use with Architecture A. The manifest's
`runtime_auto_load=false` is literal. E4's acceptance overlay resolves its historical pending
flags; rewriting those flags is forbidden.

Missing: one intentional local composition entry point, typed input/output results, a complete
session reset contract, and one resolved identity/configuration snapshot validated before solving.
`src/apex/control/base.py` intentionally has only a generic mapping context. Do not turn it into
another department's wire contract or replace it project-wide.

### 3.2 Scheduling, authority, faults and timing

`src/apex/simulation/asynchronous.py` already supplies deterministic event chronology:
one pending preparation; fixed nominal planner releases with busy misses; old valid trajectory
tracked at 100 Hz; completion before same-time tracking; waiting for future nominal start;
late acceptance only when eligible; urgent-request latching; separate codriver busy misses;
and held-input plant motion in steps no larger than 5 ms. It emulates asynchronous physical
time through sequential computation. It is not an OS worker or hardware scheduler.

`TrajectoryPlanner.prepare` is a blocking computation. It does not make its caller concurrent.
The future external simulator must continue advancing while a genuine worker prepares a plan;
this cross-process/runtime adapter is part of subsequent integration, not a P0 invention.
A local facade must preserve release snapshots and the distinction between preparation,
completion, acceptance, proposal and application. It must not treat a solver success as authority.

Legacy pending commands retain their source plan across handoff/fallback. Due application
precedes same-time fallback admission checks. The accepted manifest explicitly records missing
independent fallback-domain rechecks at every delayed application. Existing diagnostics and
simulation termination do not close this gap. Missing feedback is also not meaningfully tested
by a perfect-state loop without a separate boundary that can receive an absent observation.

Minimum independent work is therefore validation/inhibition at a local software boundary,
including caller-supplied current-time checks. It must expose request versus application identity.
It must not silently adopt S1 epoch/lease cancellation or change frozen pending-command order.

### 3.3 Safety lineage and reuse decision

S0 accepts separation of proposal feasibility, accepted authority and physical application;
unknown policy remains explicit, and no universal neutral/stop action exists. S1 adds pure
protocol contracts. At S, `records.py`, `codec.py`, `time.py`, `ordering.py`, `policy.py` and
`reducer.py` implement a candidate logical transaction system with ledgers/latches, exact-rational
clock mapping and no physical endpoint. Source says unverified. Endpoint outputs remain empty.
The enabled candidate transitions are T01/T02/T03/T06/T09/T11/T13/T14; the other six are disabled.
This is not a ready-made simulation Safety controller.

The current literal oracle registry statically contains 98 complete core candidates, 14 complete
original materializations and one additional candidate: **113 complete candidates**, plus two
core and three original partial cases. `full_trace_status=PENDING_INDEPENDENT_REVIEW`.
The unresolved cases are T06-NORMAL-BOUNDARY, T06-WARNING-BOUNDARY,
V05-A-stale-capture, V07-A-explicit-reauthorization and V19-A-missing-persistence.
They concern simultaneous fault representation, stale-fault history, reauthorization provenance
and unknown restart history. Presentation/first-decision/hash-scope questions also remain.
No case is counted as behaviorally accepted by this P0 audit.

`tests/unit/safety_authority/oracle_support.py` requires an externally supplied independently
authenticated review/digest, exact source/fixture/comparator bindings, an accepted/excluded
partition and `EXACT_LITERAL_NO_IDENTIFIER_MAPPING`. Exclusions remain `NOT_RUN_NOT_PASS`.
Expected traces are literal; actual `result.snapshot` carries forward. Command-payload,
whole-event, operation and sealed-batch hashes have different preimages. Never normalize them
into equivalence, generate expectations from the reducer or author a local approval.

**W1 reuse:** S0's accepted separation and no-policy claim discipline, plus the already accepted
Performance validators. **No runtime import, copying or cherry-picking of S1-A code/fixtures.**
This avoids duplicating the general permission protocol while allowing a much smaller local
nominal-output validation boundary. It makes no S1 completion claim. Oracle adjudication,
independent review, execution and endpoint work are separate dependencies only if later work
chooses to adopt S1. They do not block this explicitly narrower simulation MVP.

### 3.4 Reproducibility, existing tools and resource evidence

The repository already has immutable profile/fixture/source hashes, Planning validation, raw
state/control/plan/packet/segment exports, solver and full-preparation wall times, CPU observations,
thread bootstrap and archive readers. VIS launchers impose source-bound prerequisites and ordered
historical cases. They cannot simply run from E4 or a new branch with fabricated prerequisite JSON.
R0-G05 identifies that exact issue. W1 needs a small new local entry point that calls existing
controller primitives with fresh provenance; it must not pretend to reproduce the historical
campaign or modify its gates. New evidence paths never overwrite retained results.

R0-G01 (independent archive retrieval), G02 (historical binary/environment recovery), G03 (missing
C70 outputs), G04 (older ZIP provenance) and G05 (source-bound historical launchers) remain open.
New source-bound W1 execution can use an explicitly recorded available locked environment without
closing any of them. Historical CasADi/IPOPT/linear-solver binary identity must not be invented.

Efficiency F already contains detailed recorder/launcher designs and hooks. Its one clock-only
attempt does not qualify observer cost, clock allowance, numerical parity or Phase B. W1 should
reuse P's existing coarse timers and standard resource observation, not import those hooks or
restart F-PROFILE-1. No subtraction/correction of timing observations is justified.

Workbench has lifecycle, evidence storage, historical P/C0 inspection and bounded synthetic
capabilities. At committed W, M5-A's nominal attempt stopped before controller construction on a
native tuple versus JSON-list snapshot mismatch; its review also found archive ownership routing
issues. The active worktree is being edited independently. Reuse the lessons and future evidence
consumer, not its blocked launcher or scientific namespace. P0 neither repairs nor supersedes M5-A.
W1 must test real snapshot serialization boundaries before constructing NMPC, and bind actual
import paths/hashes rather than trusting labels or module counts.

## 4. Complete activity classification

Each row has exactly one primary category. Category A is the complete W1 scope. Category F
identifies sufficiently established existing capability only within the evidence boundary stated.
An unverified research file is never Category F merely because it exists.

| ID | Category | Activity / disposition |
|---|---|---|
| F01 | F | Canonical SI vectors, angle/progress conventions, separate dynamic plant and symbolic prediction, solver injection: reuse P. |
| F02 | F | Genuine N8 NMPC/IPOPT, retained warm starts, numerical-result rejection and TVLQR/longitudinal tracking mathematics: reuse bounded accepted P. |
| F03 | F | Packet structural validation, immutable arrays, buffer time/reserve/newer-plan rules and tracker saturation: reuse P. |
| F04 | F | Deterministic asynchronous event simulator, zero/injected/measured timing modes, plant motion, busy skips, gated rolling launch and existing diagnostics: reuse P within its documented assumptions. |
| F05 | F | Vehicle/Planning loaders, accepted gamma2 fixture and immutable manifests: reuse; no new Planning format. |
| F06 | F | Existing coarse controller/solver/preparation timers, resource/thread helpers and retained export/readers: reuse applicable pieces; not an end-to-end runtime guarantee. |
| F07 | F | S0 accepted architecture and S1 accepted-with-conditions contract lineage: reuse as design constraints only; no acceptance transfer to S1-A runtime. |
| A01 | A | Fixed-profile composition/identity admission and one reproducible local launch path; no retuning or generic profile editor. |
| A02 | A | Local session lifecycle, complete fresh reset, immutable boundary records and isolated state ownership. |
| A03 | A | Missing/malformed/nonfinite state, reference identity, same-clock/current-sample and sequence validation with explicit inhibition. |
| A04 | A | Nominal packet admission, command/provenance validity, existing limits, source expiry and application-check API; no physical permission. |
| A05 | A | Deterministic no-output/fault results, exception containment, negative tests and auditable event records. |
| A06 | A | Thin adapters to existing asynchronous local runner, focused chronology/noninterference and serialization tests. |
| A07 | A | Exact-source environment preflight, focused genuine zero/injected correctness fixtures, one bounded measured smoke and descriptive feasibility summary. |
| A08 | A | Fresh raw evidence, compact handoff/interface instructions, preservation audit, commit/push and final review boundary. |
| B01 | B | Generalized configuration editor, arbitrary tracks/profiles, reusable packaging/installer and extra convenience commands: defer. |
| B02 | B | New dashboards, Workbench adapters, visual exports or feature expansion: defer to Workbench owner. |
| B03 | B | Broad profiling, observer calibration, Efficiency hooks, parameter sweeps, threading experiments or optimization research: defer. |
| B04 | B | Full historical archive recovery/reproduction and C70 exporter repair: independently owned R0/VIS work; preserve failures. |
| B05 | B | Adoption/completion of the full S1-A logical protocol as a runtime dependency: defer; unnecessary for this local MVP and currently unverified. |
| B06 | B | Long-lap repeatability campaigns, new stability analyses and broad performance qualification: defer; not needed for first integration engineering. |
| C01 | C | Any objective/model/solver/gain/architecture change, C70/B predictor selection, aggression/progress switching or reserve rescue policy: Primary scientific decision. |
| C02 | C | Recovery basin, automatic degraded continuation, emergency braking, safe stop, actuator-neutral semantics, reentry/hysteresis or physical uncertainty policy: Primary policy decision. |
| C03 | C | Promote legacy baseline fallback to supervised application-time recovery, or adopt stronger epoch/cancellation rules: reviewed policy/semantics decision before implementation. |
| C04 | C | Resolve S1-A simultaneous-fault/oracle/provenance/representation questions and approve focused case selection: Safety review/Primary decision. |
| D01 | D | External Simulation state/world transforms, stepping/worker ownership, completion clock, actuator hold on inhibition and transport contract: negotiate with Simulation. |
| D02 | D | Actual Planning producer/schema/map/version agreement and online trajectory updates: Planning interface task. |
| D03 | D | Perception capture/publication/receipt clocks, freshness allowance, quality/covariance/bounded uncertainty and frame guarantees: producer data/contract needed. |
| D04 | D | ROS 2 messages/topics/QoS, Embedded transport, actuator acknowledgements/cancellation and end-to-end scheduling: departmental integration. |
| E01 | E | Identified vehicle/tire/actuator parameters, dimensions, calibration and measured uncertainty: SID/hardware work. |
| E02 | E | Representative onboard timing, power/thermal/RSS constraints and platform feasibility: actual target hardware benchmark. |
| E03 | E | Independent watchdog/e-stop behavior, physical held-input response, stopping/swept-body/HIL and physical Safety qualification: hardware and calibrated experiments. |

A new external freshness threshold is D03, not hidden inside A03. Legacy fallback mathematics
are reused as historical facts under F04; promoting them into a new Safety response is C03.
These are distinct activities. No Category B–E activity is automatically authorized by W1.

## 5. PRE-INT-W1 proposed implementation specification

### 5.1 Revision, branch and dependency rules

Scientific source is exactly P. W1 should create `codex/pre-int-w1` in its own clean worktree
from the **approved exact P0 planning commit**, which must descend from P with only this
planning file added. Record both SHAs. Do not start from moving `main`, R0, Efficiency,
Workbench or Safety, and do not merge/cherry-pick those branches. An approved replacement
base requires an explicit identity update before numerical work, not an opportunistic rebase.

Protect all existing P executable files, tests, fixtures, configurations, dependencies and
scientific evidence byte-for-byte. Add the local package beside the existing packages.
Do not edit `MPCConfig`, `IpoptSolver`, `TrajectoryPlanner`, `TrajectoryPacket`, TVLQR,
`AsyncRunner`, state utilities or vehicle/track models to make the adapter convenient.
W1's factory must use those existing public primitives and solver injection.

Before any numerical import, resolve the interpreter and installed distributions, hash the
lock/project/fixture/scientific files, inspect import search roots and detect conflicting
editable/source installations. After imports, bind actual loaded files and numerical/native
library identities, not only `sys.path` or declared versions. Record Python executable/build,
OS/architecture/CPU, package versions and available distribution/build hashes. Unknown historical
IPOPT/linear-solver provenance stays unknown. Do not claim exact historical binary equivalence.

Use an available environment whose resolved versions/distributions are consistent with the
unchanged lock and supported interpreter. W1 does not upgrade dependencies, rewrite the lock,
install a new package or independently qualify a new OS/backend. If an existing environment
cannot be admitted, continue nonnumerical software work and report the numerical gate blocked;
obtain a separately scoped setup decision. P0 does not demonstrate environment availability.
A new qualified execution on the available Mac is new W1 evidence, not R0 recovery or release.

Use fresh serial SINGLE workers. On the established macOS/Accelerate backend, use
`scripts/threading_study/config.py` environment/bootstrap before numerical imports and inspect
its returned backend setting plus actual process-thread/resource observations. Do not treat
an environment variable or empty threadpool inventory as proof of active thread counts.
An unexpected backend is a stop for numerical execution under this specification. Do not start
measurement while another benchmark, test suite, rendering job or owned guard is active.

### 5.2 Exact write allowlist

No glob grants repository-wide edits. The following are the only permitted tracked paths in W1.
New files can be omitted if their responsibility is met by another allowlisted file; no new
framework or extra file is needed for its own sake. Any additional tracked path needs review.

| Path | Change and responsibility |
|---|---|
| `src/apex/preintegration/__init__.py` | New explicit local API exports; no backend initialization on import. |
| `src/apex/preintegration/records.py` | New immutable feedback, prepared-result, command-result and fault/event records. |
| `src/apex/preintegration/profile.py` | New fixed P profile admission, composition and resolved snapshot; injected solver supported. |
| `src/apex/preintegration/validation.py` | New local input/output/authority checks using established validators and limits. |
| `src/apex/preintegration/session.py` | New lifecycle and local nominal-control facade; one state owner, no physics or OS scheduler. |
| `src/apex/preintegration/local.py` | New thin adapters for existing local event runner; no duplicate general event simulator. |
| `scripts/preintegration/__init__.py` | New script package marker only. |
| `scripts/preintegration/launch.py` | New stdlib-first parent, identity/resource admission and finite case selection. |
| `scripts/preintegration/worker.py` | New genuine-controller/local-run composition, raw result and diagnostics capture. |
| `scripts/preintegration/evidence.py` | New strict serialization, inventories and small offline summary; reuse existing timing fields. |
| `tests/unit/test_preintegration_profile.py` | New source/configuration/serialization-boundary tests. |
| `tests/unit/test_preintegration_session.py` | New lifecycle, reset, ownership and result semantics tests. |
| `tests/unit/test_preintegration_validation.py` | New malformed/stale/expired/fault/output limit tests. |
| `tests/unit/test_preintegration_evidence.py` | New honest failure/partial serialization and resource-record tests. |
| `tests/integration/test_preintegration_local.py` | New injected local boundary/chronology and adapter noninterference tests. |
| `tests/integration/test_preintegration_genuine.py` | New two short genuine zero/injected correctness cases described below. |
| `docs/pre_sid/preintegration/LOCAL_INTERFACE.md` | New concise API, clock/ownership/claim boundary and exact launch instructions. |
| `docs/pre_sid/preintegration/WORK.md` | New W1 handoff, focused checks, run outcome, gaps and review status. |
| `docs/pre_sid/preintegration/evidence.json` | New compact source/config/test/run identity and raw evidence inventory. |
| `docs/CODEX_HANDOFF.md` | Scoped W1 entry only; retain all unrelated/historical text. |
| `docs/DECISIONS.md` | Scoped local-interface architecture entry only; no new scientific decision asserted. |

Raw new output is limited to `results/preintegration/w1/<unique-run-id>/` and task-owned
cache/temp subdirectories below that root. Use a new nonexistent run directory and keep every
attempt. Logs/XML, failed/partial records and indexes belong there; small identity/hash summaries
belong in `evidence.json`. Do not change `.gitignore`; existing results exclusion is reused.
No writes to R0, Safety, Efficiency, CT, Workbench, historical `results/` or accepted manifests.
Do not alter this approved P0 specification during W1 to expand scope or redefine success.

### 5.3 Implementation order and reusable pieces

1. **Identity and configuration (A01).** Snapshot branch/status/protected refs; admit P/plan
   ancestry and all frozen bytes. Implement a fixed `apex_performance_synthetic_v1` factory,
   using P's complete manifest configuration and accepted constructor composition. Reuse
   `load_vehicle_parameters`, `load_track`, `PlanningReference(..., feasibility_policy="advisory")`,
   `MPCConfig`, `CostScales`, `make_mpc`, native planner and tracker. Check complete effective
   MPC/tracker/solver/fixture settings before first solve. No treatment overrides or fallback
   to generic defaults. Advisory Planning warnings remain visible.
2. **Records and lifecycle (A02).** Add the minimal API in 5.4, copying borrowed input arrays
   and preserving immutable packet identities. Separate per-session controller warm starts,
   tracker previous input, buffer, delay estimator and urgent state. Reset creates fresh runtime
   objects or demonstrably resets all owned state. Never reuse a consumed packet/token from a
   prior episode. Seed/fixture/start policy is explicit; there is no standstill launch.
3. **Validation and faults (A03–A05).** Implement the local perfect-state/current-clock gate,
   packet and command admission, result/exception taxonomy and append-only event records.
   Do not port S1 into this package. A command is a proposal until the caller invokes the
   application check with current feedback; a successful check is still software evidence.
4. **Local adapters (A06).** Exercise the facade through thin planner/tracker delegates around
   `AsyncRunner` and its existing packet/buffer/timing objects. Bind a single active buffer;
   never maintain a second authoritative packet beside the runner's buffer. Preserve source
   fields and underlying numerical inputs/outputs. Keep predictor clones detached from the live
   session and audit callback identity/ownership. Reuse `RollingDelay`, `UrgentReplan` and existing
   runner chronology; do not implement a second general scheduler or live OS worker in W1.
5. **Software checks and evidence (A05–A07).** Complete all targeted positive/negative and
   serialization/noninterference checks before numerical admission. Finish the genuine
   correctness prerequisites, then run the single measured smoke. Use its native timings for
   the feasibility summary, without another benchmark campaign or an observer-cost model.
6. **Delivery (A08).** Audit scientific preservation, retain raw failures and coverage, write
   the interface/handoff, commit and push the bounded result, and stop for Engineering Review.

Routine software defects within this allowlist may be corrected and affected software tests
rerun during W1. Each earlier failure remains retained. Fixing a guard does not reset an already
consumed measured-smoke attempt. No intermediate Engineering Review is needed for these steps.

### 5.4 Smallest local interface and ownership contract

Proposed Python package: `apex.preintegration`; local entry point:
`scripts/preintegration/launch.py`. This is an in-process engineering API, not a new wire format.
The future simulator supplies scheduling, completion observations and actual applied input.
The controller owns prediction/solver/tracker state; it never steps the physical plant.

| Operation | Required behavior |
|---|---|
| Construct / initialize | Admit the exact profile, vehicle, track and reference identities; create fresh owned state; prepare/validate the gated startup packet before any nominal output. Record prelaunch construction/solve/gain time separately. |
| Prepare | Receive one immutable release request: session/request/plan identity, canonical state, release/sample time, delay estimate, release-active packet and actual preceding applied control. Call genuine `TrajectoryPlanner.prepare` using original A prediction. No physical state or future completion is supplied to the predictor. Permit at most one outstanding preparation per session. |
| Complete / offer | Caller supplies actual completion time. Associate it with the same request, then accept/wait/reject with native buffer semantics and the accepted wrapped continuity envelope/nominal validity check. Never shift nominal timestamps to hide late readiness. Completion alone does not activate a packet. |
| Propose | Receive current feedback, decision time and actual preceding applied input. Use the accepted active packet and original tracker; preserve desired versus saturated/rate-limited values and source plan. No solver runs in the 100 Hz operation. |
| Check application | Receive a proposal, current feedback, check time and actual prior applied input/time. Validate session/source authority, current state and command limits, and use the existing elapsed-time steering clamp. Return validated command or inhibited/no command; do not claim a physical acknowledgement. |
| Reset / close | Reset invalidates all prior session proposals/completions, clears owned state and requires a new gated startup. Close is idempotent and leaves no valid output. In-flight old completion cannot reopen a reset/closed session. |

Records need only: run/session ID; monotonically assigned request/plan/sample IDs; six-state
SI vector; capture/sample and decision/completion/check times; known local clock ID; actual
preceding applied `[delta,a_cmd]` and its observation time; immutable source profile/fixture/packet
identity; status/reason(s); and optional valid command. Packet data reuse `TrajectoryPacket`;
no duplicate trajectory schema or generic ROS-style header is needed. Session IDs are correlation
and stale-object protection, not authentication, durable S1 epochs or physical arming authority.

`Feedback` is explicitly a perfect-state local simulation sample. Its capture time and decision
clock come from the same supplied simulation-time variable. In this MVP a new decision/check
requires a sample of that same instant: exact equality of that shared value, not an invented
physical millisecond allowance. Missing sample, older capture, future capture, unknown/different
clock, backwards decision time or conflicting sample identity inhibits. Reuse of the identical
sample for distinct operations at the same instant is allowed; replay at a later instant is not.
No wall-clock subtraction from simulation seconds and no reinterpretation of covariance is allowed.
A later interface may admit delayed feedback only after D03 supplies a reviewed freshness contract.

Use existing `state_vector` and `control_vector` for finite shape/canonical semantics, including
nonnegative unwrapped `s_abs`. Keep `[vx,vy,r,e_psi,s_abs,e_y]` and `[delta,a_cmd]`; angles in
radians, SI everywhere, left-positive lateral and CCW yaw conventions unchanged. Dynamic
`a_cmd=Fx_total/m`; it is not the measured derivative of `vx`. Retain wrapped heading residuals
and geometry-only progress wrapping. Never invent an estimator or modify incoming coordinates.

Reuse existing configured state/control/model-domain predicates through a separately injected
validation dependency; do not make the controller call a physical plant's `step` or inspect
future plant truth. For the local synthetic composition, a separate diagnostics/model instance
may implement the validation callback. Its identity and domain are recorded independently of
prediction and physical propagation. Structural validity and model validity remain distinct.

Output has one explicit status, such as `VALID_NOMINAL`, `INHIBITED`, `NOT_READY`, or `CLOSED`.
Only `VALID_NOMINAL` contains a finite two-vector. `INHIBITED` has `command=None` and reasons;
zero vectors and the optimizer's previous-command placeholder never encode inhibition. Results
carry request source and check time, not a fabricated guaranteed hold interval or physical state.
Application consumes the local proposal identity at most once; no duplicate application is
approved by this API. Caller-reported application remains a separate observation.

The caller must continue 100 Hz tracking while a preparation is pending, skip busy releases,
retain the last applied command in its own simulator during computation, and supply a new
current sample at application. These are the existing chronology requirements, not permission
to hold an inhibited result indefinitely. If the simulator cannot define its behavior on no output,
that is D01 and must be settled before connecting this API to it. The local negative-test endpoint
simply records inhibition and terminates its synthetic scenario without inventing a new input.

### 5.5 Minimum simulation Safety MVP

The MVP is software supervision of declared nominal outputs. Its explicit rules are:

- Reject malformed/nonfinite state, input, metadata, gains and packet timing; retain the cause.
  Invalid authoritative feedback, session/time corruption or closed-session use inhibits the
  session until explicit reset with fresh startup. Missing feedback at an operation likewise
  cannot silently reuse a last-known state. This latch is local memory only, not power durability.
- A failed/rejected new preparation grants nothing. Existing accepted nominal authority can
  continue only while valid. Record failed solve versus failed prediction/gain/packet separately.
  An exception becomes an observable fault/no-output result at the public boundary, retaining
  original exception type/message/traceback in evidence. Do not catch it and report success.
- Reuse `TrajectoryBuffer` availability, newer-ID, minimum-reserve and no-extrapolation rules.
  An exhausted packet has no nominal output, including the terminal boundary under native
  tolerance. A stale request, invalid/unknown source or reset-session token cannot gain authority.
- Reuse tracker box saturation and nominal steering slew. Independently validate exported
  finite values against the exact effective bounds; do not clip an arbitrary invalid external
  candidate into validity. At application reuse elapsed steering limiting and validate the
  final pair. Record requested, limited and application-checked values distinctly.
- Preserve original pending-request source even when a newer packet becomes active. A handoff
  alone is not revocation. At an explicit application check, reject an expired/invalid original
  source or invalid current feedback. Do not relabel the request with the newest plan or adopt
  S1 epoch cancellation. This new check is an explicit local boundary addition; the untouched
  legacy runner's historical application/fallback semantics remain separately reported.
- Never export legacy fallback as `VALID_NOMINAL`. No eligible nominal packet means no valid
  nominal output, even if the historical runner could enter its separate baseline mode.
  No recovery, deceleration, emergency-stop, rest or safe-hold assertion follows.
- Fault events contain stable reason codes, operation/session/source/sample identities, local
  time, observed versus missing values and output disposition. Log known simultaneous causes
  without inferring physical effects; deterministic order is a new local record convention,
  not an adjudication of S1's contested traces. Disk-write failure invalidates evidence status;
  it must not produce a successful completed-run claim.

W1's local event-runner adapters exercise the same controller-facing validation/generation path.
The accepted runner has no general pre-application callback. Therefore its `controls` application
rows are **legacy simulator observations**, not proof that the new application-check API enforced
an endpoint. Exercise that API before the explicit mock endpoint in separate integration tests.
Do not pretend a post-step diagnostic wrapper is pre-application enforcement. If genuine local
smoke output would require exporting fallback, stop the smoke as incomplete; do not bypass the
facade or silently switch policy. A live external application adapter is the next engineering stage.

This boundary is sufficient to test that invalid software outputs are withheld at the new API.
It does not establish continuous held-input validity, bounded physical uncertainty, fallback
recovery, command revocation delivery, independent watchdogs, collision safety or safe stopping.
Those capabilities remain C/D/E and are not prerequisites for the first bounded simulation run.

### 5.6 Focused checks, negative cases and experiment prerequisites

The following are proposed W1 checks, **none executed in P0**. Use exact selected node IDs,
full logs/XML and exit statuses; label fake-solver/packet/endpoint cases as software tests.
Do not call them genuine NMPC behavior or physical fault injection. Literal test expectations
come from the stated local contract, not from generating expected output with the implementation.
Existing tests remain unchanged; new tests verify meaningful boundary behavior.

| Check group | Minimum positive and negative coverage |
|---|---|
| Profile / provenance | Exact P/manifest/fixture/lock binding and effective native MPC/tracker/IPOPT snapshots; wrong base, changed file/hash, unknown field, missing option, wrong native policy or wrong import origin rejects before solve. Generic defaults must fail accepted-profile equivalence. Test real capture → JSON bytes → decode → native-snapshot comparison, including tuple/list representation, booleans, nulls and nested values. A genuine non-treatment change must still reject. |
| State / reference / clocks | Six/two dimensions and SI order; owned input copies; NaN/Inf, conversion errors, negative progress, missing state/reference/identity, invalid model domain, missing/future/older capture, unknown/mismatched clock, backwards time, conflicting/replayed sample/session. Same sample at same instant is an explicit positive case. No hidden fallback freshness threshold. |
| Lifecycle / reset | Two sessions cannot share tracker/buffer/warm-start/delay/urgent state. Reset after accepted plan and pending command invalidates old results; delayed old completion is rejected. Fresh reset agrees with fresh construction on deterministic inputs. Close is idempotent; no output before successful startup or after close/inhibition. |
| Planner / packet authority | Solver failure, success with malformed/nonfinite/infeasible solution, prediction/gain exception, invalid packet, stale plan, early completion waiting, late but eligible completion, insufficient reserve, exact expiry and unavailable authority. A rejected replacement does not overwrite healthy old authority. Failed preparation never exports the previous-command placeholder as a new nominal command. |
| Output / application | Native saturation/slew retained; finite/box/rate violations and wrong source/session denied. Application uses current sample and elapsed preceding-input time. Pending old-source request across handoff retains its identity; same-source expiry before application inhibits; repeated application is denied. Observe no endpoint call after inhibition. No zero/brake substitution. |
| Event order / noninterference | One pending solve; busy planner and busy codriver counts distinct; current valid TVLQR continues; plant moves during solve; early waiting/late rejection; coincident completion/tracker/release ordering; no catch-up releases, future truth, or time reversal. In controlled injected fixtures, facade delegates preserve native numerical input/output and accepted chronology for nominal valid cases. New gate rejections are recorded as deliberate local behavior, not forced into parity. |
| Fault / evidence / resources | Stable multi-cause events, original exception retained, missing fields versus null distinguished; nested NumPy booleans/arrays in new result serialization; malformed/unserializable values retain a failed/partial record; parent/worker exit disagreement, cancellation/timeout, missing RSS, incomplete timing endpoints and failed final index never become success. No historical archive reconciliation or status writes. |

Reuse these existing checks and helpers from P without modifying their assertions:

- `tests/unit/test_state.py`, `test_config.py`, `test_planning_reference.py`: vector/configuration
  and reference validation. Select affected tests rather than rerunning unrelated geometry studies.
- `tests/unit/test_trajectory_tracker.py`: packet arrays/timestamps/ownership, no extrapolation,
  TVLQR/tracker limits, predictor clone isolation and gain-failure packet rejection.
- `tests/unit/test_async_chronology.py`: deterministic `StraightPlanner` and approved synthetic
  plant fixtures for busy releases, failure/old authority, waiting, handoff mismatch, gated launch
  and physical motion. That planner is explicitly fake; its results are not optimizer evidence.
- `tests/unit/test_latency.py`, `test_diagnostic_timing.py`, `test_committed_prefix_runtime.py`:
  relevant motion/staleness, measured timer and request-source/pending-application cases.
  Committed-prefix tests guard legacy/default semantics; B prediction remains disabled.
- `tests/unit/test_mpc.py`: focused invalid solver result/reset tests as appropriate to callers;
  `test_threading_study.py`: relevant bootstrap/native-policy tests. No parameter-study campaign.

Before the measured smoke, require all new unit/local-boundary tests and affected inherited
checks to pass, then these **two bounded genuine correctness fixtures** in the new integration
file, fresh serial SINGLE workers, unchanged profile/initial state:

| Fixture | Evaluation conditions | Required evidence |
|---|---|---|
| G0 | 0.24 s simulated duration, planner zero delay, codriver zero delay | Genuine gated startup plus recurring preparation, no future packet use, real nominal output through local delegates. |
| G1 | 0.24 s simulated duration, planner injected 60 ms, codriver injected 25 ms | Plant motion during solve, current feedback, pending old command, codriver busy skips, distinct timestamps and censored work at cap. |

These fixtures are correctness prerequisites, not extra performance samples or hidden retries
of the measured experiment. All other fault cases use injected software fixtures. No full lap,
C70 case, new tire/model experiment or S1-A test is included. Zero/injected/measured latency
coverage is thereby explicit. Keep original scientific validity/slack limits, packet tolerances
and skipped fixed-release accounting. If a genuine fixture unexpectedly violates scientific
validity or fails to prepare, preserve it and stop numerical progression; do not tune the case.

Software gates can use multiple focused invocations as corrections require, serially and with
retained logs. Give each genuine fixture the same per-worker resource caps as the smoke below.
Do not run the full suite during WORK merely for completeness. Broad regression and exact-revision
formal acceptance tests are deferred to the explicitly authorized Verification stage.

### 5.7 One genuine smoke and the smallest feasibility benchmark

**Feasible in source, not demonstrated executable in P0.** P contains the controller, fixtures,
plant and modes needed for the experiment. Actual environment/resource/software admission must
pass in W1. No claim that the historical strict VIS launcher is directly runnable from W1.

Proposed single command after implementation (currently nonexistent and unexecuted):

```sh
PYTHONPATH=scripts:src <admitted-python> scripts/preintegration/launch.py \
  --case measured-smoke --output results/preintegration/w1/<fresh-run-id>
```

The parent must set and verify the native SINGLE bootstrap itself before any child numerical
imports. Only the finite G0/G1 prerequisite cases and `measured-smoke` are admitted; no arbitrary
controller parameter CLI is introduced. Reject an existing output directory and an uncommitted
or unbound runtime snapshot. Commit W1 executable code after software gates, before the measured
attempt, so its run uses a clean immutable producer SHA. Later report-only commits record that
producer separately; source changes invalidate applicability and do not grant another attempt.

Smoke scope is exactly one worker and one attempt, including genuine cold startup and subsequent
warm preparations, using the accepted gamma2 track/vehicle, P's exact initial state from manifest
`/evaluation_protocol/initial_state`, original A predictor/variable availability and unchanged
NMPC/TVLQR settings. Duration cap **2.0 simulated seconds**, no lap completion requirement.
Planner latency uses measured native full preparation time; codriver delay uses measured full
update time (`codriver_delay=None`). These are explicitly new W1 evaluation conditions; they do
not reproduce the historical imposed-5-ms VIS result or change a production default. Preserve
startup/preposition assumptions and record incomplete work at the duration boundary.

Use the existing `AsyncRunner` for physical chronology, with thin delegates exercising the new
input/nominal-output facade. No second timing or plotting worker runs concurrently. Preserve
native `event["planner_total_time"]` and its role in simulated availability. Record the new
boundary's enclosing duration separately, including adapter validation overhead. Never silently
subtract overhead, replace the native timer or claim it measures external transport scheduling.
The eventual external worker must report its true completion time including its full boundary cost.

Before numerical admission: verify no owned competing measurement, inspect existing measurement
guards/process ownership and acquire a task-owned exclusive measurement lease; do not delete
foreign guards. Require at least **1 GiB free disk**. Proposed per-worker administrative caps:
**60 s total launch-through-cleanup wall, 30 s process-tree CPU, 2 GiB sampled RSS and 128 MiB
new output**. Include initialization, failed startup, serialization and cleanup in wall coverage;
record sampling interval and available CPU/RSS coverage. These are resource guards for the
bounded assignment, not guarantees about solver deadline or memory maxima. If the supervisor
cannot enforce/observe its declared envelope, mark the run censored/blocked, preserve observations
and stop. Do not copy CT/F research launchers or claim their unresolved guards are qualified.

Native construction, startup solve and gain preparation are measured separately from recurring
calls, but remain in total experiment wall/CPU. The parent writes launch/identity/exit/guard
records even if the worker cannot write its final result. Predeclare this one-attempt budget;
no automatic retry, longer duration, revised delay pattern or favorable rerun after a numerical
failure, timeout, exhaustion, unexpected fallback or evidence-integrity failure.

Use this **same smoke** for the initial computational feasibility description:

- Retain every startup/runtime preparation, solver and tracker wall-duration sample, request,
  readiness/acceptance/application timestamp, busy skip, active reserve and source plan ID.
  Include the failed/unfinished population and observation coverage; do not select only successes.
- Report counts and raw samples first; min/median/p95/max of completed recurring native full
  preparation, inner solve and tracker update, with the quantile convention and small-sample
  limitation. Separate native preparation from adapter envelope, solver-only and initialization.
  If fewer than ten recurring completions are observed, mark the assessment insufficient.
- Compare full preparation observations with the **100 ms nominal release opportunity** and
  tracker observations with the **10 ms tracker period**. Architecture A has no 70/80 ms fixed
  handoff deadline. A preparation above 100 ms implies a possible busy release, not automatically
  authority loss or a codriver miss. Report actual misses/reserve/expiry as separate observations.
- Report run wall and CPU, simulated coverage and wall/simulated-time ratio; sampled RSS/thread
  counts/backend state; available CPU/host/memory metadata and competing-process admission.
  Missing observations are null plus `NOT_OBSERVED`, not zero. A sample peak is not continuous peak.
- Give one descriptive outcome: `PRELIMINARY_FEASIBILITY_OBSERVED`,
  `INSUFFICIENT_EVIDENCE`, or `FEASIBILITY_CONCERN_OBSERVED`, with the actual evidence and
  limitations. There is no invented hard timing threshold, WCET certification, embedded-platform
  assumption, real-time CI assertion or portable speedup claim. A slow result informs later work;
  it never triggers automatic Efficiency, retuning or a new run.

A slow but valid complete smoke may satisfy implementation delivery while reporting a feasibility
concern. An unexpected scientific/control fault, incomplete evidence or failed smoke cannot be
relabelled as successful completion. W1 stops with the partial result for review in that case.

### 5.8 Raw evidence, preservation and delivery

Create a new schema for **new W1** artifacts; do not feed them to the historical VIS exporter or
repair its missing records. Explicit supported conversion of native arrays/scalars into the new
schema is allowed and tested; arbitrary stringification or dropping nonfinite/missing fields to
obtain a successful JSON file is not. Invalid input representations can be retained as tagged
fault evidence, distinct from valid scientific numbers. Record the in-memory resolved snapshot
before any rejection frontier so a tuple/list guard failure cannot erase the actual comparison.

Minimum retained artifacts under each fresh run directory:

| Artifact | Required content |
|---|---|
| Admission / invocation / environment | Exact argv, working directory, UTC and monotonic origins, parent/child identities, source/plan SHA, dirty state, hashes, full resolved configuration and actual imports/backend/distributions. |
| Raw controller / chronology | States, requests and checked outputs, native controls/plans/packets, handoffs/reserve/busy events, release-known states and plant segments where available; no reconstructed missing future/application state. |
| Fault journal | Append-only operation events, no-output reasons, exception/traceback, injected versus native labels and authority provenance. |
| Timing / resources | Unmodified native times plus boundary envelope, samples/units/population/startup separation, guard/resource observations and unavailable/censored fields. |
| Completion / failure | Exit code/signal, stop reason, requested versus observed coverage, unfinished preparation/command, success/failure/censored disposition and cleanup observation. |
| Index / software logs | Relative file paths, ordinary SHA-256 and byte sizes; full prerequisite test logs/XML/commands and per-invocation results. Successful final index required for evidence completion. |

Stream a minimal operation/fault journal before offline summaries so a final serializer failure
does not erase all prior observations. Preserve failed setup/test/run attempts beside later
software corrections, with distinct attempt identities. Never pool separate invocations into one
pass count. Link the raw location and inventory in the tracked compact evidence record. Establish
an agreed retrievable delivery location for new raw files; a local path/hash alone is not an
independently verified backup. If external retrieval is not yet arranged, label that delivery
limitation instead of claiming portability or closing R0-G01.

Before and after focused checks and delivery, compare the complete protected P tree, including
all scientific source, original tests/configurations/fixtures/dependencies and committed evidence.
Authenticate the 294-entry original source map and accepted manifest/Planning hashes. Only new
allowlisted files and the two scoped general documentation entries may differ. Verify original
mathematics/configuration through source-byte identity plus complete effective constructor/solver
snapshots; matching one headline parameter or test count is insufficient.

Snapshot protected refs and task worktree status. Preserve preexisting/unrelated/concurrent
changes; do not reset, stage or claim ownership of them. Verify origin remains
`https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle.git`. Stage only allowlisted files,
commit/push normally, verify remote visibility and report producer and delivery SHA/branch/URL.
A rejected push preserves the local commit and is a delivery blocker; no force-push/merge/tag.

Deliver `WORK_COMPLETE_PENDING_REVIEW`, listing completed A01–A08, exact focused results,
experiment outcome, raw evidence, limitations and deferred complete regression. The general
handoff and decision entries describe only the new local engineering boundary. Do not rewrite
Performance acceptance, R0 status, Safety gates or Workbench reports.

### 5.9 Stop conditions and unresolved decisions

Stop the affected execution path immediately for source/config/dependency/import mismatch,
unsupported environment/backend, missing prerequisite, conflicting measurement ownership,
resource-envelope loss, unexpected physical/model/NLP validity/slack failure, invalid chronology,
future-information use, unexpected fallback/exhaustion, or corrupt/missing final evidence.
Preserve partial data, fault/exit identity and exact source. Do not weaken limits, repair scientific
outputs, change expectations to match outputs, or tune a parameter to continue.

Continue independent authorized nonnumerical work when possible. Routine local code/test failures
can be corrected within the allowlist before scientific admission. Any required edit to frozen
source, new dependency/setup, changed model/solver/gain/authority policy, S1 adoption or external
actuator semantics is a true boundary: record the smallest concrete unresolved decision and stop
its dependent work. No automatic scope expansion or extra measured attempt is allowed.

## 6. Primary review decisions requested with plan approval

| Decision | Recommended bounded resolution | Consequence if not approved |
|---|---|---|
| P1 — local Safety product boundary | Approve nominal-output validation/inhibition, same-instant perfect-state feedback, explicit application-check API and no exported recovery/fallback policy. Preserve legacy simulator code and distinguish its application rows. | Specify the required alternative. Full S1 adoption or supervised physical recovery is a different scope and cannot be smuggled into A. |
| P2 — numerical scope and environment | Approve existing-lock environment admission, G0/G1 correctness fixtures and exactly one 2 s measured smoke with the proposed resource/attempt caps, as new W1 evidence. | Implement/test the nonnumerical boundary only; smoke and feasibility milestone remain blocked, with no completion designation. |
| P3 — consolidated scope / source | Approve exact source/branch strategy, allowlist, tests/evidence and single final WORK review. No intermediate review for routine steps. | Revise this plan before implementation. |

Approval of P1–P3 is one consolidated W1 authorization, not three serial gates during WORK.
No new physical control equation, parameter or stop policy needs to be chosen to approve it.
The C/D/E decisions in section 4 remain explicitly deferred. In particular, unresolved S1 oracle
cases, historical environment recovery and full physical R1 qualification are not made critical-path
prerequisites for this narrower simulation controller stage.

## 7. Objective completion milestone and Simulation handoff

`CONTROL_PREINTEGRATION_IMPLEMENTATION_COMPLETE` means all of the following are met:

1. A01–A08 are delivered on an exact pushed candidate, with frozen scientific inputs preserved
   and no changes outside the approved allowlist. Source/dependency/import identities and the
   complete effective accepted configuration are inspectable.
2. The documented local API composes the genuine controller, preserves state/control/SI and A
   timing semantics, initializes/resets deterministically and distinguishes preparation, authority,
   proposal, checked output and caller-observed application.
3. All targeted new and affected tests pass with no unresolved correctness failure. Fault tests
   show absent/invalid state or authority never reaches the mock endpoint as a command; old valid
   authority can continue on a rejected replacement; no new physical response is invented.
4. Genuine G0/G1 prerequisites pass, and the single measured smoke reaches its bounded requested
   coverage without unexpected scientific/control failure or fallback, with genuine controller
   calls and facade input/generation paths observed. Final evidence/index and exit status agree.
   Timing/resources and any feasibility concern are honestly reported, including small population.
5. Fresh raw evidence is indexed, inspectable and retained; the handoff gives its actual retrieval
   status. A clean-source launch path, exact profile, local contract and known limitations are
   sufficient for the next engineer to begin external interface work without guessing physics.

W1 may report **milestone candidate met, WORK_COMPLETE_PENDING_REVIEW** when these conditions
are demonstrated by its focused evidence. Independent Engineering Review decides whether to admit
the exact candidate to formal Verification. The subsequent explicitly authorized acceptance gate
runs the complete required regression/acceptance set on that reviewed SHA and audits evidence,
then reports `VERIFIED_AWAITING_ACCEPTANCE`. Primary acceptance can then confirm the designation.
Do not confuse an implementation milestone, WORK delivery, verification and physical acceptance.
An unrun/blocked/censored smoke does not meet this milestone, even if all code was written.

The next Simulation integration task receives one concise package: exact scientific/plan/producer/
delivery revisions and URLs; local entry point and admitted environment instructions; the internal
API and time/ownership/event-order contract; immutable configuration/vehicle/track/reference hashes;
G0/G1 and smoke source-bound evidence and raw inventory; fault/no-output examples; application-check
versus legacy-runner limitations; and the outstanding D01–D04/C/E list. It must explicitly negotiate
external state conversions, feedback age/clock semantics, real worker completion and physical-time
progress, command application/hold policy on inhibition, reset ownership and result transport.
No external simulator agreement or integrated closed-loop success is claimed by this handoff.

## 8. Subsequent roadmap

1. Finish this consolidated Control pre-integration assignment after approval.
2. Independently review and verify the exact delivered candidate, retaining negative evidence.
3. Negotiate actual interfaces with Simulation, Planning, Perception, ROS 2 and Embedded owners.
4. Implement and validate the Simulation integration package, including true worker/world chronology
   and explicit no-output handling at its simulator endpoint.
5. Obtain genuine integrated closed-loop results with source/configuration/run identities.
6. Use the existing Workbench for controlled tuning and hypothesis tests under separate grants.
7. Benchmark representative onboard hardware; do not infer it from this Mac sample.
8. Prioritize SID when credible data and timing feasibility exist; if performance is inadequate,
   prioritize targeted Efficiency first, driven by measured bottlenecks.
9. Complete physical Safety policy, hardware enforcement and validation before physical actuation.

Complete physical R1 qualification is not a prerequisite for the first bounded simulation run.
The approximately ten-week project window favors the small A scope, parallel departmental contract
preparation after review, and evidence-driven prioritization over new research campaigns. No
unmeasured effort estimate or calendar promise is used as an acceptance criterion.

## 9. Recommended single Codex assignment after Primary approval

> **PRIMARY APEX — PRE-INT-W1: Consolidated Control Pre-Integration WORK**
>
> Implement A01–A08 exactly as specified in the approved exact commit of
> `docs/pre_sid/preintegration/PREINTEGRATION_PLAN.md`. Scientific source remains
> `48adbdf64d492592d15e23c917aca71fa58aa8a5`. Start `codex/pre-int-w1` from that planning
> commit in an isolated worktree. Preserve all frozen scientific source/configuration/
> dependency/evidence identities and independently owned R0, Safety, Efficiency, CT and
> Workbench workstreams. Use only the section 5.2 write allowlist.
>
> This single WORK grant covers the local nominal-control facade, simulation-only validation
> and inhibition, exact-profile composition, lifecycle/reset, thin existing-runner adapters,
> targeted software tests and genuine G0/G1 prerequisites, one measured 2 s smoke/feasibility
> attempt under section 5.7, raw evidence and concise documentation. P1–P3 are approved as
> written. No routine intermediate authorization or documentation-review gate is required.
>
> Do not import/promote S1-A, export a new recovery/stop policy, change controller mathematics,
> tune parameters, build ROS 2 or other departmental contracts, install dependencies, run a
> research sweep, duplicate Workbench, merge branches or perform hardware/physical work.
> If a true boundary in section 5.9 is encountered, retain the evidence, finish independent
> in-scope work and report the blocked dependent part without inventing a decision.
>
> Commit/push the exact candidate and evidence summary, verify remote availability and stop at
> **WORK_COMPLETE_PENDING_REVIEW**. Report whether the section 7 implementation milestone
> candidate is met, with exact producer/delivery SHAs and limitations. Do not automatically
> start formal Verification, external integration, Efficiency, SID or physical Safety work.

This quotation is a recommended future assignment. It grants nothing until Primary approves it.

## 10. P0 documentation checks and final boundary

P0 static checks cover source/ref identity, the 294-entry source-map and five Planning hashes,
current Safety oracle status and comparator gate, committed R0/M5-A ownership/status, the one-file
diff, commit ancestry, Markdown/link/path consistency and `git diff --check`. Other worktrees and
frozen refs are preserved; concurrent M5-A edits are not attributed to P0. This document makes no
behavioral assertion from those static checks. No handoff/decision/source/dependency/test file
outside this exact P0 path is changed.

The document audit resolved all 13 commit-qualified source links locally, checked 32 uniquely
classified activities (A8/B6/C4/D4/E3/F7), and confirmed that the W1 allowlist has 21 explicit
paths, of which only the two general documentation files already exist at P. Markdown fences
and whitespace were checked without executing project code.

The planning commit SHA and verified GitHub location are supplied in the final delivery handoff.
Required next action is Primary review of P1–P3 and this proposed W1 boundary. There is no automatic
implementation, test, smoke, benchmark, integration or release authorization.

**Stop: PLAN_COMPLETE_PENDING_PRIMARY_REVIEW.**
