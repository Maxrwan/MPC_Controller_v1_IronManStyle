# Linear axle tire — Task 004

> Task 006.1 update: racing-development composition now explicitly selects
> `SmoothCombinedGripTire` and normal-load proportional longitudinal allocation in both
> NumPy plant and CasADi prediction. The linear law and its legacy constructor defaults
> remain available for reference regression. Statements below about unlimited force or
> diagnostic-only mu describe that historical linear selection. See
> [GRIP_LIMITED_TIRE_SPEC.md](GRIP_LIMITED_TIRE_SPEC.md) for the current grip physics,
> domain reserve, diagnostics and limitations. No body/Frenet equations changed.


The force-law interface is `AxleTireModel.evaluate(slip_angle, nominal_stiffness,
normal_load, static_load) -> AxleTireResult(lateral_force, effective_stiffness)`.
Inputs use rad, N/rad and N. Forces and stiffness are AXLE AGGREGATES, not per-tire values.

The current implementation uses C_eff=C*(Fz/Fz0), Fy=C_eff*alpha. This is a provisional
educational normal-load scaling, not a complete load-sensitivity law. Nominal stiffness
and actual/static normal loads must be positive and finite. Positive slip yields force
leftward in the prescribed body-balance convention. There is no force clipping, Pacejka,
Fiala, Dugoff, friction circle or combined slip. Large-slip outputs are physically unreliable.

The vehicle computes exact atan2 front/rear slip angles; the force component does not own
vehicle kinematics, track queries, control semantics, gravity or body integration. A future
force law can implement the same small interface. Its reported effective stiffness may be
an equivalent diagnostic; the body model consumes lateral_force directly.

mu and abs(Fy)/(mu*Fz) belong to vehicle diagnostics only. Values above unity are permitted
numerically and do not authorize a claim that the tire could generate the predicted force.
