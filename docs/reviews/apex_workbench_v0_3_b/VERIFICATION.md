# APEX Workbench V0.3-B — formal functional Verification

**V0.3_B_VERIFIED_PENDING_USER_ACCEPTANCE.** Recorded 29 October 2026. **PASS.**

One fresh complete invocation of `tests/` and `tools/apex_workbench/tests/` finished with
**1,040 passed, 17 separately gated skips, zero failures and zero errors**, exit 0, 681.59 s.
Four supplemental epoch/key acceptance probes and one displayed-channel probe passed separately.
All required launcher checks and the retained scientific qualification audit passed. No blocking
finding remains. Recommend user acceptance of the reviewed Engineering Workspace within its stated
local functional and accepted finite synthetic scope. User acceptance itself remains pending.

Verified exact implementation: `ca3ef9605df3472001302dbf70c0e2815c020d1c`.
Tested clean checkout/review delivery: `95e068d759bebe5fa8116de38c6705e775c1d253`.
Branch: `codex/apex-workbench-v0-3-b`. All 435 non-documentation files, including behavioral sources,
tests, configuration, dependencies and launcher, match the reviewed Git blobs. The only descendant
changes are the six known review/handoff documents. All 56 accepted scientific dependencies also
match V0.2 `4897686e79c13757d5ef5b4373b44d4cab99b5bf` byte-for-byte. This Verification delivery
changes only reporting/handoff documentation; its containing SHA/URL is supplied after push.

Governance/current handoff and [WORK](../../apex_workbench_v0_3_b/WORK.md) were read, together with
[failed initial review](iteration_1/REVIEW.md), [failed re-review](iteration_2/REVIEW.md) and
[final independent PASS](iteration_3/REVIEW.md). Earlier counts are historical, not included in this
Verification count. No reviewed implementation, test, launcher, mathematical criterion, parameter,
source-inventory policy or scientific evidence was changed. No new qualification campaign, frozen
research campaign, hardware work or later MVP stage ran. Existing model/controller simulations ran
only within the authorized functional tests.

## Complete applicable test execution

Exact invocation from the repository root:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 BLIS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 \
MPLCONFIGDIR=results/apex_workbench_v03b_verification_20261029/mpl \
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys,pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q -x tests tools/apex_workbench/tests \
--basetemp=results/apex_workbench_v03b_verification_20261029/pytest \
--junitxml=results/apex_workbench_v03b_verification_20261029/suite.xml --durations=20 \
> results/apex_workbench_v03b_verification_20261029/suite.log 2>&1
```

The run reached 100%. `-x` omitted nothing. JUnit contains 1,057 cases: **777 repository passes,
263 Workbench passes, 17 skips**. Every skip is
`tests/integration/test_profile1_parity.py:55`: separate G2 authorization, reviewed revision/allowance
and pristine B0 root required. No G2 gate variables were enabled. No failure, setup error, retry or
harness correction occurred in this Verification. No old result is counted as freshly executed.

The [machine record](verification_record.json) binds exact source manifests, installed environment,
commands, logs/scripts/JUnit hashes, outcomes and preservation. Fresh local evidence root:
`results/apex_workbench_v03b_verification_20261029/`. All test and negative-fixture outputs are new;
no prior output was overwritten. These ignored artifacts remain local, while this report and machine
record are committed.

## Engineering Workspace acceptance matrix

| Required behavior | Result and fresh evidence |
|---|---|
| Home / Run / Inspect / Compare | PASS: actual Streamlit AppTest navigation, supported modes, explicit NMPC/TVLQR/async and other unavailable labels; original validator/default inputs |
| Approved execution and reopening | PASS: nominal BASE launched through original leased worker, completed evidence reopened with genuine telemetry/plots and captured new presentation-source hashes |
| Original qualification archive discovery | PASS: 17 source records found at their original locations, nominal/reference/refinement roles distinguished; discovery is explicitly unverified metadata |
| Distinct identity / safe deduplication | PASS: canonical aliases and exact copies group without new executions; unsealed bridges cannot merge originals; conflicting archive paths remain independently selectable with unique stable path keys |
| True states / controls / diagnostics / SI | PASS: real Inspect plots decoded from actual Plotly payloads match verified CSV timestamps/values for r, vy, delta, a_cmd, alpha_f and fyf; axes show rad/s, m/s, rad, m/s^2 and N; BASE has no invented reference trace |
| Candidate versus qualified labels | PASS: BASE/IZ actual UI shows candidate without selected Q and qualified synthetic with selected verified Q; production audit confirms all four accepted pairs |
| Corrupt/missing evidence | PASS: disposable corrupt/missing exports remain discoverable for raw inspection; invalid evidence has no scientific display/export or qualified promotion |
| Read-only archive handling | PASS: nonterminal/archive records expose no owned refresh/cancel/annotation operations; archive inspection/comparison avoids lifecycle reconciliation and original bytes remain unchanged |
| Evidence epochs | PASS: valid-to-valid replacement at comparison return or later plot reads clears classification and all plots; selected-Q anchor changes also clear display |
| Notes and outcome/evidence semantics | PASS: original prediction/request bytes retained; owned notes append versions; archive notes stay view-only; process completion, coverage, evidence validity and qualification remain separate |
| Worker lifecycle / cancellation | PASS: both real supervisor-SIGKILL lease/recovery cases, lock/admission/publication/identity checks, cancellation, limits and stale/partial/evidence-failure regressions |
| V0.1 dynamic and LQR compatibility | PASS: fresh original Task004 CLI and Task005 function byte parity plus real owned-worker functionality/parity for both accepted modes |
| V0.2 canonical-runner compatibility | PASS: independently specified canonical model/runner state/control/diagnostic byte parity and actual lab form/worker checks |
| Legacy app.py compatibility | PASS: byte-identical accepted app; existing UI tests pass; actual separate legacy server responds over loopback and is refused by the new launcher's ownership check |
| One-click launcher | PASS: actual executable, unrelated cwd, correct workspace listener, default-port loopback HTTP/browser opening, reuse, owned termination and error paths; details below |

Key fresh nodes include `test_home_and_actual_inspect_view`,
`test_actual_compare_ui_candidate_then_qualified`, `test_real_nominal_run_through_workspace_and_reopen`,
`test_dynamic_original_cli_byte_parity`, `test_lqr_original_function_byte_parity`,
`test_full_worker_dynamic_parity`, `test_existing_lqr_still_executes_under_owned_worker`,
`test_canonical_runner_and_diagnostic_byte_parity`, both
`test_r1_real_sigkill_keeps_worker_lease_and_recovers` cases, and the permanent archive/epoch/notes
regressions. Complete node outcomes are retained in JUnit, not inferred from previous reports.

Supplemental acceptance used the final review's unchanged nearby-case logic in a new verification
harness, with only its root resolved from cwd. Four cases ran in `acceptance.log`/`acceptance.xml`:
replacement after the second/third actual plot read, selected-Q commit change, and archive-key
stability across changed untrusted IDs/index ordering. **4 passed**, 5.77 s. A separate independent
payload/axis harness in `channels.log`/`channels.xml` passed **1 case**, 3.99 s, decoding the actual
serialized Plotly data. State/diagnostic rows are 101; applied controls are 100. These supplemental
counts are separate from the complete suite, not added to its 1,040 passes. No additional simulation
was needed for them. Exact invocations and harness hashes are in the machine record.

## Actual launcher and compatibility checks

`launcher_smoke.py` invokes the actual executable from a fresh different working directory. It starts
`tools/apex_workbench/workspace.py` at **127.0.0.1:8501**, verifies actual listener UID/cwd/command
and descent from the test-owned launcher, and receives HTTP 200 health/HTML. The production browser
opener returns without manual fallback. A second actual invocation reuses the same server PID.
Interrupt to the owned launcher returns exit 0, its owned server stops, and the port is available.

A temporary unrelated socket listener causes exit 1 with the occupied-port error. The unchanged
legacy `app.py` is then served separately on that port; it responds over loopback, the new launcher
refuses reuse/takeover, and the legacy process stays alive until the harness terminates its own
server. An exact launcher byte copy in a disposable root without the environment gives the setup
error and exit 1; the real environment was never renamed/removed. No existing user server was present
at preflight, and no unrelated process was terminated. No scientific execution occurred in this smoke.

Command, with the documented six native-thread variables set to 1:

```sh
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u \
results/apex_workbench_v03b_verification_20261029/launcher_smoke.py \
> results/apex_workbench_v03b_verification_20261029/launcher_audit.log 2>&1
```

Evidence: `launcher_audit.json`, startup/reuse/conflict/missing-env logs and retained script.
These establish executable/server/browser-opener functionality. Finder dispatch, screenshots and
human visual acceptance are not claimed. No old partial launcher-review result substitutes for this run.

## Retained scientific qualification and preservation

The actual unchanged production consumer reads
`results/apex_workbench_qualifications/v0_2_reviewed_20261029/qualification/qualification.json`,
revalidating all **17 original execution references**, source-run manifests/artifacts, exact data,
scientific source and numerical environment. Installed scientific/package versions match the record.
All five cases retain accepted numerical status under the original sampled criteria; no rule is
claimed empirically or physically validated by this audit.

Qualification SHA-256 remains:
`f08ae323e86cdd03964e87b091aef660ac1568e1601e42c43e82dbc0f5e429c8`.

| Original pair | Without selected Q | With exact applicable Q |
|---|---|---|
| BASE / IZ_HIGH | controlled_candidate | qualified_synthetic_comparison |
| BASE / STEER_HIGH | controlled_candidate | qualified_synthetic_comparison |
| BASE / CF_HIGH | controlled_candidate | qualified_synthetic_comparison |
| BASE / CR_HIGH | controlled_candidate | qualified_synthetic_comparison |

Four explicit copied-fixture faults reject: changed qualification bytes under the original checksum,
missing referenced manifest artifact, different selected scientific source and different selected
numerical environment. Fixture metadata was rebound only where needed to exercise the semantic
consumer; originals were never edited/resealed. No copied fixture was published as qualification.
The final original-record read remains valid and equal. The source-aware catalog/alias tests ensure
copies do not become additional scientific executions.

Exact audit command, with the documented native-thread variables set to 1:

```sh
PYTHONPATH=.:scripts:src tools/apex_workbench/.venv/bin/python -u -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import runpy; runpy.run_path("results/apex_workbench_v03b_verification_20261029/audit_qualification.py", run_name="__main__")' \
> results/apex_workbench_v03b_verification_20261029/qualification_audit.log 2>&1
```

No 17-trajectory campaign, refinement grid or parameter sweep was run. The authorized suite's ordinary
functional simulations remain software evidence, not new scientific qualification.

Before reporting edits, all **973 preexisting tracked files** were still byte-identical; all
**435 reviewed non-documentation files** matched, and all **56 scientific dependencies** matched both
recorded hashes and accepted Git blobs. There is no canonical `src/`, `scripts/`, `configs/`,
`pyproject.toml` or `uv.lock` delta from accepted V0.2. All **34,287 preexisting result files** retain
size/mtime and **856 symlink targets** are unchanged. Full before/after SHA-256 maps of all **345
accepted qualification files** are equal. The lease is available, no workers/servers remain, the
measurement preflight passes, and port 8501 is free. Evidence: `before.json`, `preflight.json`,
`preservation.json`; the containing delivery alters only authorized reporting/handoff docs.

## Limitations, observations and recommendation

macOS 26.5.1 arm64; Python 3.12.14; NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.6, Matplotlib 3.11.2,
CasADi 3.8.1, OSQP 1.1.3, Streamlit 1.66.1, Plotly 6.9.0, psutil 7.2.2, pytest 9.1.1.
Remaining versions/environment are recorded. Accelerate SINGLE was set before numerical imports;
the native API reports single mode, not exact active threads. Empty threadpool enumeration is not
proof of active-thread count. Existing threading parity tests retain their own reviewed 1/2/1 subprocess
policy. Test elapsed time is descriptive, not a latency or real-time acceptance threshold.

Original Workbench containment remains 60 s wall, 30 s CPU, 512 MiB sampled RSS, 64 MiB sampled output,
16 MiB per file and native controls, with the accepted supervisor/guard limitations. Main pytest/server
processes are not claimed to share the scientific worker's caps. No cross-platform, hardware watchdog,
hard real-time, physical vehicle or continuous-time safety qualification follows.

Product limits remain two-run/raw-time comparison, approved local archives only, no synchronized
replay/import, view-only archive notes, explicit owned refresh and existing exporter summaries rather
than new metrics. Synthetic parameters, unsaturated linear tires and accepted sampled-model/numerical
limitations remain unchanged. No unsupported controller execution or physical/Safety command path was added.

**Nonblocking observation N1:** source switching logs Streamlit's default/session-state warning for
`inspect_channels` at `tools/apex_workbench/workspace.py:77`. The retained `channels.log` includes it;
selected channels, actual payload values, SI axes and application exception/error assertions all pass.
Bare-mode ScriptRunContext warnings are also retained. No implementation change was made to suppress
these warnings. This is not a failed acceptance check or a data-integrity finding.

No blocking finding or unresolved scientific decision remains. Recommend acceptance of exact reviewed
V0.3-B for its bounded engineering scope. Final user acceptance stays pending. Multi-run comparison,
replay, CT studies, hardware telemetry and the next MVP stage remain separately authorized.

**Stop: V0.3_B_VERIFIED_PENDING_USER_ACCEPTANCE.**
