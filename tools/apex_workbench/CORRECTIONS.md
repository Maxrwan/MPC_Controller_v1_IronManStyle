# Workbench V0.1 R1–R6 corrective WORK

**WORK_COMPLETE_PENDING_REVIEW.** Authorized baseline:
`5495781d461236d1e562e1280e594a0e8dc43e20`, branch `codex/apex-workbench-v0-1`.
The original implementation and [failed Engineering Review](../../docs/reviews/apex_workbench_v0_1/REVIEW.md)
remain historical and unchanged. This candidate needs a new Engineering Review; no formal
Verification, V0.2, scientific tuning, new adapter or dependency is introduced.

## Resolution matrix

| Finding | Correction and invariant | Focused evidence |
|---|---|---|
| R1 | Supervisor passes the same execution-lock descriptor to the worker. The worker retains it until exit and independently checks supervisor birth/command identity, cancellation and existing limits. Signals require verified worker birth time, full command, role and run path. Stale corrected records reconcile under the lock; uncertain outcomes are interrupted, not successful. | Real worker briefly suspended, supervisor SIGKILL, second launch rejected while worker alive; resume causes independent self-exit. Both supervisor-loss and cancellation-after-loss cases pass. PID reuse/wrong-owner tests send no signal. |
| R2 | Initial request/status are written in a hidden fresh staging directory and published together. Readers exclude incomplete records with a retained-record warning. | Two AppTest sessions during the paused publication window have no exception; both read the completed record afterward. Injected publication interruption remains unselectable and preserved. |
| R3 | fsynced temporary JSON is linked exclusively into an append-only note filename; no partially written final filename is visible. Readers retain/skip malformed historical notes. | Paused writer, concurrent readers, two concurrent writers and interrupted publication preserve prior versions without JSON decode failures. |
| R4 | Verified scientific source, model/tire/vehicle/controller, geometry, timing, numerical environment and telemetry schema/units determine eligibility. Changed inputs and fingerprint differences are explicit. Git revision alone is excluded. | Controlled real-duration comparison; documentation-only revision change remains controlled. Source/composition/track/timing differences are illustrative; incompatible units are invalid. UI labels and overlay gating pass. |
| R5 | An exclusive execution receipt preserves scientific outcome. Status is finalizing while hashes/manifest are prepared; final status commits the manifest hash last. Evidence failure has a separate failed state even after scientific completion. Interrupted finalization recovers conservatively. | Injected manifest-hash failure yields scientific outcome completed, evidence failed, explanatory error and quarantined telemetry. Interrupted final commit recovers the known receipt; a receipt cannot be relabeled. |
| R6 | Selected CSV/JSON artifacts and new manifest anchors are verified before ingestion. Changed/incomplete/unverified data is quarantined. A bounded cache includes expected hash, inode, size, mtime and ctime. | Changed CSV/request/manifest rejected; same-size edit plus restored mtime still invalidates the cache. Tampered UI comparison renders no plot. Unrelated artifacts are not read. |

Record version 2 is a tooling/evidence correction, not a change to the canonical telemetry state
order or scientific implementation. The worker exports its telemetry contract using canonical
STATE_NAMES/UNITS and CONTROL_NAMES/UNITS. No absent numerical telemetry is synthesized.

## Focused checks and applicability

- **49 Workbench tests passed** on the final candidate contents. This includes the original 17
  cases, all new regressions, the real UI execution and both original-entry-point parity tests.
  Supervised dynamic and LQR outputs also match direct adapter/original-entry-point states,
  controls where applicable, and summaries byte for byte. Native controls remain SINGLE.
- **68 selected scientific unit tests passed** (`test_frenet.py`, `test_baseline.py`,
  `test_runner.py`) in the preceding combined invocation. That log reports 99 passes and 18
  setup errors in Workbench comparison-dependent cases. The scientific files, fixtures,
  transitive canonical/script dependencies, dependencies and environment did not change afterward;
  those 68 applicable passes are reused, not claimed as a fresh rerun or full repository acceptance.
- Ruff check/format, whitespace, documentation links, source hashes and preservation checks
  accompany the [machine-readable correction record](correction_record.json).

Final Workbench command, from the repository root:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:scripts:src \
tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; native=configure_accelerate(1); import json, sys, pytest; print(json.dumps(native)); raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tools/apex_workbench/tests --durations=6 \
--basetemp=results/apex_workbench_corrections_20261027/confirmed-pytest \
> results/apex_workbench_corrections_20261027/confirmed-tests.log 2>&1
```

The combined scientific selection appended `tests/unit/test_frenet.py tests/unit/test_baseline.py
 tests/unit/test_runner.py`; its exact command/environment is recorded in the JSON. All output
locations were fresh; do not rerun into retained evidence directories. The original review harness
was read and its SIGKILL/barrier/altered-file/hash-fault scenarios were adapted into corrective
regressions with positive assertions. The historical negative-assertion harness/report was not edited.

## Retained negative evidence

Local logs and all run records remain under `results/apex_workbench_corrections_20261027/`:

1. Initial existing selection: 17 passed.
2. Initial new selection: 26 passed, one LQR interruption. The worker guard observed a Matplotlib
   font-cache lock file disappear between scan and stat. The run remained interrupted. The sampler
   now skips only vanished files, retaining fail-closed behavior for other monitoring faults;
   a regression checks this case. No scientific assertion or resource bound was weakened.
3. Sampler-repair selection: LQR/worker parity passed; the new sampler test had a missing Path
   import (NameError). That test-only import was corrected. Both log and source-failure context remain.
4. Combined selection: 99 passed, 18 setup errors sharing one seed fixture. The next seed was
   submitted after terminal status but before supervisor lease release. Descriptor release is now
   explicit after finalization, and sequential test waits require the lease to be free. The rejection
   was retained; no lock check was bypassed or unrelated worker terminated.
5. Final Workbench selection: 49 passed, zero failures/skips.

This is corrective functional testing, not a latency study. SIGSTOP is used only briefly to force
the process-ownership race; no physical timing or trajectory conclusion is drawn from that probe.
No expensive regression, benchmark, NMPC, async planner, measured-latency, VIS-2, Efficiency or
hardware campaign ran. Original historical result files and failed-review bytes are preserved.

## Remaining limits and next gate

- Guard deadlines/RSS/output checks are sampled and depend on Python/OS scheduling. A suspended
  worker retains its lease and cannot admit an overlapping run. Kernel CPU/file limits remain;
  none of this provides physical stopping, a hardware watchdog or hard real-time qualification.
- This implementation is checked on the existing macOS/local-filesystem setup. flock, same-directory
  rename and hard-link publication are required; network filesystems and power-loss durability
  are not qualified. Complete storage failure may prevent an error record from being written;
  recovery remains conservative and never manufactures successful evidence.
- Historical records are not migrated or rewritten. Legacy artifacts can be inspected individually
  only with valid recorded hashes; records lacking the new telemetry comparison contract are invalid
  for controlled comparison. Failed/censored outcomes remain available individually.
- Hash validation detects mismatches against retained metadata; it is not cryptographic authentication
  against someone rewriting all records. Keep scientific source stable during a run; source hashes
  record launch identity. No physical-model validity is inferred from parity or process success.

No R1–R6 issue is intentionally deferred in this candidate; the resolution claims await Engineering
Review. Next: inspect the exact correction commit and evidence, decide on any further correction,
then separately authorize formal Verification. Full regression/resource-exhaustion qualification
and V0.2 remain outside this WORK delivery.
