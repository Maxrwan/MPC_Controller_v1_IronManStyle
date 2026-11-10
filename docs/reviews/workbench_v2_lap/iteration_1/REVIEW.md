# Independent Engineering Review — BLOCKED

Candidate: `19aff134a797da755c1ee985e892f2b6bcc5b80c` on `codex/workbench-v2-lap`.
Accepted V1 base: `511b0a884e0f8474760817620fcdef46e7860142`.
Frozen science: `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Reviewer: independently delegated agent `/root/workbench_v2_lap_independent_review`.
Completed: 2026-11-10 14:30 UTC.

**Outcome: BLOCKED. Do not install a PASS policy or start a genuine pilot/full-lap attempt on this candidate.**
Three concrete functional/admission defects remain. No scientific/controller/plant execution occurred in this review.

## Findings

### R1 — P1: unsuccessful pilot can authorize the full-lap budget

`tools/apex_workbench/lap/analysis.py:212-240` checks baseline configuration, summary coverage and `raw.failure`, but ignores the pilot's terminal scientific outcome. `config.access()` then uses this budget at `config.py:115-126` without adding a successful-outcome requirement.

An independent metadata fixture with `status.state=cancelled`, `scientific_outcome=cancelled`, valid evidence, completed coverage and no native failure is accepted by `resource_budget()`. This is a reachable distinction: cancellation or a resource/finalization failure can happen after the native simulation and summary have completed. A retained, complete simulation window does not establish that the pilot execution succeeded.

Evidence: `cancelled_pilot_fixture.json`, `reproduced/cancelled_pilot.json`; deterministic reproduction in `reproduce_findings.py`.

Minimal correction: require a terminal completed/valid pilot with a successful worker exit, in addition to the existing baseline, complete coverage and no-native-failure requirements. Reject cancelled, timed-out, interrupted, failed and missing-outcome/return-code cases before full-lap admission. Add negative fixtures for these states. Preserve unsuccessful attempts and their consumed slot.

### R2 — P2: changing replay window keeps the previously acknowledged payload

`tools/apex_workbench/lap/panels.py:109-123,209-215` changes the selected state window but preserves the run directory and full evidence anchor. The unchanged accepted bridge at `tools/apex_workbench/scratch_replay.py:174-213` keys the component by run directory and its epoch by that anchor. After the first load is acknowledged, selecting a different start therefore sends `payload=None` with the same component key/epoch. The browser viewer (`scratch_replay_web/viewer.mjs:148-155`) retains the earlier window.

The independent software bridge fixture uses the real `replay_window`, `payload` and `replay` functions, replacing only Streamlit session/component transport. Selecting start 0 then start 10 yields the same key and epoch and withholds the second payload. No browser or server was launched by the reviewer.

Evidence: `replay_window_fixture.json`, `reproduced/replay_window.json`; deterministic reproduction in `reproduce_findings.py`.

Minimal correction: add a V2-only presentation identity that includes the selected native window and causes its payload to load, while preserving the full source/evidence anchor, original run identity and fail-closed invalidation. Keep accepted V1 bridge/renderer files unchanged. Test selection changes after acknowledgment, switching back, and evidence quarantine across windows.

### R3 — P2: native missing slack after a failed preparation crashes sector analysis

`tools/apex_workbench/lap/analysis.py:96` computes a maximum over `p.get("max_slack", 0)` without filtering unavailable observations. The frozen `MPCController.compute_control()` explicitly initializes `max_slack=None` for unsuccessful optimizer results. A sector containing both a successful preparation (`max_slack=0.01`) and a failed one (`max_slack=None`) raises `TypeError: '>' not supported between instances of 'NoneType' and 'float'`.

`panels.presentation()` calls sector analysis for inspection, and comparison calls it for both runs; their exception handlers do not handle this TypeError. Genuine failed-preparation evidence can therefore break the requested failure/feasibility analysis.

Evidence: `failed_plan_sector_fixture.json`, `reproduced/failed_plan_sector.json`; deterministic reproduction in `reproduce_findings.py`.

Minimal correction: summarize only finite numeric slack observations, report missing/failure counts, and keep maximum slack unavailable when no valid observation exists. Do not substitute zero for missing scientific evidence. Add mixed-success/failure and all-missing fixtures.

## Independent checks and supporting observations

- Read AGENTS.md, the staged workflow, Primary authority, WORK/report record, every new lap package file and test, relevant accepted V1 lease/storage/replay/composition code, and the exact frozen AsyncRunner/planner/controller/dynamic-model source.
- Independently reran the focused file: **40 passed, 0 failures/errors/skips, 33.29 s**. This count is separate from the parent's prior 40-pass result. The existing suite did not cover the three findings above.
- Command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:src:scripts VECLIB_MAXIMUM_THREADS=1 /Users/marwansaber/Grad_proj/The_Project_PREP/MPC_Controller_v1_IronManStyle/tools/apex_workbench/.venv/bin/python -B -m pytest -q -p no:cacheprovider tools/apex_workbench/tests/test_lap_v2.py --basetemp=results/apex_workbench_v2_lap/review/iteration_1/fixtures --junitxml=results/apex_workbench_v2_lap/review/iteration_1/focused.xml`.
- The focused file includes metadata-only helper-process lease/supervisor-loss/cancel/output checks. Its single frozen configuration subprocess blocks `casadi.nlpsol`, `AsyncRunner.run` and `DynamicBicycle.step` and composes three configurations without solving or stepping. No genuine execution is inferred from these checks.
- Independently reproduced all three findings with software metadata/transport fixtures: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. VECLIB_MAXIMUM_THREADS=1 <approved-python> -B results/apex_workbench_v2_lap/review/iteration_1/reproduce_findings.py`.
- Native two-crossing composition is correct by inspection: the first crossing from `s_abs=1 m` is excluded; `lap_times[1]` is the complete same-phase interval. The native runner and its crossing interpolation are reused, rather than recreated. The exact resolved controller/initial-state composition remains unchanged apart from declared simulation duration.
- Independent V2 finite wall/CPU/RSS/output/file caps exist; CPU/file caps precede numerical imports. Startup validates the inherited common lease inode and process module/role/run identity. Continuous ownership/cancel/resource monitoring retains the inherited lease until worker exit. Actual full-worker resource behavior has not been tested with genuine execution.
- The source/current/review/Git/Primary access bindings and once-only consumption precede probing/execution. Full-lap host capacity and a retained pilot-supported finite preflight remain required before any later genuine attempt; this review does not qualify resource extrapolation as a runtime guarantee.
- Scientific metrics consume all retained observations; display reduction does not replace them. Predictions match target native timestamps within the explicit 1 ns float allowance and retain missing targets. Comparisons check non-cost source/environment/configuration and coverage, and do not rank weighted objectives. These observations do not override the R2/R3 functional defects.
- **12,546 historical files and 508 links match the retained preservation anchor.** Seventeen accepted V1 protected producers/launcher/replay entries match the accepted base. All **333 frozen runtime files** match the pinned scientific source. No `src/`, `scripts/`, `configs/`, dependency, V1 profile/launcher/replay modification appears in the candidate diff. The work record's source/evidence/authority hashes match current bytes.
- `git diff --check` and V2 launcher `zsh -n` pass. Git HEAD stayed exactly the candidate; the tracked working tree remains clean. The reviewer created only ignored review artifacts under this iteration directory.

## Limits and stop

Full process enumeration via `psutil.process_iter()` was denied by the filesystem/process sandbox (`PermissionError` from `sysctl() malloc 1/3`). This is retained as `NOT_OBSERVED_SANDBOX_DENIAL` in `static_audit.json`; no claim of a complete host process inventory is made. Explicit reviewer test, reproduction and audit subprocesses have exited, including the focused suite's waited/cleaned metadata helpers.

**All reviewer tests and audits are terminated before any parent pilot.** The reviewer performed no optimizer solve, controller run, plant step, genuine extended run, full-lap run, hardware work, browser control, server launch, broad regression or formal Verification. This review authorizes no numerical attempt. Correct only the minimal defects, preserve this failed review, and submit the new exact revision for independent re-review before genuine execution.
