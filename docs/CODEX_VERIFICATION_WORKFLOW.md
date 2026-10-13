# Codex work, engineering review and verification

This workflow reduces redundant execution, not scientific acceptance thresholds. Follow
[AGENTS.md](../AGENTS.md), the current authorized assignment and applicable scientific specifications.
It does not reopen Task007D-C conclusions or authorize any subsequent controller work.

## Stages and responsibility

| Stage | Responsibility | Exit evidence |
|---|---|---|
| WORK | Codex implements the bounded assignment, writes necessary tests, runs focused correctness/prerequisite checks and only authorized experiments. | Reviewable changes and concise `WORK_COMPLETE_PENDING_REVIEW` handoff; scoped verification, commit and push remain required. |
| ENGINEERING REVIEW | The user and Secondary APEX Engineering Orchestrator inspect code and evidence, then decide whether to request corrections, formal verification or additional experiments. Primary APEX retains scientific direction and final approval. | Explicit next instruction; inspection or a pending-review status alone authorizes no new work. |
| VERIFICATION | Codex runs the complete required regression and acceptance checks on the exact reviewed revision, audits artifacts and reports failures/limits. | `VERIFIED_AWAITING_ACCEPTANCE` only after required checks pass; scoped evidence committed and pushed. Scientific acceptance remains with the review chain. |

For small documentation-only assignments, one stage with consistency, reference, formatting and
changed-file checks is sufficient when authorized. State that verification scope explicitly;
`VERIFIED_AWAITING_ACCEPTANCE` does not imply controller or experiment validation.

## Test now or defer

Run immediate focused tests when changing mathematics, coordinate/state conventions, model validity,
constraints, prediction, serialization, controller/plant interfaces, chronology or packet authority.
Include affected callers: a packet-schema change also needs historical-reader tests. Test diagnostic
instrumentation for noninterference, causal inputs, reconstruction and censoring before using its
results. Use the [test guide](CODEX_TEST_GUIDE.md) to select files and dependency coverage.

Every explicitly required prerequisite must pass before an experiment. Preserve all assignment-specific
hard stop gates, including physical boundary/slack limits, solver/model failures, invalid chronology,
future-information leakage, reserve/exhaustion and unexpected fallback. Stop the affected branch and
preserve evidence; never weaken assertions, tune away a failure or replace an unfavorable run to
advance. The staged policy cannot defer a gate that the current assignment requires immediately.

Broad regression may wait for Engineering Review when focused checks support the current change,
all immediate gates pass, and no assignment requires it earlier. List the unexecuted suites and why.
Do not automatically run the whole suite after every edit, and do not use a focused pass as a full
acceptance claim. At an authorized formal verification gate, run the complete required set; any
proposal to reuse prior results must satisfy the applicability rules below and the gate's instructions.

## Failures, revisions and applicable prior verification

Keep the command, exact revision, environment, exit status and complete failure log. Inspect the
failure and smallest relevant dependency set first. Correct within the existing authorization,
rerun failed/affected checks, and broaden only for changed dependencies, unresolved risk or an
explicit acceptance requirement. A scientific stop or correction outside scope requires review.
Do not repeatedly rerun a failing timing case to obtain a favorable sample.

Formal verification targets an exact reviewed Git SHA. If source, tests, fixtures, configuration or
dependencies change, identify which results are invalidated and submit the changed revision for
the required review. Do not silently verify a moving working tree. For WORK checks before commit,
record the base SHA plus dirty diff/source hashes, then associate the tested contents with the
delivery commit. If a fix changes reviewed behavior, the previous approval does not silently cover it.

Prior passes remain applicable only when their provenance is available and the tested implementation,
transitive dependencies, tests/assertions, fixtures, relevant configuration and numerical environment
are unchanged. Compare the exact revisions and hashes; identical test filenames alone are insufficient.
Record the earlier SHA, command, result/log and the reason for reuse. Documentation-only descendants
can retain applicable numerical evidence without claiming a fresh test run. Changed numerical libraries,
thread policy or measured workload invalidate associated timing comparisons. When uncertain, run the
affected checks or report the gap. Never claim an unrun or inapplicable test passed.

## Experiments and resource isolation

An experiment finishing is execution evidence, not scientific acceptance of its conclusions. Keep
completed/failed/censored runs, coverage limits and negative findings distinguishable from accepted
recommendations. Preserve raw evidence, source/fixture hashes and previous reports; write new runs
to fresh task-specific directories. Reuse existing analysis scripts and unchanged results.

Before timing-sensitive work, inspect active processes and the task's measurement guards, including
`results/**/MEASURED_ACTIVE` and `results/task007d/D3_ACTIVE`. Preserve the applicable disk floor
(currently 1 GiB in Task007D launchers) and native-thread policy. Use fresh sequential SINGLE workers
where specified. Never overlap measurements with tests, rendering, analysis or another benchmark.
Do not remove a guard without investigating its owner. Defer conflicting work and report it.
Host wall time is descriptive; deterministic timing tests are not hard-real-time certification.

## Concise handoffs, logs and context

Use the compact convention at the top of [CODEX_HANDOFF.md](CODEX_HANDOFF.md). Report status/scope,
exact reviewed/tested SHA, delivery SHA/URL, changed files, gates, tests, experiments, failures,
artifacts and the next required review decision. A status is never permission to start another stage.
`COMPLETE` in a task-specific report must identify whether it means WORK completion or completed
verification; neither status grants final scientific acceptance.

For successful tests, report selection/command, pass/fail/skip counts, applicable revision and log
location; include duration only when useful. Label inherited passes and intentionally unexecuted
checks separately. For failures, add the failing node ID, concise cause and disposition. Store full
logs in fresh ignored task evidence directories under `results/`; small documentation checks may
use a task-specific temporary log. Link detailed reports rather than copying them into the handoff.

Read only relevant instructions, specifications, source and evidence while honoring mandatory
repository rules. Use targeted searches and compact status updates; inspect verbose logs for failures
or scientific anomalies. Avoid reopening whole histories, regenerating unchanged figures or repeating
experiments merely to recover context. Use existing timing evidence; collect pytest durations at the
next authorized full run instead of launching a suite just to estimate its cost.

## Git delivery

The standing commit/push authorization is unchanged for both staged and documentation-only work.
Inspect status/branch/remote, preserve unrelated changes, stage only authorized files/hunks, push
normally and verify the remote SHA. A pushed WORK commit can await review without broad regression
if that deferral is authorized and explicit. A rejected push remains a delivery blocker, not permission
to force-push. Report the exact delivery SHA and URL after successful push.

The tracked handoff records the exact reviewed/tested revision; its own containing commit cannot
embed its own SHA. Supply that delivery SHA in the final GitHub handoff after committing, without
creating a circular sequence of metadata-only commits. Separate task branches/worktrees remain a
future isolation option, not a new required branch/merge policy. No additional framework, dependency,
pytest marker migration or automatic follow-on work is introduced.
