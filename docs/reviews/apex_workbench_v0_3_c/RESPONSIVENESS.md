# V0.3-C responsiveness correction and formal Verification

**PASS — V0.3_C_VERIFIED_PENDING_USER_ACCEPTANCE_AND_SCENARIO_DECISION.** 30 October 2026. Base delivery `ad69feadc126448a025f1204cc9ee9dd7307f864`;
reviewed starting source `8cff10bca8475f0992221d2cebf8862414210056`. Exact reviewed correction `34f98a4894e457900d2fae3b2fd09ead4f5ba5a0`
pins the candidate. Branch `codex/apex-workbench-v0-3-c`. Independent review satisfied the user's
condition. One complete formal invocation and the required
acceptance audits passed; final user acceptance and scenario decisions remain pending.

## Measured diagnosis and correction

The original [N1 review](iteration_2/REVIEW.md), failed 45/60 s AppTest attempts and 89.886 s render
remain unchanged. A fresh bounded baseline did **not** reproduce that historical outlier. It identifies
repeatable application costs, not a proven unique cause of the old spike. In a process-cold two-run
Q selection, 2.943 s total included 2.903 s in the workspace script and 0.040 s outside it. The accepted
qualification consumer ran twice (1.353 s inclusive, 36 source bindings); 38 verified frame reads,
3,528 artifact reads and 3,698 manifest reads occurred. These are nested counts/times, not sums.
A three-run exact seek triggered two full comparison operations, six pair decisions and eight complete
Q consumptions; total 9.903 s, 9.862 s inside the script. Discovery, snapshot/currentness, qualification,
plot/serialization and wrapper costs are individually recorded in the raw profile.

The correction reuses already-verified native frames **only within the current presentation operation**
for plots. The frozen plot style and literal data/reference/geometry payloads are preserved by parity
tests. It uses widget callbacks for seek/step and changes the replay timer before costly reads, avoiding
the extra seek rerun. Secondary Compare configuration/provenance loads are explicitly on demand.
No persistent cache, memoized qualification decision, checksum bypass, reader modification, scientific
threshold change or hidden telemetry interpolation is introduced. All existing epoch and artifact
currentness checks remain; late corruption/replacement still clears plots and labels. The existing
late-plot regression injects replacement at the new snapshot-figure construction boundary; its scientific
assertions and all original 45/60 s defaults/assertion bodies are unchanged.

Same instrumentation/environment and original deadlines; fresh processes, OS cache uncontrolled:

| Interaction | Before [s] | Final correction [s] |
|---|---:|---:|
| two_Q_cold | 2.943 | 2.427 |
| two_Q_warm | 2.878 | 2.349 |
| three_Q | 5.480 | 4.703 |
| three_seek_0125 | 9.902 | 4.869 |

“Cold” means first selected Q in the process, after imports/candidate setup; “warm” repeats the same
selection/evidence. These are bounded observations, not a percentile, physical guarantee or hard
performance threshold. The 10 s investigation target is not installed as a scientific criterion.
Frozen full Q validation remains the largest necessary cost; pair count still increases its work.

An actual browser session used the unchanged default launcher from an unrelated cwd. First/repeat
Q selection reached the newly qualified heading in 1.259/1.351 s; three-run seek reached native sample
25 at 0.125 s in 4.817 s. These include browser/protocol/polling and end at those visible signals,
not full server-only duration. The same original BASE/IZ/CF IDs, stored XY and qualified/illustrative
context were observed. The default narrow viewport was retained. Browser locator/popup mistakes
and premature waits are recorded separately from application behavior. Owned startup/reuse/shutdown
passed; no experiment was submitted and no user server was stopped.

## Focused evidence and preservation

Fresh `focused-1`: **52 passed**, zero failures/skips/errors, 60.02 s. This precedes only the final
on-demand detail toggle. After that final UI change, the original two timeout tests plus its direct
caller check passed separately: **3 passed**, 13.45 s. No deadline was raised. The independent review
must evaluate the exact candidate; these counts are never combined into an unexecuted suite result.
Tests cover native plot parity, one comparison operation per seek, actual samples/units/labels,
read-only replay, late missing/changed bytes, valid evidence replacement, metadata containment and
original workflows. No mathematical assertion was weakened. Ruff lint/format and whitespace pass.

All 56 accepted scientific dependencies, the launcher, original qualification bytes and both racing
design documents remain unchanged. Before/after hashes and historical metadata preservation are in
[the machine record](responsiveness_record.json). Fresh local raw evidence:
`results/apex_workbench_v03c_n1_20261030/` (profile scripts/JSON/logs, JUnit, browser DOM/screenshot,
environment and preservation). No 17-trajectory campaign, new geometry/profile/adapter, CT, frozen
research or hardware work ran. Existing approved simulations occur only in bounded software tests.

## Independent gate and conditional formal Verification

[Independent review](responsiveness/iteration_1/REVIEW.md): **PASS** at exact `34f98a4894e457900d2fae3b2fd09ead4f5ba5a0`.
Fresh unchanged-deadline selection: **53 passed**, 63.98 s. Separate independent cold/warm Q:
1.215/1.167 s; three seek 2.446 s; four-Q/seek 3.740/3.822 s. No material responsiveness finding
remains within the bounded gate. The historical 89.886 s cause remains unexplained; no tail/real-time
guarantee follows. Independent negative probes and 79 channel/3 XY payload comparisons support PASS.
One reviewer probe mistakenly assumed optional legacy controls existed; its 10-pass/1-harness-failure
result remains failed, with a separate corrected payload-only pass. Counts are never combined.

The user-authorized conditional full Verification ran once after that exact-source PASS.
Tested documentation-only checkout `d603575d5c399d261c458288f5efef8079353ccb` has identical behavioral sources,
tests and launcher to the reviewed source. This final delivery changes documentation only.

## Formal functional Verification

One fresh complete `tests/` + `tools/apex_workbench/tests/` invocation: **1,069 passed, 17 skipped,
zero failures/errors**, exit 0, **735.12 s** (pytest). Split: 777 repository + 292 Workbench passes.
All 17 skips are `tests/integration/test_profile1_parity.py:55`, requiring separate G2 authorization,
reviewed revision/allowance and pristine B0 root. Gate variables were absent; no frozen campaign ran.
No complete-suite retry or source/test change occurred. This count includes no WORK/reviewer passes.

The approved macOS 26.5.1 arm64/Python 3.12.14 environment and all 12 recorded package versions
match the reference. Fresh-process Accelerate API reports SINGLE before numerical imports, with
six native ceilings set to one; exact active native thread count is unavailable. Preflight had no
measurement guards, active workers or Streamlit servers. Exact argv, environment and checkout,
JUnit, logs, source hashes and accepted skip reasons are in the machine record and
`results/apex_workbench_v03c_n1_20261030/formal/`. Full-suite command uses the documented SINGLE
bootstrap, `-q -x tests tools/apex_workbench/tests`, fresh `--basetemp`, `--junitxml` and durations;
the exact unabridged argv is retained in `suite-command.json`. It reached 100%; `-x` omitted nothing.

| Acceptance | Formal evidence / outcome |
|---|---|
| Original V0.1 dynamic/LQR and V0.2 canonical runner | PASS: fresh original CLI/function/owned-worker byte parity, actual approved nominal worker and independent canonical-runner tests |
| V0.3-B navigation/run/reopen/notes/archives | PASS: full retained UI, read-only/alias/unique identity, append-only note, cancellation/lifecycle/SIGKILL and evidence regressions |
| Native inspection/replay and invalid data | PASS: exact .125 samples, onset/terminal/partial/multirate meaning, no interpolation or inferred commands, malformed metadata containment and late valid/corrupt/missing evidence clear displays |
| Pairwise two-to-four-run comparison | PASS: original UI candidate/qualified tests; fresh production audit of four accepted pairs and six four-run edges (three qualified BASE / three illustrative treatment edges). Four-run UI also retains exact-source independent evidence, not recounted as a fresh browser run |
| Actual automatic browser replay | PASS: original canonical-reference archive sample 19/.095 paused → sample 28/.140 playing automatically → paused at 28/.140, stable over 17.071 s. No scientific execution or mutation command. DOM/screenshot retained |
| Production retained qualification | PASS: original 17 execution references and accepted calculation unchanged; all four conditional BASE/treatment pairs, manifest/source/environment checks; four disposable checksum/missing/source/environment faults reject. No trajectory rerun or record publication |
| Launcher / legacy compatibility | PASS: actual default 8501 launcher from unrelated cwd, correct workspace listener/loopback/browser opener, second-click reuse, owned interrupt shutdown; occupied port and missing-env errors; legacy app serves and is refused takeover |
| Source/evidence preservation and cleanup | PASS: all 56 accepted Git blobs, all 345 original Q-file hashes, both scenario documents and historical result stats/symlinks unchanged. All 425 reviewed behavioral hashes and 98 original review evidence hashes pass; no owned workers/servers remain, lease released and 8501 free |

The original qualification hash remains `f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.
The source/evidence audit spans 987 initial tracked files (only authorized changes), 44,303 old result
size/mtime entries and 1,382 symlink targets. This is not a full-content rehash of all historical
results. Original failed review/timeout logs remain retained; independent reports are unedited.
Existing approved scientific simulations ran only as functional-test fixtures; no new qualification,
racing, Performance/CT/frozen research or hardware campaign was launched.

## Limitations and acceptance recommendation

Observed reference interactions are in seconds; no percentile, broad-host scaling, hard real-time,
physical validity or hardware claim follows. Full Q validation remains necessary and scales with
qualifying pairs within the fixed four-run bound. The historical 89.886 s outlier's unique cause is
still unknown; it is preserved rather than explained speculatively. All final original-deadline,
independent gate and full-suite checks passed. No material responsiveness or blocking functional
finding remains in this bounded Verification scope.

**Recommend user acceptance of corrected V0.3-C for the verified local engineering/accepted finite
synthetic scope.** Acceptance itself is not recorded. The unchanged S1/S2/S3 racing decisions remain
for Primary; no new scenario, controller adapter, CT or hardware work follows automatically.

**Stop: V0.3_C_VERIFIED_PENDING_USER_ACCEPTANCE_AND_SCENARIO_DECISION.**
