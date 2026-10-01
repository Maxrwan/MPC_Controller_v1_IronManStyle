# Task 006.4 — completed

Implementation and 26 two-lap experiments complete. Decision: A, retain TVLQR. Task 007 is
not implemented; next step is PRE-TASK-007 REVIEW GATE. Read LINEAR_MPC_CODRIVER_STUDY.md,
LINEAR_MPC_CODRIVER_RESULTS.md, LINEAR_MPC_REPRODUCTION.md and PRE_TASK007_CONTROL_REQUIREMENTS.md.

MPC candidate: N=8, LTV, Q=[100,100,4,1], R=25, W=0, DARE terminal, affine defect,
100 Hz, OSQP 1.1.3 builtin, max400/check10/adaptive-rho25, tol1e-6, no polishing,
shifted primal/zero dual. Absolute/slew limits and longitudinal P unchanged.
Candidate C, 10 Hz N4/0.4 s, one native thread, approved plant and 0.08 m margin frozen.

Phase A identical packets: TVLQR/MPC lateral trajectory RMS 0.447/1.064 mm.
Phase B measured nominal: 0.415/0.287 mm and steering TV 2.729/2.177 rad; MPC improves
smoothness but disturbance/stress tracking and recovery do not establish a material benefit.
Total architecture CPU 0.5149/0.7993 core-seconds/s. Fixed-input p95 1.175/3.060 ms.
Warm starts did not beat zero starts in sampled benchmark; retain recorded candidate, no retuning.

26 physical chronology/fallback/replay audits pass; 108 model checks complete. Baseline 411
result files verified byte-identical; existing dependencies unchanged. Only existing runtime
changes: optional forecast hook in prediction.py and finalization hook in asynchronous.py.
New local_mpc modules and OSQP dependency. Final review added finite dual-residual validation:
measured source archived in benchmark_sources, all 54982 accepted logged QPs had finite residuals.
21 local-MPC tests pass including this guard and zero/injected scheduling. Ruff lint/format pass for 148 active Python files.

Full regression: 454 passed in 817.84 s. Final focused suite: 21 passed in 1.73 s; it covers
the two tests added after full-suite collection (456 distinct tests covered overall). Logs and
validation.json are saved in results/linear_mpc_codriver. Final source_snapshot.zip and
provenance.json preserve source/result hashes; all case hashes match benchmark_sources.
28 plots generated; paired replay and stress-recovery plots visually reviewed. No work remains
for Task 006.4. Do not start Task 007 without the PRE-TASK-007 REVIEW GATE.

The final response must use the exact 35 headings from the user brief at attachment
74e99761-a04f-4f63-a880-d157481ab273/Pasted text.txt. All commands are documented in
LINEAR_MPC_REPRODUCTION.md. No subagents, Pi deployment, racing line or speed generation.
