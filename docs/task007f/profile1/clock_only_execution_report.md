# F-C3 one-shot clock-only execution report

**ONE_SHOT_ATTEMPT_COMPLETE_PENDING_REVIEW. WORK_COMPLETE_PENDING_REVIEW.**
Recorded 27 October 2026. One invocation was actually made under the human F-C3 decision.
All ten mandatory preflight gates passed; no retry or alternate experiment occurred.
This is factual execution/mechanics evidence, not scientific acceptance of a clock allowance.

Documentation authority: `b53d92f8284e5f1c87c86b05916ea3019bba859f`.
Executable implementation: `c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a` in the clean detached
`/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle_FC1_c99b9df` checkout. The literal command in the approved protocol was
passed unchanged to the shell exactly once. It retained the approved mode, clock_probe fixture,
source-root, reviewed SHA, output, sanitized environment and console redirection. No manual
--_worker or --clock-allowance flag was supplied. Ledger/command hashes are preserved below.
The delivery commit containing this report binds the documentation only; it is not a new run SHA.

[Machine-readable delivery record](clock_only_execution_record.json),
[original protocol](clock_only_protocol.json), [approved limitations](clock_only_environment_and_resources.json).

## Verified preflight

All ten gates passed immediately before invocation: exact clean detached HEAD/remote; eleven
source/test/helper hashes and unchanged b53d92f package bytes; CPython executable/libpython/
header/BUILD/747-file stdlib inventory; runtime arm64 CPython 3.12.14 and prefix; exact eighteen
copied psutil 7.2.2 distribution files; isolated parent and child startup origins; fresh empty
cache/no unexpected startup hooks; fresh output and owned supervisor envelope; disk headroom;
no known competing measurement process or guard; and exclusive owner reservation/start identity.

Runtime preflight inspected parent with -S and child-style startup without -S; these were identity
checks, not additional clock workers. The parent imported psutil solely from the approved copy;
child-style startup imported neither it nor any numerical package. No mutable .venv or foreign
research origin was present. Cache paths remained isolated; G1 source was not changed.

The preflight process scan examined 509 processes, excluded only the supervisor's own ancestry,
and found no relevant competing process or existing measurement guard. Relevant roots included
Efficiency, detached G1, Safety and CT-1. The supervisor reservation records PID 25831, actual
OS process-start identity/command and UTC acquisition. Free disk at final admission was
14,908,563,456 bytes, above the approved 2 GiB initial requirement.
This owner reservation plus observation is not an atomic global OS admission lock.

## Actual counts and mechanics

| Observation | Actual result |
|---|---:|
| Clock-only invocations | 1 |
| Clock-probe calls | 1 |
| Standalone clock_empty spans | 1,000 |
| clock_parent spans | 1,000 |
| Nested clock_child spans | 1,000 |
| Total begun / closed spans | 3,000 / 3,000 |
| Wall / process CPU endpoints | 6,002 / 6,002 |
| Missing endpoints / open spans | 0 / 0 |
| Recorder faults / negative exclusive residuals | 0 / 0 |
| Literal launcher / clock child exit code | 0 / 0 |

Raw endpoints are non-Boolean integer nanoseconds and nondecreasing within each clock.
Unique tokens/sequences, the exact auxiliary parent graph and occurrence identities were audited;
each nested child has occurrence 1 under its distinct parent. Signed inclusive/exclusive values
were independently recomputed from existing raw endpoints, subtracting immediate complete
children only. No zero substitution, clamp, new clock reading or tolerance fitting was used.

The raw clock-call envelope is 11,709,125 ns wall / 11,701,000 ns process CPU. This includes
recorder loop/bookkeeping observation and is not pure clock-read cost, solver time, precision,
controller speedup or full software latency. No per-call cost correction is inferred.

Clock metadata names mach_absolute_time() and clock_gettime(CLOCK_PROCESS_CPUTIME_ID), both
monotonic/non-adjustable. Reported resolutions are nominal metadata, not measured error bounds.
The export is complete and its SHA matches the actual file. However, **observer_validity remains
incomplete**, reconciliation allowance_status is **unresolved**, and clock_allowance is null.
structural_valid and clock_order_valid are true. Exit zero does not resolve those scientific gates.
raw_not_returned=true is intentional for this no-physical-population probe, not lost simulation data.

## Actual resource and supervision observations

Literal invocation UTC start: `2026-10-26T22:34:11.853721+00:00`; end: `2026-10-26T22:34:12.686983+00:00`.
Whole literal-invocation wall time was **0.833299333 s**, including shell/Python startup, parent,
clock child, export and cleanup. It is separate from the recorder envelope above.

The reviewed parent retained five direct-child RSS/CPU/thread observations at elapsed
0.001776, 0.105013, 0.210261, 0.315508 and 0.420734 seconds from its own monitoring origin.
Maximum **sampled** child RSS was **42,385,408 bytes** (40.421875 MiB); this is not a true peak.
All samples reported one process thread; that is not proof of universal native-thread control.
The last observed child CPU values were 0.216042576 s user and 0.021119666 s system; final CPU
was not measured by that last sample. No resource timeout or termination escalation was observed.

Final worker-directory logical size was **1,757,731 bytes** across six files. Additional external
observations retained output sizes [0, 12100, 16203, 1757731]. The supervisor
envelope/logs, copied dependencies and checkout are outside that worker-directory limit.
Parent output/RSS/CPU observation is sampled; no hard memory/output quota, process-group kill,
whole-parent deadline or hard 30/32-second bound is claimed. Approved two-second grace and
unbounded-final-wait paths were not needed in this attempt.

Four external process/guard observations found no confirmed competing measurement process.
One observation at 0.712523375 s enumerated the expected own-output MEASURED_ACTIVE path,
then found it no longer a regular file when reading ownership. This is **consistent with normal
reviewed parent cleanup**, but ownership at that instant was unavailable. The original
unexpected_guards/content=null row is preserved verbatim and classified as a non-atomic
own-guard cleanup observation gap, not erased or promoted to an observed owner identity.
The last external observation-to-return tail was about 0.120776 s and was not fully sampled.

The launcher guard and supervisor reservation were both removed through their own normal owner
cleanup. No remaining MEASURED_ACTIVE/D3_ACTIVE guard or partial export was found. No unknown
owner guard was deleted. The observation gap remains available for Engineering disposition.

## Actual imports and preserved evidence

The actual parent verbose trail contains only vetted base Python/stdlib, copied psutil/native
extension, and pinned threading_study.config. The latter's environment helper was used; no
Accelerate configuration API was called on the clock route. Actual child imports are stdlib
plus pinned task007f.profile1.recorder and its namespace parents. NumPy, SciPy, CasADi, IPOPT,
APEX control/model/simulation, threadpoolctl, test modules and foreign research origins were
not found. Loaded source/extension paths were allowlisted and hashed in import_origin_audit.json.
This verbose-trail audit is not an import sandbox or structured final sys.modules manifest.

Actual worker directory: `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1/fc1-clock-c99b9df-001`.
Actual supervisor envelope: `/Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/results/task007f/profile1/fc1-clock-c99b9df-001-envelope`.

All six produced worker files exist: clock_metadata.json, clock_probe_counts.json,
preparation_sidecar.json, sidecar_export.json, parent_exit.json and worker.log. The envelope
preserves the actual parent_console.log, setup/runtime identity/import preflights, owner/process/
guard preflight, invocation ledger, supervisor observations/result, release record, source/stdlib/
repository preservation snapshots and factual execution_review.json. External supervisory,
identity and audit source bytes were archived verbatim afterward as provenance, without replay.
No missing worker output was backfilled; no failed/partial record was discarded or replaced.

The full file-by-file path/size/SHA256 inventory is delivery_artifact_hashes.json (30 files,
excluding that manifest itself), also embedded in clock_only_execution_record.json.
Manifest SHA256: `7736bad8872e21f6c35b75e8fcba8dae84968d3ca42db36b832cfa651348da2e`.
Raw preparation_sidecar.json SHA256:
`6bf979124574fdc4d4e6072e80d93bcd786d11b5cce7c9857dce93b9b6449c83`.
Original artifact_hashes.json remains intact as the earlier audit snapshot; later provenance is
additive. Large raw evidence is retained locally under ignored results, not silently treated as a
Git-backed archive or backup. No source evidence/partial was reconstructed.

## Preservation, delivery and remaining review

Immediately after the attempt and before documentation authoring, all 862 original tracked files
matched their preflight hashes, all 11,646 original results files retained size/mtime metadata,
all eleven pinned G1 hashes matched and the 747-file base stdlib inventory was unchanged.
This is not a full rehash/backup of the historical raw archive. The detached checkout remains
clean at G1. Frozen main/release E4/tag and accepted manifest are unchanged. Safety/CT-1 remain
independent; no source, configuration, dependency or existing test was edited.

The delivery adds this report and clock_only_execution_record.json and prepends the scoped
result to docs/CODEX_HANDOFF.md. Original F-C1/G1 documents remain historical and byte-identical.
The exact delivery SHA/URL is supplied after normal commit/push; the executable SHA stays G1.

**One authorized attempt is consumed. No retry or continuation.** Engineering and Primary must
review the actual raw records, unresolved observer status and retained supervision gap before
any later decision. **No clock-reconciliation allowance was calculated, proposed or approved.**
No numerical controller/optimizer/vehicle simulation or test suite ran; no other 43 proposed G2
workers, Phase B, historical warm reconstruction or controller tuning ran. There is no numerical
speedup, timing-certification, full-software-latency or physical-safe-stopping acceptance claim.
Final exit: **WORK_COMPLETE_PENDING_REVIEW**.
