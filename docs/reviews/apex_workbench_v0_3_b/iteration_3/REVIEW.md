# Final independent Engineering Review — APEX Workbench V0.3-B

**Outcome: PASS for Engineering Review. Ready for separately authorized formal functional Verification.**

Reviewed exact candidate: `ca3ef9605df3472001302dbf70c0e2815c020d1c`, branch
`codex/apex-workbench-v0-3-b`. Review date: 29 October 2026. This closes the reviewed ordinary software
findings after two bounded correction iterations. It does not grant formal Verification, scientific
acceptance, user acceptance or authority for the next MVP stage.

The failed `889c808` and `f6a8660` reviews remain preserved under
`docs/reviews/apex_workbench_v0_3_b/iteration_1/` and `iteration_2/`. Their failures were not removed
or reclassified as passes. This report covers the new exact candidate independently.

## Findings and closure

**No blocking or actionable nonblocking finding remains in the reviewed V0.3-B scope.**

- **R1 closed.** A genuine qualified BASE/IZ decision cannot retain its qualified label/plots after
  the tested valid-to-valid evidence replacement. Replacement at comparison return yields an invalid
  display with no scientific overlays. Replacement after the first, second or third actual plot read
  clears the full result container, including earlier plots and classification. Replacement inside
  classification is invalidated. Changing the selected disposable qualification's commit anchor during
  plotting also clears display. Stable-evidence views still show genuine candidate/qualified results.
- **R2 closed.** The unsealed owned BASE-ID/IZ-worker bridge no longer merges distinct original
  archives. Exact owned copies plus the conflicting bridge preserve all 17 original paths and keys,
  expose the conflict and retain archive read-only ownership.
- **R2-A closed.** The disposable conflicting archive fixture now retains both original source paths,
  gives them different selection keys and quarantines the corrupt source independently. Those keys
  stay stable after changing the corrupt source's claimed run ID and reversing reference-index order.
  An additional exact-copy fixture deduplicates two byte-identical archive copies into one record;
  adding an owned copy and reversing references retains the same primary path/key, three aliases and
  read-only ownership. Copies are not presented as new executions.
- **R3 closed.** Request, manifest, worker and status self-symlinks are contained per disposable record;
  discovery continues and the affected entries fail inspection rather than crashing the workspace.

The final catalog correction is limited to preserving conflicting archive anchors and deriving archive
selection keys from canonical source paths. Other corrected views and the launcher are unchanged from
the preceding reviewed candidate. No frozen scientific dependency, criterion or historical evidence
was changed to obtain these results.

## Independent checks

The preceding 19 independent probes were copied into `reviewer_3`, with the exact candidate SHA updated.
The residual R2-A test gained unique/stable-key assertions. One exact archive-copy deduplication case
was added. The implementation's own 24-pass affected-file result was not treated as independent proof.

Command, from repository root:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
MPLCONFIGDIR=results/apex_workbench_v03b_work_20261029/reviewer_3/mpl \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q -s results/apex_workbench_v03b_work_20261029/reviewer_3/test_independent_review.py \
results/apex_workbench_v03b_work_20261029/reviewer_3/test_nearby_cases.py \
--basetemp=results/apex_workbench_v03b_work_20261029/reviewer_3/fixtures \
--junitxml=results/apex_workbench_v03b_work_20261029/reviewer_3/independent.xml \
> results/apex_workbench_v03b_work_20261029/reviewer_3/independent.log 2>&1
```

Result on exact `ca3ef960`: **20 passed, zero failures/errors/skips**, 24.57 s. No reviewer harness
correction or rerun was required for this invocation. Full logs, JUnit, reviewer scripts and disposable
fixtures are retained separately under `reviewer_3/`; prior failed review evidence remains intact.
Counts from different implementation/review invocations are not combined.

Independent preservation and applicability checks passed:

- All **56** required scientific files match their Git blobs at accepted V0.2
  `4897686e79c13757d5ef5b4373b44d4cab99b5bf`, including original `app.py` and `plots.py`.
- Current presentation/test source hashes and launcher hash match the current WORK machine record.
- All **17** actual accepted archive source runs inspect successfully without lifecycle, cancellation
  or note writes. Full campaign file SHA-256 maps before and after the read-only probe are equal.
- Actual Q SHA-256 remains
  `f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.
  The unchanged production reader accepts Q against current frozen sources. All four actual
  BASE/treatment pairs remain controlled candidates without Q and qualified synthetic comparisons
  with Q; BASE/BASE and IZ_HIGH/CF_HIGH remain illustrative.
- Actual yaw traces preserve native retained values/timestamps and `rad/s` axes. Nonterminal archives
  expose no owned refresh/cancel/annotation controls. Missing-state evidence remains invalid with
  raw diagnostic access. No reference, alignment, interpolation or metric was fabricated by these probes.

Final `git status --short` and `git diff --check` were empty, and HEAD remained
`ca3ef9605df3472001302dbf70c0e2815c020d1c`. The reviewer changed no source, repository tests or docs,
made no commit, and wrote only separate review evidence.

## Limits and next gate

This is bounded independent Engineering Review of presentation/catalog behavior. No new worker
simulation, launcher smoke, trajectory generation, qualification campaign, full repository suite,
formal Verification, hardware action or physical inference occurred. The user-owned listener was
neither reused nor signaled. The unchanged launcher's earlier full implementation evidence and partial
independent check remain separately identified evidence; this report does not claim a new complete
launcher run. Earlier full-directory and affected-file test counts retain their own source provenance.

The existing product limits remain explicit: two-run comparison, raw native time, approved local run
roots, view-only archive notes, absent channels labeled unavailable, and no new controller, replay,
physical telemetry or Safety command path. The fault probes establish the tested fail-closed software
behavior; they do not constitute physical validation or a general concurrency/real-time guarantee.

No unresolved scientific decision was identified. The exact candidate is ready for the separately
authorized formal functional Verification gate, including its applicable regression, execution/legacy
compatibility and launcher acceptance requirements. Do not repeat the numerical qualification campaign
merely for this presentation change. Any subsequent implementation change needs an applicability
assessment and exact-revision review as required by the repository workflow.

**V0.3_B_ENGINEERING_REVIEW_COMPLETE_PENDING_VERIFICATION — PASS on ca3ef960.**
