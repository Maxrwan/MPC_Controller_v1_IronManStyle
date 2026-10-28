# V0.2-A2 — Proposed finite scientific cases

**Proposal, not scientific acceptance or executed evidence.** Source/design pin:
`d975a1141ae94d836b31d0ed8457870fbe9c98b6`. D1–D5 are approved policy; the concrete cases,
new initial pose, event times and qualification criteria below require Primary APEX review.
Proposed case contract: `apex-vdl-linear-cases-v1`. No continuous slider interval is implied.

## Five cases, four comparisons

Share one baseline rather than introduce a separate seed or horizon for each question. Case IDs
are metadata; keep the canonical vehicle `name` identical so it is not a second changed field.
In this table, parameters not shown are fixed by the complete snapshot below.

| Proposed case ID | m [kg] | Iz [kg m²] | Cf [N/rad] | Cr [N/rad] | Post-step delta [rad] | Declared treatment versus VDL1_BASE |
|---|---:|---:|---:|---:|---:|---|
| VDL1_BASE | 2.0 | 0.025 | 45.0 | 45.0 | 0.020 | Shared baseline |
| VDL1_IZ_HIGH | 2.0 | 0.030 | 45.0 | 45.0 | 0.020 | `yaw_inertia` only |
| VDL1_STEER_HIGH | 2.0 | 0.025 | 45.0 | 45.0 | 0.025 | Post-step steering amplitude only |
| VDL1_CF_HIGH | 2.0 | 0.025 | 54.0 | 45.0 | 0.020 | `front_cornering_stiffness` only |
| VDL1_CR_HIGH | 2.0 | 0.025 | 45.0 | 54.0 | 0.020 | `rear_cornering_stiffness` only |

**Origins and rationale.** The baseline physical values come from the existing
[synthetic YAML](../../configs/vehicles/synthetic_dynamic_test_vehicle.yaml) and
[dynamic specification](../DYNAMIC_BICYCLE_SPEC.md); they are software fixtures, not measured APEX
properties. Steering 0.020 rad occurs in [compare_bicycle_models.py](../../scripts/compare_bicycle_models.py).
The 0.025 rad magnitude occurs in [test_dynamic_accuracy.py](../../tests/regression/test_dynamic_accuracy.py),
with a different initial state, acceleration, track and horizon. Neither source qualifies this new
step experiment. Iz=0.030 and Cf/Cr=54.0 are **new engineering proposals**, each +20% of its baseline;
the steering treatment is +25%. Increasing Iz avoids introducing a faster yaw acceleration solely
through a smaller inertia. Modest stiffness increases keep positive values near the existing fixture
and give separate front/rear questions. These choices do not establish conditioning, convergence,
realizability, or a physical sensitivity range. Their usefulness still needs the bounded qualification.

Mass sensitivity is deferred from the minimum registry/workload. D1 already permits it as an
independent synthetic counterfactual. At fixed `a_cmd`, changing mass changes `Fx=m*a_cmd`, axle loads
and lateral specific force, while Iz stays independently specified. A future finite mass family needs
its own reviewed numerical cases; no mass–inertia–geometry coupling law or extra run is added here.

## Full parameter snapshots

Each column is the complete effective `VehicleParameters` object, including inherited nulls.
`null` means unknown/unused, never zero. No YAML is changed and no generic unknown value is filled.

| Canonical field [SI unit] | BASE | IZ_HIGH | STEER_HIGH | CF_HIGH | CR_HIGH |
|---|---:|---:|---:|---:|---:|
| name [text] | synthetic_dynamic_test_vehicle | synthetic_dynamic_test_vehicle | synthetic_dynamic_test_vehicle | synthetic_dynamic_test_vehicle | synthetic_dynamic_test_vehicle |
| mass [kg] | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| yaw_inertia [kg m²] | 0.025 | 0.030 | 0.025 | 0.025 | 0.025 |
| wheelbase [m] | 0.30 | 0.30 | 0.30 | 0.30 | 0.30 |
| lf [m] | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 |
| lr [m] | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 |
| cg_height [m] | 0.04 | 0.04 | 0.04 | 0.04 | 0.04 |
| vehicle_width [m] | null | null | null | null | null |
| vehicle_length [m] | null | null | null | null | null |
| front_cornering_stiffness [N/rad] | 45.0 | 45.0 | 45.0 | 54.0 | 45.0 |
| rear_cornering_stiffness [N/rad] | 45.0 | 45.0 | 45.0 | 45.0 | 54.0 |
| tire_road_friction_coefficient [1] | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| maximum_steering_angle [rad] | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 |
| maximum_steering_rate [rad/s] | null | null | null | null | null |
| maximum_acceleration [m/s²] | 2.0 | 2.0 | 2.0 | 2.0 | 2.0 |
| maximum_braking_deceleration [m/s² magnitude] | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 |
| maximum_speed [m/s] | 6.0 | 6.0 | 6.0 | 6.0 | 6.0 |

## Common initial state, inputs and composition

Propose the canonical tuple **[vx, vy, r, e_psi, s_abs, e_y] = [2.0, 0, 0, 0, 0, 0]**,
with units [m/s, m/s, rad/s, rad, m, m]. vx=2 and zero-slip body states occur in
[dynamic unit fixtures](../../tests/unit/test_dynamic_bicycle.py); the full tuple also occurs in
[runner tests](../../tests/unit/test_runner.py). Its use with this real dynamic plant, track and
step schedule is a **new proposed experiment**, not a previously validated trajectory.
The pose is fixed at the first waypoint, aligned with its tangent, on its centerline. It is not the
legacy demo's near-steady seed. D3 independence remains approved; this minimum release offers this
finite common seed, rather than claim that arbitrary independent vx/vy/r edits have been qualified.

| Quantity | Proposed value | Origin/status |
|---|---|---|
| Steering prefix | 0 rad for 0 ≤ t < 0.100 s | Zero-slip fixture magnitude; new prefix/onset |
| Steering after onset | Case amplitude above for 0.100 ≤ t < 0.500 s | Existing magnitudes, new schedule |
| a_cmd | 0 m/s² throughout | Existing zero-force input; no speed regulation |
| Duration | 0.500 s | New short teaching window; 0.400 s of excitation, usefulness unqualified |
| Nominal plant/input period | 0.005 / 0.005 s | Existing dynamic default; new runner profile, unqualified here |
| Track | Existing `synthetic_track()` default: radius-5 m, 128 waypoints, left/right widths 0.6/0.9 m | Existing canonical spline construction, not an analytic-circle replacement |
| Model | DynamicBicycle + LinearAxleTire + QuasiStaticLongitudinalLoadTransfer, gravity 9.81 m/s², no allocator | Existing default linear composition; fixed |
| Runner | SimulationRunner; latency=None, target_laps=None, stop_on_boundary=False | Approved D4; ideal modeled input timing, sampled corridor monitoring |

The short horizon avoids an unnecessary multi-lap campaign; it is not an analytical assurance of
low slip, containment or resolvable rear response. Commands are held across each RK4 step. Exact
event/export rules and refinement profiles are in [NUMERICAL_CONTRACT.md](NUMERICAL_CONTRACT.md).

## Analytical checks and independent expectations

These are scalar deductions from the existing [body/slip/load equations](../DYNAMIC_BICYCLE_SPEC.md),
not adapter outputs, simulated results or golden trajectories.

- All populated parameters are finite and positive; h=0.04 is nonnegative. L=lf+lr=0.30 m,
  satisfying the canonical geometry check. The initial vx=2 is between the existing 0.5 and 6 m/s
  guards. All schedule levels satisfy abs(delta)≤0.4 and −3≤a_cmd≤2. Initial s_abs=0 is nonnegative.
- Initially e_y=0 gives D=1−kappa*e_y=1, independently of the spline curvature. Initial CG corridor
  membership follows from −0.9≤0≤0.6 m. Finite constructed track geometry remains a runtime check.
- At a_cmd=0 the longitudinal load-transfer term vanishes. All five cases have actual/static
  front and rear loads m*g/2=9.81 N, above the existing 1e-9 N rejection floor for the whole prescribed
  schedule. Thus Cf_eff=Cf, Cr_eff=Cr here. This says nothing about later slip or coordinate validity.
- Before the step, zero steering, vy and r give zero body forces/derivatives and vx=2, conditional
  on continued valid coordinate execution. On the curved track the Frenet pose still changes;
  zero body yaw is not centerline tracking or a circular equilibrium.
- `a_cmd=Fx/m`, and `dvx/dt=a_cmd+r*vy`. After steering, a_cmd=0 does **not** generally hold vx constant.

At the **same body state (vx,vy,r)=(2,0,0)** with a valid Frenet pose, immediately after applying
the declared step, alpha_f=delta and alpha_r=0. The following are analytical values only:

| Case | Fyf [N] | Fyr [N] | lf*Fyf−lr*Fyr [N m] | dr/dt [rad/s²] | dvy/dt [m/s²] |
|---|---:|---:|---:|---:|---:|
| VDL1_BASE | 0.900 | 0 | 0.13500 | 5.40 | 0.4500 |
| VDL1_IZ_HIGH | 0.900 | 0 | 0.13500 | 4.50 | 0.4500 |
| VDL1_STEER_HIGH | 1.125 | 0 | 0.16875 | 6.75 | 0.5625 |
| VDL1_CF_HIGH | 1.080 | 0 | 0.16200 | 6.48 | 0.5400 |
| VDL1_CR_HIGH | 0.900 | 0 | 0.13500 | 5.40 | 0.4500 |

All have instantaneous dvx/dt=0 at that shared body state, not throughout the response. Maximum
initial front utilization among these cases is 1.125/9.81 <1; initial abs(alpha_f)≤0.025 rad.
Those initial inequalities do not qualify their trajectories or validate the synthetic tire.

| Experiment | Immediate reasoning | Longer-term confounders and required interpretation |
|---|---|---|
| Inertia | dr/dt=(lf*Fyf−lr*Fyr)/Iz; the +20% Iz case initially has 5/6 of baseline yaw acceleration at identical forces | Slips and forces subsequently diverge; no guaranteed peak, damping, settling or steady-state trend |
| Steering | At the same state/load, increasing delta increases alpha_f and front force; rear force is initially unchanged | Ideal instantaneous actuator; vx drift and nonlinear slip/Frenet coupling prevent a universal tracking/handling claim |
| Front stiffness | At fixed positive alpha_f, Fyf scales by 54/45=1.2; its yaw contribution is positive | Evolving slip can reduce or reverse the force difference; increased stiffness may require a smaller dt |
| Rear stiffness | Zero initial rear slip gives the same initial force and body derivative, despite Cr changing | Rear slip must develop. Locally at onset, d(alpha_r)/dt=−(dvy/dt−lr*dr/dt)/vx=0.18 rad/s for baseline and CR_HIGH. This motivates later excitation, but proves neither a detectable finite-window difference nor its overall direction |

For nonzero slip, rear force scales with Cr and contributes −lr*Fyr to yaw; front contributes
+lf*Fyf. Signs reverse with slip. No understeer/oversteer, stability or physical identification is
established. Required actual telemetry is specified once in
[IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md#telemetry-and-provenance).
Insufficient excitation, invalid domains, unqualified convergence or bad evidence make the affected
comparison inconclusive/invalid under [VALIDITY_CONTRACT.md](VALIDITY_CONTRACT.md), without tuning or
discarding the failed case. These five cases remain proposed until scientific acceptance.
