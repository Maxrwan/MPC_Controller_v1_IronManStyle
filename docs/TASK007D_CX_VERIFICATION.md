# Task007D-CX — Formal verification, Studies 1 and 2

**VERIFIED_AWAITING_ACCEPTANCE.** Formal verification passed on reviewed revision
`935e98b7af6c2fda8458551f1fbcbddb3bf8932d`. This does not select or promote an architecture,
authorize Study 3, freeze Performance or start Efficiency. Primary APEX scientific acceptance remains pending.

## Revision and scope

Started from clean `main` at the exact reviewed SHA; remote verified as
`Maxrwan/MPC_Controller_v1_IronManStyle`. The complete suite and evidence audits ran before any
tracked edits. All **627 reviewed tracked files** retained their SHA256 through these checks.
Existing controller, scheduler, solver/predictor, configuration, fixtures and dependency lock files
also match the pre-WORK core `77ba86f28e24d2780d01b5b0058e5405dde3d6ec` (empty Git diff).
The [formal manifest](task007d/cx/formal/verification.json) contains the reviewed tree identity,
core/fixture hashes, test/environment records, export comparisons and log SHA256 values.

This delivery adds verification documentation and compact verification records, and prepends the
handoff. It does not alter reviewed executable code, tests/assertions, fixtures, scientific tables,
figures or results reports. Its containing commit differs from the reviewed scientific revision;
the exact documentation delivery SHA and verified remote URL are reported after push.

## Environment and resource gate

Python 3.12.14; macOS 26.5.1 arm64; NumPy 2.5.3, SciPy 1.18.1, CasADi 3.8.1,
pytest 9.1.1, Matplotlib 3.11.2, psutil 7.2.2 and threadpoolctl 3.7.0. Existing environment/lock
unchanged. Accelerate SINGLE was configured before numerical/pytest initialization; native set
status 0, mode 1. Existing threading tests also exercise their explicitly isolated backend cases.
No experiment/benchmark worker or active measurement guard was present. Initial free disk was
9.317 GiB, above the existing 1 GiB floor; process inventory is retained locally.

## Full regression result

**709 passed; 0 failed, 0 errors, 0 skipped. Pytest duration 597.59 s (9 min 57.59 s).**
The wrapper measured 598.597 s including pytest startup/shutdown. JUnit suite time is 597.562 s.
These are test execution durations, not new planner performance measurements.
Directory counts: **31 integration, 3 regression,
675 unit tests**. The suite ran once, with no fixes or reruns. Existing lap-shaped
regression fixtures are part of the authorized test suite, not a new Study 3 research campaign.

Complete verbose output and every setup/call/teardown duration are retained in
`results/task007d/cx/formal_935e98b/full_suite.log`; machine-readable results are in
`full_suite.xml`, with invocation and exit JSON records. Compact per-test totals are committed in
[test_durations.csv](task007d/cx/formal/test_durations.csv).

Command (SINGLE configured before imports):

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys, pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-vv -x tests --durations=0 --durations-min=0 \
--junitxml=results/task007d/cx/formal_935e98b/full_suite.xml
```

The actual invocation used the same bootstrap/arguments with a wrapper recording elapsed time
and exit status. `-x` was never triggered. No second complete run was performed.

Slowest per-test totals (rounded JUnit setup/call/teardown totals):

| Test | Seconds |
|---|---:|
| `tests.integration.test_mpc_tracking::test_nmpc_two_laps[oval]` | 70.654 |
| `tests.integration.test_mpc_tracking::test_nmpc_two_laps[circle]` | 66.562 |
| `tests.unit.test_aggressive_reference::test_scaling_geometry_and_cap` | 56.891 |
| `tests.integration.test_baseline_tracking::test_two_laps_all_schedule_nodes[1.0-oval]` | 50.064 |
| `tests.integration.test_baseline_tracking::test_two_laps_all_schedule_nodes[1.0-circle]` | 44.132 |
| `tests.integration.test_baseline_tracking::test_two_laps_all_schedule_nodes[2.0-oval]` | 25.145 |
| `tests.integration.test_baseline_tracking::test_two_laps_all_schedule_nodes[2.0-circle]` | 21.941 |
| `tests.unit.test_task007b_export::test_progress_export_and_delayed_physical_chronology` | 18.667 |
| `tests.integration.test_baseline_tracking::test_two_laps_all_schedule_nodes[3.0-oval]` | 16.850 |
| `tests.integration.test_baseline_tracking::test_two_laps_all_schedule_nodes[3.0-circle]` | 14.805 |

## CX and dependency coverage

These results are extracted from the same full run, not additional test executions:

| Module | Passed | Result |
|---|---:|---|
| test_cx_closure | 13 | PASS |
| test_fixed_handoff_scheduler | 26 | PASS |
| test_fixed_handoff_contract | 4 | PASS |
| test_fixed_handoff_analysis | 5 | PASS |
| test_async_chronology | 11 | PASS |
| test_diagnostic_timing | 12 | PASS |
| test_prediction_diagnostics | 15 | PASS |
| test_trajectory_tracker | 25 | PASS |
| test_mpc | 23 | PASS |
| test_dynamic_bicycle | 50 | PASS |
| test_grip_tire | 20 | PASS |
| test_task007c_physics | 3 | PASS |
| test_threading_study | 19 | PASS |

**226 relevant tests across 13 modules**, including all 13 CX tests. The remaining full-suite
coverage also passed, including prior regression fingerprints and other model/controller tests.
The historical WORK metadata said “14 focused unit files”; its actual reproduction command lists
13. This is a documentation count correction only. Historical WORK counts/logs are retained as-is;
they are not substituted for this fresh full-suite result.

Scoped Ruff check and format passed on eight CX Python files. No mathematical assertion,
tolerance, serialization contract or runtime behavior changed.

## Retained C1 compatibility

Ran the existing `task007dcx.reuse` recorded-packet audit to a fresh ignored output, without an
optimizer experiment. Both C1 histories reproduce exactly: physical states, releases, handoffs,
reserves, fixed cycles, urgent/miss/fallback records, RK4 segments and controls excluding host wall
telemetry. Twenty causal preparation inputs per history were checked. The regenerated audit JSON
is identical to the reviewed reuse_audit.json.

The audit confirms the original 85/87 source matches, all five Planning fixture files and vehicle
hash. The two differences versus historical capture remain the accepted urgent-bookkeeping edits
in asynchronous.py/fixed_handoff.py; neither retained history has urgent demand. No new source
incompatibility was introduced. C1 evidence was reused; accepted fixed-C experiments were not rerun.

## Numerical and figure consistency

Rebuilt the existing CX report from unchanged raw histories into a fresh ignored directory:
**all 51 table/export files match byte-for-byte**, including aggregate/per-run/cycle/miss tables,
provenance, jitter residuals, controls/references and original segment timestamps. Supplemental
WORK study1 snapshots match the canonical tables. Rebuilt all ten figures from those tables:
**all ten PNG SHA256 values match exactly**, preserving the already reviewed rendering and labels.
No visual or numerical evidence was replaced.

Independent raw checks reproduce complete preparation distributions, release/accepted/busy counts,
all fixed misses and recovery timestamps, grid alignment, late discard and exclusion from authority.
No fixed-only timestamps are fabricated for variable A. Missing/not-applicable fields remain null
or omitted under the existing schema. Source/raw/fixture hashes and recorded causal-match results
were cross-checked. All 602 release forecasts remain represented as exact NMPC-input matches.

| Architecture | Runs | Runtime releases | Accepted | Fixed misses | Busy release skips | Preparation mean / p95 / max, ms |
|---|---:|---:|---:|---:|---:|---|
| A | 10 | 190 | 190 | N/A | 0 | 64.286 / 70.735 / 79.934 |
| C70 | 10 | 189 | 179 | 10 (5.291%) | 1 | 65.931 / 70.034 / 120.735 |
| C80 | 10 | 185 | 182 | 3 (1.622%) | 5 | 69.368 / 73.084 / 337.787 |

All 13 actual fixed misses remain in the miss table and figures; all recover and no late packet
becomes active. The 120.735 ms C70 and 337.787 ms C80 outliers remain in the distributions and
consequence analysis. No scientific failed run was removed; all 32 original runs had empty stop-gate
lists. The original WORK fixture-diagnostic test failure log remains byte-identical and is distinct
from these scientific outcomes.

The preliminary conclusions reproduce: C70 strongly suppresses matched sub-deadline jitter but
retains tiny RK4-partition differences; fixed candidates improve average steering/tracking while
heading/peak errors, response and reserve show tradeoffs. Minimum recorded A/C70/C80 reserves remain
0.655/0.501/0.304 s. Verification supplies no new reason to choose a production winner or revise the
WORK recommendation of insufficient evidence to freeze an architecture.

## Preservation, failures and discrepancies

Before documentation updates: all **627 reviewed tracked files** and **11,283 prior raw file
size/mtime records** are unchanged. Relevant raw experiment contents also match their recorded
SHA256 values. Current core/fixtures match reviewed and pre-WORK hashes. The specification,
predeclared protocol, historical figures, unfavorable outcomes and original handoff remain intact.
New logs/rebuilt copies live only in the fresh `formal_935e98b/` directory.

No reviewed test or scientific verification failed. Two verification-tool observations are retained:

- The first ad hoc read-only audit raised `KeyError: urgent_demands` because variable-A serialization
  intentionally omits fixed-only fields. After inspecting the existing conditional schema, a separate
  audit reader treated absent fixed-only collections as empty; all checks then passed. Both reader
  scripts/logs are preserved locally. No reviewed executable code, fixture or assertion was repaired.
- Figure reconstruction emitted sandbox font-cache warnings and used a temporary cache. It completed
  successfully and produced ten byte-identical PNGs. No rendering discrepancy remains.

The WORK “14 files” versus actual 13-file command typo is documented above without overwriting the
reviewed historical metadata. There is no scientific discrepancy requiring experiment repetition.

## Reproduction and local evidence

Existing reviewed scripts were used unchanged, after the full suite finished:

```sh
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dcx.reuse", run_name="__main__")' \
--output results/task007d/cx/formal_935e98b/reuse_audit.json

VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_module("task007dcx.report", run_name="__main__")' \
--source results/task007d/cx --output results/task007d/cx/formal_935e98b/tables

MPLBACKEND=Agg VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=scripts:src .venv/bin/python -m task007dcx.figures \
--tables results/task007d/cx/formal_935e98b/tables \
--output results/task007d/cx/formal_935e98b/figures
```

Those output paths now exist and must not be overwritten. Commands document this verification,
not authorization to repeat it. Original [reproduction guide](TASK007D_CX_REPRODUCTION.md) and
[WORK report](TASK007D_CX_RESULTS.md) remain unchanged. Full logs, JUnit, before snapshot,
independent read-only audit and reconstructed exports are retained locally under the path above;
compact manifest/log hashes and per-test durations are committed.

## Deferred work and delivery boundary

No outstanding Studies 1–2 verification check remains. Scientific acceptance remains with Primary
APEX. Study 3/full-lap research, final architecture selection, Performance freeze, Efficiency,
Architecture B/lightweight reinvestigation and later controller phases remain unexecuted and
unauthorized. This verification makes no real-world or embedded hard-real-time certification claim.

Stop after the verification documentation commit/push and await acceptance or a new bounded instruction.
