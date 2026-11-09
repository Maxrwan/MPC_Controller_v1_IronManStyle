# Bounded package validation — 9 November 2026

**WORK_COMPLETE_PENDING_REVIEW**

**STOP: PI COMPUTATIONAL BENCHMARK PACKAGE READY FOR HARDWARE TESTING.**

Base checkout: `d14f9ade48e9fdd3c9bb904cd9b58fd504e73035`.
Branch: `codex/pi-compute-benchmark-v0`.
Machine record: [validation_record.json](validation_record.json).

## Executed

- Built the pinned Python 3.12.14 image on a **Linux ARM64 Docker Desktop VM** on
  a Darwin ARM64 host. Exact hash-checked Linux ARM64 wheels resolved and installed;
  `pip check` passed. CasADi 3.8.1's original IPOPT plugin executed successfully.
  No optimizer, version or numerical-option substitution was needed.
- Docker build startup checks performed genuine frozen NMPC preparation and a TVLQR
  update. The observed tracker returned exactly the unwrapped tracker's command.
- Compared all **66 copied files**, including **57 Python modules**, byte-for-byte
  with frozen scientific revision `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
  All copied runtime/configuration files also match producer `e577f2c…`.
  The package checks those source/configuration hashes before execution and records
  harness hashes, resolved configuration and imported APEX identities.
- Focused ARM64 tests: **9 passed**, zero failures/skips. Controlled failed-solver
  reporting, process timeout/kill retention, partial-journal recovery, hash rejection,
  strict JSON, timing quantiles/populations and bounded scenario identity were checked.
  The first invocation passed with file-handle warnings; those warnings were fixed,
  and the second invocation passed cleanly. Both logs remain retained.
- One invocation of the actual read-only/offline `run.sh` launcher executed all three
  2-second closed-loop windows. Each completed at exactly 2 simulated seconds with
  no solver failure, unprepared packet or fallback. There were **60 real IPOPT calls**
  (3 startup/cold, 57 recurring/warm) and **599 actual TVLQR updates**.
- All sampled worker process thread counts were one. Loaded NumPy/SciPy/CasADi
  OpenBLAS pools reported one thread. Sampled per-thread CPU deltas and actual loaded
  native-library identities are retained, with their observation limits.
- Ruff lint/format, shell syntax and scoped diff checks passed for the new harness.

## Retained scheduling observation

The high-curvature window recorded one `codriver_busy` tick at synthetic time 1.87 s.
At the preceding request, TVLQR itself took about 0.039 ms, while command validation
took about 13.479 ms; total validated request computation was about 13.525 ms.
The total therefore exceeded the nominal 10 ms period even though the TVLQR kernel
did not. This observation remains in the raw simulation and separate applied-control
timing populations. No attempt was made to remove it or repeat the window.

After inspecting this observation, summary-only reporting added separate validation
and total validated/applied tracker distributions. One focused aggregation test
passed. Existing native raw data and original reports remain unchanged; the additional
derived report is `results/functional-analysis-v1.json` / `.csv`. Worker, runtime,
configuration and source hashes are unchanged, so no new controller run was required.

## Evidence and limits

Local detailed evidence lives only under this package's ignored `results/`:

- `docker-build-attempt-*.log`
- `package-tests-attempt-1.log`, `package-tests-attempt-2.log`
- `timing-aggregation-test.log`
- `launcher-functional-attempt-1.log`
- `run-20261109T030041Z-nYuu17/` (raw states, controls, timings, resource samples)
- `functional-analysis-v1.json` / `.csv`
- `host-process-snapshot.txt`, `existing-measurement-guards.txt`

No preexisting measurement guard was present. The Mac had background ANE compiler
activity; these are functional/exploratory samples from a VM under host load, not
controlled Pi comparison measurements. No thermal/throttling telemetry was exposed
for a Raspberry Pi; missing readings are unknown. No Pi timings were fabricated.

**Physical Pi 4/5 execution remains unverified.** Run the same saved image and command
on each board to obtain its CPU, memory, temperature, throttling and timing evidence.
Image archive/export instructions are in [README.md](README.md). Image IDs belong in
run evidence, since a document inside an image cannot embed that image's own ID.

No formal scientific Verification, full repository regression, PRE-INT one-shot
rerun, Workbench modification, frozen-source edit, physical IO, tuning, WCET claim,
guaranteed deadline claim or deployment qualification occurred. Changes outside the
portable folder are limited to the mandatory repository handoff update.
