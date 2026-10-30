# V0.3-D formal functional Verification

**PASS within the contracted software scope, with the platform limitation below.**
30 October 2026. **V0.3_D_VERIFIED_PENDING_USER_ACCEPTANCE_AND_RBT_DECISIONS.**

Exact verified implementation: `c5f3db6852af8f8ffccf4e5e9e6f11d01fa861b4`.
Tested clean documentation-only review delivery: `49f7eb98fcec6fac5869371f70dc2e7d2daf7dff`,
branch `codex/apex-workbench-v0-3-d`. All **428** tracked files outside documentation/results
and Markdown match the reviewed Git blobs before and after execution, including behavioral
source, tests, configurations, dependencies and launcher. This containing delivery is documentation
only. [Engineering Review](iteration_1/REVIEW.md), [machine evidence](verification_record.json).
No application correction, new scientific implementation, full-suite retry or weakened criterion.

## Complete applicable suite

One fresh invocation of **`tests/` and `tools/apex_workbench/tests/`**:
**1,089 passed, 17 skipped, zero failures/errors**, exit 0, **747.90s** pytest time
(749.47s supervising invocation). Split: 777 repository passes plus 17 G2 skips; 312 Workbench passes.
The 17 skips are exclusively the existing separately authorized G2 parity cases. No G2 authorization
variables were present. Earlier WORK/reviewer results are not included in this total.

Exact argv/bootstrap/environment are retained in
[invocation](../../../results/apex_workbench_v03d_verification_20261030/full_invocation.json),
[log](../../../results/apex_workbench_v03d_verification_20261030/full_suite.log) and
[JUnit](../../../results/apex_workbench_v03d_verification_20261030/full_suite.xml).
The machine record includes the command, environment, full behavioral hashes,40 selected acceptance
node results and evidence hashes. Fresh temporary outputs were used throughout.

Reference platform: macOS 26.5.1 arm64, Python 3.12.14; NumPy 2.5.3/SciPy 1.18.1/Streamlit 1.66.1/
Plotly 6.9.0, with all package versions retained. Accelerate SINGLE was configured through its native
API before numerical imports (`set_status=0`, mode1); environment controls alone are not the evidence.
Exact active native-thread count is unavailable. These are bounded functional observations on one
Mac, not latency-tail, broad-platform, hard-real-time or physical qualification.

The complete suite exercises existing finite model/controller simulations, original V0.1 CLI/function
parity, V0.2 canonical-runner/diagnostic parity, worker lifecycle/SIGKILL/ownership/locks/cancellation,
evidence integrity, V0.3-B/C navigation/replay/comparison and original45/60s responsiveness checks.
It is not a new racing qualification, Performance/Efficiency/CT/Safety campaign or RBT execution.

## Functional acceptance

| Area | Fresh outcome |
|---|---|
| P source/integrity |PASS:25 original files, three pinned external authority records, manifest/self-seal and 15 artifact bindings. All 294 scientific and 11 exporter hashes match historical Git8dbd1c5. Current runtime is not substituted. |
| Native telemetry |PASS: all retained rows for selected core/reference/diagnostic/control channels match literal CSV float conversions; all 14,310 event identities/times/payloads/order/missingness match original rows. Controls begin at computation 0/application 0.005 s; neither stream is resampled or shifted. |
| Status meaning |PASS: actual solver payload `Solve_Succeeded` is distinct from packet `accepted`; missing A `valid_from` and unspecified ties remain missing. Reconstructed XY/reference labels and synthetic/historical limitations remain visible. No fabricated event, hold, telemetry or score. |
| Nine sectors |PASS: original native-progress half-open definitions partition all 12,448 state rows once with unchanged run/export identities. Whole original Planning geometry remains context; selected visits use markers. Controls/cycles/events remain explicitly full-run. |
| Invalid evidence/read-only |PASS: full-suite disposable corruption, missingness, resealed source/schedule, symlink and late-replacement cases quarantine plots/labels. Archive and export acceptance paths forbid start/cancel/reconciliation calls; no Safety/actuator path. |
| Existing workflows |PASS: original V0.1/V0.2 paths, Home/Run/Inspect/Compare, native replay/0.125s samples, pairwise controlled/qualified labels, original notes/evidence semantics and oval preparation. Legacy `app.py` starts separately; launcher refuses to take over that listener. GP remains excluded from execution/comparison. |
| Retained qualification |PASS: production `read_qualification` revalidates 17 original references and recorded calculation; all four baseline/treatment pairs remain controlled candidates without Q and conditionally qualified with the exact selected Q. Four-run matrix stays 3 qualified BASE edges / 3 illustrative treatment edges. Four disposable checksum/missing/source/environment faults reject. No trajectory or qualification publication. |
| HTML generation/content |PASS: actual AppTest download-button path produces a 5,350,055-byte report for hairpin/preparation_ready rows 5–104. Its 906 native state-row identities, 100 actual event payloads, source/manifest/run identity and limits are exact. Full hash check occurs before publication. Generation 0.076 s; complete AppTest button interaction 0.755 s. These timings are descriptive. |
| Local reopening |PASS: the same generated file reopens in the real browser through an isolated loopback static server, with rendered Plotly whole-track context and exact source/sector/event metadata. No Workbench/controller process serves it. HTML has no external script/style dependency or form. System internet was not disabled; dependency inspection and self-contained local rendering establish that no internet asset is required for this view. |
| Browser automatic download |**NOT CONFIRMED within 10 s**, explicitly not counted as a successful download. Same-source vehicle-vx/hairpin browser preparation displayed the button in 1.444 s; one click returned in 0.298 s, with no observed console error or new matching Downloads file. Native Codex dialog inspection was refused by the computer-use tool; no bypass/repeated download attempted. |

The earlier 1,558.497s browser-tool return remains preserved. This check uses a different observation
method, avoiding event/path-wait APIs; it neither reproduces nor establishes the original cause and
makes no performance-improvement claim. Core report generation and local reopening pass; automatic
file delivery through the embedded browser remains a **nonblocking platform limitation**, not an
asserted application failure or a verified download success. User acceptance must retain that limit.

## Launcher exit-status disposition

The unchanged executable launcher passes shell syntax, actual startup from an unrelated directory,
loopback identity/ownership/HTTP, second-launch reuse of the same listener, unrelated-listener refusal,
legacy-app refusal without takeover and the missing-environment branch using an exact disposable copy.

Two predetermined interrupt checks were run once each:

- SIGINT directed to the owned supervising Python process: actual launcher exits 0, owns/terminates
  its server and releases8501.
- Actual PTY Ctrl-C (`0x03`, ISIG enabled) to the verified foreground process group: shell wait status 2
  means **termination by SIGINT(2)**, not an ordinary numeric exit code. Port release completed in
  0.513 s, with no surviving owned process. Logs show the normal stopping path and no traceback.

The earlier tool-reported exit1 is not rewritten as0 or proven to have a unique cause. Fresh evidence
distinguishes supervisor exit from terminal/process-group signal termination and demonstrates safe
owned cleanup under both. Disposition: **no blocking shutdown/resource-leak defect demonstrated**;
terminal/session status remains route-dependent. No launcher change or favorable retry.

## Preservation and decision

Before/after content hashes match all 428 reviewed behavioral files, all 56 frozen scientific files,
all 345 qualification files, 25 GP files, 4 legacy oval files and 42 retained WORK/reviewer evidence files.
The 56 also match accepted V0.2 Git `4897686e79c13757d5ef5b4373b44d4cab99b5bf` directly.
All 49,675 preexisting result size/mtime observations and 1,713 symlink targets are unchanged; this
metadata check is **not** a full content rehash of every historical result. Old failure/reviewer
correction attempts remain separate and unchanged. No frozen profile, threshold, dependency or source
was altered. Both owned loopback listeners are closed and the execution lease is available.

No blocking application finding remains in the agreed single-P-archive scope. Recommend acceptance
of this exact V0.3-D software within that scope, retaining the embedded-browser download limitation
and original synthetic/resource/platform boundaries. The successful P archive contains no failure/
fallback episode: broader M4 C0/asynchronous failure-archive inspection remains subsequent separately
contracted work, not a defect or a demonstrated capability here. G/C70 remain unsupported. RBT-S/N/V,
numerical budgets and future G/P execution decisions remain with Primary; no implementation or run.

**Stop: V0.3_D_VERIFIED_PENDING_USER_ACCEPTANCE_AND_RBT_DECISIONS.**
