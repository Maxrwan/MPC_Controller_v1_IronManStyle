# Control architecture

Task 005 implements BaselineController under control/baseline, using the unchanged
Controller.compute_control(state,context) protocol. Track geometry and current speed feed
steady linear cornering references and dynamic steering feedforward. Scheduled discrete
LQR supplies lateral feedback; a separate PI controller tracks the supplied speed profile.
The controller clips commands to configured bounds and exposes diagnostic snapshots.
See LQR_BASELINE_SPEC.md for equations, gains, limitations and exact rates.

Perfect plant state is used directly in Task 005. simulation/runner.py owns plant stepping,
integer controller ticks, held inputs, progress/lap monitoring and CSV data. It accepts any
compatible controller/model and optional diagnostics/reset callbacks, not a baseline type.
The nonlinear plant and lateral design model remain separate; no optimization is involved.

Future progression, unimplemented:

1. Time-optimal racing MPC and then LMPC safe sets/learned costs/identified local models.
2. Energy-aware MPC after battery/motor modeling.
3. Defensive racing after opponent prediction and tactical planning.

Retain baseline as benchmark/fallback candidate and reference utilities. Future fallback
must explicitly assess current validity and feasibility; Task 005 is not guaranteed safe
from arbitrary failed-MPC states. Task 006 implements a conservative application-time eligibility check for solver-failure fallback.

## Task 006 tracking NMPC

General tracking NMPC is implemented. control/mpc separates symbolic prediction, numeric preview, costs, multiple shooting,
warm starts and controller orchestration. optimization/solvers/ipopt.py owns the backend;
SolverResult includes statistics without importing CasADi in the solver-neutral base.
MPC uses an independent CasADi model; the physical NumPy plant is untouched.

The generic runner supports explicit zero/measured/injected latency and application-time
callbacks. A failed optimization can select baseline fallback only after checking the
current application state. No overlapping solves, implicit emergency controller, or latency
compensation. See NMPC_BASELINE_SPEC.md. Racing objectives remain Task 007 and later.

## Task006.1 physics selection

Racing composition explicitly matches grip-limited NumPy plant and CasADi prediction through
TirePhysics; references and controller weights remain unchanged. Application-time checks also
reject longitudinal demands outside the reserved friction domain, including fallback commands.
No latency redesign or compensation was added. Task006.2 computational work is next.
