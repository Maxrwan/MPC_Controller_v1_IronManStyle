# APEX Workbench V0.2-E — formal functional Verification

**V0.2_VERIFIED_PENDING_USER_ACCEPTANCE.** Recorded 29 October 2026.

**PASS.** One complete combined invocation finished with **1,016 passed, 17 skipped, 0 failures and
0 errors**, exit 0, in 673.24 s. The actual retained qualification and all four accepted comparisons
remain valid. Launcher functional checks pass. No blocking finding remains. Recommend final user
acceptance within the accepted finite synthetic scope; acceptance itself remains pending.

Verified exact implementation: `4897686e79c13757d5ef5b4373b44d4cab99b5bf`.
Clean tested checkout / qualification report: `cd4da167166af63d758f715ede166a0e6a73b76a`.
Branch: `codex/apex-workbench-v0-2-c`. Accepted contract:
`0cc7e4f626311aec05977bd3beda40c346fa4214`. The tested checkout is a documentation-only descendant:
all 56 required source identities and all behavioral implementation/test files match the reviewed
revision. The containing delivery changes authorized reporting/handoff documentation only.

Primary explicitly accepted V0.2-D qualification for the five synthetic cases and four comparisons
in this task. No scientific implementation, parameter, threshold, validity filter, dependency or
frozen-profile change was made. No new 17-trajectory campaign, frozen research campaign or hardware
work occurred. Existing numerical/solver regression simulations ran within the authorized test suite.

The evidence chain is the [final independent Engineering Review](../apex_workbench_v0_2_c/iteration_2/REVIEW.md),
the accepted [V0.2-D report](../../apex_workbench_v0_2_d/QUALIFICATION.md) and
[machine execution record](../../apex_workbench_v0_2_d/execution_record.json), under the unchanged
[numerical](../../apex_workbench_v0_2_a/NUMERICAL_CONTRACT.md) and
[validity](../../apex_workbench_v0_2_a/VALIDITY_CONTRACT.md) contracts.

## Verification matrix

| Required area | Outcome and evidence |
|---|---|
| Exact source / approved environment | PASS: 56 required Git-blob hashes match; no behavioral delta; Python/platform and installed numerical packages match the qualified environment |
| Complete applicable suite | PASS: 777 repository tests plus 239 Workbench tests; 17 frozen G2 skips; no failures/errors/setup errors; one combined invocation |
| Frozen gates | PASS: no G2 authorization variables enabled; all 17 skips retain their explicit separate-authorization reason |
| Retained qualification / four comparisons | PASS: production reader checks all 17 source-run references, artifacts, source/environment identity and record checksum; four actual pairs become qualified only with the selected verified record |
| Invalidation / evidence integrity | PASS: actual-record disposable checksum, missing-artifact, source and environment probes reject; full suite also covers omitted inventory, contradictory aliases, manifest epochs, duplicate execution identity and publication/integrity cases |
| V0.1 dynamic and LQR modes | PASS: fresh original-entry-point byte parity and real owned-worker parity/functionality for both modes |
| V0.2 canonical-runner parity | PASS: independent literal-provider/canonical-construction state/control/diagnostic byte parity and XY checks |
| Lifecycle / cancellation | PASS: real supervisor SIGKILL/worker-lease recovery, cancellation, stale-state/identity/publication cases and complete-horizon unsuccessful-outcome fixtures |
| One-click launcher | PASS: unchanged executable, shell syntax, actual default-port startup from unrelated cwd, reuse, HTTP availability/browser opener, clean owned shutdown, occupied-port error and disposable missing-environment branch |
| Preservation / cleanup | PASS: 953 preexisting tracked files byte-identical after checks; 28,139 old result files present with unchanged size/mtime; owners terminated, lease released, port 8501 available |

## Complete test execution

The exact invocation, from the repository root, was:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
MPLCONFIGDIR=results/apex_workbench_v02e_verification_20261029/mpl \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
  -q -x tests tools/apex_workbench/tests \
  --basetemp=results/apex_workbench_v02e_verification_20261029/pytest \
  --junitxml=results/apex_workbench_v02e_verification_20261029/suite.junit.xml \
  --durations=20 \
  > results/apex_workbench_v02e_verification_20261029/suite.log 2>&1
```

`-x` was fail-fast protection; it omitted nothing because the run reached 100% without a failure.
Fresh JUnit evidence contains 1,033 cases: 1,016 passes and 17 skips. No historical pass is counted
as newly executed and no multiple-run count was combined. The only skips are
`tests/integration/test_profile1_parity.py:55`: separate G2 authorization, reviewed revision/allowance
and pristine B0 root required. Those requirements remain unfulfilled and unreauthorized.

Key freshly passed checks include:

- `test_dynamic_original_cli_byte_parity`, `test_lqr_original_function_byte_parity`,
  `test_full_worker_dynamic_parity`, `test_existing_lqr_still_executes_under_owned_worker`.
- `test_canonical_runner_and_diagnostic_byte_parity`.
- Both `test_r1_real_sigkill_keeps_worker_lease_and_recovers` cases;
  `test_cancel_and_unique_run_directories`; C3 full-output/partial/UI cases.
- Source-inventory omission/import-closure, diagnostic aliases, controlled comparisons,
  refinement admission/ticks, manifest/source/environment/qualification integrity, literal evaluator
  and copied-execution identity tests. Exact node IDs/outcomes are retained in JUnit.

## Read-only production qualification audit

The accepted immutable record remains at:
`results/apex_workbench_qualifications/v0_2_reviewed_20261029/qualification/qualification.json`.
Its SHA-256 remains:
`f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.

The actual production reader revalidated the record and all 17 source-run references. All five
cases retain numerical qualification. Without a selected record, each of the four nominal pairs
remains a `controlled_candidate`; with the real verified record, each becomes a
`qualified_synthetic_comparison`. Each case source, schema, numerical environment and selected
scientific export must match. This audit reads retained CSV/JSON bytes; it does not integrate a model.

| Actual pair | Without selected record | With accepted verified record |
|---|---|---|
| BASE / `VDL1_IZ_HIGH` | `controlled_candidate` | `qualified_synthetic_comparison` |
| BASE / `VDL1_STEER_HIGH` | `controlled_candidate` | `qualified_synthetic_comparison` |
| BASE / `VDL1_CF_HIGH` | `controlled_candidate` | `qualified_synthetic_comparison` |
| BASE / `VDL1_CR_HIGH` | `controlled_candidate` | `qualified_synthetic_comparison` |

Four deliberately invalid disposable fixtures were rejected: changed qualification bytes under the
original checksum; a missing source-run manifest artifact; a known different selected source;
and a known different selected numerical environment. Only disposable copies were changed/resealed.
No original record was rewritten, no fixture was published as qualification and no new trajectory
was run. A final read confirmed the original qualification remained identical and valid.

Additional exact audit commands, with logs at the same fresh evidence root:

```sh
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python \
  results/apex_workbench_v02e_verification_20261029/audit_qualification.py \
  > results/apex_workbench_v02e_verification_20261029/qualification_audit.log 2>&1
tools/apex_workbench/.venv/bin/python \
  results/apex_workbench_v02e_verification_20261029/launcher_smoke.py \
  > results/apex_workbench_v02e_verification_20261029/launcher_audit.log 2>&1
```

The reporting scripts and their hashes are retained locally with the logs; they are not production
changes or new permanent tests. The qualification campaign directory still contains exactly the
original 17 runs. The numerical qualification was consumed, never rerun.

## Launcher and V0.1 preservation

The unchanged `Launch_APEX_Workbench.command` is executable and passes `zsh -n`. Its actual
executable was invoked from a fresh unrelated working directory. It started its owned server at
127.0.0.1:8501; health and HTML requests returned HTTP 200. The production browser opener returned
without its manual-opening fallback. A second actual invocation reused the same server PID.
An interrupt to the owned launcher Python entry returned exit 0 and terminated its owned server;
the port was then free. A temporary unrelated listener produced the expected occupied-port error.
An exact launcher byte copy in a disposable root with no environment produced the setup-missing
message and exit 1. The real environment was not renamed or removed.

These are executable/server/browser-opener observations. Finder dispatch and human visual acceptance
were not claimed. Fresh V0.1 dynamic CLI/function and LQR function/owned-worker parity checks support
both accepted modes; no extra scientific run was added merely for the launcher.

## Environment, resources and evidence limits

- macOS 26.5.1 arm64; Python 3.12.14; NumPy 2.5.3, SciPy 1.18.1, CasADi 3.8.1, OSQP 1.1.3,
  pandas 3.0.6, Streamlit 1.66.1, pytest 9.1.1. Remaining exact versions are in the machine record.
- Main-process Accelerate SINGLE was set before numerical imports. Existing Workbench workers
  retain their reviewed native/resource policy. The existing native-thread parity unit test uses
  fresh 1/2/1 configurations under its unchanged contract. Empty `threadpoolctl` enumeration does
  not measure exact active Accelerate threads. No new timing/parallel-performance conclusion follows.
- Reviewed Workbench limits remain 60 s wall, 30 s CPU, 512 MiB sampled RSS, 64 MiB output and
  16 MiB per file. Guards/supervisor sampling are soft containment, not hard-real-time certification.
  Whole-suite elapsed time is descriptive. No cross-platform or hardware qualification is claimed.
- Synthetic parameters, unsaturated linear tires, provisional quasi-static loads, ideal steering,
  sampled model windows and quarter-grid numerical-reference limitations remain. Functional and
  finite-case numerical qualification do not establish physical validity, actuator feasibility,
  continuous-time safety or unsupported controller capability.

## Evidence, preservation and acceptance recommendation

Raw logs, JUnit, preflight/build identities, reporting scripts, disposable fixtures, launcher logs,
ownership cleanup and preservation records are retained at:
`results/apex_workbench_v02e_verification_20261029/`.
The [machine-readable verification record](verification_record.json) binds exact commands,
source/test hashes, environment, counts/skips, production-consumer results and all supporting hashes.

Immediately after functional checks, all 953 preexisting tracked files were byte-identical; all
28,139 preexisting result files remained present with identical size/mtime. Canonical source,
configurations, dependencies, accepted thresholds, frozen profiles and historical review/qualification
evidence remain unchanged. The actual retained qualification is separately content-hash verified.
The historical size/mtime audit is not a full content rehash or backup claim. Only this report, its
machine evidence record and current handoff are delivery changes. Generated results stay ignored.

**Unresolved blocking findings: none.** Recommend final user acceptance of this exact reviewed
V0.2 functional implementation within Primary’s accepted finite synthetic qualification. User
acceptance remains a separate decision. No automatic V0.3, additional campaign or hardware work.

**Stop: V0.2_VERIFIED_PENDING_USER_ACCEPTANCE.**
