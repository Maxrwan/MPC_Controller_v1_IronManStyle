# V0.2-B independent Engineering Review

**PASS WITH CONDITIONS — ENGINEERING_REVIEW_COMPLETE_PENDING_DECISION.**
Finalized 29 October 2026.
Reviewed implementation: `895ecddf55754e94d5dbf53d5aca01f91f013a05`, branch
`codex/apex-workbench-v0-2-b`. Accepted contract: `0cc7e4f626311aec05977bd3beda40c346fa4214`.
Review documentation branch: `codex/apex-workbench-v0-2-b-review`.
No implementation/test/configuration changes were made. The containing documentation commit is the
review delivery; its exact SHA/URL is supplied after push. This is not authorization to run a campaign.

## Decision and independence

No blocking nominal scientific-wiring defect was found. The lab faithfully composes the accepted
synthetic cases, canonical plant/runner and prescribed inputs, and retains useful verified evidence.
It is suitable to advance to a **separately scoped qualification-preparation decision**, subject to
the conditions below. This pin cannot directly execute the planned three-grid campaign: refinement
admission and qualification-record ingestion/evaluation were explicitly deferred by WORK.

The user-requested separate reviewer ran in a fresh Codex context without implementing-chat history.
That reviewer inspected sources/contracts and performed metadata probes only, without numerical
imports/execution. The root separately reproduced tests, wrote a new literal canonical-runner
reference and confirmed the reviewer's findings on fresh review records. Implementer assertions
were treated as evidence to inspect, not proof. Both contexts left implementation files unchanged.
Raw scripts, logs and copied-record findings are bound by [review_record.json](review_record.json);
[REPRODUCTION.md](REPRODUCTION.md) records commands, fixture changes and limitations.

## Revision-specific assessment

| Area | Decision | Demonstrated evidence / practical limit |
|---|---|---|
| Five cases and one treatment | PASS | All 17-field snapshots match the accepted table; nominal mass=2 kg, Iz=0.025 kg m², Cf/Cr=45 N/rad; independent Iz=0.030, delta=0.025 versus 0.020, Cf=54 or Cr=54. Name/nulls/geometry/limits remain fixed. Literal construction and same-state analytical oracles pass for all five. |
| Scientific composition | PASS | Immutable canonical VehicleParameters, DynamicBicycle, explicit LinearAxleTire and quasi-static loads; existing 128-waypoint radius-5-m track; no allocator. Existing RK4/SimulationRunner are called directly. No duplicated dynamics, hidden feedback/speed loop, equilibrium reconstruction or parameter coupling. |
| Seed, clock and applied inputs | PASS | [2,0,0,0,0,0], 5 ms plant/input ticks, steering changes at tick 20/time 0.100 s, a_cmd=0, duration 0.500 s; 101 states/100 controls. Held input remains fixed through RK4 stages; final command is informational. Independent literal-reference bytes agree. |
| Telemetry and interpretation | PASS WITH CONDITIONS | Canonical diagnostics preserve SI, nominal/effective stiffness, slip, force/load and diagnostic-only utilization. Genuine nominal exports match the canonical reference. Redundant diagnostic/input aliases are not cross-checked on rebound records (C2). |
| Integrity and comparisons | PASS WITH CONDITIONS | Missing/changed artifacts, changed snapshots/schedules/timestamps/controls/units, incomplete environment and false qualification claims are rejected. Four BASE/treatment candidates remain unqualified; known source differences are illustrative. Source-inventory completeness needs C1 hardening. |
| Completion/failure separation | PASS WITH CONDITIONS | Genuine partial prefixes remain inspectable and invalid for comparison; no terminal row is filled. Reader overconstrains a modeled noncompleted process retaining a complete integration horizon (C3). No live late-cancellation race was run. |
| Numerical/physical boundaries | PASS | Approved provisional numbers are unchanged: grids 5/2.5/1.25 ms, component tolerances 1e-5 SI, floor 1e-12, contraction 0.5, yaw margin 10, slip0.050 rad, utilization1, zero sampled corridor violations. Numerics stays unqualified; no physical/real-time/controller capability claim follows. These criteria were not empirically qualified. |
| V0.1 preservation | PASS | Fresh original dynamic/LQR entry-point and owned-worker parity plus lifecycle/publication/integrity/UI regressions pass. Canonical source, original scripts/core tests, configs/dependencies and launcher have no diff from the accepted contract revision. |

All five cases received construction/oracle checks. Fresh nonlinear software smokes and the extra
reference used nominal BASE/STEER_HIGH, not a sweep of all treatment trajectories. The other three
full trajectories, convergence, repeatability and usefulness remain for authorized qualification.

## Findings and minimum corrections

**Blocking findings: none for the scoped nominal implementation.** The following findings require
an explicit disposition; none was silently corrected. C1/C2 probes deliberately rebind disposable
manifests and status anchors to test faulty-producer/schema semantics. They are not ordinary checksum
bypasses and do not demonstrate corrupted genuine output or authentication against rewriting all data.

| ID / severity | Exact reproduction and impact | Minimum corrective scope |
|---|---|---|
| C1 — Conditional; close or explicitly enforce before qualification | Remove only `src/apex/simulation/runner.py` from both copied requests' `provenance.source_sha256`, rebind copied anchors. `verify_captured_sources()` accepts each fresh pinned request; `read_record()` accepts both; comparison remains `controlled_candidate` with no source differences. Genuine records include runner/state/Frenet/track hashes. [lab_evidence.py](../../../tools/apex_workbench/lab_evidence.py) lines 108–132 requires only part of the dependency inventory; [lab_comparison.py](../../../tools/apex_workbench/lab_comparison.py) lines 15–24 compares only entries present. | Require a versioned complete scientific source inventory at admission and consumption, including SimulationRunner, state/Frenet and actual track dependencies; missing entries invalid, known different identities illustrative. This adds metadata checks, not equations or new criteria. Preserve this review and reproduce the missing-source tests on a corrected revision. |
| C2 — Nonblocking semantic hardening | In a rebound copy, set diagnostic `a_cmd=1.0` at row 25, leaving state/applied control at 0, then recompute the two summaries. Reader accepts it. Ordinary unchanged-anchor edits are rejected. [lab_evidence.py](../../../tools/apex_workbench/lab_evidence.py) lines 183–204 checks diagnostic time but not shared input/geometry aliases. Nominal producer diagnostics are correct. | Compare diagnostic a_cmd with the recorded input, and shared track_s/curvature with corresponding state rows. Do not rerun dynamics or add physics equations in readers. |
| C3 — Nonblocking modeled failure-presentation gap | In a disposable full-output record, retain `horizon_reached=true` but set receipt/status outcome to cancelled and rebind copied anchors. Reader rejects it because `complete != horizon_reached` at [lab_evidence.py](../../../tools/apex_workbench/lab_evidence.py) lines 199–204. [app.py](../../../tools/apex_workbench/app.py) lines 238–263 then stops before evidence tabs. This models cancellation after integration/export; it is not a demonstrated live race. | Enforce completed implies a valid full horizon, while allowing a noncompleted process to retain recorded full integration coverage. Keep noncompleted outcomes ineligible for controlled comparisons, and raw summary/receipt/logs inspectable. Add a bounded regression; no outcome promotion. |

The recorded source inventory should be checked explicitly for every future qualification artifact
until C1 is closed or an equivalent reviewed qualification preflight supplies that condition.
C2/C3 can be handled in a narrowly scoped corrective WORK task; they do not invalidate the demonstrated
nominal trajectories or turn completed software checks into numerical/physical qualification.

## Fresh review evidence and historical test credibility

- **127 passed, zero failures/errors**, exit 0: all 49 laboratory tests and all 78 existing Workbench
  regressions on the exact pin. This includes literal parameters/components, controls/timestamps,
  real workers/form submission, CSV plots, partial/failure retention, quarantine, original-entry-point
  parity, SIGKILL lease/recovery/cancellation, publication and comparison behavior. No full-suite run.
- A newly authored reference uses literal accepted parameters, direct canonical track construction,
  SimulationRunner and a precomputed 20-zero/80-step command table. It uses no adapter resolver/provider
  to construct expected outputs. State/control/diagnostic CSVs are byte-identical; all 101 XY samples
  agree. These two nominal review trajectories establish adapter parity, not ODE accuracy.
- Root-authored copied-record probes cover 15 snapshot/schedule/input/time/artifact/source/unit/
  qualification/partial scenarios; all expected outcomes reproduced. The separate reviewer independently
  found C1–C3, and root confirmed them on fresh records, without numerical imports for metadata probes.

Equal adapter/reference SHA-256 values:

| Artifact | SHA-256 |
|---|---|
| states.csv | `43e9945f2c458ce80dd3f234da6b3c2b4639c760c8c4ddd6321bae5e5c9ec389` |
| controls.csv | `139c0767e1ba41ae44a3a45fdd7c609d6c57b604812556e38b1fcea29c4c6577` |
| diagnostics.csv | `55730ba2c41350e8e34685e815f178e92805b5168f896d483e361e22bc0e0463` |

The implementer's historical logs/hash bindings were inspected: 44 passed/2 failed initially,
297 passed/1 failed in the mixed selection, then 50 affected passes. The first failures were decimal
plot parsing and a positional test selector; the mixed failure caught extra lab charts in legacy
comparisons. The pin uses round-trip lab parsing, a label-based selector and lab-scoped extra charts;
the fresh127-pass review reproduces the relevant corrected paths. The claim of 301 distinct focused
cases across multiple WORK invocations is correctly qualified; no clean 301-pass invocation existed.
The earlier 174 canonical passes were inspected as historical evidence, not rerun/counted fresh here.

## Preservation and next gate

Implementation hashes and archived WORK log hashes match their records. All non-`.DS_Store` files
in the 19,101-file pre-WORK result population retain size/mtime; this is not a fresh content rehash.
The WORK record reported one changed Finder metadata file at delivery. At review, three `.DS_Store`
files differ from that earlier baseline (results root, task007d, task007d/c/amended). Their Bud1-format
headers identify filesystem-view metadata, not numerical evidence. The observation does not establish
which process changed them; they are left untouched. Raw failed reviews/tests/results are preserved.

Next decision: accept this conditional nominal assessment and authorize a narrowly bounded corrective/
qualification-preparation WORK stage, or explicitly dispose of the conditions. Reviewed refinement
admission, tick/metadata checks for those profiles and qualification-record association are still
needed before the 17-trajectory campaign can run through the lab. Any code change needs its own exact
revision review. Numerical qualification and formal Verification remain separately authorized gates.
No new parameter values, physical assumptions, controller work, sweeps, refinements or hardware ran.

**Stop: ENGINEERING_REVIEW_COMPLETE_PENDING_DECISION.**
