# V0.3-C independent Engineering Review — iteration 1

**FAIL — bounded ordinary software correction required.** Reviewed exact candidate
`c57603ea0e80b7b2121648ae687ac2afa03cb33d` on
`codex/apex-workbench-v0-3-c`, 29 October 2026. This is separate-context Engineering Review,
not formal Verification, scientific acceptance, or permission to execute the scenario proposals.
The candidate remained fixed throughout review. No implementation or candidate test was edited;
no commit or push was made by the reviewer.

The authorized task is the V0.3-C brief, section 7. Governance, the current handoff, the changed
implementation/tests/documentation, relevant accepted readers, retained Q evidence, and canonical
scenario source pointers were inspected. Implementer reports were treated as evidence; the results
below are fresh reviewer checks unless explicitly marked inherited.

## Blocking finding R1 — malformed optional legacy metadata escapes the new presentation boundary

Priority **P2**, blocking this candidate's Engineering Review. A disposable, resealed copy of a
genuine completed, owned V0.2-style `dynamic_demo` record passes the unchanged accepted
`engineering_views.inspect` reader. Opening it in C's Inspect page raises an uncaught application
exception before normal raw/provenance details can be reached. The exact B workspace source
`ca3ef9605df3472001302dbf70c0e2815c020d1c` contains every same fixture without an application
exception. This is a new presentation regression, not a request to change the frozen reader.

| Disposable fault | New C assumption / failure | B result | C result |
|---|---|---|---|
| `request.execution_context=[]` | `recorded_view.py:41`, object `.get` | contained | uncaught AttributeError |
| `request.provenance=[]` | `workspace_panels.py:293`, object `.get` | contained | uncaught AttributeError |
| `worker_result.json=[...]` | `workspace_panels.py:304`, summary `.get` | contained | uncaught AttributeError |
| `request.execution_context.role=123` | `recorded_view.py:39-42`, text concatenation | contained | uncaught TypeError |
| `request.provenance.git_revision=123` | `workspace_panels.py:290-293`, text concatenation | contained | uncaught TypeError |
| `worker_result.sampled_model_window=[]` | `workspace_panels.py:305`, nested object `.get` | contained | uncaught AttributeError |

The exception boundary at `workspace_panels.py:369` does not contain AttributeError/TypeError,
and the new snapshot loader assumes optional metadata shapes that the non-lab frozen reader
does not promise. The authoritative seed is
`results/apex_workbench/20261028T114258172191Z_f1c73c037c1c4d3ebe20458a2fd425b9`.
Only copied fixtures were modified/resealed; original evidence was never repaired or upgraded.

**Minimum bounded correction:** validate the optional structures/text fields consumed by the new
snapshot/panels, quarantine an invalid new scientific view with a clear error, and contain expected
malformed-data exceptions so original raw records/provenance remain accessible. Preserve literal
malformed values for inspection; do not silently normalize them into valid metadata. Add focused
regressions covering top-level and nested shapes, valid legacy records and raw access. This can be
done entirely in the additive presentation layer; no frozen dependency or source-identity migration
is needed. Commit the correction to an exact revision and request re-review.

## Direct reproduction and retained results

All logs, JUnit, literal fixtures, source/sample records and scripts are retained under
`results/apex_workbench_v03c_review_20261029/iteration_1/`. The machine record is
[review_record.json](review_record.json). Run `zsh` on that root's `reproduce.sh` only within an
authorized bounded review: it checks this exact candidate and creates a fresh output root, refusing
to overwrite earlier attempts. The script uses the approved Workbench Python, a fresh Accelerate
SINGLE bootstrap before numerical imports, six native environment ceilings, fresh Matplotlib roots,
`PYTHONPATH=.:scripts:src`, and unique pytest base/JUnit/log paths.

| Fresh invocation | Result | Exit | Raw evidence |
|---|---|---|---|
| `probe_metadata.py` | 3 B passes, 3 C failures, 11.54 s | 1 | `metadata.log`, `metadata.xml`, six metadata JSON records |
| `probe_nested_metadata.py` | 3 B passes, 3 C failures, 9.09 s | 1 | `nested.log`, `nested.xml`, six nested JSON records |
| `probe_core.py` | 15 passed, 131.73 s | 0 | `core.log`, `core.xml`, `native_samples.json`, `pairwise.json` |
| Candidate `test_recorded_view.py` + `test_engineering_workspace.py` | 38 passed, 122.50 s | 0 | `ui38.log`, `ui38.xml` |

These are separate invocations. Counts are not added to the implementer's earlier runs or to B's
formal suite. No failed assertion was weakened or rerun to obtain a favorable result. No reviewer
harness failure occurred in the pytest invocations. An initial sandbox `ps` denial is retained in the
tool transcript; the same read-only process inspection then succeeded under scoped escalation.
It did not require a test retry or a change to any scientific condition. Timings are observations,
not benchmarks, acceptance limits or real-time evidence.

## Findings that passed within this review scope

- **Exact sample meaning:** independently read native CSVs, rather than model output, for BASE/IZ
  state/control/diagnostic/stored-XY sample 25 at exactly 0.125 s. Actual yaw rates are
  0.08489185848304563 and 0.07598743026071822 rad/s respectively; both applied steering rows
  are 0.02 rad. At 0.100 s the state yaw rate is still zero and the new applied steering is
  0.02 rad; at 0.095 s applied steering is zero. The viewer does not interpolate or infer a hold.
- **Terminal/partial/coverage:** completed terminal state 0.500 s has no applied-control interval;
  the terminal diagnostic row is informational. Focused candidate tests retain partial last/attempted
  diagnostic meaning and invalid comparison eligibility. Off-grid, missing, multirate and
  out-of-coverage sources remain unavailable. Unsupported profile fixtures retain explicit static/raw
  access. Stored XY/state timebases must agree; position is never reconstructed by the viewer.
- **Pairwise science:** the production Q consumer revalidates actual 17 references and all four
  permitted BASE/treatment pairs. Without selected Q each is controlled candidate; with exact Q each
  is qualified synthetic. Four-run BASE/IZ/CF/CR has six edges: three BASE edges qualify, three
  treatment/treatment edges remain illustrative. Three-run behavior is also freshly covered by the
  candidate UI selection. No group-qualified experiment or unsupported causal ranking is displayed.
- **Epochs and selection:** changed/missing telemetry, duplicate/nonmonotonic times, mismatched XY,
  late source bytes, late Q anchors and wrong catalog identity/profile are rejected. A late mutation
  during rendering clears the scientific plot container. Four-run Q switching while playing resets
  and pauses; source/page/run/timebase behavior, exact seek, previous/next, deterministic bounded
  ticks and end-of-record pause pass focused checks. There is no wall-time catch-up or dynamics call.
- **Read-only archive and provenance:** forbidden lifecycle/annotation APIs are not called during
  retained replay. Archive cancellation/annotation controls are absent. Optional owned notes retain
  the accepted append-only implementation. New presentation modules enter full source provenance.
- **Layout and warning:** direct Home/Run/Inspect/Compare controls, compact columns, collapsed
  provenance and the three diagnostics/evidence/notes tabs remain available. The channels default/
  session-state warning does not recur in the fresh source-switch tests. The implementer's retained
  desktop screenshot was visually inspected as inherited evidence, not a fresh reviewer browser run.
- **Legacy scope:** original V0.1/V0.2 app, plots, launcher, workers, readers, models/configuration and
  lifecycle are byte-identical to B. The affected candidate tests freshly reopen a genuine nominal
  owned run. Prior complete engine/launcher/browser evidence is inherited where unchanged; no new
  full engine suite or independent live launcher/browser smoke was run in this review.

## Scientific scenario package

No scientific blocker was found in the design-only package. All five requested families are addressed
with a complementary three-part shortlist. Static source checks confirm the existing oval constructor
and baseline initialization, GP's 43 control points and manifest sector boundaries, Task007A's external
Candidate-C N4 configuration/rolling initialization, synthetic YAML values and existing guard constants.
The proposals correctly distinguish L's low-slip scheduled LQR/PI, historical conservative G, and exact
accepted N8/gamma2 Performance P source `e603672b209985f11ed26b6f44d3949ffd5675c5`.

No straight geometry, prescribed schedule, physical parameters or numerical threshold is invented.
Closed-loop racing versus open-loop response, state/control meanings, geometry versus trajectory
validity, exact-source qualification, component versus integrator oracles, low-speed/braking limits,
latency, partials and rejected evidence remain explicit. S1/S2/S3 end in concrete Primary decisions;
approval still does not authorize execution or transfer VDL Q to a new scenario. No proposal was added
to the executable registry or run. This is a static design assessment, not new geometry, dynamics,
stability, robustness or physical validation.

## Preservation and disposition

Before/after audit passes: all **56** scientific files match both B's inventory and the actual accepted
V0.2 Git blobs at `4897686e79c13757d5ef5b4373b44d4cab99b5bf`; all **983** preexisting tracked files
retain their hashes; all **345** original qualification campaign files retain full SHA-256 hashes.
All **42,014** preexisting result files retain size/mtime and **1,256** symlink targets are unchanged.
This historical result audit is a preservation observation, not a full rehash of all old results.
Audit completed with the candidate HEAD unchanged and clean status before adding these review docs.
Review artifacts are new authorized outputs. No unrelated file, original evidence, campaign or
source inventory was modified.

**FAIL at c57603e:** resolve R1 through the authorized bounded correction process, then independently
review the changed exact revision. Do not advance to formal full-suite Verification, a new racing
scenario, scientific tuning, CT/Safety/hardware work or final user acceptance from this review.
