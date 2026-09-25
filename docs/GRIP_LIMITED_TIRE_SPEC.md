# Smooth combined-grip axle tire — Task 006.1

## Purpose and scope

`SmoothCombinedGripTire` is a transparent engineering approximation, **not Pacejka,
Fiala, Dugoff, Magic Formula, or a fitted real-tire model**. It prevents a future racing
optimizer from exploiting unlimited lateral force. Task 006.1 adds force physics only:
no racing objective, solver optimization, actuator redesign or latency compensation.

The unchanged `LinearAxleTire` remains the explicit low-slip/reference law. Its force
may exceed friction capacity and is not physically credible there. Low-level legacy
constructors retain linear defaults for reproducible Task 004–006 regression; racing
composition explicitly selects the new model on BOTH plant and prediction sides.

## Components and configuration

- `models/tire/grip.py`: NumPy combined tire, immutable result and validity exception.
- `models/tire/linear.py`: unchanged reference force law and four-argument API.
- `models/tire/config.py`: immutable `TirePhysics` selection.
- `models/vehicle/force_allocation.py`: replaceable allocation protocol and normal-load
  proportional implementation. Allocation does not live inside the tire law.
- `DynamicBicycle`: computes loads/slips, calls the selected force law and preserves body balances.
- `control/mpc/symbolic_model.py`: independent CasADi transcription; never calls NumPy tires.
- `MPCConfig.tire_physics`: matches the prediction model to the selected plant physics.

`configs/models/synthetic_racing_tires.yaml` explicitly selects smooth combined grip and
normal-load proportional allocation. `linear_reference_tires.yaml` selects the linear law
with the same allocation for comparable combined-utilization diagnostics. Load with
`load_tire_physics`. `run_mpc_baseline.py` defaults to the racing selection and saves to
`results/mpc_grip`; `--tire-model linear` or `--tire-config PATH` selects a reference.
`run_grip_regression.py` uses the explicit racing selection for all cases.

Vehicle parameters remain independent. Grip requires configured finite mu>0. No missing
coefficient or drivetrain is guessed. `generic_1_10_racecar.yaml` is untouched. The test
vehicle's mu=1 is synthetic, not measured APEX grip. Custom numerical allocation can be
injected into the plant; a new allocation strategy needs a matching independent symbolic
implementation and parity tests before MPC use. The symbolic configuration rejects unknown
strategies. Generic linear constructors do not silently assign a drivetrain.

## Equations and input meaning

The canonical control remains [delta,a_cmd], with total requested tire force

    Fx_total = m*a_cmd

The idealized generic all-wheel allocation is

    Fx_f = Fx_total*Fzf/(Fzf+Fzr)
    Fx_r = Fx_total*Fzr/(Fzf+Fzr)

This is not a claim that the eventual vehicle is AWD. Allocation validates positive finite
loads and the plant checks finite outputs and conservation of total force. Later RWD/FWD,
torque splits and brake bias belong behind this interface, not inside saturation.

Existing longitudinal load transfer remains

    Fzf0=m*g*lr/L; Fzr0=m*g*lf/L
    Fzf=Fzf0-m*a_cmd*h/L; Fzr=Fzr0+m*a_cmd*h/L

For each axle, with C its nominal axle stiffness and alpha its exact atan2 slip:

    C_eff = C*Fz/Fz0
    F_limit = mu*Fz
    Fy_linear = C_eff*alpha
    Fy_capacity = sqrt(F_limit**2-Fx**2)
    Fy = Fy_capacity*tanh(Fy_linear/Fy_capacity)
    utilization = hypot(Fx,Fy)/F_limit

No hard clipping or hidden epsilon inside the square root. The load scaling is the existing
provisional linear approximation, not an identified tire load-sensitivity model.

## Domain and differentiability

Loads and stiffness must be positive finite; mu must be positive finite. The dimensionless
longitudinal reserve is **eta=1e-6**:

    abs(Fx)/(mu*Fz) <= 1-eta < 1

Requests exceeding this reserved boundary raise `TireForceValidityError`, including demands
at/beyond the full friction boundary. Longitudinal demand is never clamped by the plant.
At the reserved boundary the remaining lateral capacity is still positive, approximately
0.001414 times the friction limit. The reserve is numerical, not a measured safety margin.

CasADi adds the same per-axle normalized constraints at each control stage. Since allocation
is proportional and Fzf+Fzr=mg, longitudinal utilization is a_cmd/(mu*g), independent of state.
The acceleration variable bounds also intersect ±mu*g*(1-eta) and the positive-load bounds.
With existing zero IPOPT bound relaxation, this keeps trial evaluations within the square-root
domain. This is domain enforcement, not hidden force clipping. No max/sqrt regularization is
used. Load/domain checks are retained; application-time checking covers optimizer and fallback
commands. Existing actuator limits remain tighter for the synthetic mu=1 benchmark.

The force and dynamic equations have finite CasADi Jacobians in the open valid domain,
including zero slip and the smooth transition into saturation. Tests compare analytic steering
partials with central finite differences and evaluate near both longitudinal boundaries.
The diagnostic Euclidean force norm itself is nondifferentiable at the exactly zero force
vector; it is not used as a differentiable NLP constraint/objective. Normalized longitudinal
constraints and analytic force saturation enforce the envelope instead.

## Small- and high-slip limits

For z=Fy_linear/Fy_capacity,

    tanh(z)=z-z**3/3+O(z**5)
    Fy/Fy_linear=1-z**2/3+O(z**4)

Thus the zero-slip slope is exactly C_eff, although at finite slip saturation lowers the force.
The small-slip unit test uses alpha<=1e-5 rad and |z|<=5.625e-5, giving relative loss below
1.06e-9; its stated tolerance is 1.1e-9. At large signed slip, force approaches ±Fy_capacity.
Since |tanh(z)|<=1, Fx²+Fy²<=mu²Fz² algebraically, up to floating-point roundoff.

Longitudinal force reduces remaining lateral capacity at fixed load. Acceleration unloads the
front and loads the rear; braking does the reverse. Total friction capacity follows those
loads. Remaining lateral capacity additionally includes longitudinal utilization, so increasing
rear load does not imply unlimited remaining capacity at extreme acceleration.

## Body equations and diagnostics

No state or force-balance convention changes:

    dvx=a_cmd+r*vy
    dvy=(Fyf+Fyr)/m-r*vx
    dr=(lf*Fyf-lr*Fyr)/Iz

Front forces are still NOT rotated through steering-angle sine/cosine factors in the body
balance. This acknowledged simplification remains future model work. Frenet equations,
progress/wrapping semantics, and physical RK4 stages are unchanged.

Diagnostics expose Fx_f/r, Fy_f/r, Fzf/r and static loads, alpha_f/r, nominal/effective
stiffness, total friction limits, remaining lateral capacities and combined utilization.
Legacy lateral-only utilization fields retain their meaning. For the reference model,
combined utilization can exceed one; a nonexistent remaining capacity is reported as None,
not clipped. Selected grip outputs always obey the envelope within numerical tolerance.
Closed-loop scripts save all diagnostics as `tire_*` plant-state columns.

## Validation and artifacts

- Tire unit tests: small-slip limit, zero, odd symmetry, saturation, randomized/sample envelope,
  longitudinal tradeoff, load effects, allocation conservation and invalid demand.
- Independent NumPy/CasADi parity: 1000 seeded cases, symmetric/asymmetric geometry and stiffness,
  two friction coefficients; derivative, forces, utilization and 50ms RK4 comparisons.
- Jacobian tests: finite through transition and near admissible longitudinal boundaries;
  finite-difference checks. No deliberately invalid zero-capacity point is tested as valid.
- Scripted low/high demand vehicle maneuvers plus R=2m increasing-speed demand snapshots.
  Snapshots use linear-reference seeds to demonstrate saturation; they do not claim achieved
  steady grip-model circles above physical feasibility. A separate equilibrium root sweep
  (`check_grip_equilibria.py`) validates accepted R=2m solutions with original actuator
  limits and propagates them for0.5s; rejected roots do not prove global infeasibility.
- Matched plant/prediction NMPC: two laps each circle/oval at2m/s, representative disturbance,
  and45ms injection. Costs, references, horizon, integration and solver options stay unchanged.
- Existing full regression and latency tests; new grip-specific held-input/staleness/deadline tests.

The force-slip plot includes a tire-only a=6m/s² equivalent demand to make the
combined-force tradeoff visible. This is outside the configured vehicle actuator bound;
no dynamic-vehicle limit is changed.

See `results/tire_model` for curves, raw CSV, parity and vehicle comparisons. New NMPC output
is isolated in `results/mpc_grip`; Task006 historical output remains in `results/mpc_baseline`.
Task006.2 timing data include construction costs, raw IPOPT evaluation statistics, Jacobian/
Hessian sparsity and cold/warm observations. Timing is host/load dependent; no performance
optimization or horizon sweep is introduced here.

## Limitations and future models

Axle-aggregate bicycle forces; idealized longitudinal allocation; no longitudinal slip ratio,
wheel speeds, individual wheel loads, lateral load transfer, camber, tire temperature/wear,
measured tire parameters, or steering-frame force rotation correction. Friction is synthetic.
No combined-slip transient relaxation or fitted peak/post-peak curve. The smooth envelope
is bounded but does not establish real-world handling accuracy or racing safety.

A later identified Pacejka/Fiala/Dugoff or measured force map could replace this component
under a new specification. This task deliberately implements none of those named models.
Next: **Task006.2 computational cost and latency reduction**, then specified racing work.
