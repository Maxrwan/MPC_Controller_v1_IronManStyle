# Vehicle model specification and progression

> Task 006.1 update: racing-development composition now explicitly selects
> `SmoothCombinedGripTire` and normal-load proportional longitudinal allocation in both
> NumPy plant and CasADi prediction. The linear law and its legacy constructor defaults
> remain available for reference regression. Statements below about unlimited force or
> diagnostic-only mu describe that historical linear selection. See
> [GRIP_LIMITED_TIRE_SPEC.md](GRIP_LIMITED_TIRE_SPEC.md) for the current grip physics,
> domain reserve, diagnostics and limitations. No body/Frenet equations changed.


Task 003 implements a CG kinematic bicycle. Task 004 adds dynamic CG force/moment
balances, unsaturated linear axle tires and provisional longitudinal load transfer.
Battery, drivetrain and improved tire/suspension physics remain unimplemented.

1. Kinematic bicycle: implemented; see KINEMATIC_BICYCLE_SPEC.md for equations and validity.
2. Nonlinear dynamic bicycle: implemented; see DYNAMIC_BICYCLE_SPEC.md and LINEAR_TIRE_SPEC.md.
3. Initial load transfer: implemented quasi-static front/rear longitudinal axle-load approximation.
4. Improve tire/load transfer with lateral transfer, independent tire loads, pitch/roll,
   and potentially aerodynamics; consider a four-wheel model after validation.

Future dynamic-model equations, assumptions, operating limits and numerical integration
choices require later engineering specifications and mathematical tests. Plant and controller prediction
models may deliberately differ; document their fidelity and parameters separately.

## Configuration contract

`VehicleParameters` is a frozen dataclass. The YAML template documents SI units for each
field. Unknown values are null; name is mandatory. Omitted numeric fields also remain None.
Known values must be finite real numbers, excluding booleans. All must be positive except
CG height, which may be zero. Maximum braking deceleration is a positive magnitude;
braking acceleration commands are negative. Cornering stiffness fields represent axle aggregates [N/rad], never per-tire stiffness.
When supplied together, wheelbase must equal lf + lr (relative tolerance 1e-6,
absolute tolerance 1e-9 m). These are configuration checks, not a dynamics model.

`validate_for_simulation()` or loader `require_complete=True` rejects every undefined
numeric parameter. This conservative readiness gate may be specialized for a future
model's actual requirements; the template is deliberately not runnable.
No measured or estimated physical parameter values are provided in Task 001.

## Task 003 model-specific readiness

`validate_for_kinematic()` requires only wheelbase, lf and lr. It does not weaken the full
simulation/configuration gate. Kinematic propagation treats body-CG vx, e_psi, s_abs and
e_y as independent states and reconstructs vy/r algebraically from steering at each stage.
No tire forces/saturation, sideslip dynamics, yaw inertia, load transfer, braking forces,
drivetrain, steering actuator or high-slip racing behavior is represented. The dynamic
bicycle will be the first model with meaningful racing lateral dynamics.

## Task 004 dynamic readiness and input distinction

validate_for_dynamic requires mass, yaw_inertia, wheelbase, lf, lr, cg_height and front/rear
axle cornering stiffness. mu is optional diagnostic metadata; the synthetic fixture supplies
it. Other model validation contracts remain unchanged. All six states are now differential
states in DynamicBicycle. Its a_cmd=Fx/m=dvx/dt-r*vy differs explicitly from KinematicBicycle.
No automatic switch/blend is performed below the dynamic speed threshold. See the dynamic
specification for provisional load scaling, unsaturated forces and numerical validity.
