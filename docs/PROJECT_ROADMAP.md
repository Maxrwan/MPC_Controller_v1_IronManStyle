# Project roadmap

- Phase 0 — repository/simulation architecture (Task 001: architecture only; no simulation physics).
- Phase 1 — track geometry + Frenet transformations (Task 002 implemented and validated).
- Phase 2 — CG kinematic bicycle model (Task 003 implemented and validated).
- Phase 3 — dynamic bicycle plant + linear axle tires + simple load transfer (Task 004 validated).
- Phase 4 — feedforward + gain-scheduled LQR + PI baseline (Task 005 implemented).
- Phase 5 — general tracking NMPC (Task 006 implemented, with latency-aware simulation).
- Task 006.1 — smooth combined-grip tire model (implemented; validation recorded in handoff).
- Task 006.2 — staged synchronous NMPC parameter/Pareto study (implemented and validated).
- Task 006.2.2 — isolated multicore latency study (complete; no useful acceleration, one-thread baseline retained).
- Task 006.3 — asynchronous NMPC trajectory planner plus high-rate trajectory-following codriver (complete; 21 experiments audited and 435 regression tests passed).
- Task 006.4 — small high-rate linear MPC versus TVLQR (complete; 26 audited cases; 454 full-regression and 21 final local tests passed; retain TVLQR).
- Phase 6 — Task 007 RACING-REFERENCE INTEGRATION AND NEAR-LIMIT APEX TRACKING.
- Task 007A — offline Planning-reference interface and synthetic Grand Prix baseline (complete; 479 tests passed, three chronology cases audited).
- Task 007B — progress-seeking APEX and progressively aggressive offline references (complete; 500 regression tests passed; conservative-case progress selection, high-demand limitations retained).
- Task 007C — near-limit APEX formulation diagnosis (initial gate stop retained historically; resumed C1–C4 study and final audits complete; stopped for review; see TASK007C_RESUMED_RESULTS.md).
- Task 007C-R — near-limit reproducibility and timing-causality gate (complete; exact historical replay, fixed-timing determinism, timing-history sensitivity; 518 tests passed; C1–C4 scientifically cleared and subsequently executed in the resumed study).
- Phase 7 — LMPC + system identification.
- Phase 8 — battery/energy model.
- Phase 9 — energy-aware racing MPC.
- Phase 10 — opponent model/prediction.
- Phase 11 — defensive racing strategy.
- Phase 12 — integrated defensive racing MPC.
- Phase 13 — robustness/Monte Carlo evaluation.
- Optional — RL / hybrid MPC-RL investigation.

Each phase requires explicit engineering specifications, tests for implemented mathematics,
and an updated decision log and handoff. The user authorized Task 007A after the review gate; Task 007B is complete; adaptive codriver switching remains deferred. Task 006 supplies tracking, constraint and latency infrastructure; optional local terminal-progress optimization is implemented in Task 007B; global Planning remains offline.

Planning owns the offline global racing line AND velocity profile. Task 007 does not generate
these products online in APEX. Its temporary synthetic generator is test infrastructure only.

## Mandatory checkpoint after accepted online system identification

Only after online system identification is implemented and accepted, update the APEX workbench
for identified parameters, spatial parameter maps versus progress, uncertainty, prediction
residuals, nominal versus identified predictions, learned grip/tire trends and cross-lap comparisons.
Then begin real-time identification experiments covering estimator computational cost and control
scheduling, parameter-update rate, asynchronous model updates, delay before model adoption,
HIL/bench execution where available, sensor/actuator latency injection, missed identification
updates and uncertainty-aware control response. This is a future mandatory review checkpoint;
none of this is implemented or authorized as part of Task007C.

C1–C4 resumed 2026-10-07 and experiments/reporting completed2026-10-08 under `TASK007C_RESUMPTION.md`. Review `TASK007C_RESUMED_RESULTS.md` before adaptive codriver,
LMPC, online identification, energy management or opponent racing. The later timing-architecture
comparison is documented there and is not part of the current implementation.
