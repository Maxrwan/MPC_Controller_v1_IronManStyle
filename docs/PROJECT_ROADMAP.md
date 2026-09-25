# Project roadmap

- Phase 0 — repository/simulation architecture (Task 001: architecture only; no simulation physics).
- Phase 1 — track geometry + Frenet transformations (Task 002 implemented and validated).
- Phase 2 — CG kinematic bicycle model (Task 003 implemented and validated).
- Phase 3 — dynamic bicycle plant + linear axle tires + simple load transfer (Task 004 validated).
- Phase 4 — feedforward + gain-scheduled LQR + PI baseline (Task 005 implemented).
- Phase 5 — general tracking NMPC (Task 006 implemented, with latency-aware simulation).
- Task 006.1 — smooth combined-grip tire model (implemented; validation recorded in handoff).
- Task 006.2 — reduce NMPC computational cost and control latency (next; not implemented).
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
and an updated decision log and handoff. Task 006.2 is next; Task 007 remains deferred. Task 006 supplies tracking, constraint and latency infrastructure; racing optimization is not implemented.
