# V0.3-D independent Engineering Review — iteration 1

**PASS within the contracted single-P-archive engineering scope.** 30 October 2026.
Exact implementation: `c5f3db6852af8f8ffccf4e5e9e6f11d01fa861b4`, branch
`codex/apex-workbench-v0-3-d`, base/Primary C acceptance
`7da7100fe624481e6066390d503abea5b4292b4d`. Independent reviewer context; no implementation,
producer, scientific source, candidate-test or protocol edits and no reviewer commit/push.
No blocking finding or corrective implementation iteration is required. This is Engineering
Review, not full formal Verification, scientific approval or user acceptance.

Reviewed the D brief, current governance/handoff, Primary C acceptance, the separately approved
[archive contract](../../../apex_workbench_v0_3_d/ARCHIVE_CONTRACT.md), actual changed code/tests,
retained P evidence, original producer/export semantics and the unimplemented RBT-0.1 proposal.
Working implementation/tests and proposal equal the exact candidate; subsequent collaborator
changes are documentation bookkeeping/handoff only. [Machine record](review_record.json) identifies
fresh commands, artifacts, hashes and scope.

| Area | Independent assessment |
|---|---|
| Source and integrity | All three authority anchors, manifest/self-seal, all25 external inventory files and15 artifact bindings match. All294 scientific and11 exporter source hashes independently match historical Git `8dbd1c5`. No current-runtime substitution. Discovery remains unverified until inspection. |
| Native values and clocks | Independently parsed every retained state/control row for selected core/reference/control channels and every event's time, export identity, source, payload/order/missingness. Plotted applied/requested controls use their complete native application/computation clocks, beginning0.005/0 s. Dynamic `a_cmd=Fx/m` is explicit. Cycle packet status is distinguished from actual solver payload status. Missing `valid_from` and unspecified event ties remain missing. |
| Sectors and geometry | Independent per-row sector partition retains the original run/export IDs and native progress. All nine half-open sectors cover each original state once; whole original Planning geometry remains context. Sector traces use markers without connecting visits; controls/cycles/events remain explicitly full-run. Stored XY/reference reconstruction is labeled. No exporter, interpolation, new score or reconstructed event runs. |
| Fail-closed behavior | Actual copied-byte corruption of unplotted `raw.json`, missing archive, equal-size/restored-mtime state replacement during figure construction, and replacement during HTML serialization withhold the view/report. Failed UI contains no scientific plots or verified label. Existing tests additionally cover resealed manifest/source, schedule, missing evidence and symlink faults. |
| Read-only/UI/export | Actual AppTest paths forbid lifecycle calls. GP→existing archive→existing execution forms and oval preparation work without a request/worker. GP is excluded from comparison/execution. HTML embeds the native view, exact row/provenance/source/inventory identities and historical limits, with no external script dependency or command form. Original oval evidence is honestly unavailable for source-bound ingestion; existing accepted execution interface remains accessible. |
| Qualification and preservation | Production `read_qualification` and four `eligibility` calls retain17 original references/four qualified conditional pairs. All56 current scientific files also match accepted V0.2 Git `4897686`. Before/after full content hashes match all25 GP,345 qualification and4 old oval files. Original failed/partial evidence is not rewritten. |
| RBT proposal | Explicit canonical dynamic/linear-tire/load-transfer composition, GP geometry, rolling state/schedule, guards, finite stop, independent analytical/component/integrator roles and failure classes are present. Static source inspection supports the stated equation/guard meanings. It remains unimplemented, unexecuted and not execution-ready: RBT-S/N/V and component numerical budgets require Primary scientific decisions. G/P alternatives remain distinct and unselected. |

Fresh independent invocations are separate, never an aggregate pass count:

| Invocation | Result |
|---|---|
| Candidate's two new test files |20 passed,0 failed/skipped,8.78 s; complete log/JUnit retained. |
| Reviewer native/integrity/UI probes, original |9 passed /2 reviewer-probe failures,8.76 s, exit1. Both failures were incorrect reviewer assertions: historical source hashes legitimately name `worker.py`; existing `dynamic_demo` has no Track input. Original script/log/JUnit remain unchanged. |
| Only those two corrected reviewer probes |2 passed,0 failed/skipped,3.71 s, exit0. No application/test-contract correction. |
| Targeted prior UI/provenance/default/quarantine/replay/seek checks |7 passed,0 failed/skipped,20.93 s, exit0. Original45/60 s AppTest policies remain. No scientific worker or trajectory execution. |
| Independent stdlib source/inventory audit; production Q audit |Both exit0; hashes/reference counts as above. No trajectory, exporter or racing execution. |

All use the approved Workbench Python/environment; Accelerate SINGLE is configured through its
native API before numerical imports. This demonstrates accepted mode selection, not an exact
active-thread count, timing guarantee or physical qualification. The original20-test orchestration
retained complete success output/JUnit but discarded the returned process-session receipt; its
process exit code is not separately claimed in the machine record.

The implementer's initial13-pass/1-fail catalog regression and corrected59-pass invocation remain
retained supplementary WORK evidence. A retained request records378 source hashes: only
`gp_panels.py` differs from the59-test invocation due to the later sector-context addition.
Workspace/catalog/archive hashes match. Thus59 is **not** promoted to a fresh exact-final59 result;
the final20 new tests and fresh targeted7 checks assess the final changed paths. All nine prior
Workbench test files and all frozen scientific/dependency bytes are unchanged. Full formal
Verification and wider regression remain a separately authorized gate.

Scope limits remain explicit: this successful controlled_A P case has no failure/fallback episode,
so broader M4 controller-failure inspection is incomplete; G/C70 are unsupported. The retained
1558.497 s browser-download tool outlier has unknown cause and is not app-performance evidence.
The implementer reports owned shutdown/port cleanup with PTY exit1 after Ctrl-C; this review did
not repeat launcher/browser measurements or infer a cause. Neither observation is erased by the
fresh software checks. No physical, recovery, standstill-braking or hard-real-time claim follows.

Evidence root: `results/apex_workbench_v03d_review_20261030/`. Recommended stop:
`V0.3_D_ENGINEERING_REVIEW_COMPLETE_PENDING_VERIFICATION_AND_EXPERIMENT_APPROVAL`.
No full formal suite,17-trajectory qualification rerun, racing/RBT simulation, profile selection,
frozen research campaign, Safety or hardware operation was authorized or executed by this reviewer.
