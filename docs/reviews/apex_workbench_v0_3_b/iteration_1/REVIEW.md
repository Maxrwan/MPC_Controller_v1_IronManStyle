# Independent Engineering Review — APEX Workbench V0.3-B

**Outcome: FAIL — bounded ordinary software corrections and exact-revision re-review required.**

Reviewed candidate: `889c8084f7632d5f343cd7f0865a3931c3e7e933`, branch
`codex/apex-workbench-v0-3-b`. Accepted design basis:
`03055a183be0f5d3691714103588d5b263748128`. Review date: 29 October 2026.
This is independent Engineering Review, not formal Verification or scientific/user acceptance.

## Scope and method

I read the authorized task, repository workflow, accepted V0.3-A design and acceptance scenarios,
the exact candidate diff, new catalog/views/workspace/tests, launcher and WORK records, and relevant
unchanged storage, lifecycle, comparison, plotting, source-inventory and qualification readers.
I examined behavior independently rather than adopting the implementation's test counts as review results.

All source files remained unchanged. Review scripts, disposable fault fixtures and logs are under
`results/apex_workbench_v03b_work_20261029/reviewer_1/`. No source correction, commit, qualification
campaign, worker simulation, full repository suite, controller experiment or hardware activity occurred.
The tests consumed actual retained Q data read-only. Disposable copies were explicitly fault fixtures,
not new scientific executions. Existing qualification evaluation only consumed retained evidence.

## Blocking findings

### R1 — P1: qualified classification can survive replacement of the evidence it describes

Location: `tools/apex_workbench/workspace.py:344-372`, particularly the second inspection at
354-357 and later path-based plotting at 372; `show_channels` also rereads paths at 91-98.

`views.compare` returns a classification for one evidence epoch. The workspace then inspects both
paths again, tests only `item.valid`, and renders the earlier label and decision with the newly
read data. A changed record may remain individually valid while no longer qualifying for the
previous comparison. The final UI guard covers corruption, but does not bind the decision to the
status/manifest/request identity being plotted.

Concrete reproduction: copy actual accepted BASE and IZ_HIGH into a disposable owned root, with
archive discovery disabled so those copies are the selected paths. Invoke the genuine accepted
comparison reader with the actual Q record; it returns `qualified_synthetic_comparison`. At the
comparison-return boundary, replace only the disposable IZ directory with an intact copy of BASE.
No accepted file is altered or resealed. The two subsequent inspections pass. AppTest shows
`Qualified Synthetic Comparison`, three scientific plots, and no error/exception, while a fresh
accepted comparison of the displayed paths returns `illustrative` for BASE versus BASE.
The test wrapper selects the real Q for the genuine classification call and injects only the
controlled replacement timing; it does not fabricate a classification or plot.

Evidence: `test_independent_review.py::test_valid_epoch_swap_must_withhold_stale_qualification`,
`independent.log` line 37 and the retained failing assertion. Observed record:
`shown_label=["Compare two retained runs", "Qualified Synthetic Comparison"]`,
`actual_current_classification="illustrative"`, `chart_count=3`, `errors=[]`, `exceptions=[]`.

Minimum correction: bind the decision and all presentation reads to stable status/manifest identities;
withhold both the classification and scientific overlays when those identities change. Render data
from the checked snapshot, or guard the later path reads as well. Checking validity alone is insufficient.
Add a literal valid-to-valid epoch-replacement regression, then re-review the corrected SHA.

### R2 — P2: one unverified identity bridge hides a distinct original accepted execution

Location: `tools/apex_workbench/run_catalog.py:95-99,143-166`.

Discovery treats any shared run ID, worker PID/birth or manifest digest as a transitive union edge.
An unsealed, invalid owned record can combine identifiers from two unrelated original runs and merge
both archive records into one group. Reporting a conflict after the union does not preserve access
to both distinct originals: only one primary directory becomes selectable.

Concrete reproduction: under a disposable owned root, write `request.json` containing only BASE's
`run_id`; write IZ_HIGH's original `worker.json`; write `status.json` with `state="failed"`.
Provide no artifact manifest or scientific record. Discover this root plus the real unchanged Q.
The catalog falls from 17 original runs to 16 records. BASE remains selectable; the distinct original
IZ_HIGH directory disappears from `Catalog.runs`, appearing only as an alias of BASE alongside the
invalid bridge. This defeats direct BASE/IZ inspection/comparison even though both originals remain valid.

Evidence: `test_independent_review.py::test_unverified_identity_bridge_must_not_merge_distinct_originals`,
`independent.log` line 35 and retained fixtures. Observed record:
`before=17`, `after=16`, `base_visible=true`, `iz_visible=false`.

Minimum correction: preserve distinct original execution anchors and attach ambiguous aliases without
allowing their conflicting weak identifiers to union those originals. Keep the conflict/invalid record
inspectable and prevent it from propagating identifiers into another group. Preserve ordinary exact
copy/canonical-path deduplication and stable selection keys. Add this unsealed bridge regression.

### R3 — P2: cyclic metadata symlink crashes discovery for the entire workspace

Location: `tools/apex_workbench/run_catalog.py:17-20,65-72`; analogous manifest resolution at 89-94.

On the approved Python 3.12 environment, `Path.resolve()` raises `RuntimeError` for a symlink loop.
The candidate catches only `OSError` and `ValueError`, so one corrupt record aborts `discover()`;
the workspace calls discovery before creating its navigation.

Concrete reproduction: create one disposable direct owned directory with
`request.json -> request.json`, a normal failed `status.json` and an empty `worker.json`.
Calling `discover(owned_root=..., qualification_root=<empty>)` raises
`RuntimeError: Symlink loop from .../request.json`. Other valid records and even the Run page are
then inaccessible until the corrupt entry is removed externally.

Evidence: `test_independent_review.py::test_cyclic_metadata_symlink_is_quarantined_instead_of_crashing_catalog`
and its complete traceback in `independent.log`.

Minimum correction: contain path-resolution failures per discovered record/metadata file, expose a
quarantine/discovery issue and continue catalog construction. Cover request and manifest cycles in
focused disposable tests. No frozen backend change is needed.

## Confirmed behavior and preservation

- Independently compared all 56 required files byte-for-byte against Git blobs at accepted V0.2
  `4897686e79c13757d5ef5b4373b44d4cab99b5bf`. All matched, including `app.py` and `plots.py`.
  New presentation/test hashes and launcher hash match the candidate's machine record.
- Independently discovered and inspected all 17 actual accepted Q source paths without lifecycle,
  cancellation or annotation calls. Full before/after SHA-256 maps of files under the accepted
  campaign remained equal in the successful corrected read-only probe.
- Actual Q SHA-256 remains
  `f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.
  The production reader accepts it against the unchanged current 56-source inventory. Each of the
  four actual BASE/treatment pairs is a controlled candidate without selected Q and qualified synthetic
  with Q. IZ_HIGH/CF_HIGH and BASE/BASE remain illustrative in the accepted reader.
- Actual BASE/IZ yaw traces preserve retained sample values/timestamps and `rad/s` axes. No reference,
  interpolation or new metric was synthesized by the independent probe. Actual UI candidate/qualified
  labels and genuine plot data work in the stable-evidence case.
- A disposable nonterminal archive remains read-only in the UI, offers no owned refresh/cancel/note
  controls and emits no scientific plots; its bytes remain unchanged. A missing-state fixture fails
  inspection and retains raw diagnostic access.
- Launcher diff changes only the two intended application-path occurrences. Matching both startup
  and listener identity to `workspace.py` preserves the prior ownership design statically.

## Independent execution record

Main bootstrap, from repository root:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
MPLCONFIGDIR=results/apex_workbench_v03b_work_20261029/reviewer_1/mpl \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q -s results/apex_workbench_v03b_work_20261029/reviewer_1/test_independent_review.py \
--basetemp=results/apex_workbench_v03b_work_20261029/reviewer_1/independent-fixtures \
--junitxml=results/apex_workbench_v03b_work_20261029/reviewer_1/independent.xml \
> results/apex_workbench_v03b_work_20261029/reviewer_1/independent.log 2>&1
```

Initial invocation: **4 passed, 4 failed**, 13.02 s. Three failures are R1-R3. The fourth was a
reviewer harness field typo (`dt_s` instead of the recorded `dt_control_s`), not a candidate defect.
The initial script/log/XML remain preserved. After correcting only that reviewer field, the single
previously blocked read-only test was rerun with the same bootstrap, its exact node ID,
`--basetemp=.../read-only-fixtures`, `--junitxml=.../read-only.xml`, and output `read-only.log`:
**1 passed**, 2.78 s. Thus the eight distinct review probes have **five confirmed passing behaviors
and three reproducible product failures**; no claim is made that a fresh combined eight-case run passed.

Independent launcher script command used the same native thread environment and approved Python:

```sh
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u \
results/apex_workbench_v03b_work_20261029/reviewer_1/launcher_review.py \
> results/apex_workbench_v03b_work_20261029/reviewer_1/launcher_review.log 2>&1
```

Host permission was used for psutil/lsof. The exact executable started from an unrelated temporary
working directory, served loopback HTTP, launched the correct primary script, and a second invocation
reported reuse of the same observed listener. Interrupt stopped the review-owned server; its log
records shutdown and an immediate listener check returned none. The following bind probe failed,
so the script did not complete its remaining conflict/legacy checks or write a passing machine record.
The first interpretation was TCP TIME_WAIT; subsequent host inspection established a separate
workspace launcher/server on port 8501 (PID 22700, parent launcher CWD `/Users/marwansaber`, distinct
from the review's unique temporary CWD). That server was preserved and never signaled. A corrected
probe invocation also stopped at the occupied port. Both failures remain retained. Independent
launcher coverage is therefore **partial**, not a complete pass and not evidence of a launcher defect.
The implementation's separate full launcher evidence was inspected, but its passes are not counted as
independent executions. No further launcher attempts are needed in this failed review iteration.

Final source check: exact HEAD remained `889c8084f7632d5f343cd7f0865a3931c3e7e933`;
`git status --short` and `git diff --check` returned no source changes/errors.
Implementation counts (254 prior directory cases, then 17 final new-view cases) remain implementation
evidence only; these are separate invocations and were not added to the independent counts.

## Disposition

R1-R3 are ordinary presentation/catalog software corrections within the authorized V0.3-B scope.
They do not require new controller equations, scientific criteria, a source-inventory change or a new
qualification campaign. Preserve this failed candidate/review, correct the new modules with literal
regressions and request fresh exact-revision Engineering Review. No unresolved scientific decision
was identified. Formal Verification and the next MVP stage remain unexecuted and unauthorized here.

**V0.3-B candidate 889c808: FAIL. Stop before formal Verification.**
