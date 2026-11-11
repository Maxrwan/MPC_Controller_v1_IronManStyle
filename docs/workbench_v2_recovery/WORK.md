# V2 retained full-lap recovery

Starting delivery `3b2bdb0dd9c1f1b633216c3d0862e5de200e0906`, branch `codex/workbench-v2-ui`.
[Primary authorization](PRIMARY_WORK.md) permits software correction and read-only recovery only.
The recorded numerical source remains `740a268a2d2c6b92a67a45456292a3b2cafb2479`; frozen science
remains `48adbdf64d492592d15e23c917aca71fa58aa8a5`. No simulator, optimizer or plant execution occurred.

**WORK complete; short independent integrity check pending.** Exact source and machine evidence are
recorded in `work_record.json`; delivery SHA is supplied after committing.

## Correction and admission

The runner computes crossing durations from NumPy arrays. The lap validator called a global
JSON-number guard that deliberately accepts only exact Python int/float types, rejecting finite
positive `numpy.float64` durations. Only lap validation now converts native NumPy float16/32/64
scalars to built-in floats, an exact conversion for those binary formats. It preserves precision and
JSON serialization, and still rejects NaN/infinity, zero/negative durations, bool/NumPy bool, strings,
arrays, complex, NumPy integers, Decimal/Fraction and unsupported scalar formats. The global guard
and canonical runner remain unchanged.

`evidence.read_run(..., recover_failed=True)` explicitly admits the approved original capture only,
bound to its exact run ID, original status SHA and original manifest SHA. The default strict reader
and successful-run requirements remain unchanged. Recovery verifies all 39 original manifest members,
complete native/derived row correspondence, captured parameters/source/environment and current
evidence epoch. Missing, changed, extra or re-sealed files are quarantined; new file membership is
also checked during presentation. Existing primary and compatibility inspection paths opt in and
show a persistent **descriptive observations from a failed Workbench run** warning.

The transient view has a recovery annotation and **no summary field**. It supplies no missing CPU,
coverage or worker-result value, writes no archive artifact and retains failed / valid evidence /
exit2 status. Native complete-circuit observations do not imply completed execution. Comparison now
also requires both authoritative lifecycles completed/valid/exit0 and neither recovered; an otherwise
matching recovered full lap remains noncontrolled/unqualified. Execution and acceptance code are
unchanged; recovery cannot satisfy their successful-run condition.

## Focused and actual-browser evidence

Final focused invocation: **137 passed, 1 deliberately deselected, 0 failures/skips, 47.12s**.
It covers scalar rejection/precision, original exact observations, disposable corruption/deletion/
resealing, post-read replacement, comparison/acceptance exclusion and existing V2 UI/admission tests.
No controller, plant, simulation or CasADi modules were imported; read-only geometry helpers closed.
The excluded unchanged source-configuration subprocess imports scientific execution modules and was
unnecessary here. A prior separate 137-pass invocation (45.24s) preceded the circuit-RMS display
addition; counts are not combined. A subsequent strengthened acceptance-guard test passed once
(2.59s), isolating authoritative failed lifecycle from stale-source and strict-reader rejection.
No production code changed after the 137-pass invocation. Ruff passed after a line-length correction; tooling initially
looked for Ruff in the Workbench venv, then used the existing main-checkout tool without installation.

Actual IAB browser on the normal V2 launcher, started from `/private/tmp`, reopened the genuine
archive. All seven native windows are selectable. Playback automatically continued across verified
10s boundaries, with changed payload epochs and no scientific time accrued during verification.
Observed live packet375 at native37.585s and packet621 at the final native62.230s; all nine nodes,
eight intervals and terminal command absence remain. Final applied steering was the original
0.055711912693227825rad, applied62.225s from request62.22s, with its distinct nominal overlay value.

Analyze reopened Tracking, Actuation & grip and Solver & events. It shows the whole-record overview
separately from the descriptive full-circuit RMS, lap/sector metrics and native solver/grip channels.
The failed-run warning remains visible. Run stays disabled; no execution control was triggered.
IAB iframe pointer operations failed twice, while keyboard actions completed the same replay checks;
these harness observations are retained, not application failures. Screenshots and DOM observations
are local under `results/apex_workbench_v2_recovery/`, hash-referenced in the machine record.

## Recovered descriptive observations

Original run: `2026-11-11T095747.505385_0000_6a18eaab96bd4949835d7c481116806e`.

| Observation | Retained value |
|---|---:|
| Native stop reason / stop time | target_laps /62.23500000000001s |
| First crossing, excluded as partial | 31.061572635639408s |
| Complete-circuit interval | 31.1719003976093s |
| Four quarter-distance sectors | 8.625144717830757 /7.023554059383791 /7.981099618438272 /7.542102001956479s |
| Complete-circuit native samples | 6,234 |
| Complete-circuit lateral RMS | 0.02095028863796588m |
| Entire recording states /controls /preparations | 12,447 /6,223 /623 |
| Recorded successful solver preparations | 623 |
| Authoritative lifecycle | failed /valid evidence /exit2 |

Metrics reuse existing native-sample and within-native-segment crossing functions, never resample
telemetry or rerun physics. They remain synthetic/experimental/unqualified. Replay ends at the last
recorded state62.230s, before the final integration stop62.235s; it does not extrapolate to the later
crossing. Recorded crossing/sector measurements remain accessible in Analyze. Whole-record RMS
includes the initial partial circuit and therefore differs from the explicitly labelled circuit RMS.

## Preservation and remaining gate

The original 39-member manifest, failed status, native/derived/journal bytes, pilot, reviews and
consumed Full Lap slot remain untouched. Summary and worker-result files remain absent. Protected
scientific/configuration/dependency files, execution/resource/admission code, renderer/clock and
launchers are unchanged. Detailed before/after inventories and source hashes are in the machine record.

Normal accepted-interactive V2 execution remains a separate decision. Current producer hashes now
differ from the old reviewed-WORK policy, both historical slots are consumed, and the authoritative
failed run cannot meet the current successful-run acceptance-proposal contract. No policy was
re-sealed, no slot reset or added, and no repeatable execution was activated. Primary must separately
decide the source-bound interactive admission contract; recovered observations do not silently grant it.

Stop at `WORKBENCH_V2_FULL_LAP_RECOVERY_READY_FOR_PRIMARY_ACCEPTANCE` after the short integrity check.
