# C0 descriptive adapter — formal functional Verification

**Outcome: PASS within the authorized non-simulation software scope, with the limitations below.**
2 November 2026. **C0_DESCRIPTIVE_ADAPTER_VERIFIED_PENDING_PRIMARY_ACCEPTANCE.**

Exact reviewed/tested implementation: `d246f1e9639737e4ecbbd12f8bd0c9b2f1574712`.
Authenticated checkout/review delivery: `dd0ff721ac88456f0111e1fc3eaf22d984e83250`.
Branch: `codex/apex-workbench-c0-descriptive-adapter`.
[Independent Engineering Review](iteration_2/REVIEW.md), [machine Verification record](verification_record.json).
The Verification evidence revision is the commit containing this report, supplied in the final
delivery. It changes documentation only; no implementation correction was made during Verification.

**G1 remains OPEN. `descriptive_only / source_unverified` remains the classification.**
Successful inspector verification authenticates software behavior against known retained bytes;
it does not authenticate the original capture producer, configuration, environment, controller,
optimizer, physical measurements or scientific conclusions.

## Authority and exact source gate

Primary APEX explicitly authorized this formal Verification assignment in the current chat.
Before tests, all **433** tracked behavioral/configuration/test/dependency/launcher files outside
documentation/results/Markdown were content-hashed against immutable implementation `d246f1e…`:
zero mismatches. The clean checkout was exactly `dd0ff721…`, whose six changed paths relative to
the implementation are documentation, including the Workbench README. No newer implementation
was substituted. The remote adapter branch was independently observed at `dd0ff721…` before
execution. Source identity, all package versions and environment receipts are retained.

The environment matches the reviewed Mac: macOS 26.5.1 arm64, Python 3.12.14, NumPy 2.5.3,
SciPy 1.18.1, pandas 3.0.6, Streamlit 1.66.1, Plotly 6.9.0 and pytest 9.1.1. Accelerate SINGLE
was configured through its supported native API before numerical imports (`set_status=0`,
threading mode 1). The environment receipt records one process thread after NumPy import;
no exact active native-worker count, latency guarantee or parallelism claim is made.
No active measurement guard or competing Python/measurement process was found; over 36 GB was
free before execution. All G2 authorization variables were absent.

## Single applicable functional regression

One fresh invocation: **209 passed, 17 G2 skipped, 172 deselected, zero failures/errors**,
exit 0; pytest 69.34 s, supervising invocation 71.56 s. JUnit records 226 executed/skipped
cases, including **all 69 C0 tests passed** and **140 other Workbench functional passes**.
The existing 17 G2 cases skipped at their unchanged authorization gate; no G2 activity ran.
No WORK/reviewer result is aggregated into these counts. `-x` retained the required first-failure
stop behavior; no failure occurred and no suite retry was made.

The no-controller-simulation restriction controls the applicable selection. All Workbench test
files were collected; execution-capable cases and cases depending transitively on `lab_runs` or
`completed_runs` were explicitly deselected **before fixture setup**. Those 172 cases can launch
producer/model/worker executions or depend on such generated outputs. They were neither replaced
with fabricated fixtures nor counted as passes. The separate scientific/model/controller `tests/`
suite was not run; only its existing G2-gated module was included. This is **not** a fresh full
repository numerical regression or a repeat of the prior 1,089-pass V0.3-D invocation.

The selection question was raised because the previous broad regression launches simulations.
No broader authorization was inferred from the pending clarification; the explicit prohibition
was applied conservatively. Execution-heavy compatibility tests remain historical evidence.
Acceptance must retain this scope; an unqualified whole-repository regression claim is unsupported.

Exact command, from repository root (the receipt records absolute argv and environment):

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:scripts:src \
MPLCONFIGDIR="$PWD/results/apex_workbench_c0_verification_20261102/mpl" \
tools/apex_workbench/.venv/bin/python -u \
results/apex_workbench_c0_verification_20261102/functional_suite.py \
-q -x tools/apex_workbench/tests/ tests/integration/test_profile1_parity.py \
--basetemp="$PWD/results/apex_workbench_c0_verification_20261102/pytest_tmp" \
--junitxml="$PWD/results/apex_workbench_c0_verification_20261102/functional_suite.xml" \
--durations=20 > results/apex_workbench_c0_verification_20261102/functional_suite.log 2>&1
```

The fresh ignored verification wrapper configures SINGLE, records the environment and applies
only the disclosed collection exclusions. Original implementation, test code, expected outcomes,
deadlines and fixtures are unchanged. Complete selected/excluded node IDs and reasons are in the
[selection receipt](../../../../results/apex_workbench_c0_verification_20261102/suite_selection.json).
[Exact invocation](../../../../results/apex_workbench_c0_verification_20261102/functional_invocation.json),
[full log](../../../../results/apex_workbench_c0_verification_20261102/functional_suite.log),
[JUnit](../../../../results/apex_workbench_c0_verification_20261102/functional_suite.xml).

## Nine requirements

| Requirement | Fresh evidence and disposition |
|---|---|
| 1. Exact artifact admission | **PASS.** Original path is exactly 152,600 bytes, SHA-256 `2bd7d2385e7e2072a04e5d952eff9af8861eb7e63f016138d5289573c411f2d5`. Production read returns these exact bytes and validates the five contemporary authority/shape anchors. This identifies retained bytes only. |
| 2. Tokens, pointers, missingness, chronology and labels | **PASS.** All **4,034** numeric tokens and all other values/key/array order match an independent standard-library token-preserving parse. Explicit examples retain `-0.0`, integer `0` versus real `0.0`, `0.41500000000000004`, `0.0050000000000000044`, original field names and JSON pointers. Present-null acceptance/use/authority stays distinct from absent startup `valid_from` and trigger `busy`. Busy skips and fixed misses remain separate; state/reserve coverage ends at `0.595`, controls at `0.59`, declaration at `0.6`, without a fabricated endpoint or causal tie order. Live/HTML labels retain G1 and capture-unverified reference interpretations. |
| 3. Fail-closed evidence | **PASS.** Same-invocation tests reject missing, changed, malformed, oversized, directory, symlink, linked-root and alternate-filename evidence; changed contract/review/shape anchors; same-size/mtime replacement; invalid conditional types/keys/dimensions; duplicate and nonfinite JSON. Actual disposable late-render and post-serialization/download-preparation replacements clear scoped publication/export. Secondary parser tests do not weaken production SHA admission. Originals are never mutated. |
| 4. Live and HTML output restrictions | **PASS.** Actual AppTest and settled live browser show three static C0 tables, plain provenance/raw text, no native dataframe CSV/code/JSON clipboard surface and no visible Plotly image/cloud controls. Actual Plotly invocation configurations disable modebar/image/cloud actions in live and standalone HTML. The sole offered C0 output is the explicitly prepared metadata-bearing HTML download. Ordinary browser text selection is outside the controlled-output contract. |
| 5. HTML generation and reopening | **PASS for core behavior; browser delivery limit retained.** The actual AppTest preparation path generated a **5,085,769-byte** standalone report for controls/`physical_latency`, SHA-256 `e99cb0285332fc3a4f31337cb92ce3463fb820105160bf3c5f3712f35308c3b4`. It includes complete original decoded JSON including outer whitespace, pointers, exact tokens, source hash, classification and limitations. The same file reopened in the actual in-app browser through an owned loopback static server, rendering one Plotly figure and full context with zero visible modebar/download/copy controls. No external script/style dependency or form is required. Internet was not disabled; this is self-contained local rendering, not network-isolation qualification. |
| 6. No execution path from inspection | **PASS.** Production C0 reader imports only standard-library modules; panels import HTML/JSON, Plotly, Streamlit and that reader. C0 acceptance ran with worker/lifecycle entry points replaced by failing spies: **zero calls**. Same-invocation UI/dependency tests prohibit execution/comparison admission and lifecycle calls. Browser actions stayed on Inspect and HTML preparation; no Run action, planner, controller, simulator or actuator was invoked. |
| 7. Accepted Workbench compatibility | **PASS within the non-simulation scope.** The 140 non-C0 passes cover retained-record integrity, Home/Inspect/Compare and legacy forms, P native inspection/currentness, qualification calculation/consumption over literal or retained evidence, source inventories, replay/native `0.125` samples and original UI responsiveness deadlines. C0-to-P navigation passes. Existing worker/controller execution parity is unexecuted here under the explicit restriction; unchanged source/dependencies and preserved historical evidence support retention, not a new execution claim. |
| 8. Frozen sources and historical evidence | **PASS.** After execution, all **433** reviewed behavioral files and **1,734** selected preexisting protected files retain hashes. All **56** scientific files also match accepted immutable Git `4897686e79c13757d5ef5b4373b44d4cab99b5bf`; all **345** original qualification files, **25** retained P files and **4** legacy oval files match retained accepted hashes. Original C0 evidence, Section A, corrected contract and failed reviews/logs remain unchanged. All **53,515** preexisting result size/mtime observations and **1,945** symlink targets are unchanged; those metadata observations are not a full historical-content rehash. |
| 9. Launcher lifecycle | **PASS within the existing accepted contract.** The original launcher bytes pass shell syntax, actual startup from an unrelated directory, owned loopback identity/HTTP, same-listener second-launch reuse, occupied-port refusal, legacy-app refusal without takeover and missing-environment messaging using an exact disposable launcher copy. Supervisor-targeted SIGINT exits 0 and cleans up. One actual terminal Ctrl-C yields shell **SIGINT(2)**, not ordinary exit code 2; the port is released and no owned survivor remains. Route-specific observations remain distinct. |

## Browser delivery and launcher limits

The actual live C0 preparation displayed exactly one governed download. One click returned in
267 ms, but no new matching C0 file was observed in Downloads within a separately bounded
10.17 s observation. **AUTOMATIC BROWSER DELIVERY NOT CONFIRMED**, not counted as download success
or an application failure. Native save-dialog completion was not observed. No repeated download
or workaround was used. This is separate from successful generation and actual local reopening.
The earlier V0.3-D browser delays and unresolved causes remain historical; no improvement or
common-cause claim is made.

The terminal Ctrl-C port-release observation was 5.324 s on this invocation, with zero survivors;
it is descriptive, not a timing threshold, improvement claim or real-time guarantee. The earlier
launcher tool exit 1 and prior route-specific observations remain preserved. The actual launcher
and temporary static server were shut down, and a final process inspection found no remaining
Python/pytest/Streamlit/worker/HTTP server. No unrelated listener or user process was signaled.

## Preservation, evidence and stop

Full commands, package identities, source hashes, JUnit, selected/excluded node IDs, raw numeric
tokens, HTML, acceptance receipts and logs are retained in
`results/apex_workbench_c0_verification_20261102/`. The [machine record](verification_record.json)
binds those files by SHA-256. Eleven supplementary C0 acceptance checks are reported separately;
they are not added to the 209 pytest passes. Launcher and terminal observations are also separate.

Initial read-only setup encountered a wrong historical snapshot filename and sandbox restrictions
on process inspection/loopback binding. Correct source lookup and authorized escalation resolved
them before the regression. These are retained harness/environment notes, not behavioral defects
or a favorable test retry. A preliminary P-file lookup found duplicate matching summary copies;
the final audit used the explicit original retained P root and verified all 25 files.

No blocking behavioral defect was observed. No implementation, tests, contract, scientific source,
frozen baseline, qualification, original archive or historical review was repaired. Only this
report, its machine record and the mandatory handoff are committed. PR #1 remains draft/unmerged.
No scientific qualification campaign, controller simulation, RBT, Performance/Efficiency/CT/Safety,
Pre-SID R0 or hardware work occurred. No merge, release promotion, provenance reclassification,
M5-A or other feature work is authorized.

**Stop: C0_DESCRIPTIVE_ADAPTER_VERIFIED_PENDING_PRIMARY_ACCEPTANCE.** Primary acceptance must
retain G1 OPEN, the descriptive-only classification, explicit regression exclusions and the
automatic-browser-delivery limitation. This report does not grant acceptance itself.
