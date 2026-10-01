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
- Phase 6 — Task 007 time-optimal racing MPC (after computational baseline work).
- Phase 7 — LMPC + system identification.
- Phase 8 — battery/energy model.
- Phase 9 — energy-aware racing MPC.
- Phase 10 — opponent model/prediction.
- Phase 11 — defensive racing strategy.
- Phase 12 — integrated defensive racing MPC.
- Phase 13 — robustness/Monte Carlo evaluation.
- Optional — RL / hybrid MPC-RL investigation.

Each phase requires explicit engineering specifications, tests for implemented mathematics,
and an updated decision log and handoff. The PRE-TASK-007 REVIEW GATE is next; Task 007 remains deferred. Task 006 supplies tracking, constraint and latency infrastructure; racing optimization is not implemented.
