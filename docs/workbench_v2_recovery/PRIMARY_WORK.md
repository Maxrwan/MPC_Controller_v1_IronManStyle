# PRIMARY APEX — V2 FULL-LAP POSTPROCESSING RECOVERY

**Decision: AUTHORIZE BOUNDED SOFTWARE CORRECTION AND READ-ONLY EVIDENCE RECOVERY**

Repository: `Maxrwan/MPC_Controller_v1_IronManStyle`

Branch: `codex/workbench-v2-ui`

Latest delivery: `3b2bdb0dd9c1f1b633216c3d0862e5de200e0906`

Reviewed numerical implementation: `740a268a2d2c6b92a67a45456292a3b2cafb2479`

Frozen scientific source: `48adbdf64d492592d15e23c917aca71fa58aa8a5`

## Objective

Recover normal read-only Workbench replay and scientific analysis of the retained native full-lap recording.

The native runner successfully recorded one complete 31.1719003976093-second circuit. Workbench postprocessing subsequently failed because its lap-duration validator rejected valid NumPy floating-point scalars.

The original run is authoritatively failed, with valid retained evidence. Preserve that status.

**Do not execute the simulator again.**

## 1. Correct scalar validation

Inspect:

- `tools/apex_workbench/lap/analysis.py`
- `tools/apex_workbench/nmpc_analysis.py`

The native `lap_times` are positive finite `numpy.float64` values.

Implement the smallest technically sufficient correction to accept valid native NumPy floating-point scalars alongside built-in Python floats.

Preserve rejection of:

- NaN and infinity.
- Zero or negative crossing durations.
- Boolean values.
- Strings, arrays and unsupported numeric objects.

Ensure reconstructed lap values serialize correctly and retain numerical precision.

Avoid changing unrelated global validation semantics unless necessary.

## 2. Recover read-only access to the existing archive

Inspect `lap/evidence.py` and the current Workbench UI ingestion paths.

The failed run contains 39 validated manifest artifacts, including native data and presentation data, but lacks `summary.json` and `worker_result.json` because postprocessing failed.

Support an explicit read-only recovery/inspection path for this case.

Requirements:

- Verify the original status, manifest and every listed artifact.
- Preserve source, environment, run and evidence identities.
- Use only existing retained observations.
- Never invent missing summary fields.
- Never overwrite native, derived, journal, status, manifest or historical files.
- Never change the authoritative lifecycle outcome from failed to completed.
- Clearly label recovered metrics as descriptive observations from a failed Workbench run.
- Reject or quarantine malformed, incomplete or altered evidence.

If necessary, construct a transient in-memory analysis view from verified retained files without writing a replacement summary.

Normal successful-run validation must remain unchanged.

## 3. Restore playback and analysis

The existing V2 interface should reopen the genuine recording and provide:

- Full recorded vehicle trajectory.
- Automatic verified replay-window continuation.
- Actual active NMPC packets.
- Nine-node prediction microscope.
- Native applied commands and steering visualization.
- Tracking and heading errors.
- Recorded full-lap and sector times.
- Solver and grip diagnostics.

Reuse existing scientific metrics and the V2 renderer.

Do not build another interface.

Prevent this failed archive from being misclassified as a completed or qualified experiment in controlled comparisons, acceptance logic or execution admission.

## 4. Exact recovery checks

Using the retained original archive, verify:

- Native runner stop reason: `target_laps`.
- First crossing: approximately 31.061572635639408 s, excluded as partial.
- Complete lap: 31.1719003976093 s.
- Native stop: approximately 62.235 simulated seconds.
- Four sectors: 8.6251447, 7.0235541, 7.9810996 and 7.5421020 s.
- Complete-circuit lateral RMS: approximately 0.0209503 m.
- 623 recorded successful solver preparations.
- All 39 original manifest members remain valid.
- Failed / valid-evidence / exit-2 execution status remains unchanged.

Validate actual replay behavior in the existing browser.

Run focused tests for NumPy scalar handling, missing-summary recovery, evidence mutation rejection and preservation.

A short independent integrity check is appropriate because the archive reader is changing. Do not launch another broad scientific Engineering Review or Verification campaign.

## 5. Authorization boundaries

No optimizer solves, plant steps, simulator execution, additional full-lap attempt, pilot, retry or numerical campaign.

Do not reset the consumed full-lap authorization slot.

Do not alter accepted NMPC/TVLQR dynamics, scientific source, scheduling, execution limits or historical data.

Do not silently activate accepted-interactive V2 execution in this correction.

## 6. Deliverables

Provide:

1. Exact root cause and corrected source revision.
2. Focused test results.
3. Confirmation that the original full-lap recording opens in Replay and Analyze.
4. Recovered numerical summary explicitly identified as descriptive.
5. Original failed lifecycle and evidence-preservation confirmation.
6. Any remaining obstacle to normal accepted-interactive V2 use.

Stop at:

`WORKBENCH_V2_FULL_LAP_RECOVERY_READY_FOR_PRIMARY_ACCEPTANCE`

**Priority: Recover and use the successful native circuit observation without repeating an expensive numerical experiment or compromising scientific provenance.**