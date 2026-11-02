# Independent C0 adapter Engineering Re-review — iteration 2

**Outcome: PASS for exact correction candidate `d246f1e9639737e4ecbbd12f8bd0c9b2f1574712`.**
2 November 2026; branch `codex/apex-workbench-c0-descriptive-adapter`. This independent reviewer
did not author or amend either candidate. One of two authorized routine correction iterations
has been used. **G1 remains OPEN; descriptive_only / source_unverified.**

## R1 closure

The [iteration-1 BLOCKED review](../iteration_1/REVIEW.md) remains unchanged in
`f60c523af69aed920e25a578ae94dbd34b3db11c`. Its native output finding is **closed**:

| Controlled surface | Independently observed corrected behavior |
|---|---|
| Live Plotly image/cloud controls | Actual AppTest protobuf sets `displayModeBar=false`, removes `toImage`, and sets `displaylogo=false` / `showSendToCloud=false`. The installed frontend passes this configuration to Plotly; no separate wrapper download action was found. |
| Nested standalone HTML image control | The actual generated `Plotly.newPlot` invocation contains the same disabled configuration, plus `responsive=true`; the check targets the invocation rather than bundled defaults. |
| CSV / clipboard component controls | Actual C0 output contains three static tables and plain text, with zero dataframe, code or JSON components before and after HTML preparation. Installed static-table rendering has no download/clipboard handlers. |
| Governed output | No download exists initially. Explicit preparation supplies exactly one metadata-bearing HTML download. Ordinary browser text selection is outside the controlled-output scope. |

Plain-text display boundaries preserve the **complete original decoded JSON including outer
whitespace**. Independent row inspection retains signed `-0.0`, the extended readiness token
`0.41500000000000004`, original control keys, present-null acceptance and absent startup validity.
The chronology retains separate busy-skip/fallback rows at the same literal `0.4` time. Provenance,
source hash, full banner, G1 and uncertainty limitations remain visible; the HTML retains the
complete original raw content and required metadata. No scientific or causal promotion was added.

Disposable evidence changed during static-table publication and download preparation was
quarantined, clearing all scoped figures, tables, labels, raw/provenance text and downloads.
The native-output correction preserves the existing currentness boundaries. No new material
issue was found in the bounded changed-surface inspection.

## Independent evidence and applicability

A fresh independent probe completed **4 checks**, covering actual widget/configuration output,
exact text/literal rows, both late-change paths and the serialized HTML configuration. A separate
focused invocation passed **8 tests, 0 failures/errors/skips**, JUnit 6.168 s: native-action guards,
actual C0 navigation, literal HTML preservation, export currentness, late-render/download
quarantine, and C0-to-P navigation. No `lab_runs` fixture or worker was invoked.
Commands, node IDs, source/environment hashes, complete logs and the frontend inspection evidence
are in [review_record.json](review_record.json) and the fresh ignored directory
`results/apex_workbench_c0_adapter_review2_20261102/`. Native browser downloads and clipboard
operations were not invoked; this review assesses their removed controlled actions using actual
payloads and installed rendering code.

Earlier independent reader/admission/shape/token/path/currentness findings remain applicable:
`c0_archive.py`, `c0_shape.json`, `workspace.py`, the original archive and contract/authority
identities are unchanged from `7f78df15470c99968ebd9ca473080a8822d81da7`. Those broad audits were
not rerun. The correction diff contains only C0 presentation/tests and supporting documentation;
no scientific/worker/producer path, model or dependency changed. The author's 69-pass correction
run and prior 24 compatibility passes are supplementary historical evidence, not this review's
fresh independent counts. The author's first 68-pass/1-failure correction attempt is preserved;
its actual text-trimming problem was corrected with display boundaries without weakening the
exact-content assertion. Neither failed reviews nor failed logs were amended.

Fresh before/after hashes found **zero changes in 1,412 selected tracked/protected files** during
this review. Exact original identity is 152,600 bytes, SHA-256
`2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5`.
The original blocked review/record match `f60c523…` byte-for-byte. Reviewed runtime/test contents
match Git candidate `d246f1e…`; preserved selections include the retained scientific, qualification,
P/legacy evidence and approved contracts. Reviewer writes are limited to this new report/record
and ignored reviewer evidence. No source, test, contract, handoff or branch edit; no commit/push.

## Stop

**C0_DESCRIPTIVE_ADAPTER_ENGINEERING_REVIEW_COMPLETE_PENDING_VERIFICATION.** PASS is Engineering
Review of this exact bounded adapter, not formal Verification, scientific acceptance or G1
closure. No full regression, producer/simulation/controller execution, numerical experiment,
qualification campaign, RBT/CT/Safety or hardware activity ran. Separate explicit authorization
is required for formal Verification or any later phase; no automatic merge or next task.
