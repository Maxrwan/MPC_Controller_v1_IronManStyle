# V0.1 functional Verification

**V0.1_VERIFIED_PENDING_USER_ACCEPTANCE.** Repository stage: **VERIFIED_AWAITING_ACCEPTANCE**.
Recorded 28 October 2026, Africa/Cairo. Exact reviewed/tested implementation:
**`77d018b11bbbfc39ab81d98c9bef70e90ab82725`**, branch `codex/apex-workbench-v0-1`.
The final documentation-only delivery descendant does not change implementation, tests,
configuration, dependencies or fixtures. Its exact SHA/URL is reported after push.

The [separate-context technical review](REVIEW.md) passed before execution. The explicit user
delegation supplies functional Verification authority. No named external Secondary approval,
Primary scientific acceptance or physical certification is claimed.

## Executed result

**855 passed, 17 skipped, zero failures/errors; exit 0; 667.18 s (11:07).**
Selection: complete `tests/` plus `tools/apex_workbench/tests/` (outside default pytest testpaths).
This includes **all 78 Workbench cases**, existing unit/integration/regression checks and fresh
original-entry-point/full-worker dynamic and LQR parity. No old pass is counted as fresh here.

All 17 skips are `tests/integration/test_profile1_parity.py:55`: frozen G2 work requires separate
authorization, reviewed revision/clock allowance and a pristine B0 root. Those parameters were not
provided or enabled. The skipped G2 campaign is outside this Workbench delegation and is **not passed**.
No other test was skipped. Applicable existing NMPC/async/threading software checks ran as part of
the repository acceptance suite, not as a new scientific or performance campaign.

The exact executed command/environment is in [verification.json](verification.json). Equivalent
selection/controls, from the reviewed checkout, with a fresh output directory:

```sh
VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONPATH=.:scripts:src \
tools/apex_workbench/.venv/bin/python -c \
'from threading_study.config import configure_accelerate; configure_accelerate(1); import sys,pytest; raise SystemExit(pytest.main(sys.argv[1:]))' \
-q tests tools/apex_workbench/tests --durations=10 \
--basetemp=<FRESH_OUTPUT>/pytest > <FRESH_OUTPUT>/complete-tests.log 2>&1
```

The actual bootstrap additionally asserted exact HEAD/clean status and printed source/runtime/native
identity before pytest. No source was edited during the run. Do not reuse the retained basetemp.

## Separate conclusions

| Category | Conclusion |
|---|---|
| Execution/test correctness | Applicable complete suite passes; malformed/incomplete data is visibly quarantined; valid dynamic/LQR workflows remain functional. |
| Artifact integrity | Ten original real supervised run manifests were checked in full, including manifest anchors, containment, byte sizes and every recorded SHA256. Their outcomes remain seven completed, one interrupted and two cancelled. Deliberately corrupt copies/direct fault fixtures are separately tested negative evidence. |
| Scientific adapter parity | Both original CLI/function parity and full supervised-worker parity pass freshly; existing source/configuration remains fixed. |
| Scientific-model validity | Software contracts/parity do not establish measured vehicle parameters, global stability, tire physical validity, collision safety or hardware behavior. No new physical acceptance claim. |
| Resources/platform | Existing macOS environment, local filesystem/flock/atomic publication; sampled wall/RSS/output safeguards, no hard real-time or hardware watchdog guarantee. No resource-exhaustion/power-loss qualification. |

Python 3.12.14; NumPy 2.5.3; SciPy 1.18.1; CasADi 3.8.1; Streamlit 1.66.1. Full versions/native
metadata are retained in JSON. Verification starts with Accelerate SINGLE before numerical imports;
Workbench workers retain their own SINGLE controls. The existing macOS threading-parity unit test
intentionally runs sequential fresh child ceilings 1/2/1 as specified by its unchanged test. This is
functional parity evidence, not statistical scaling/performance or exact active-thread qualification.

## Launcher and preservation

A fresh actual final-pin smoke passed: launch from `/private/tmp`, health 200/ok, repeat-click reuse
of the owned server, SIGINT shutdown, reusable-address bind, foreign-listener refusal without
termination and exact-copy missing-environment error. Owned test processes/server are gone.
Zsh/embedded Python syntax, scoped Ruff/format, whitespace and documentation references pass.

All **896 tracked files** remained byte-identical throughout Verification. The broader stabilization
audit confirms only authorized Workbench/launcher/documentation changes; canonical `src/`, scripts,
scientific tests, configurations, profiles and core dependencies are unchanged. All **14,100
pre-existing result files** retain size/mtime. This metadata audit is not a new content hash/backup
of every large historical artifact. Old failed reviews, partials, measurement records and guards
were preserved; no frozen G2 allowance or authorization was invented.

Evidence root:
`results/apex_workbench_stabilization_20261028/verification-77d018b/` contains the full log,
preflight source manifest, final audit, genuine run fixtures and final launcher logs. The
machine-readable record includes their hashes. Earlier failed candidates/logs remain alongside it.

## User handoff

V0.1 supports existing open-loop dynamic and fixed LQR/PI experiments with allowlisted inputs,
genuine retained plots, classified comparisons and append-only learning notes. Use the existing
repository-root `Launch_APEX_Workbench.command` icon.

Vehicle/tire definitions and controller tuning remain fixed/synthetic; perfect state and ideal
modeled timing remain explicit. NMPC/async adapters, physical identification, hardware control,
new safety/performance campaigns and V0.2 are not enabled. Stop here for user acceptance; no
routine software correction or further execution is required by this delivery.
