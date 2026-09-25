# Dynamic CG bicycle — Task 004

> Task 006.1 update: racing-development composition now explicitly selects
> `SmoothCombinedGripTire` and normal-load proportional longitudinal allocation in both
> NumPy plant and CasADi prediction. The linear law and its legacy constructor defaults
> remain available for reference regression. Statements below about unlimited force or
> diagnostic-only mu describe that historical linear selection. See
> [GRIP_LIMITED_TIRE_SPEC.md](GRIP_LIMITED_TIRE_SPEC.md) for the current grip physics,
> domain reserve, diagnostics and limitations. No body/Frenet equations changed.


## Scope and components

This is the first APEX model with independently propagated body-longitudinal velocity,
lateral velocity and yaw rate. All six channels [vx,vy,r,e_psi,s_abs,e_y] are dynamic.
It is a nonlinear vehicle/slip/Frenet model with a LINEAR, unsaturated lateral tire law.
It is not validated against an actual APEX vehicle and is physically credible only within
the assumptions of the low-slip force model. No controller is implemented.

- `models/vehicle/dynamic_bicycle.py`: orchestrates components and body force/moment balance.
- `models/tire/base.py`, `linear.py`: replaceable axle lateral-force law.
- `models/vehicle/load_transfer.py`: replaceable axle loads and immutable load result.
- `models/frenet.py`: shared positive-branch validity and Frenet kinematics.
- `models/integration.py`: classical RK4 independent of vehicle equations.
- `models/constants.py`: the single gravity default, 9.81 m/s².

Track is injected into the constructor. The unchanged DynamicsModel.step protocol allows
separate plant/prediction instances. `derivative(state,control)` exposes deterministic
NumPy f(x,u) for future finite-difference Jacobians, model validation and identification.
No CasADi-specific equations or controller dependencies are introduced.

## Parameters and stiffness naming

Dynamic readiness requires mass, yaw_inertia, wheelbase, lf, lr, cg_height,
front_cornering_stiffness and rear_cornering_stiffness. Friction coefficient is optional
for generic configurations; diagnostics return None when unavailable. The supplied synthetic
configuration includes it. Missing battery, motor, aero, body size or steering-rate fields
do not block dynamic propagation. Kinematic/full readiness checks remain separate.

The established configuration keys `front_cornering_stiffness` and
`rear_cornering_stiffness` implement Cf and Cr (the task's conceptual
cornering_stiffness_front/rear), in N/rad, AXLE AGGREGATES. They are not per-tire values.
No silent key rename, duplicate parameter source or factor-of-two conversion is introduced.
Existing positive/finite checks and wheelbase≈lf+lr consistency remain in force.

## Body-frame equations and input semantics

For this model ONLY:

    Fx_total = m*a_cmd
    dvx/dt = Fx_total/m + r*vy = a_cmd + r*vy
    dvy/dt = (Fyf+Fyr)/m - r*vx
    dr/dt = (lf*Fyf-lr*Fyr)/Iz

Therefore a_cmd=dvx/dt-r*vy, the longitudinal inertial-acceleration component along the
body axis. It is NOT the Task 003 convention a_cmd=dvx/dt. Controllers must know which
model interprets the input. Even a_cmd=0 can change dynamic vx through r*vy.
There is no longitudinal tire force allocation, wheel speed, powertrain or brake model.

Implement the task's equations literally: no front tire force steering-frame rotations,
cos(delta) factors or longitudinal projections of front lateral force are added. Exact
atan2 slip angles do not make these simplified body force equations a full wheel-frame
force transformation. This deliberate approximation is part of Task 004 fidelity.

## Slip and axle lateral force

For forward vx:

    alpha_f = delta - atan2(vy+lf*r, vx)
    alpha_r = -atan2(vy-lr*r, vx)

There is no small-angle approximation in these angle calculations. Positive slip produces
positive (leftward) axle lateral force. The tire law is separately defined:

    Cf_eff = Cf*(Fzf/Fzf0)
    Cr_eff = Cr*(Fzr/Fzr0)
    Fyf = Cf_eff*alpha_f
    Fyr = Cr_eff*alpha_r

The proportional load scaling is a provisional first-order educational approximation,
NOT a physically complete tire load-sensitivity model. See LINEAR_TIRE_SPEC.md.
mu is diagnostic only: abs(Fy)/(mu*Fz) may exceed one and is never used to clip forces.
No slip-angle threshold is invented; users must interpret large-slip output as physically
invalid rather than mistake numerical finiteness for tire-model validity.

## Quasi-static longitudinal axle loads

With L=lf+lr, gravity g and height h:

    Fzf0 = m*g*lr/L
    Fzr0 = m*g*lf/L
    Fzf = Fzf0 - m*a_cmd*h/L
    Fzr = Fzr0 + m*a_cmd*h/L

Use a_cmd, not body-coordinate dvx/dt, so no algebraic iteration with r*vy is needed.
Positive acceleration unloads the front; braking unloads the rear. Total load remains m*g.
`QuasiStaticLongitudinalLoadTransfer(gravity=...)` makes g configurable; default g=9.81
comes from one constants module. Require all actual/static axle loads >1e-9 N; values
at/below this conservative numerical-zero tolerance raise VehicleModelValidityError.
No clamping, wheel-lift simulation or suspension dynamics is implemented.

AxleLoads exposes front, rear, front_static, rear_static. Custom load components must
meet the same positive finite output contract. The dynamic model checks injected outputs.

## Frenet kinematics

At every derivative evaluation, wrap only the geometry query:

    track_s = wrap_progress(s_abs, track.length)
    kappa = track.sample(track_s).curvature
    D = 1-kappa*e_y
    ds_abs/dt = (vx*cos(e_psi)-vy*sin(e_psi))/D
    de_y/dt = vx*sin(e_psi)+vy*cos(e_psi)
    de_psi/dt = r-kappa*ds_abs/dt

The Task 003 rule D>1e-3 is shared without changing its behavior. FrenetGeometryError
reports invalid geometry rather than clipping D. s_abs remains unwrapped and nonnegative;
lap crossings neither reset state nor terminate propagation. e_psi wraps to (-pi,pi]
only after the completed integration step. No monotonic-progress clamp is imposed.

## Integration and validity

Classical fixed-step RK4 integrates all six states under zero-order-held delta/a_cmd.
Default dynamic dt=0.005 s; constructor default_dt and per-call dt are configurable.
Task 003 retains its 0.01 s default and existing stopping behavior. Every RK4 stage
recomputes slip, loads, stiffness, forces, curvature and D. Final state is also validated.

The dynamic low-speed default is configurable v_dynamic_min=0.5 m/s. Reject vx below
v_dynamic_min by more than 1e-10 m/s with LowSpeedValidityError. Values inside this
roundoff tolerance are used UNCHANGED, not replaced with an epsilon/minimum. Zero/negative
speed and reversing are unsupported. Braking through the threshold raises; it does not
stop at zero or switch to a kinematic model. A future hybrid plant may explicitly switch.

Configured steering/positive-acceleration/braking-magnitude bounds are rejected without
clipping. Configured maximum_speed is checked at input, every evaluated stage and final
output, with 1e-10 m/s roundoff tolerance, also without modifying vx. Undefined limits
remain undefined. No steering-rate actuator constraint exists. Unlike the kinematic tan
formula, dynamic slip uses atan2 and adds no independent steering tangent-domain limit;
large steering remains outside credible low-slip use even if no physical bound is supplied.

Finite shape-checked state/control inputs are copied, never mutated. Derivative/tire/load
outputs are checked for finiteness. Invalid conditions are exceptions, not race-completion
flags. RK4 checks evaluated states; it does not detect every possible between-stage
violation. Large steps can be unstable, inaccurate or cross unobserved validity regions.
Choose dt using convergence and trajectory-domain checks.

## Public API

    model = DynamicBicycle(parameters, track, default_dt=0.005, v_dynamic_min=0.5,
                           tire_model=None, load_model=None)
    state_dot = model.derivative(state, control)
    next_state = model.step(state, control, dt=None)
    diagnostics = model.diagnostics(state, control)

Default components are LinearAxleTire and QuasiStaticLongitudinalLoadTransfer. Protocols
require only evaluate methods and immutable result records; no suspension framework exists.
Diagnostics include alpha_f/r, Fyf/r, Fzf/r and static loads, Cf/Cr and effective values,
track_s, curvature, D, Fx_total, a_cmd, mu and optional lateral-utilization ratios.
These ratios exclude longitudinal force and are NOT combined-slip utilization.

## Synthetic validation vehicle (NOT actual APEX parameters)

Every value below is synthetic validation data only, not experimentally identified.
The 2 kg mass, 0.3 m wheelbase and 0.025 kg m² inertia provide a small-scale reproducible
benchmark; the inertia corresponds to a radius of gyration about 0.112 m. Stiffnesses
are chosen for a stable, low-slip software exercise, not inferred from tire measurements.

| Parameter | Synthetic value | Unit |
|---|---:|---|
| mass | 2.0 | kg |
| yaw inertia | 0.025 | kg m² |
| wheelbase | 0.30 | m |
| lf / lr | 0.15 / 0.15 | m |
| CG height | 0.04 | m |
| front / rear axle stiffness | 45 / 45 | N/rad |
| friction coefficient | 1.0 | dimensionless |
| steering bound | 0.4 | rad |
| acceleration bound | 2.0 | m/s² |
| braking magnitude bound | 3.0 | m/s² |
| speed bound | 6.0 | m/s |

The main generic vehicle YAML remains null. Its stiffness comments now explicitly state
axle-aggregate units. Synthetic geometry for the demo is a radius-5-m 128-point circle
with half-widths 0.6/0.9 m. Initial [vx,vy,r]=[2,0.024,0.4], e_psi=-atan2(0.024,2),
s_abs=L-0.5 and e_y=0 are a near-steady synthetic seed, not measured equilibrium.
Held steering=0.06 rad; a_cmd=0 for 0–2 s, +0.5 for 2–4 s, 0 for 4–6 s, -0.5 for
6–8 s, then 0. Changes take effect at step starts; no feedback is present.

The separate comparison uses the same parameters, a synthetic radius-15-m track,
steering=0.02 rad, a_cmd=0, dt=0.005 s, duration=4 s, initial vx=2 m/s and a shared
kinematic-consistent initial state. Dynamic tire slip introduces a transient and a different
lateral velocity. Its small vx drift is also expected from the different input semantics.
Neither model is established as physical truth by this comparison.

## Limitations and progression

Task 004 does NOT include nonlinear tire saturation, combined longitudinal/lateral slip,
wheel-speed dynamics, individual left/right wheel loads, lateral load transfer, roll,
pitch, suspension dynamics, aerodynamic drag/downforce, drivetrain, electric motor,
battery, steering actuator dynamics, or road surface variation. Load transfer and its
stiffness scaling are intentionally provisional. No tire saturation is hidden in diagnostics.
No boundary/vehicle-footprint collision model or controller is added.

Future tire/load components may replace the current evaluate implementations. Improved
models require specified physics and measured data. Task 005 should use these interfaces
for a baseline controller, without treating unvalidated synthetic parameters as APEX data.
