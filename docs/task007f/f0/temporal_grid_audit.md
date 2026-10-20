# Temporal prediction-grid audit — Task007F-0

**Static dependency audit; proposals only.** Source is E4 checkpoint
`48adbdf64d492592d15e23c917aca71fa58aa8a5`, byte-equivalent to the accepted scientific inventory.
No equations, timestep, controller, solver or runtime behavior were changed or executed here.
The [experiment matrix](experiment_matrix.json) records candidate arithmetic and ablations;
the [main specification](../../TASK007F0_EFFICIENCY_SPEC.md) governs gates.

## 1. Implemented assumptions and required later work

Links below are immutable, commit-qualified source references, not promises that the current
implementation supports a duration vector.

| Implementation evidence | Current behavior | Required design/test before a grid candidate |
|---|---|---|
| [problem.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/problem.py#L74) | One `model.rk4(config.dt, config.substeps)` reused at every stage. X has 6(N+1), U 2N, corridor slack 2(N+1) variables. | Positive finite stage durations and cumulative offsets; stage-specific transitions and substep counts. Keep equal-duration A path numerically identical. |
| [problem.py constraints](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/problem.py#L113) | Corridor slack at N+1 shooting nodes. Speed/denominator at nodes and RK4 evaluation states; loads/grip per held input. Steering increment bound is rate × scalar dt. | Audit node loss independently; retain existing physical-domain checks and a common physical-time diagnostic grid. Resolve slew-time convention below. No weaker corridor claim. |
| [problem.py guess/reward](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/problem.py#L230) | Cold start clips steering using dt and propagates one shared map. Progress normalization elsewhere is `maximum_speed*N*dt` (weight zero in A). | Stage durations in guess propagation and elapsed slew. Normalize any separately authorized progress term by sum(dt); keep lambda_s=0 here. |
| [cost.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/cost.py#L51) | Unweighted stage sums; input increments, not derivatives. Slack penalties include terminal node. Terminal P is a 100 Hz DARE schedule, clamped to 1–3 m/s; no terminal set. | Version cost meaning independently; unchanged numeric Q/R/W alone does not mean unchanged time weighting. Do not silently redesign terminal policy. |
| [controller.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/controller.py#L65) | Context dt must match config dt; preview uses N/dt; diagnostics export scalar prediction_dt and arange offsets. | Duration-vector API, N+1 preview and explicit offsets; legacy schema compatibility. Full N control sequence remains until a separately specified block map. |
| [warm_start.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/warm_start.py#L6) | Shift X/U/slack by one column, duplicate last, replace initial X. No physical-time alignment. | Compare index shift with causal time-based warm guesses; separate performance/feasibility effects from grid effects. |
| [preview.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/preview.py#L37) | N+1 geometry/reference samples. Racing progress increment `dt*v_ref*cos(epsi_ref)/(1-kappa_track*ey_ref)`. | Advance by each stage duration, terminal sample at cumulative H; retain Planning interpolation and reference definitions. Increasing H changes preview lookahead, not just cost. |
| [symbolic_model.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/mpc/symbolic_model.py#L63) | RK4 dt/substeps, held control and exogenous curvature per interval; exposes four evaluation states per substep. | Preserve independent symbolic/NumPy models. Compare internal resolution; interval-held curvature is coarser for 0.2/0.3 s even with 25 ms steps. Any intermediate curvature sampling is a separate model/preview-policy change requiring review. |
| [planner.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/trajectory/planner.py#L38) | Predictor A to release+estimate; nominal times start+arange×controller dt; gains follow packet creation. | Use actual cumulative stage offsets; keep forecast target, estimator, startup and gain validity unchanged. Never shift packet start to actual solver finish. |
| [tracker.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/trajectory/tracker.py#L28) | Jacobians and backward gains at 100 Hz over full physical H; interval sampling uses packet states and held inputs/curvature. | Nonuniform nominal nodes may already be sampled, but fidelity and terminal-gain validity require tests. Longer H increases gain work even at fixed N. Keep tracker law/rate unchanged. |
| [packet.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/trajectory/packet.py#L50) | Strictly increasing timestamps (not uniformity) and N/N+1 shapes. Linear locally unwrapped state interpolation, ZOH controls/gains/curvature, no extrapolation; trim keeps physical time. Buffer rejects unavailable/stale/insufficient-reserve packets and expired sampling. | Packet support alone is insufficient. Prove planner offsets, boundary ZOH selection, trim, gain coverage and historical serialization. Coarse interpolation is not continuous nonlinear feasibility. |
| [prediction.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/control/trajectory/prediction.py#L88) | A follows release-active packet via cloned tracker and ≤5 ms RK4 forecast; ideal future feedback; no pending-command replay in A. Target is duration, bounded by available horizon. | Reuse A equations/interface; irregular packet interpolation can change forecast values. Never use future truth/duration; keep B and lightweight prediction out of these grid studies. |
| [asynchronous.py](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/48adbdf64d492592d15e23c917aca71fa58aa8a5/src/apex/simulation/asynchronous.py#L284) | Application → completion/availability → waiting/fixed resolution → disturbance/exhaustion → codriver → nominal/urgent release → held-input physics. A releases every 0.1 s or eligible urgent opportunity, independently of prediction N. | Keep Performance scheduler, planner 10 Hz, tracker 100 Hz, physical ≤5 ms partitioning, busy/latch and fallback policies unchanged. Prediction-grid duration must not become release cadence. |

## 2. Analytical work, not measured speedups

Let N be shooting intervals, X six-dimensional, U two-dimensional, and two slacks per node.
The existing layout has `6(N+1)+2N+2(N+1)=10N+8` variables. G1 has 68 versus A's 88,
a reduction of 20/88 = **22.727%**, with 12 versus 16 input variables. Constraint/Jacobian
size and sparsity also change; factorization cost is not proportional to variable count.

| Candidate | Durations (s) | H (s) | N | Variables | 4/stage steps; max internal dt (s) | ≤25 ms steps | 100 Hz gain intervals |
|---|---|---:|---:|---:|---|---:|---:|
| A | 8×0.1 | 0.8 | 8 | 88 | 32; 0.025 | 32 | 80 |
| E-G1 | 4×0.1 + 2×0.2 | 0.8 | 6 | 68 | 24; 0.050 | 32 | 80 |
| E-G2 | 4×0.1 + 4×0.2 | 1.2 | 8 | 88 | 32; 0.050 | 48 | 120 |
| E-G3 | 8×0.2 | 1.6 | 8 | 88 | 32; 0.050 | 64 | 160 |
| E-G4 | 8×0.3 | 2.4 | 8 | 88 | 32; 0.075 | 96 | 240 |

Each RK4 substep entails four derivative evaluations plus associated domain/Jacobian work.
Counts do not include solver iteration count, sparse factorization or gain preparation. Matched
25 ms resolution gives G1 per-stage substeps `[4,4,4,4,8,8]`. Its unchanged H also retains
approximately 80 TVLQR gain intervals; fewer optimization variables promise no reduction there.
No candidate was instantiated, solved or benchmarked in F0.

## 3. Warm-start alternatives for review

The present one-column shift is a pragmatic guess, not a physical-time shift even when variable
availability changes the next predicted start. On a nonuniform grid a 0.1 s release advance
cannot be represented by shifting every column once.

Proposed policy W-time: store previous nominal absolute node/input times with the primal solution;
map new absolute node time `t_new + tau_k` onto the previous solution. Interpolate states with
heading locally unwrapped and progress continuous, select held controls by old interval, resample
nonnegative slacks, and set new x0 to the causal predictor output. Interpolation is a **guess**,
not feasibility or authority. Do not interpolate packet IDs. For times past prior H, use an
explicitly reviewed terminal-hold/control extension or cold-start rule; never extrapolate active
packet authority. A guess extension is not a forecast of future truth.

Alternative W-roll: resample old held controls, then reintegrate a guess from new x0 on the new
symbolic grid, recomputing geometric slacks. This costs extra integrations but may improve dynamic
consistency. Preserve domain/load/grip checks; recomputing slacks does not authorize positive
scientific slack. Compare W-index, W-time, W-roll with identical grid/objective on valid saved
contexts first; report CPU cost, feasibility residuals, cold starts, iterations and failed solves.
No dual warm-start rule is invented; current implementation supplies shifted primal only.

## 4. Cost policy derivation and unresolved choices

For stage lengths `d_k`, let `h0=0.1 s`, tracking error `e_k`, reference input error `v_k`,
and increment `du_k=u_k-u_(k-1)` (predicted previous input for k=0). The accepted objective is
`sum(e_k'Q e_k + v_k'R v_k + du_k'W du_k) + Phi(x_N)` plus
`sum_(k=0..N) (1e4*sum(slack_k)+1e5*||slack_k||²)`.
There is no dt multiplier. Q concerns `[vx,vy,r,e_psi,e_y]`; progress is not a sixth quadratic
state term. Canonical state storage remains `[vx,vy,r,e_psi,s_abs,e_y]`.

Two **separately versioned** candidates must not be conflated:

- **J-discrete:** preserve the per-node sum/increment semantics. Changing node count changes
  sampling weights and total penalty. It is a useful diagnostic baseline, not proof of
  physical-time cost equivalence to A.
- **J-density:** interpret the running state/input terms as rectangle quadrature calibrated to
  A: use `(d_k/h0)*(e_k'Qe_k+v_k'Rv_k)`. This exactly recovers those terms on uniform A nodes
  and preserves a constant-in-time running penalty over a fixed H. It does not guarantee equal
  trajectories or global discretization accuracy. Keep increments separate as discrete jumps
  unless an explicit derivative objective is authorized.

If a physical derivative regularizer were independently selected, linear-ramp interpretation
gives `integral(dot(u)' W_cont dot(u) dt) ≈ du_k' W_cont du_k / ell_k`. Choosing
`W_cont=h0*W` yields `(h0/ell_k)*du_k'Wdu_k`, matching uniform 0.1 s only when `ell_k=h0`.
This is **not** the derivative of actual ZOH actuator input (jumps are discontinuous), and is not
silently the existing W penalty. The first increment's preceding-input timing and later node-to-node
`ell_k` must be specified. Version/ablate this independently; never divide by arbitrary future
solver time or equate nominal control smoothing to physical steering-rate enforcement.

Slack is a soft node violation penalty, not a physical-time quantity by definition. A possible
A-preserving J-density variant weights running slack by `d_k/h0` for k<N and retains terminal
slack weight 1. This reproduces A on its uniform grid but retains an endpoint penalty; it is not
trapezoidal quadrature. Alternatively trapezoidal slack weights change A's endpoint penalties and
require a new objective plus their own parity expectations. **Review must choose before coding.**
Regardless of weighting, maximum scientific slack remains ≤1e-6 m and fewer corridor nodes must
not hide excursions. Physical/native endpoint diagnostics and common fine-time prediction checks
are mandatory; if additional hard constraints/slacks are needed, recount the NLP dimension.

Keep the accepted terminal multiplier/P schedule and speed penalty as the first experimental
terminal policy. Do not multiply terminal cost by stage duration. Its 100 Hz, 1–3 m/s-clamped
linear design is not a terminal invariant-set or long-horizon stability guarantee. Longer H changes
the terminal state/reference and potentially gains even with identical terminal code.

## 5. Integration, steering and physical acceptance

For each interval use `m_k=ceil(d_k/0.025)` for the matched-resolution arm and `h_k=d_k/m_k`.
The current four-substep arm is a separate accuracy/work ablation. Retain speed/Frenet-domain
checks at every returned RK4 evaluation state and all shooting nodes, load/grip input validity,
actuator boxes and finite outputs. Do not replace the physical plant integrator. Intermediate
curvature currently stays at the interval-start preview value; finer RK4 alone does not reduce
that geometry approximation. A future varying-curvature map needs separate equations and review.

The current bound `|delta_k-delta_(k-1)| <= rate*0.1` hides a convention because all intervals
are equal. For ZOH controls applied at node starts, k>=1 increments are separated by **d_(k-1)**,
not automatically d_k. For k=0 the predictor's preceding command and target timing require an
explicit initial slew-budget convention; current implementation uses one nominal interval. A
stage-indexed `rate*d_k` convention would differ at the 0.1→0.2 transition. Resolve and test this
before candidate code; do not silently loosen the first coarse-stage slew budget. Actual actuator
application continues its existing elapsed-time clamp regardless of NLP discretization.

Coarse nodes allow more between-node interpolation error. Present runtime packets interpolate
states linearly and hold controls/curvature; they do not certify a continuously feasible nonlinear
curve. A common ≤25 ms **offline candidate feasibility audit** should check state/input/domain,
corridor and prediction residuals without inserting physical scheduler events. Selection of exact
reconstruction/acceptance tolerances is a prerequisite, not authority to weaken hard validity.
The synthetic 0.08 m tracking margin is not a body-clearance guarantee; vehicle footprint and
continuous safety remain unavailable. Safety S0 may not be bypassed for lower compute.

## 6. Asynchronous and verification boundary

A's target remains `release + clipped median of last ten observed preparation delays` (initial
17 ms, maximum estimate 300 ms); that cap is not a solve-duration bound. The plant keeps moving,
100 Hz TVLQR tracks the accepted unexpired packet, one planner solve remains pending, and due
old commands preserve their original request provenance across handoffs. Packet nominal start,
completion, accepted time, expiry and applied-command time remain distinct. Buffer minimum
handoff reserve is 50 ms, warning below 200 ms, critical below 50 ms; warnings do not implement
proactive rescue. Longer H can raise reserve while also raising computational cost and stale-plan
exposure. Do not score that reserve gain as reduced preparation work.

Later prerequisites: existing `tests/unit/test_mpc.py`, `test_trajectory_tracker.py`,
`test_async_chronology.py`, `test_fixed_handoff_contract.py`, `test_fixed_handoff_scheduler.py`,
`test_planning_reference.py`, `test_grip_tire.py`, `test_task007c_physics.py`,
`test_threading_study.py` and relevant export/metric tests. Add targeted tests for cumulative times,
uniform-vector parity, duration-scaled constraints/costs, warm-start alignment, coarse-boundary
sampling, domain/curvature checks, gain horizon, causal target and rejection/exhaustion behavior.
Preserve existing mathematical tolerances. No tests were run in F0.

The initial G1 comparison changes only a versioned experimental predictor grid/objective policy
under **variable A scheduling**, after uniform plumbing parity. Its necessary coupled changes
are explicitly measured through the matrix's control-block, shooting, integration and cost ablations.
The listed grids cannot alone isolate every factor: H=N×mean(dt). Additional companion grids
are proposals requiring approval, never an invitation to expand the first bounded pair.
