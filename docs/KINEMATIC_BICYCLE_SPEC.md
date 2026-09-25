# CG kinematic bicycle — Task 003

## Purpose and validity

This is an architecture/geometry/low-dynamic validation model and a possible future
simple prediction model. It is not a meaningful high-slip racing plant. It does NOT
represent tire forces, tire saturation, sideslip dynamics, yaw inertia, load transfer,
braking force physics, drivetrain dynamics, steering actuator dynamics or high-slip
racing behavior. The later dynamic bicycle is the first model intended to represent
meaningful racing lateral dynamics.

## Reference point, state manifold and parameters

The vehicle reference point is the CG. Canonical state ordering remains
[vx, vy, r, e_psi, s_abs, e_y], with vx and vy measured in the body frame at the CG.
Canonical vx is body-longitudinal velocity, NOT total CG speed.

Only z=[vx, e_psi, s_abs, e_y] is independently propagated. vy and r are algebraic
channels, reconstructed from current vx, steering and geometry at every RK4 stage
and after each step. Incoming finite vy/r are accepted but ignored by propagation;
NaN/Inf inputs are still rejected. `consistent_state` explicitly reconstructs them
without advancing time. A steering jump can instantly change both channels. There
are no invented lateral-acceleration or yaw-acceleration differential equations.

`VehicleParameters.validate_for_kinematic()` requires only wheelbase, lf, lr. The
existing positivity and wheelbase≈lf+lr checks (rtol 1e-6, atol 1e-9 m) still apply.
The equations use L=lf+lr. The full `validate_for_simulation()` gate remains unchanged;
it still requires all numeric fields. No mass, inertia, CG height, stiffness or friction
is required by this model. Any supplied optional field still obeys generic config validation.
The main generic race-car template remains null. synthetic_test_vehicle.yaml is explicitly
NOT experimentally identified and NOT representative of the final APEX vehicle.

## Equations

The zero-order-held input is u=[delta, a_cmd]. Ideal instantaneous steering has no
actuator state or rate dynamics. Define:

    L = lf + lr
    beta = atan((lr/L) * tan(delta))
    vy = vx * tan(beta)
    r = (vx/lr) * tan(beta)

At every derivative evaluation:

    track_s = wrap_progress(s_abs, track.length)
    kappa = track.sample(track_s).curvature
    D = 1 - kappa*e_y
    dvx/dt = a_cmd
    ds_abs/dt = (vx*cos(e_psi) - vy*sin(e_psi)) / D
    de_y/dt = vx*sin(e_psi) + vy*cos(e_psi)
    de_psi/dt = r - kappa*(ds_abs/dt)

The acceleration command is specifically d(vx)/dt; it is not a wheel force, torque,
or derivative of total speed. CG path curvature is r/hypot(vx,vy), not r/vx. At zero
speed, this curvature ratio is undefined even though the algebraic model is finite.

## Numerical integration and stopping event

Classical fixed-step RK4 advances only z. For held input u and derivative f:

    k1 = f(z,u)
    k2 = f(z+h*k1/2,u)
    k3 = f(z+h*k2/2,u)
    k4 = f(z+h*k3,u)
    z_next = z + h*(k1+2*k2+2*k3+k4)/6

Each stage recomputes beta, vy, r, wrapped progress, curvature and denominator from
its stage state. Heading is wrapped only after propagation using the existing
(-pi,pi] utility. s_abs is never wrapped. No seam crossing terminates the model.
The exact scalar solution vx_next=vx+a_cmd*h is used at the output to avoid residual
roundoff in this linear channel; all geometric channels use RK4.

Default timestep is one named constant, 0.01 s. Configure `default_dt` on construction
or pass dt to step; every timestep must be finite and positive. Controls are held for
the entire call. There is no automatic adaptive integration or general substepping.

If a_cmd<0 and stopping time t_stop=vx/(-a_cmd) falls within the step, integrate one
RK4 interval of length t_stop, set vx exactly zero, and freeze geometric state for the
remainder. vy/r also become zero. If already stopped under braking, hold the state.
A subsequent positive acceleration restarts forward motion. This unilateral stop policy
is a kinematic task requirement, not a braking-force/contact/friction model. Nonlinear
motion before a stop still has the accuracy of one RK4 interval of length t_stop.

## Validation and numerical policies

- Forward speed: reject vx<-1e-10 m/s. Negative values within 1e-10 m/s of zero are
  corrected to zero; small positive values are not automatically discarded.
- Configured maximum speed: validate input, stage and predicted/output speed. Excess
  >1e-10 m/s raises ModelValidationError. Only excess within that boundary tolerance
  can be corrected to the configured limit. No material speed saturation is implemented.
- Configured steering, acceleration and braking bounds are enforced without clipping.
  Braking deceleration is a positive magnitude. Undefined bounds impose no configured
  physical limit. maximum_steering_rate is intentionally unused: no actuator state exists.
- Mathematical steering domain: choose the principal branch -pi/2<delta<pi/2 and reject
  abs(cos(delta))<=1e-8 near tangent singularities. This numerical/model-domain restriction
  is distinct from an invented physical maximum steering angle.
- Frenet geometry: require D>1e-3, dimensionless, at input, every evaluated RK4 stage and
  final state. Both near-zero and negative denominators raise FrenetGeometryError with
  D, curvature, lateral error and progress. The threshold is conservative; D>1e-3 limits
  the local reciprocal factor to below 1000. The denominator is never clipped.
- All state/control entries must be finite and correctly shaped. Progress must remain
  nonnegative. Forward body vx does not guarantee positive track progress if the vehicle
  points against the track; the equations are not clamped to force monotonicity.
- A fixed RK4 method checks evaluated states, not every intermediate point of the unknown
  exact trajectory. Large steps can be inaccurate or miss a between-stage violation.
  Choose dt through convergence and domain testing; no dense event detector is claimed.
- Geometry validity failure is an exception, not an episode/lap termination flag.
  Track boundaries are not enforced and no collision/vehicle-footprint logic is present.

## API and architecture

`KinematicBicycle(parameters, track, default_dt=0.01)` stores the Track dependency.
`step(state, control, dt=None)` implements the existing model protocol without modifying it.
This lets future plant/prediction implementations use separate parameters/equations while
preserving controller and track interfaces. No controller imports exist in this module.

`diagnostics(state, control)` returns frozen KinematicDiagnostics with beta, vy, yaw_rate,
track_s, curvature and frenet_denominator. Diagnostics do not alter the canonical vector.
`consistent_state(state, control)` returns a copy with reconstructed vy/r and wrapped e_psi.
Inputs are never mutated.

## Validation and demonstration

Unit tests isolate equations with local analytical straight geometry and an exact circle;
these test doubles do not pretend an infinite straight line is a closed physical circuit.
Integration tests use Task 002's actual periodic spline and cross both L and 2L without
resetting progress. Regression uses a smooth constant-steering/constant-acceleration case
with an independent closed-form Cartesian trajectory; halving dt yields approximately
16-fold position-error reduction. No order claim is made for stopping/threshold cases.

The headless demo uses explicit synthetic geometry, radius-5-m 128-waypoint track,
fixed steering from the analytical circle geometry, and an a_cmd schedule: +0.25 m/s²
for the first 2 s, zero until 6 s, then -0.25 m/s². Starting vx=2 m/s, e_psi=-beta,
s_abs=L-0.5 m and e_y=0 are synthetic initial conditions. Controls are functions of time
only; no feedback correction hides spline approximation error. At arbitrary configured
steps, schedule transitions take effect at the next step start (zero-order hold).

CSV rows describe state and the command applied starting at that row; the final row's
command is informational because no subsequent interval is simulated. Every CSV includes
time, six canonical states, delta, a_cmd, track_s and curvature. The script also writes
summary.json and optional trajectory.png under results/kinematic_demo/.

Task 004 must add separately specified tire/load/force physics, not retrofit hidden
corrections into this kinematic reference model.
