# V0.3-B — Engineering Workspace & Run Inspection

**WORK_COMPLETE_PENDING_REVIEW.** Recorded 29 October 2026. Branch
`codex/apex-workbench-v0-3-b`, from accepted design `03055a183be0f5d3691714103588d5b263748128`.
Exact candidate SHA is recorded by the subsequent independent review; the containing commit binds
these tested files. This WORK report does not grant formal Verification or user acceptance.

## Delivered behavior

`workspace.py` is the primary Streamlit Home / Run / Inspect / Compare entrypoint. It displays
actual supported modes, explicitly unavailable capabilities, adapter/outcome filters and unverified
catalog metadata. Existing worker admission, nominal lab resolution, defaults, validation, ownership,
limits and cancellation are reused. Engineering run notes and append-only observations are optional.
The launcher changes only its two application-path occurrences to the workspace; `app.py` remains
an unchanged compatibility entrypoint, documented on port 8502.

`run_catalog.py` discovers direct owned directories and the accepted qualification's original
17 source-run paths. It does not import arbitrary folders, copy/reseal records, or grant trust.
Canonical paths and captured run/worker/manifest identities group aliases. Conflicts are disclosed;
owned ambiguous records are withheld from lifecycle controls. Original qualification sources remain
independently verifiable even if an owned alias conflicts. Archive origins are always read-only,
including when the same canonical path is also discovered under an owned root.

`engineering_views.py` uses frozen storage, lab, comparison, qualification and plot readers.
It verifies required artifacts and every manifest-listed artifact before scientific display.
Inspection exposes actual configuration, resolved parameters, outcomes, coverage/native rows, source
and numerical provenance, summary fields, telemetry contracts, stored XY/track, states, controls and
diagnostics. Recorded references appear only when present; unavailable channels stay unavailable.
Units come from existing contracts; undeclared channels are explicitly labeled. Each selected
channel has its own axis. Plots retain native time without alignment or new metric calculations.

Two selected records use accepted classification and applicability rules. The pure lab reader is
called directly for archives, avoiding the legacy comparison wrapper's lifecycle reconciliation.
Mixed archive/owned overlays retain the existing cross-adapter illustrative rule and verify the
legacy fingerprint. Invalid evidence has raw diagnostic access and no scientific plots. A changed
record between classification and display withholds the overlay. The verified ZIP preserves original
manifest-listed bytes and committed status/manifest anchors; changed anchors abort export. Notes
remain append-only for owned runs, view-only for archives. No archive reconciliation/cancel/write
controls are attached.

## Demonstrated workflows

| Requirement | Fresh evidence |
|---|---|
| A — find accepted BASE | AppTest discovers the original qualification path; verified configuration/101 state rows/100 control rows, source identity, XY, state/control/diagnostic plots and absent-reference labeling |
| B — BASE / IZ_HIGH | Actual archive pair is `controlled_candidate` without selected qualification and `qualified_synthetic_comparison` with the accepted record; actual yaw and diagnostic channels display |
| C — accepted execution | One nominal BASE request through the workspace/original worker, completed retained evidence reopened, new presentation hashes captured; ordinary test smoke, no qualification authority |
| D — investigate invalid evidence | Disposable missing-state/corrupt metadata/active-archive fixtures retain raw records; scientific display/export/classification fails closed |
| E — compatibility | Both original V0.1 entry-point/owned-worker checks, V0.2 independent canonical-runner parity and legacy UI tests pass; primary legacy-mode forms retain accepted defaults; original app serves HTTP separately |

No 17-trajectory campaign ran. The focused suite contains its preexisting small software-test
refinement fixture, which remains explicitly ineligible for numerical qualification. No CT,
Efficiency, Safety, NMPC/TVLQR/async execution, hardware, replay or multi-run feature was added.

## Focused checks and retained evidence

Local evidence root: `results/apex_workbench_v03b_work_20261029/`. It is ignored and is not staged.
The [machine record](work_record.json) binds log/script/content hashes, versions and exact commands.
Tests use fresh output roots. Numerical workers remain serialized under the original lease.

- The initial 15-test file stopped at one Streamlit magic-rendering error after 11 passes. Replaced
  conditional rendering expressions with ordinary `if` blocks; retained `new-1.log`/JUnit. Three
  remaining cases were not run in that attempt. No scientific result was repaired or retried.
- Corrected new file: **15 passed**, `new-2.log`/JUnit, 12.56 s.
- One focused Workbench directory invocation: **254 passed, zero failures/errors/skips**,
  `workbench.log`/JUnit, 75.24 s. Includes all 239 preexisting Workbench cases and the 15 new cases.
- A final presentation guard and two added UI tests are checked separately in `new-final.log`/JUnit;
  **17 passed, zero failures/errors/skips**, 13.46 s. This is an affected-file rerun, not another
  254-pass run.
  The prior 239 backend/legacy checks retain unchanged dependencies. Counts are not added together.
- Changed Python Ruff check/format and shell syntax pass. Documentation/scope/whitespace checks
  precede commit. Root `tests/` and the full formal Verification suite are intentionally deferred.

Exact focused directory command, from the repository root:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
MPLCONFIGDIR=results/apex_workbench_v03b_work_20261029/mpl \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys,pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q -x tools/apex_workbench/tests \
--basetemp=results/apex_workbench_v03b_work_20261029/workbench \
--junitxml=results/apex_workbench_v03b_work_20261029/workbench.xml --durations=10 \
> results/apex_workbench_v03b_work_20261029/workbench.log 2>&1
```

Individual new-file invocations use that environment/bootstrap, the explicit new test file,
`--durations=5` and fresh `new-1`, `new-2`, `new-final` output/JUnit/log names.

The actual launcher executable was run from an unrelated directory at 127.0.0.1:8501. HTTP/health
and browser opener succeeded, a second click reused its exact listener, interrupt stopped its owned
server, and the port became free. An unrelated listener and the running unchanged legacy app were
both rejected without takeover. An exact byte copy in a disposable missing-environment root returned
the setup error. Evidence: `launcher_smoke.py`, `launcher_smoke.log`, `launcher_audit.json` and
`launcher-smoke/`. No experiment ran in this smoke. These establish executable/server behavior;
Finder dispatch and human visual acceptance are not claimed.

The production qualification audit (`audit.py`, `audit-2.log`, `audit.json`) reads the accepted
record, all 17 manifests/source/environment identities and actual finite-case data. All five cases
remain qualified; each of the four actual BASE/treatment pairs is a controlled candidate without
Q and qualified synthetic with Q. Original qualification SHA-256 remains
`f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.
The first audit invocation omitted the required native-thread parent environment and stopped before
reading qualification; `audit.log` preserves it. It was corrected at invocation only. An initial
preflight used core Python, which lacks Streamlit; the approved Workbench environment was used for
all tests. No dependency or environment was installed/changed.

## Preservation, limits and review gate

All **56 accepted dependency hashes** match reviewed V0.2 `4897686e79c13757d5ef5b4373b44d4cab99b5bf`;
legacy `app.py`/`plots.py`, workers/readers/evaluator, canonical plant/tire/controller/integrator,
configs, dependencies, criteria, research profiles and historical evidence are untouched. Before/after
checks retain all 30,389 historical result files with the same size/mtime. New presentation modules
are captured by unchanged full provenance; being outside the 56-file inventory does not confer
presentation verification. The new test explicitly checks their source hashes.

Host: macOS 26.5.1 arm64, Python 3.12.14, accepted Workbench numerical environment. Accelerate SINGLE
configured before numerical imports; API reports single mode, not exact active threads. Original
60 s wall/30 s CPU/512 MiB sampled RSS/64 MiB output/16 MiB file controls remain. No hard real-time,
physical safety, measured APEX parameters or unsupported controller claims follow.

Current limitations: two-run/raw-time plots only; no synchronized cursor/replay/import; only approved
local archive layout; source/manifest metadata discovery is untrusted; archive notes are view-only;
owned status uses explicit refresh; actual exporter summaries remain JSON rather than new calculated
scores. Evidence logs are bounded raw text and explicitly unverified for invalid/active records.
No unresolved scientific decision is required by this scope.

An exact candidate must receive separate-context Engineering Review. Preserve failed review records
and re-review any corrected source revision, at most three substantive bounded correction iterations.
The next gate is separately authorized exact-revision formal functional Verification. After that,
the accepted roadmap's pairwise multi-run/common-time inspection is the next MVP extension; no
extension starts automatically here.
