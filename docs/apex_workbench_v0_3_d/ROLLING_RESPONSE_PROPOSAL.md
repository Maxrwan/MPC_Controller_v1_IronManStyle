# Rolling braking / turn-in protocol proposal — RBT-0.1

**DESIGN ONLY — PENDING PRIMARY SCIENTIFIC REVIEW.** Prepared 30 October 2026 from
documentation-only acceptance descendant `7da7100fe624481e6066390d503abea5b4292b4d`.
This is one proposed open-loop synthetic response, not an executable Workbench preset or
an authorization to implement or run it. No model construction, numerical calculation,
reference generation, test, simulation or qualification was performed for this proposal.
V0.3-C's accepted engineering functionality and V0.2's retained qualification are unchanged.

The question is how the existing model's longitudinal load redistribution and a subsequent
steering step interact during finite rolling deceleration. The brake-only prefix supplies
an analytical body-motion oracle; the later response exposes yaw/lateral transients and the
distinction between `a_cmd=Fx/m` and `dvx/dt=a_cmd+r*vy`. This experiment would not establish
closed-loop stability, controller robustness, real braking performance or stopping distance.

## Proposed fixed composition and conditions

| Item | Proposed RBT-0.1 value and meaning |
|---|---|
| Track | Reuse the **entire** existing `configs/planning/synthetic_grand_prix_v1/track_source.json` through `apex.planning_reference.track.load_track`; canonical periodic cubic `ClosedTrack`, SI, left-positive Frenet. Source SHA256 `5f4d1734d7fec7de56d346e8f90bf272a3de9c05ac42f76cd49004e7f9183e55`; manifest circumference 154.76345492731022 m; original half-widths 0.55/0.55 m. No new geometry, sector loop or reference generation. |
| Track interpretation | Literal start `s_abs=1 m` lies in the manifest's nominal `long_straight` sector. That name does **not** assert exact-zero spline curvature. Keep full original track identity and sampled curvature. Describe this as rolling response on the existing GP geometry, not an analytical straight-track experiment. |
| Plant | Canonical NumPy `DynamicBicycle`, no controller/prediction/optimizer, no feedback, no speed regulation and no equilibrium reconstruction. |
| Tires and loads | Explicit `LinearAxleTire`; explicit `QuasiStaticLongitudinalLoadTransfer(gravity=9.81 m/s²)`; no longitudinal axle allocation. This is the existing linear reference composition, not the smooth combined-grip racing composition. `mu` and lateral utilization remain diagnostics; no friction saturation or combined-slip behavior is claimed. |
| Vehicle | Unmodified `configs/vehicles/synthetic_dynamic_test_vehicle.yaml`, SHA256 `df1b853d21a1d3efaf858f7e58401151f2c5237793c40e16bb4189ed651f9cf3`: mass 2 kg, Iz 0.025 kg m², lf/lr 0.15/0.15 m, wheelbase 0.30 m, CG height 0.04 m, Cf/Cr 45/45 N/rad, mu 1, and all original configured limits. These are synthetic software values, not identified APEX parameters. No overrides. |
| Initial state | Literal `[vx,vy,r,e_psi,s_abs,e_y]=[2,0,0,0,1,0]` in `[m/s,m/s,rad/s,rad,m,m]`. Rolling `vx=2 m/s` follows the existing low-speed synthetic examples. Zero vy/r is deliberate excitation initialization, not a path-following equilibrium or a GP/P launch state. |
| Runner | Existing `SimulationRunner`, canonical RK4; prescribed integer-tick inputs, `latency=None`, input period equal to each plant grid; no worker/controller fallback behavior. |
| Horizon and stop | Finite 0.800 s, `target_laps=None`, proposed `stop_on_boundary=True`. End at horizon or an earlier existing model/domain/boundary failure; retain the last valid state, attempted command and exception/stop reason. No terminal braking extension, clamp to zero, reverse, automatic KinematicBicycle substitution or recovery. |

All values above are **proposed choices requiring scientific approval**, even where an
amplitude has a prior software example. The −0.5 m/s² braking amplitude is used in the
Task004 demonstration; +0.02 rad appears in its separate dynamic/kinematic comparison.
Their reuse reduces arbitrary excitation choices but supplies no validation for this
new coupled condition. The proposed 0.800 s horizon leaves a brake-only interval, a
combined interval and a post-brake steering interval without targeting standstill.

## Proposed ZOH input schedule

Inputs are `[delta,a_cmd]` in `[rad,m/s²]`. Changes apply at the **start** of the listed
interval, with the new command held through that interval; no ramps or interpolation.

| Native time interval [s] | delta [rad] | a_cmd [m/s²] | Purpose |
|---|---:|---:|---|
| `[0,0.100)` | 0 | 0 | Zero-slip rolling prefix. |
| `[0.100,0.300)` | 0 | −0.5 | Isolate braking/load redistribution before steering. |
| `[0.300,0.500)` | +0.02 | −0.5 | Observe turn-in while braking. |
| `[0.500,0.800)` | +0.02 | 0 | Observe steering response after brake release. |

The state at a transition is continuous and precedes propagation under the new input.
Record both pre-transition and new-command diagnostics explicitly if both are shown;
do not label a new-command force/load sample as the old held interval's value. The
0.800 s state is terminal information with the last held command and no subsequent
application interval. There is no new command at the horizon.

## Expected behavior and independent oracles

These are mathematical expectations under the stated model, not numerical results.

1. Before turn-in (`t≤0.300 s`), zero delta, vy and r imply zero axle slip/lateral force
   and zero lateral/yaw body derivatives. Thus `vy=r=0` and
   `vx(t)=2−0.5*max(0,t−0.100)` on that prefix. This body-channel identity does not require
   a zero-curvature Track. Curvature can still change e_psi/e_y relative to the spline;
   **do not** apply the straight Frenet oracle `s=s0+v0*t+0.5*a*t²`, assume e_psi/e_y stay
   zero or call the initial state a centerline equilibrium.
2. Independently transcribe the published load identities:
   `Fzf0=m*g*lr/L`, `Fzr0=m*g*lf/L`, `Fzf=Fzf0−m*a_cmd*h/L`,
   `Fzr=Fzr0+m*a_cmd*h/L`, `Fzf+Fzr=m*g`, with `L=lf+lr`.
   Braking raises front load/effective stiffness and lowers rear load/effective stiffness;
   brake release restores the static values instantly in this quasi-static model.
3. At the first steering evaluation, body vy/r remain zero, so
   `alpha_f=+0.02`, `alpha_r=0`, `Fyf=Cf*(Fzf/Fzf0)*0.02`, `Fyr=0`.
   The initial lateral acceleration and yaw acceleration are positive under the declared
   body equations. Independently evaluate `dvy=(Fyf+Fyr)/m−r*vx` and
   `dr=(lf*Fyf−lr*Fyr)/Iz`; do not generate expected values by calling model diagnostics.
4. After turn-in, compare `dvx−r*vy` to the applied `a_cmd`; body vx need not follow the
   brake-only affine formula. The provisional linear load scaling does not establish how
   a real tire's braking/turning response changes. No analytical full six-state transient
   or exact steady endpoint is available on the GP spline.
5. A separately coded direct step loop with the same canonical model and literal schedule
   can check adapter/SimulationRunner parity. It is a **composition/chronology** oracle,
   not an independent physics implementation. A segmented DOP853 reference using the
   canonical derivative is an independent integrator check only; it shares the equations.
   Analytical identities in items 1–3 provide the independent equation checks.

## Required retained evidence and domain disposition

Retain exact source/configuration/track/environment identities; literal state/schedule;
integer transition ticks; full native states and applied controls; terminal/partial rows;
stop reason, failed command and original exception. Required sampled diagnostic channels:
alpha_f/r [rad], Fyf/r and Fzf/r/static loads [N], nominal/effective Cf/Cr [N/rad],
Fx_total [N], a_cmd [m/s²], lateral utilization [dimensionless], curvature [1/m],
Frenet denominator [dimensionless], track_s/s_abs/e_y/widths [m], and yaw/heading [rad/s,rad].
Distinguish native telemetry from diagnostics evaluated at retained states and from any
producer-reconstructed XY. Missing combined utilization is expected for this no-allocation
linear composition; do not invent it. No reference-speed or tracking-error target exists.

Preserve canonical finite-state/control/derivative checks, nonnegative s_abs, configured
steering/acceleration/braking/speed limits, dynamic `vx≥0.5 m/s` with its existing 1e−10 m/s
roundoff allowance, actual/static axle loads above 1e−9 N, and `1−kappa*e_y>1e−3` at all
evaluated RK4 stages and final states. These are existing mathematical guard values, not
new empirical limits. Keep actual boundary violations and speed/domain failures visible.
RK4 stage guards and sampled center-corridor checks do not guarantee continuous corridor
containment, swept-body safety or validity between evaluations.

Do not import V0.2's slip/utilization/corridor teaching filters. No empirically supported
slip-angle or linear-tire validity envelope exists for this proposed response. Report
actual extrema without converting “finite” or a utilization below one into physical
validity. Primary must decide whether the intended outcome is strictly **sampled-model
numerical qualification** or additionally requires a justified model-validity window.

## Proposed bounded numerical assessment — approval required

Use the same physical schedule at `h=0.005,0.0025,0.00125 s`; corresponding horizon ticks
are 160/320/640 and transition ticks are `[20,60,100]`, `[40,120,200]`, `[80,240,400]`.
The nominal step is the canonical DynamicBicycle default; halving twice tests this new
transient rather than assuming that V0.2's finite trajectory results transfer. Evaluate
at **shared native ticks only**, using wrapped heading differences; no telemetry interpolation.
Assess each smooth interval and each transition separately so a switching error is visible.

Proposed future execution budget is three RK4 trajectories plus one segmented alternative-
integrator reference, after adapter/source review and separate execution authorization.
Do not run extra grids, steering signs, amplitude sweeps or replacement trajectories to
obtain a favorable result. This budget is a proposal, not permission to execute four runs.

Required acceptance mechanism:

- All runs preserve full horizon and schedule, satisfy the existing guards, and retain
  valid source-bound evidence. A partial is never a numerically qualified full response.
- Literal configuration/input chronology and canonical-runner parity must match; analytical
  prefix/load/force/moment residuals require an approved floating-point comparison budget.
- Define a separate absolute error budget for **each** channel vx, vy, r, e_psi, s_abs and
  e_y, with its SI unit, plus any relative term and near-zero rule. Require nominal versus
  quarter-grid and nominal versus alternative-integrator errors to satisfy those budgets.
  Require the alternative reference's own error-control budget to be tighter than them.
- Show successive-grid differences and interval-local refinement behavior. Classical RK4
  suggests fourth-order reduction on sufficiently smooth resolved intervals, but a fixed
  16× ratio is not an unconditional pass criterion near roundoff, spline knots, angle wraps
  or input discontinuities. A non-resolved trend is an inconclusive/failed numerical gate,
  not a reason to raise a threshold or silently refine again.

**Unresolved numerical decision RBT-N:** existing source/regression tests supply component
identities and an alternative-integrator method, but no error budget derived for this
0.800 s coupled response or its intended engineering interpretation. This proposal therefore
does not invent six numerical tolerances, reuse V0.2's values or promote the unrelated
regression's mixed-unit maximum-state bound. Primary must approve explicit component budgets,
oracle roundoff limits, reference settings and the refinement decision rule before this
protocol becomes execution-ready. Until then, no qualification PASS can be produced.

## Failure classes and remaining decisions

| Disposition | Required interpretation |
|---|---|
| Evidence/source failure | Quarantine changed/missing artifacts, source/config mismatch, malformed schedule or unsupported schema. Preserve original bytes; no scientific conclusion. |
| Canonical model/domain failure | Retain low-speed/load/Frenet/control/speed exception and last valid native state. Failed/partial response, no fallback model or favorable retry. |
| Corridor stop | Retain first sampled violation and original stop coverage; no full-horizon qualification or collision/safe-stop claim. |
| Numerical failure | Approved component/parity/oracle criterion fails. Preserve discrepancies and stop for review; do not tune the protocol. |
| Inconclusive | Missing required diagnostic, unresolved refinement trend/reference quality or unapproved validity/accuracy criterion. Do not convert to PASS. |
| Bounded numerical pass | Only after separately approved complete criteria and execution: faithful finite sampled-model response under this exact contract. No physical, closed-loop, recovery or real-time claim. |

Primary decisions are: **RBT-S** approve literal GP asset/state/schedule/stop and explicit
linear-tire/no-allocation interpretation; **RBT-N** resolve the numerical budgets above;
**RBT-V** decide/justify any additional model-validity window; then authorize adapter WORK,
independent review and a separately bounded qualification execution. An exact-zero-curvature
straight experiment would require a different reviewed geometry contract; do not substitute
the test-only `straight_geometry` or change the GP spline under this proposal.

## G versus P — separate future controller-execution alternatives

This RBT open-loop protocol selects **neither** racing controller profile.

| Future alternative | Exact existing identity to preserve | Separate decision needed |
|---|---|---|
| Historical conservative **G** | Original Task007A full GP/reference, external Candidate-C configuration, N4/dt0.1/four RK4 substeps, gamma1, progress0, smooth combined grip with explicit allocation, original APEX/TVLQR chronology and rolling launch. | Approve the exact source/configuration/archive binding and proposed owned execution adapter; qualify under that profile's original and newly approved runtime criteria. G is not P and is not newly accepted from its historical presence. |
| Accepted Performance **P** | Immutable Performance Synthetic v1 at `e603672b209985f11ed26b6f44d3949ffd5675c5`, Architecture A, N8/dt0.1/H0.8/four substeps, gamma2, original predictor, progress0, manifest-bound costs/scales/timing/native thread policy and original accepted conditions. | Approve exact-source deployment/adapter and qualification disposition. Current Workbench code/configuration resemblance does not inherit P source identity. Historical evaluation delays/stop conditions are not promoted controller defaults. |

Read-only P archive inspection does not choose P for new execution; an illustrative G/P
overlay is not a controlled treatment comparison. Keep C70 incomplete/censored evidence,
unknown build/physical limitations and original acceptance boundaries. Do not merge profile
settings, update frozen research or run NMPC/async/CT/hardware campaigns through this design.

Sources: [dynamic specification](../DYNAMIC_BICYCLE_SPEC.md),
[linear tire specification](../LINEAR_TIRE_SPEC.md),
[canonical model](../../src/apex/models/vehicle/dynamic_bicycle.py),
[loads](../../src/apex/models/vehicle/load_transfer.py),
[GP loader](../../src/apex/planning_reference/track.py),
[GP manifest](../../configs/planning/synthetic_grand_prix_v1/planning_manifest.json),
[runner](../../src/apex/simulation/runner.py),
[component oracles](../../tests/unit/test_dynamic_bicycle.py),
[integrator regression](../../tests/regression/test_dynamic_accuracy.py),
[existing demonstration](../../scripts/run_dynamic_bicycle_demo.py),
[existing comparison amplitude](../../scripts/compare_bicycle_models.py),
[C proposals](../apex_workbench_v0_3_c/RACING_SCENARIO_PROPOSALS.md),
[P acceptance](../TASK007E4_PERFORMANCE_ACCEPTANCE.md).
