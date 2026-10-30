# V0.3-C responsiveness correction and conditional Verification

**WORK_COMPLETE_PENDING_REVIEW.** 30 October 2026. Base delivery `ad69feadc126448a025f1204cc9ee9dd7307f864`;
reviewed starting source `8cff10bca8475f0992221d2cebf8862414210056`. The containing correction commit
pins the candidate. Branch `codex/apex-workbench-v0-3-c`. No formal full suite has run at this point.
The new task authorizes it only after independent exact-revision PASS with no material response issue.

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

Next: commit exact candidate and obtain independent-context review. Formal Verification remains
conditional on PASS without an unresolved material responsiveness issue, then one complete applicable
suite and the required launcher/retained-evidence acceptance checks. Primary scenario decisions and
final user acceptance remain separate; no new scenario work is authorized.
