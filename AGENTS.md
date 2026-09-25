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
plant motion under held prior control during solving, application-state staleness and skipped
fixed deadlines. Never pause physics or silently remove latency; measured timing is not an
exact CI pass/fail assertion. Task006.2 solver optimization and Task007 racing are not implemented. Further tire/suspension physics, estimation,
identification, energy, opponent and tactics require later specifications.
