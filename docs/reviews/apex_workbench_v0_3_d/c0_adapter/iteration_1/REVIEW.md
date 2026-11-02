# Independent C0 adapter Engineering Review — iteration 1

**Outcome: BLOCKED — R1 requires a bounded presentation correction.**
Reviewed candidate: `7f78df15470c99968ebd9ca473080a8822d81da7`, branch
`codex/apex-workbench-c0-descriptive-adapter`. Inspection and focused checks: 31 October 2026;
clipboard assessment and finalization after interruption: 2 November 2026. Candidate stayed unchanged.
This reviewer did not author or amend the implementation. **G1 remains OPEN.**

## R1 — native download/copy actions bypass the governed output path

**Priority: P1; blocking contract compliance.** In
[the new C0 presentation](../../../../../tools/apex_workbench/c0_panels.py), line 131 supplies no
Plotly configuration; line 98 likewise leaves the standalone HTML chart's modebar at defaults.
Lines 136, 138 and 144 use `st.dataframe`; lines 127 and 162 use `st.json` and `st.code`.
These provide application-supplied client output actions in addition to the checked HTML download:

- Actual AppTest chart protobuf has `config = {}`. The installed Plotly bundle adds `toImage` by
  default. The standalone report's actual `Plotly.newPlot` call has only `{"responsive": true}`.
  The resulting image contains the shortened descriptive/source-unverified plot title, but omits
  G1, the full required banner, preservation identity and authoritative hover tokens/pointers.
- The installed Streamlit dataframe frontend defaults `disableDataExport` to false and enables
  **Download as CSV** for these bounded tables. Actual payloads contain 42 chronology rows,
  29 missingness rows and 16 selected raw-field rows. Their columns contain pointers/literals
  and presence, but no classification, G1 or original SHA. The frontend serializes/downloads the
  table directly through its file-picker/Blob path.
- The new raw JSON `st.code` surface has a native clipboard button. Its frontend sends the code
  text directly to the shared clipboard handler. `st.json` enables copying individual JSON
  subtrees using `JSON.stringify(e.src)`; a subtree can omit the enclosing provenance context.
  These handlers call `navigator.clipboard.writeText` without a server rerun/currentness check.

The live native actions do not call `snapshot.current()` and can publish the already supplied
payload after evidence changes, without triggering the scoped quarantine path. The explicit HTML
preparation path does recheck evidence correctly. An offline HTML report is a checked snapshot;
the issue with its nested PNG action is loss of required context, not a demand for an offline file
to monitor the repository. This finding concerns controlled UI actions, not ordinary browser text
selection or a claim to prevent all copying.

This conflicts with binding contract sections 2, 3, 6 and 7: inherited classification/G1 and exact
source-token identity across exports/copied summaries, source-linked output, and fail-closed
publication/export boundaries. Passing the existing software tests does not cover these native
frontend actions.

**Minimum routine correction:** remove native bare export/copy controls from the new C0 surfaces.
Disable Plotly image exports in both live and HTML charts; use readable static tables/plain text
for the bounded row, provenance and raw-JSON views, or another scoped surface without automatic
bare downloads/copy actions. Keep the checked, metadata-bearing HTML path. Add focused assertions
on actual widget/configuration and serialized HTML output so these controls cannot return. No
scientific/descriptive contract, reader admission, controller or worker change is needed.

Exact reproduction payloads, installed-frontend handler snippets/hashes and source references are
retained in `results/apex_workbench_c0_adapter_review_20261031/plotly_export_reproduction.json`,
`clipboard_code_route.json`, `clipboard_button_route.json` and
`clipboard_source_inspection_2.json`. `independent_checks_3.py` and its complete log record the
successful live-config/table/HTML reproduction. Native browser download delivery and clipboard
invocation were not exercised; enabled behavior is established by actual AppTest payloads and the
installed frontend code. A later clipboard diagnostic failed its strict byte-equality assertion;
its partial log is retained and is not used as proof of exact copied bytes.

## Independent checks and preservation

The independent retained-byte parser compared **all 4,034 numeric lexemes**, integer/real forms,
318 objects, 86 arrays and 13 nulls. It independently regenerated the complete contemporary
per-index shape/nested dimensions. Original control keys, independent endpoint coverage, all
29 row missingness entries, and 42 literal chronology fields matched without inferred cross-stream
ordering or physical/causal interpretation.

Disposable same-size alterations at the original and all five contract/review/shape anchors were
rejected by fresh and currentness checks. File/ancestor/root symlinks, traversal, absolute paths,
missing files, directories and oversize evidence were withheld. A late review-anchor replacement
cleared scoped plots, labels, tables and download controls. Reader imports are standard-library
only; actual navigation under prohibited lifecycle-call sentinels called no worker and introduced
no C0 comparison candidate. Descriptive/source-unverified/G1 labels and reference limitations were
present. Only R1 was found blocking in this bounded inspection.

The reviewer separately ran the candidate's two new focused test files: **67 passed, 0 failed,
0 errors, 0 skipped**, JUnit 6.993 s. The review's independent checks comprise **11 completed
checks plus the reproduced R1 finding**, not a scientific acceptance suite. Commands, exact
source hashes, environment, logs and failed harness attempts are in [review_record.json](review_record.json)
and the fresh ignored evidence directory. Earlier author results were not treated as independent
proof; the author's separate 24 compatibility passes were not rerun or relabeled as fresh evidence.

Fresh before/after hashing found zero changes among **1,410 selected tracked/protected files**;
1,398 applicable files from the 1,401-path base selection match, excluding its three explicitly
authorized presentation/documentation modifications. All 56 scientific source hashes were also
rechecked against the prior verification record. The exact original fixture, approved contract,
Section A evidence, prior failed reviews, retained qualification/P/legacy evidence and implementation
remain preserved. Preservation selection was reused; hashes were freshly computed. Reviewer files
are only this report/record and ignored reviewer evidence; no implementation, test, contract or
handoff edits, branch changes, commit or push occurred.

Two earlier independent-check harness attempts failed on overbroad string searches (a run UUID
containing `c0`, then bundled Plotly source containing the searched configuration name). Corrected
review scripts and all failed scripts/logs remain retained; no implementation was changed to make
a check pass. The later clipboard diagnostic partial is also retained.

## Stop

**BLOCKED_PENDING_BOUNDED_PRESENTATION_CORRECTION.** Parent may use the already authorized routine
correction allowance, then obtain independent review of the exact corrected revision. This report
does not authorize another phase. No producer, simulation, controller, numerical experiment,
qualification campaign, full regression/formal Verification, RBT/CT/Safety or hardware activity ran.
No historical execution/provenance, optimizer performance, causality, recovery, physical or Safety
qualification is established. **G1 OPEN; descriptive_only / source_unverified remains mandatory.**
