# V0.3-C N1 independent Engineering Review — iteration 1

**PASS** at exact correction `34f98a4894e457900d2fae3b2fd09ead4f5ba5a0`, branch
`codex/apex-workbench-v0-3-c`, 30 October 2026. **N1 is closed for the authorized bounded
responsiveness gate. No unresolved material responsiveness or functional finding remains in this
review scope. The conditional full-Verification gate is satisfied.** The parent may perform its
separately authorized complete Verification once on this implementation. This review is not formal
Verification, scenario approval, physical validation or final acceptance.

The reviewer independently inspected governance, the current handoff, the exact implementation/test
diff, frozen consumers, the original two reviews, and retained evidence. Implementer claims were
assessed as evidence, not accepted as proof. The reviewer made no implementation/test edit, commit
or push. Raw reviewer outputs are under `results/apex_workbench_v03c_n1_review_20261030/`;
[review_record.json](review_record.json) records commands, hashes and dispositions.

## Decision and preservation of the original failures

The unchanged original 45 s Q-selection and 60 s three-run seek tests now pass in the fresh exact
**53-case** selection. The independent single-sequence observations below also put cold/warm Q and
three/four-run common-time interactions in practical seconds. Each seek performs one comparison
operation. These checks support closure without replacing deadlines, qualification consumers,
scientific conditions or unfavorable evidence.

The original iteration-1 R1 FAIL, iteration-2 **45 passed / 2 deadline failures**, and supplemental
**89.886135 s** Q render remain intact. All 66 evidence hashes declared by those two review records
match, including the failed logs and render records. The earlier 89.886 s outlier was not reproduced
or uniquely explained. No host, OS, library or application cause is asserted. Its unresolved causal
explanation remains historical uncertainty; the exact corrected candidate's fresh original-deadline
passes and bounded interaction checks leave no material responsiveness condition open at this gate.
The 10 s investigation target was not turned into a scientific assertion or real-time claim.

## Fresh checks, kept as separate invocations

| Invocation | Result | Exit | Evidence |
|---|---|---:|---|
| Exact candidate: `test_engineering_workspace.py`, `test_recorded_view.py`, `test_responsiveness.py` | **53 passed**, 63.98 s | 0 | `focused.log/xml` |
| Independent disposable integrity/metadata/payload probe | **10 passed, 1 reviewer-harness failure**, 20.66 s | 1 | `integrity.log/xml` |
| Corrected payload-only reviewer probe | **1 passed**, 3.88 s | 0 | `payload.log/xml`, `payload_result.json` |
| Independent two/three/four-run UI sequence | Completed, native/pair assertions passed | 0 | `ui.log`, `ui_observations.json`, `ui_result.json` |
| Corrected process-cold/warm Q probe | Completed, original 45 s render deadline | 0 | `cold.log`, `cold_observations.json` |

The failed independent probe is retained as failed: it incorrectly indexed optional legacy
`controls.csv`, absent in the genuine `dynamic_demo` seed. The application uses the existing
optional-source behavior. Only the positive payload probe was corrected to intersect available
sources and use optional controls; no candidate source/test was changed and no fault case was
rerun. Its complete Plotly JSON matches the original verified plotter for 79 native channel figures
across retained BASE/IZ and the genuine legacy seed, plus three geometry/stored-XY figures.
Reference presence/absence follows the native control frames; no reference or telemetry is invented.

The first UI harness also read Q once during setup. Its 1.203/1.159 s first/repeat UI observations
are retained but are **not process-cold evidence**. One separate fresh-process probe removed that
setup preconsumption and asserted zero full Q reads before selection. This is a disclosed harness
correction, not a retry after an application timing failure. The four-run sequence was not repeated.

| Independent operation | Wall [s] | Process CPU [s] | Matrix calls / full Q reads |
|---|---:|---:|---:|
| First full Q consumption in fresh process | 1.215 | 1.195 | 1 / 2 |
| Same selected Q, warm | 1.167 | 1.168 | 1 / 2 |
| Three-run seek to native 0.125 s | 2.446 | 2.446 | 1 / 4 |
| Four-run selected Q render | 3.740 | 3.754 | 1 / 6 |
| Four-run seek to native 0.125 s | 3.822 | 3.828 | 1 / 6 |

“Cold” means first full Q consumption in that Python process after imports and unqualified UI
setup; OS cache state is uncontrolled. These are bounded AppTest wall/CPU observations, not browser
paint timings, percentiles or guarantees. This lightly instrumented reviewer harness differs from
the implementer's detailed nested profiler; their absolute durations are not a controlled speedup
comparison. The implementer's unchanged before/after profiler and browser/launcher results remain
inherited evidence; all 31 declared hashes match. The retained narrow browser screenshot was
inspected, but the reviewer did not run a new browser/launcher session.

## Semantics, invalidation and remaining cost

The diff removes duplicate work in presentation only. Figures consume the already verified native
frames in the current operation; no frame, qualification decision or scientific identity persists
across operations. Seek/step callbacks update the cursor before rendering, and play/pause installs
or removes the viewer timer before costly reads. Secondary configuration/provenance remains
accessible through its explicit on-demand toggle. No scientific calculation, frozen reader,
qualification criterion, source inventory, launcher, scenario document or replay time meaning changes.
The two original timeout test function ASTs are identical to `8cff10b`; the whole recorded-view test
file is byte-identical. The late plot fault hook moved to the new figure-construction boundary;
its assertions and the original timeouts remain intact.

Fresh independent checks confirm:

- All six original R1 metadata faults remain quarantined with clear errors, no scientific plot/cursor,
  raw/provenance access and byte-identical manifest-verified exports. The nine candidate metadata
  regressions also pass in the 53-case selection.
- Late changes to disposable telemetry, artifact manifests and Q anchors clear every scientific
  figure and qualified/candidate heading. Candidate tests also reject missing bytes and valid
  individually resealed evidence replacement. Source identity is checked on each Q consumption;
  changing a disposable copy of a scientific dependency rejects the next consumption and clears the UI.
  This is consumer validation, not a new continuous filesystem watcher.
- Actual BASE/IZ/CF sample 25 at exactly 0.125 s matches independent native state/control/diagnostic/
  stored-XY CSV lookup. BASE/IZ yaw-rate values differ, and applied steering is 0.02 rad. Four-run
  BASE/IZ/CF/CR displays six edges: three qualified BASE edges and three illustrative treatment edges.
  There is no group qualification, interpolation, inferred command hold or reconstructed XY.
- Retained replay calls no start/reconcile/cancel/annotation API. Native timeline, exact seek,
  deterministic bounded ticks, onset/terminal/partial meaning, source/run/Q reset and raw access pass
  the focused selection. No new qualification or racing trajectory was executed by the reviewer probes.

Full Q revalidation is still the dominant necessary work and grows with qualifying pair count
(two/four/six complete consumptions here). This finite four-run maximum was checked directly;
no broader scaling or general latency claim follows. The correction retains all existing epoch,
manifest and artifact-currentness checks rather than relying on cache invalidation assumptions.
No material stale-display regression was found.

## Audit and handoff

The candidate stayed at `34f98a4` throughout. Before adding these review documents, the audit confirms
all **990** preexisting tracked files unchanged; all **56** scientific files match B's inventory and
accepted Git blobs at `4897686e79c13757d5ef5b4373b44d4cab99b5bf`; all **345** original qualification
files retain full hashes; **44,960** historical result files retain size/mtime; **1,426** symlink targets
are unchanged. Historical size/mtime preservation is not a full-content rehash. Both scenario design
documents match the original reviewed candidate. Original review evidence hashes additionally pass
full-content checks. No measurement guard or conflicting owned Python/Streamlit workload was found;
read-only process inspection needed sandbox escalation. No owned review workload remains.

**PASS; N1 closed; conditional formal-Verification gate satisfied.** Parent retains commit/push and
one complete applicable Verification invocation, exact-source audit and acceptance responsibilities.
No full suite ran in this independent review. Do not infer new scenario, CT, Safety, hardware,
scientific tuning or final user acceptance authorization.
