# V2 resumed Full Lap — retained run, postprocessing failure

**V2_FULL_LAP_FAILED_PENDING_PRIMARY_DECISION**

Primary accepted final V2 UI and authorized one resumed unused Full Lap attempt, without source
changes, another pilot, a new slot or retry. Execution used reviewed implementation
`740a268a2d2c6b92a67a45456292a3b2cafb2479`, delivery
`f85ac524e3bca686b4971c005fda11d1bae84d5c`, branch `codex/workbench-v2-ui`, unchanged frozen science
`48adbdf64d492592d15e23c917aca71fa58aa8a5` and the successful original 10-second pilot.
Exact command, gates, source identities, metrics and local artifact hashes:
[machine record](full_lap_resume_record.json).

## Admission and execution

The fresh host gate passed on 2026-11-11 at 11:57:42 Cairo time (09:57:42 UTC): RAM
1,788,477,440 bytes exceeded the unchanged 1,610,612,736-byte threshold. The preferred 2 GB margin
was not available, but is not an admission requirement. Disk was 21,112,688,640 bytes; no competing
process or active measurement guard was found. Source/environment and existing ownership/lease
checks passed. Wall/CPU/RSS/output/file/simulation caps remained 900s /720s /768MiB /256MiB /4MiB /80s.

The driver was invoked exactly once for this resumed assignment. It consumed the preserved Full Lap
slot and started run `2026-11-11T095747.505385_0000_6a18eaab96bd4949835d7c481116806e`.
No additional pilot, parameter change, disturbance, automatic retry or new authorization slot occurred.

## Observed result and failure

The native runner reached `target_laps`, with no recorded native model/control failure, at simulated
62.235s. Its retained crossing intervals are 31.061572635639408s (partial launch crossing) and
**31.1719003976093s** (one complete finish-line-to-finish-line circuit on the 154.76345492731022m track).
The first partial interval is excluded from the complete lap.

Workbench postprocessing then raised `ValueError: Invalid native lap-crossing interval` at
`tools/apex_workbench/lap/analysis.py:17`, called by `worker.py:180`. Source inspection and a
scalar-only reproduction identify a type mismatch: the canonical runner's crossing expression
produces positive finite `numpy.float64` durations, whereas `nmpc_analysis.numeric` accepts only
exact built-in `int`/`float` types. The unchanged validator rejects those native values. The exact
positive values survive JSON serialization; reading them as built-in floats makes the existing
lap calculation succeed. This read-only reproduction did not simulate, solve, change source or
rewrite the execution outcome.

Terminal Workbench status remains **failed / evidence valid / exit2**. Neither `summary.json` nor
`worker_result.json` was emitted. The actual production reader also rejects the failed native-bearing
archive with `IntegrityError: Unverified artifact summary.json: 'summary.json'`. This is an additional
failed-run inspection limitation, not missing or corrupted recorded telemetry. No summary was
fabricated, status repaired, archive promoted or successful-run acceptance proposal generated.

## Retained measurements

These are read-only descriptive results from hash-verified native/derived files of the failed run,
not an official completed Workbench summary. Sector timing uses the existing within-native-segment
progress-crossing convention; scientific telemetry is never interpolated.

| Complete-circuit measure | Retained result |
|---|---:|
| Lap interval | 31.1719003976093s |
| Quarter-distance sector 1 | 8.625144717830757s |
| Quarter-distance sector 2 | 7.023554059383791s |
| Quarter-distance sector 3 | 7.981099618438272s |
| Quarter-distance sector 4 | 7.542102001956479s |
| Native samples within complete circuit | 6,234 |
| Racing-reference lateral error RMS / peak absolute | 0.02095028863796588m /0.09905057325957668m |
| Racing-reference heading error RMS / peak absolute | 0.063978705467237rad /0.20550183972434422rad |
| Mean / peak recorded longitudinal speed | 4.9303862319574545m/s /5.966550232827406m/s |
| Boundary-violation rows | 0 |

Across the entire retained recording: 12,447 states, 6,223 controls, 623 preparations/packets,
621 handoffs, 622 releases, zero planner/codriver misses and zero fallbacks. All 623 solver records
report `Solve_Succeeded`; the final prepared packet remains incomplete/pending at the stop, rather
than acquiring authority. Mean/maximum host solve duration was 0.03249935662193765s /0.1737794999498874s;
mean/maximum iterations 12.18940609951846 /18. These host durations are distinct from the approved
controlled simulated packet-availability pattern; no real-time or physical validation is claimed.

Supervisor wall runtime was 160.7565652920166s; sampled peak worker RSS 236,503,040 bytes;
retained output 39,627,994 bytes; largest file 2,097,097 bytes. No resource-abort record exists.
Total worker CPU time is unavailable because summary construction failed before retaining it.

## Preservation and disposition

All 39 manifest members validate; manifest SHA-256:
`b6b8b56c9d70906860f471203f1cdef947b8fd2d573b9f05b66ad3e0278c8ba5`.
Pre/post source and numerical environment identities match. All 47 reviewed producers, 333 frozen
runtime files and 335 canonical/configuration/dependency files remain unchanged. Historical
13,280 files /573 links were rechecked: only the existing access policy changed, by consuming its
previously unused Full Lap slot. The original pilot, old blocked RAM observation, reviews and
scientific evidence remain intact. Worker/supervisor exited before analysis. Raw logs, journals,
native/derived chunks and inspection negatives remain locally retained and hash-referenced;
this is not an off-host backup claim.

No source or test change, new Engineering Review, pytest suite, broad Verification, acceptance
installation or numerical rerun occurred. This delivery changes documentation only.

The native circuit is recorded, but ordinary user-triggered V2 admission is **not enabled**: this
attempt is spent and the successful-run acceptance condition is not met. Recommend a separate bounded
Primary corrective WORK decision for native NumPy scalar validation and failed-archive inspection,
with the original failed evidence and slot consumption preserved. Do not reset the slot or infer
authorization for another execution from this report. Any later source-bound acceptance transition
must follow its applicable review/acceptance contract; no transition was installed here.
