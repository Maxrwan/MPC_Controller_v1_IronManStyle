# Decisions and recommended next assignment

**Design complete, pending review. No implementation is authorized by this document.** Primary's
V0.3-A instruction accepts V0.2 and makes practical engineering the product priority. Routine
navigation, layout, view state, catalog filtering, notes and safe data handling are software choices;
they do not require new scientific approval when semantics and evidence protections are preserved.

## Recommended first WORK — Engineering Workspace & Run Inspection (M1)

Suggested next assignment title: **V0.3-B — Engineering Workspace & Run Inspection**. This is a
new engineering-first ordering, not continuation of an assumed prior B/C/D laboratory sequence.
Complexity **Medium**: a presentation/catalog change with a bounded backend regression surface.

**Outcome:** an engineer opens one primary workspace, finds an actual run/failure, inspects its
configuration/evidence/available outputs, compares two retained runs, and can launch the same three
accepted experiments. Learning prompts remain optional. Existing supported mathematics does not change.

Proposed narrow scope:

1. Add `tools/apex_workbench/workspace.py`, `run_catalog.py` and a small presentation module such as
   `engineering_views.py`. Use Streamlit/Plotly and frozen backend APIs, not a plugin framework.
2. Provide one engineering home and Run/Inspect/Compare views. Show supported versus unavailable
   execution capabilities, recent/failed records, source-aware selection, outcome/evidence/coverage
   and available channels. Rename new primary-view prompts to optional engineering notes while
   preserving original stored prediction/observation/explanation and append-only note behavior.
3. Catalog the owned run root and explicitly discovered accepted Q source-run directories read-only.
   Do not move/copy/reseal originals, make a path alias into a new execution, or hide invalid entries.
   No arbitrary external-folder or physical-telemetry import in this first stage.
4. Reuse `configuration.validate`, accepted case resolution, `jobs.start_run`, cancellation/ownership,
   storage/readers, plots, comparison and qualification applicability. No duplicated equations,
   derived metric calculator or source/evidence bypass. All three supported adapters keep their exact
   parameter/default/timing behavior. NMPC/TVLQR execution is explicitly unavailable.
5. Show existing summary metrics, references, controls/flags/gains and diagnostic traces with units,
   reference owner and actual coverage. Put comparison and provenance ahead of learning exercises.
   Two-run comparison is enough for M1; multi-run pairwise logic and replay follow M2/M3.
6. Preserve the current accepted `app.py` compatibility entrypoint and **all 56 required source files**.
   Make the existing launcher target the new primary presentation, retaining exact listener ownership,
   loopback, reuse, port-conflict and shutdown protections. Update only its entrypoint handling;
   no new server framework or silent reuse/termination of a legacy/unrelated server.
7. Add focused new-view/catalog/qualification/UI tests and ordinary documentation. Candidate allowlist:
   those new presentation files, a new focused test file, launcher, Workbench README and task/handoff/
   decision documents. No edits to `lab_sources.py`, `app.py`, `plots.py`, qualification/evaluator,
   worker/model/controller/runner code or accepted artifacts. If those are necessary, return a narrow
   scope/provenance decision; do not quietly transfer qualification to changed required source.

**Meaningful acceptance:** scenario 1 at a bounded software-smoke level; direct reopen of the actual
Q BASE/IZ sources without moving them; correct candidate-versus-qualified labels with/without Q;
actual trace/metric/reference values; raw invalid-record inspection; optional notes; preserved existing
export access; both V0.1 entry-point/worker parities; launcher ownership/reuse/cleanup. Inventory the
new presentation files in full provenance; prove the 56 scientific hashes remain unchanged and Q still
passes the production consumer for all four accepted pairs. New presentation correctness needs its
own review/Verification; being outside the old inventory does not confer verification.

**Explicit exclusions:** new controller adapters/profiles, new tire/parameter semantics, LQR/TVLQR
retuning or new matrix analyses, scientific campaigns, full multi-run/replay implementation, physical
telemetry, Safety commands, source-inventory relaxation and broad frontend replacement. Deliver
`WORK_COMPLETE_PENDING_REVIEW`, obtain independent Engineering Review, then applicable exact-revision
Verification before acceptance. Reuse unchanged applicable evidence; no automatic qualification rerun.

## Scientific decisions only when needed

No new scientific choice blocks M1 as scoped above. The following are **separate future decisions**,
not a bundled approval request and not permission to implement now.

| Decision / trigger | Concrete engineering example and consequence | Recommendation |
|---|---|---|
| D1 — scientific/presentation source identity, **only if frozen dependencies must change** | Changing one caption in current `app.py` changes a required hash and makes current-source Q application fail, even if numerical trajectories are untouched | Keep all 56 files unchanged for M1. A later inventory/version migration needs explicit scientific provenance policy, exact-source review and qualification applicability disposition; never delete hashes or disable enforcement to obtain a favorable label |
| D2 — physical producer clocks, frames and units | A Pi boot-relative timestamp reset can make an old observation look new; image-plane position cannot be treated as Frenet s/e_y | Agree versioned Control/Perception/Embedded producer semantics before a physical importer. Keep the MVP's known software-data profiles and viewer clock separate |
| D3 — measurement model and uncertainty for observability/estimation | Gyro yaw rate and wheel speed do not supply direct measurements of every canonical state; the discretizer's I4 does not authorize physical C=I | Specify y=h(x), channel/frame/time/uncertainty and sensor/estimator dynamics separately. No synthetic observability result is a vehicle sensor guarantee |
| D4 — new metric mathematical meaning or acceptance threshold | Irregular event rows give different row-weighted versus time-weighted RMS; packet tracking error differs from centerline error | Initially display unchanged exporter metrics/windows. Review each new formula/reference/window/censoring definition before ranking or thresholding; no invented universal “controller quality” score |
| D5 — new execution profile, composition or perturbation | A Q-qualified linear-tire stiffness case does not qualify grip-limited NMPC; dropping preparation time/plant motion to fit UI resource limits changes the experiment | Specify one canonical adapter/profile and its source, timing, model and resource/evidence contract; approve any new excitation/domain separately. Preserve frozen Performance, C/F gates and rejected evidence |
| D6 — physical command/Safety authority | A red stale-telemetry indicator is informative; automatically sending “stop”, arming or acknowledging cancellation changes authority and requires an endpoint/watchdog contract | Keep monitoring one-way and read-only. No Workbench command/Permission path, S1-A reducer integration or physical-test control under this roadmap without separate authorization |

The CT aggregate timer issue, unexecuted L3/CT-1N/R, F observer allowance and S1-A oracle/endpoint
gates remain on their owning research branches. They block corresponding advanced integrations,
not ordinary engineering discovery/inspection. No scientific source or research correction was made.

## Delivery boundary

The six documents in this directory share the [audit revision ledger](ENGINEERING_CAPABILITY_AUDIT.md).
This task changes only these documents, the current handoff and a proposed ADR. Validation is static:
source/evidence hash preservation, path/link/contract consistency, branch/scope audit and whitespace.
No application, numerical import, scientific test/benchmark, simulation or physical interface ran.

**V0.3_ENGINEERING_MVP_DESIGN_COMPLETE_PENDING_REVIEW.** Review this scope before authorizing M1.
