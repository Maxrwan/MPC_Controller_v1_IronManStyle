# APEX Workbench V0.1 corrective Engineering Review

**Decision: FAIL. Not eligible for formal Verification yet.**
**ENGINEERING_REVIEW_COMPLETE_PENDING_DECISION.** Recorded 28 October 2026, Africa/Cairo.
Reviewed source: **`219b9358409fa73fc59f24a7755da66771883e6b`**, branch
`codex/apex-workbench-v0-1`. This report does not authorize corrections or another gate.

Worker ownership, atomic publication, comparison classification and evidence finalization are
substantially improved. Two nearby retained-record failures remain blocking: incomplete request
metadata crashes the app, and deletion of required retained geometry silently removes its plot
without an integrity warning. The fresh combined suite also has one R1 synchronization failure.

## Review matrix

| Finding | Decision | Invariant and fresh evidence |
|---|---|---|
| R1 ownership/recovery | PASS WITH CONDITIONS | A live worker retains the same execution lease; verified process identity gates termination; stale uncertain work becomes interrupted. Real SIGKILL/cancellation tests and a separate unsuspended-worker loss probe exercise this. One regression reads recovery before lease release; resolve its synchronization before claiming a clean acceptance test result. |
| R2 initial publication/readers | FAIL | Request and initial status must appear together, and incomplete retained records must remain inspectable/excludable without crashing. Hidden staging closes the original publication window; two concurrent AppTest readers pass. A valid JSON request missing `prediction` still passes selection and raises KeyError in the app. |
| R3 notes | PASS | Readers see complete, exclusive, append-only note versions. Paused publication, interrupted link, two writers/24 saves and concurrent readers pass. Prior note bytes remain unchanged. |
| R4 comparison | PASS | Controlled comparisons require matching verified scientific composition/environment/contracts; differences must be explicit; incompatible units or unverified data must be invalid. Real-output fixtures distinguish controlled duration changes, documentation-only revision changes, seven illustrative composition differences, incompatible units and altered data. |
| R5 finalization | PASS | Scientific outcome and valid retained evidence are separate; final status anchors a complete manifest. A real completed worker plus injected hash-read failure yields completed scientific outcome, failed evidence and quarantined telemetry. Receipt immutability and interrupted final-status recovery pass. |
| R6 integrity on consumption | FAIL | A required selected artifact must either verify or produce a visible incomplete/unverified result. Modified CSV/request/manifest and restored-mtime cache tests pass. Deleting manifest-listed geometry bypasses verification through the missing-file early return; the UI presents eight charts, no error/warning, and a trajectory with its geometry silently absent. |

## Blocking reproductions

**C-R2 — incomplete selected metadata crashes the app (P2).** Copy a genuine completed run,
delete only the `prediction` key from its request JSON, and leave manifest/status untouched.
`storage.list_runs()` selects it without an incomplete-record warning. Plot ingestion correctly
detects the request mismatch, but the unconditional notes-tab read raises **KeyError: 'prediction'**.
All Streamlit tabs execute even while Trajectory is selected. This is an availability/tolerant-reader
gap; the old initial-publication race itself did not recur.

Pinned sources: [selection contract, lines 116–124](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/219b9358409fa73fc59f24a7755da66771883e6b/tools/apex_workbench/storage.py#L116-L124),
[raw request read](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/219b9358409fa73fc59f24a7755da66771883e6b/tools/apex_workbench/app.py#L146),
[unguarded prediction read](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/219b9358409fa73fc59f24a7755da66771883e6b/tools/apex_workbench/app.py#L279).
Required disposition: validate/tolerate required selected metadata and quarantine damaged records
without an uncaught app exception. Preserve the damaged evidence; do not repair historical files.

**C-R6 — missing retained geometry is silently treated as optional (P2).** Copy the same genuine
completed run and delete only `experiment/geometry.csv`. Its manifest still lists that file.
`plots.trajectory()` returns just `Plant trajectory`; AppTest renders **eight charts with zero
exceptions, errors or warnings**. The completed/valid status remains visible. No absent geometry
warning is supplied, although the caption still discusses track boundaries. The plotted XY bytes
are genuine and verified; the defect is undisclosed missing required evidence, not fabricated XY.
Comparison does reject missing geometry because its fingerprint uses `artifact_bytes()` directly.

Pinned source: [missing-file early return](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/219b9358409fa73fc59f24a7755da66771883e6b/tools/apex_workbench/plots.py#L11-L17),
[trajectory composition](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/219b9358409fa73fc59f24a7755da66771883e6b/tools/apex_workbench/plots.py#L49-L68).
Required disposition: distinguish an unsupported/not-produced optional channel from a required or
manifest-listed artifact that has disappeared; visibly reject or label incomplete selected plots.
The nearby missing-state/control/XY early-return paths also need bounded checks in corrective WORK;
those additional deletions were inspected, not separately executed in this review.

Both reproductions use disposable copies, **no resealing**, no new scientific execution, and the
unmodified pinned app. [Reproduction commands](REPRODUCTION.md), [observations/hashes](evidence.json)
and [review-only probes](review_probes.py) accompany this report.

## R1 ownership and the failed regression

Fresh combined result: **116 passed, 1 failed, 0 setup errors, 0 skipped**, 50.89 s.
Breakdown: **48 Workbench passes/1 failure; all 68 selected scientific unit tests passed**.
The failing case is `test_r1_real_sigkill_keeps_worker_lease_and_recovers[False]` at line 109:
after the worker ceased to match `owned_process`, the next status read returned `running`
instead of `interrupted`. The cancellation-after-supervisor-loss variant passed.

Do not turn this into a green result by dropping the failure or counting a favorable rerun.
The failed record's worker independently wrote `worker_abort.json` with interrupted outcome.
The original failed-test state was archived byte-for-byte before diagnostic reconciliation.
Later checks found both owners gone and the lease free; `status_for()` then recovered interrupted
with valid partial evidence and remained idempotent. A separate actual supervisor SIGKILL with
an **unsuspended** worker produced five lock-busy/running observations followed by interrupted
recovery; it never admitted another worker or claimed successful science.

The source permits this conservative intermediate status: identity checks can cease matching
during process exit before the inherited descriptor is finally released. `status_for()` returns
the old active status while the lease is busy. The regression's immediate absence-of-identity
check is therefore not a reliable recovery barrier. This is the supported explanation, not an
exact measurement of the failed case's descriptor-release instant. A separately authorized
correction should assert eventual bounded recovery after lease availability and retain the
independent assertion that admission stays blocked while the worker holds it.

Process ownership binds PID, birth time, full command, role and unique run directory. Worker
signals use psutil identity checks, not blind process-group termination. Mocked wrong-birth/
command/role/directory tests are narrow negative tests, not proof of actual OS PID reuse.
An additional live unrelated `/bin/sleep` process was rejected by `terminate_owned()` and stayed
alive until the harness cleaned up its own process. Legacy stale records are reported as unknown/
interrupted without rewriting their bytes. Recovery is demand-driven by status/admission, not a
separate persistent recovery service.

The worker guard independently checks supervisor loss, cancellation and the existing sampled
wall/RSS/output limits. The inherited lease blocks concurrent admission even during SIGSTOP.
No kernel/OS crash, power-loss, prolonged suspension or resource-exhaustion campaign was run;
sampled guards are scheduling-dependent and provide no hard deadline or physical stopping claim.

## Test credibility and the earlier 18 errors

The regressions contain actual subprocess workers, original numerical entry points, OS signals,
AppTest sessions and filesystem publication barriers. Mocking is confined to controlled scheduling,
ownership mismatches and fault injection. Comparison fixtures deliberately change and reseal copies
to isolate compatibility classification; they do not establish physical equivalence of different
controllers/models. Integrity probes change unresealed copies instead. Assertions check outcomes,
retained receipts, errors, classifications and plotted values, not just mocked call counts.

Both original-entry-point parity tests passed freshly. Additional full-worker dynamic and LQR
checks matched retained states/summaries and LQR controls byte-for-byte against direct entry-point
execution. These are short deterministic software-consistency checks, not physical validation,
integration convergence, long-horizon stability or hardware timing evidence.

The historical combined log reports 99 passes/18 setup errors from a single module-scoped seed
fixture failing admission with `Another Workbench experiment is running`. That failure caused the
dependent setup errors; they were not 18 independent numerical defects. The final source explicitly
closes the supervisor descriptor after finalization, and sequential completion helpers require lease
availability. The newly executed combined invocation has **zero setup errors**, so that setup problem
is not reproduced. Its different R1 test still lacks that completion barrier. Historical 49/68-pass
correction claims were inspected and are **not** included in the fresh totals.

## Launcher: PASS WITH CONDITIONS, separately assessed

Only the launcher **at the pinned revision** is reviewed. The main checkout started at later
`b49844c85b53ab3b77572156f4824689e7f80405`; that descendant changes only the launcher,
README and handoff. Its server-reuse/proxy improvements are outside this assessment.

The exact pinned executable launched from `/private/tmp`, reached loopback health **200 / ok**,
and its own Streamlit PID was verified listening on 127.0.0.1:8501. Chrome displayed APEX Workbench,
its actual experiment controls and scientific-limit labels. A repeat launch returned exit 1 with
the port-unavailable message and left the original server alive. An exact copy beside no Workbench
environment returned exit 1 with the setup/README message. SIGINT to the verified launcher helper
exercised its shutdown/finally path; the owned server and helper were gone afterward, and connection
attempts were refused. Browser inspection submitted no experiment.

Retained negative smoke evidence: the sandbox initially prohibited loopback bind (EPERM), which
the launcher labels as port unavailable. Startup was then tested with the authorized local bind
permission. The smoke harness later failed its immediate plain-bind assertion after clean shutdown
with EADDRINUSE. Follow-up found no live owned server, connection refusal and successful
SO_REUSEADDR bind. TCP address reuse can therefore make the pinned launcher's pre-bind report busy
briefly after shutdown. This does not show a surviving server. The original harness/log remain;
the follow-up finishes the independent missing-environment check without changing the launcher.

Conditions/limits: all bind errors are conflated with a busy port; a port-check/readiness race and
proxy behavior are not qualified. Finder/Terminal GUI launch was not separately automated; the
actual executable was launched by absolute path. The launcher starts the app and opens a browser;
it submits no experiment and bypasses no job lock/provenance/resource/scientific check. Closing
the app server is not cancellation of an independently supervised scientific worker.

## Revision, preservation and scientific boundaries

Governance, original review/reproductions, correction report/record, relevant implementation/tests,
launcher, README/capabilities, scientific entry points and applicable specifications were read.
An isolated shared local clone is detached at the exact pin; its tracked status is clean. The only
tooling accommodation is an excluded `.venv` symlink to the existing installed environment. All 11
correction source-manifest entries match. Imports in the test header point to the pinned clone.
No dependency was installed and no implementation, test or scientific source was edited.

The diff from pre-Workbench `37b3f19a5d58f9a76cfd9dee5cb5bf4352edc980` to the pin is empty for
`src/`, `scripts/`, `configs/`, `tests/`, `results/` and core dependency files. Thus canonical
models, tires, controllers, integrators, optimizers, frozen profiles and tracked historical results
are unchanged. A before/after audit of the original checkout found all **887 tracked files**
byte-identical before review documentation, and all **13,376 pre-existing result files** unchanged
in size/mtime. This metadata audit is not a fresh content hash of every large ignored result.

An additional clone-local default 10 s dynamic UI run, timestamped 20:55:51 UTC on 27 October,
was found when work resumed after the interaction gap. It is outside the recorded test/probe
commands, its origin is unattributed, and it is excluded from review success/parity evidence.
It remains untouched in the clone; no scientific conclusion is drawn from it.

Canonical SI/order/contracts remain; adapters call original Task004 main/Task005 run_case, and XY
uses the canonical Frenet API. Linear tires remain unsaturated with diagnostic mu; parameters are
synthetic and state is perfect. Scientific execution completion, evidence validity and scientific
acceptance are separately labeled. No physical validation, unsupported MPC capability or hard
real-time qualification is claimed. No full regression, NMPC, async, measured-latency or hardware
campaign ran.

This is a fresh technical audit in the same implementing chat. It is **not personnel-independent
Secondary approval**; the requested external decision remains with the user/Engineering Orchestrator
and Primary. No conclusions from the implementing correction report were accepted as proof.

## Recommended next gate

Authorize narrow corrective WORK for C-R2/C-R6 and the R1 regression barrier, preserving these
negative results. Then review the new exact correction SHA. Only after those findings are closed
should the Orchestrator separately authorize formal Verification. Do not launch Verification,
V0.2 or additional scientific campaigns from this report.
