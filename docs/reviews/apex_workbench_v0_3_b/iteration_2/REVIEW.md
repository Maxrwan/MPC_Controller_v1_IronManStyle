# Independent re-review — APEX Workbench V0.3-B, correction iteration 1

**Outcome: FAIL — one residual ordinary catalog defect requires correction and exact-revision re-review.**

Reviewed candidate: `f6a8660f3674ae46a11bd377b807665d765ae00f`, branch
`codex/apex-workbench-v0-3-b`. Review date: 29 October 2026. This is independent Engineering Review,
not formal Verification. The failed `889c808` review remains preserved verbatim under
`docs/reviews/apex_workbench_v0_3_b/iteration_1/`.

## Closure of the original reproductions

- **R1 closed for the reviewed bounded cases.** Genuine qualified BASE/IZ evidence replacement at
  comparison return now yields an invalid display with no overlays or stale qualified label. Additional
  independent replacements after the first, second and third actual plot reads clear the entire result
  container, including earlier plots and the old classification. A replacement inside classification
  is invalidated, and changing a selected disposable Q commit anchor during plotting also clears display.
- **R2 original owned-bridge reproduction closed; related archive conflict remains blocking below.**
  The unsealed owned BASE-ID/IZ-worker bridge leaves all 17 accepted original paths selectable. Exact
  copied aliases plus a bridge preserve all original paths and keys, retain read-only ownership, disclose
  conflicts and continue to inspect the actual originals successfully.
- **R3 closed for the reviewed bounded cases.** Request, manifest, worker and status self-symlinks in
  disposable records no longer abort discovery; their entries remain discoverable and fail inspection.

## Blocking residual R2-A — P2: conflicting archive metadata can still hide a distinct original path

Location: `tools/apex_workbench/run_catalog.py:143-169`, especially shared-token matching at 151-162.
The new loop runs archive candidates before owned candidates, but applies the same weak-identifier
attachment rule to the archive candidates themselves. One archive with corrupt/unverified metadata
can therefore attach to another archive instead of becoming its own source anchor. A conflict caption
on the chosen primary does not make the other source independently selectable.

Concrete reproduction, using only disposable copies:

1. Copy actual BASE and IZ_HIGH into two different source directories under a disposable approved-layout
   `v0_2_reviewed_20261029/runs/` tree.
2. Change only the copied IZ request's `run_id` to BASE's ID. Do not reseal its manifest: this is an
   intentionally corrupt source that must remain discoverable for raw inspection.
3. Supply a discovery-only qualification index naming both paths. Its commit is explicitly unverified;
   no production qualification is applied and no scientific validity is claimed.
4. Call `discover` with that disposable qualification root and an empty owned root.

Observed result: the two source paths become one selectable BASE record; IZ exists only in BASE's
`aliases`, with `Conflicting alias identities; only the selected original source can be verified`.
The invalid IZ evidence cannot be selected or investigated on its own. This is the remaining instance
of the original trust-separation defect: discovery metadata hides a distinct corrupt source before
production validation can quarantine and explain that source. All actual accepted files remain untouched.

Evidence:
`results/apex_workbench_v03b_work_20261029/reviewer_2/test_nearby_cases.py::test_conflicting_unverified_archive_metadata_does_not_hide_distinct_original_path`,
its retained disposable fixture, and `ARCHIVE_METADATA_CONFLICT` plus the failing assertion in
`reviewer_2/independent.log`.

Minimum correction: establish separate anchors for distinct archived source paths when their captured
identities conflict. Do not merge those anchors on a single unverified run/worker/manifest hint. Exact
canonical aliases or consistent exact copies can still be grouped without claiming new executions.
Also ensure selectable keys remain distinct when conflicting source records share a claimed run ID;
currently key material at 181-184 uses that ID alone. Add this archive-conflict regression alongside
existing copy/bridge coverage and re-review the corrected exact revision. No scientific decision or
frozen-backend edit is required.

## Independent execution and preservation

The original independent test file was copied into `reviewer_2`, with only its candidate SHA changed;
its previously corrected `dt_control_s` harness field was preserved. Eleven additional bounded nearby
cases were added as a separate reviewer-owned test file. No implementation source or repository test
was edited.

Command, from repository root:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
MPLCONFIGDIR=results/apex_workbench_v03b_work_20261029/reviewer_2/mpl \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q -s results/apex_workbench_v03b_work_20261029/reviewer_2/test_independent_review.py \
results/apex_workbench_v03b_work_20261029/reviewer_2/test_nearby_cases.py \
--basetemp=results/apex_workbench_v03b_work_20261029/reviewer_2/fixtures \
--junitxml=results/apex_workbench_v03b_work_20261029/reviewer_2/independent.xml \
> results/apex_workbench_v03b_work_20261029/reviewer_2/independent.log 2>&1
```

Result on exact `f6a8660`: **18 passed, 1 failed, zero skips**, 25.06 s. The sole failure is R2-A;
there were no reviewer harness failures in this invocation. These independent counts do not include
the implementation's separate 22-pass correction evidence.

The independently passing checks confirm:

- All 56 required scientific files still match Git blobs at accepted V0.2
  `4897686e79c13757d5ef5b4373b44d4cab99b5bf`, including original `app.py` and `plots.py`.
- Current presentation/test source hashes and launcher hash match the current WORK machine record.
- All 17 actual accepted archive sources inspect successfully without lifecycle/cancel/note writes.
  Full campaign file SHA-256 maps before and after that read-only test are equal.
- The actual Q SHA-256 remains
  `f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`; production consumption
  and all four BASE/treatment candidate/qualified classifications remain applicable. Same-case and
  incompatible treatment pairs remain illustrative.
- Actual yaw data retain native sample values/timestamps and `rad/s` axes; archive lifecycle controls
  remain absent, and missing-state evidence fails closed while retaining raw records.

Final `git status --short` and `git diff --check` were empty; HEAD remained the exact reviewed SHA.
No source writes, workers, trajectory generation, qualification campaign, full repository suite,
formal Verification, new launcher smoke or hardware action occurred. The unrelated user-owned listener
was neither reused nor signaled. Launcher behavior is unchanged by this correction; prior implementation
launcher evidence and the earlier partial independent check remain separately labeled evidence.

## Disposition

The correction substantially closes the original observed failures, but R2-A still violates source-aware
invalid-evidence discovery. Preserve this failed re-review, make the second bounded ordinary correction,
and obtain exact-revision independent Engineering Review before separately authorized formal functional
Verification. No new scientific decision or qualification campaign is needed. Later MVP stages remain
outside this review.

**V0.3-B candidate f6a8660: FAIL. Not yet ready for formal Verification.**
