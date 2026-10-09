# Task007C resumed C1–C4 reproduction

This continues after the passed Task007C-R gate. `TASK007C_REPRODUCTION.md` preserves the
original failed measured-anchor attempt; its stop status is historical. Current work and
remaining deliverables are in `CODEX_HANDOFF.md` and `TASK007C_RESUMPTION.md`.

Run from the repository root with the existing `.venv`. All commands preserve original
Task007B/C/CR records. Completed experiment identities are reused only when their immutable
cell specification matches; they are not fresh repetitions on rerun. New measurements require
new authorized repeat identities rather than overwriting old ones. Finite replay histories
are never extended. Numerical analysis and rendering must wait for every measured worker.

## Controlled formulation grids

```bash
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/campaign.py c1
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/campaign.py c1-progress
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/campaign.py c2
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/campaign.py c2-followup
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/campaign.py c3
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/campaign.py c4
```

The campaign stops at any new boundary, solver/domain or fallback failure. Reviewed failures
are hash-bound in `reviewed_failures.json`. They remain rejected evidence; a review is not an
acceptance waiver or permission to discard the run.

## Candidate chronology and sustained confirmation

```bash
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/validation_campaign.py horizon-coverage
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/validation_campaign.py representative-g2
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/validation_campaign.py representative-g2p1
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/validation_campaign.py repeat-fixed
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/confirmation_report.py
```

`repeat-fixed` also includes zero/injected checks and three-crossing sustained cases. Three
crossings mean one rolling segment from s_abs=1m followed by two full geometric laps. The
exact N6/N8 parity report uses the candidate horizon's six-state decision-block size.

## Isolated backend and measured timing

First verify that no other numerical jobs are active. Fresh workers configure native SINGLE
before imports. The backend audit additionally samples actual process threads and CPU/wall;
process inspection must be available. Environment variables alone are insufficient evidence.

```bash
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/backend_audit.py --case g2_w0_vy1_r1_n6_fixed_l1
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/backend_audit.py --case g2_w0_vy1_r1_n8_fixed_l1
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/measured_campaign.py --gamma 2 --horizons 4 6 8 --repeats 5
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/measured_campaign.py --gamma 2.2 --horizons 6 --repeats 5
```

Run these sequentially. Do not start analysis, rendering, tests or a competing benchmark.
The exclusive `MEASURED_ACTIVE` guard enforces this for the campaign tools but cannot stop
unrelated preexisting processes. Rotated gamma2 order and UTC journals are retained. A failed
repetition keeps its original identity and outcome; completing the remaining repetitions does
not replace it. Wall timing is descriptive, never an exact CI assertion.

## Offline reports and plots

Only after measured workers exit:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/analyze.py
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/history_report.py --gamma 2
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/history_report.py --gamma 2.1
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/history_report.py --gamma 2.2
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/measured_report.py
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 MPLCONFIGDIR=/private/tmp/apex-matplotlib .venv/bin/python scripts/task007c_resume/measured_plots.py
```

For a principal or failure case, use `analyze.py --cases CASE --physics`, then
`render.py --cases CASE --sectors hairpin technical_section fast_sweeper`. Both wrappers launch
fresh SINGLE workers. Optional `--phase-output NAME.png` compares the listed cases' sector
phase portraits. `render.py --comparisons c1 c2 c3 c4` regenerates controlled figures.

## Final audit

```bash
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/final_audit.py
.venv/bin/ruff check scripts/task007c_resume tests/unit/test_task007c_physics.py
```

The audit verifies frozen runtime/fixtures/settings, original B/C/CR hashes, physical held
commands, nonoverlapping solves, timestamped references and steering-rate limits, including
zero/injected and failed measured cases. Its final manifest inventories source, reports and
results; rerun the inventory after any subsequent artifact edits. Controller mathematics,
TVLQR and production defaults remain as documented in the protocol.

## Post-hoc failure-history and reversal diagnostics

These diagnose the observed measured N6 failure and the retained steering-reversal caveat;
they are not extra favorable measured repetitions or retrospective acceptance gates.

```bash
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/failure_replay.py
PYTHONPATH=scripts .venv/bin/python scripts/task007c_resume/analyze.py --cases g2_w0_vy1_r1_n6_measured_n6_exhaustion_l1 g2_w0_vy1_r1_n8_measured_n6_exhaustion_l1
PYTHONPATH=scripts VECLIB_MAXIMUM_THREADS=1 .venv/bin/python scripts/task007c_resume/reversal_review.py
```

N6's replay is checked for exact physical/NLP parity. N8's replay ends at driver-trace
exhaustion18.760s with0.196621s reserve; no unavailable driver tail is invented and no completed
recovery is claimed. The measured failure remains in the original five-run distribution.
