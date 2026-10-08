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

1. Racing-reference integration and near-limit APEX tracking, then LMPC safe sets/learned costs/identified local models.
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
compensation. See NMPC_BASELINE_SPEC.md. Task007B adds the optional local terminal-progress objective; global Planning remains offline.

## Task006.1 physics selection

Racing composition explicitly matches grip-limited NumPy plant and CasADi prediction through
TirePhysics; references and controller weights remain unchanged. Application-time checks also
reject longitudinal demands outside the reserved friction domain, including fallback commands.
No latency redesign or compensation was added. Task006.2 computational work is next.

## Task 007A Planning-reference integration

Planning OFFLINE racing line + velocity profile → validated serialized reference →
APEX NMPC ONLINE and always active at 10 Hz → trajectory buffer → TVLQR at 100 Hz.

The synthetic generator is temporary test infrastructure under scripts/task007a; runtime
apex/planning_reference only loads, validates and interpolates the files. Task 007 integrates
and tracks an offline racing reference; it does not generate a global time-optimal racing line.
The racing-mode preview adds nonzero ey/epsi targets and distinct reference curvature while
Frenet dynamics retain centerline curvature. See TASK007A_RACING_REFERENCE_INTERFACE.md.
Adaptive/fuzzy codriver switching and direct-tracker architecture-value comparisons are future
reviewed experiments. Neither changes the always-active APEX primary architecture here.


## Task007B nominal intent and optional progress

The accepted Task007A global line and baseline remain reproducible. Task007B is authorized
by its explicit brief: Planning intent may be well-formed but dynamically demanding. Runtime
control never repairs or optimizes the global package. An explicit advisory validation policy
retains all hard schema, geometry, margin and speed-domain checks while reporting feasibility
warnings. Offline capped speed polynomials preserve exactly scaled/capped nominal intent.

APEX remains always active. Its optional terminal reward is
-lambda_s*(s_N-s_0)/(v_max*N*dt), using existing unwrapped progress and defaultlambda0.
No new variable, tire-utilization reward or hard-constraint relaxation. CandidateC tracking,
control, increment, terminal and slack penalties stay frozen in the first sweep, as does TVLQR.
Objective groups are exported separately. Predicted-node Planning→APEX deviations and
vehicle-minus-active-packet tracking errors are separate first-class telemetry families.
See TASK007B_PROGRESS_SEEKING_RACING.md. Adaptive codriver and nominal-state redesign remain
deferred pending evidence review; this task does not implement switching.

Task 007B selects lambda=2 only for the conservative synthetic gamma=1 experiment; progress
defaults to zero. The high-demand progress cases expose planned oscillation and tracking-margin
slack, so they are retained and rejected without model, cost or codriver retuning. See
[TASK007B_RESULTS.md](TASK007B_RESULTS.md) for the separate adaptation/tracking evidence.

## Task 007C diagnostic boundary

Task 007C is authorized as a controlled formulation study after a mandatory Task 007B anchor
reproduction gate. Planning and plant remain unchanged; APEX remains continuously active and
TVLQR stays fixed. Dynamic pseudo-reference cost ablations, fixed-dt horizon sensitivity and
static progress maps are separate experiments, not a combined controller retune. No production
scheduler or adaptive codriver is introduced. See
[TASK007C_NEAR_LIMIT_APEX_DIAGNOSIS.md](TASK007C_NEAR_LIMIT_APEX_DIAGNOSIS.md).

Task007C reproduction outcome: the mandatory gate did not pass after six anchors and two
additional E/F repetitions. No runtime formulation changes were made. C1–C4 and adaptive
codriver remain deferred; see `TASK007C_RESULTS.md` and ADR-152.
