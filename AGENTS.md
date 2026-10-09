# APEX repository rules

- Do not change canonical state ordering or coordinate conventions without explicit instruction.
- Do not invent unspecified control equations or physical vehicle parameters.
- Do not silently change mathematical models; prefer TODOs over invented mathematics.
- Preserve SI units everywhere.
- Keep physical plant and controller prediction models separate and independently injectable.
- Keep simulator independent of controller choice and optimization independent of solver backend.
- Write tests for implemented mathematical behavior; do not test fictional dynamics.
- Update documentation when architecture changes and docs/DECISIONS.md for architectural decisions.
- Update docs/CODEX_HANDOFF.md after every substantial task.
- Report ambiguity rather than guessing.
- Keep modules small and testable; avoid premature optimization and unnecessary frameworks.
- Do not introduce ROS or RL libraries unless explicitly requested.

Tasks 001–006 establish geometry, propagation, baseline LQR/PI and constrained tracking NMPC.
Follow TRACK_MODEL_SPEC.md, KINEMATIC_BICYCLE_SPEC.md, DYNAMIC_BICYCLE_SPEC.md and
LINEAR_TIRE_SPEC.md under docs. Preserve kinematic vy/r algebraic channels and dynamic
independent vy/r states. Dynamic a_cmd=Fx/m differs from kinematic a_cmd=dvx/dt.
The explicit linear reference remains unsaturated; mu is diagnostic only for that law.
Task006.1 racing configurations use matched NumPy/CasADi smooth combined grip; follow
GRIP_LIMITED_TIRE_SPEC.md, preserve explicit allocation and hard longitudinal validity.
Generic physical values remain unknown; synthetic grip is not measured APEX data. Follow LQR_BASELINE_SPEC.md for
the baseline: separate linear design and nonlinear plant, perfect state, 100/200 Hz rates.
Follow NMPC_BASELINE_SPEC.md for Task 006. Keep symbolic prediction separate from the NumPy
plant. ALL future computational controllers must test zero/injected/measured latency, physical
plant motion during solving, application-state staleness and skipped fixed deadlines.
Synchronous controllers hold the prior command; Task006.3 asynchronous planners keep the
100 Hz codriver tracking the active valid trajectory. Distinguish planner misses from
codriver/actuator misses. Never pause physics or silently remove latency; measured timing is not an
exact CI pass/fail assertion. Task006.2 synchronous tuning is documented in NMPC_PARAMETER_STUDY.md; preserve its reference and explicit candidate configurations. Task006.3 asynchronous planning is implemented; follow ASYNC_PLANNER_CODRIVER_SPEC.md.
Task 006.4 comparison is complete; retain TVLQR as default. See LINEAR_MPC_CODRIVER_STUDY.md.
Task 007A offline racing-reference integration is complete; follow TASK007A_RACING_REFERENCE_INTERFACE.md.
Planning owns the offline racing line and velocity profile. Keep APEX always active and TVLQR fixed.
Task 007B progress/aggression study is implemented; follow TASK007B_PROGRESS_SEEKING_RACING.md.
Progress defaults disabled; lambda=2 is selected only for the conservative synthetic gamma=1 case.
Retain rejected high-demand cases and keep adaptive switching deferred pending separate review. Further tire/suspension physics, estimation,
identification, energy, opponent and tactics require later specifications.

Threading experiments must retain an explicit deterministic single-thread mode. Inspect the
active backend, configure its supported controls before initialization in fresh subprocesses,
and verify actual CPU/thread behavior; environment variable values alone are not evidence
of parallel execution. Serialize latency benchmarks and preserve frozen controller mathematics.
See docs/NMPC_MULTITHREADING_STUDY.md; the current Mac study recommends one native thread.

## Standing GitHub workflow

Complete only the currently authorized subtask, then stop for Engineering Orchestrator review.
For work producing reviewable repository changes, verify, commit and push before reporting
completion. Inspect status and branch first; verify the GitHub remote is
`Maxrwan/MPC_Controller_v1_IronManStyle`. Preserve preexisting/unrelated changes and large
historical or ignored experiment artifacts. Stage only authorized files/hunks; never use
blanket `git add .` in a dirty tree. Use the appropriate existing branch when safe; a normal
push to main is authorized when already working on main. Never force-push or rewrite shared
history. If a push is rejected, preserve the local commit and report the blocker. Do not
create empty commits. Verify successful push/remote visibility before claiming GitHub
availability, and report the exact SHA, branch and commit URL. This standing authorization
supersedes older handoff notes requiring separate commit permission; it does not authorize
the next subtask or override safety/review gates.
