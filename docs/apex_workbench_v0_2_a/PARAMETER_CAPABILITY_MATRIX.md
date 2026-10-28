# Parameter capability matrix

Read with the [scope and review decisions](README.md). All defaults below are **existing synthetic
software fixtures**, never measured/identified APEX properties. A code-enforced mathematical
contract is not an experimentally validated range. No new numeric parameter range is proposed.

## Source and coverage key

| Key | Canonical source / inspected coverage |
|---|---|
| P | [VehicleParameters](../../src/apex/models/vehicle/parameters.py): frozen dataclass, constructor and `validate_for_dynamic()` |
| CFG | [Safe loaders](../../src/apex/config.py); [synthetic dynamic YAML](../../configs/vehicles/synthetic_dynamic_test_vehicle.yaml); [generic unknown YAML](../../configs/vehicles/generic_1_10_racecar.yaml) |
| D | [DynamicBicycle](../../src/apex/models/vehicle/dynamic_bicycle.py): constructor, `_inputs`, `_evaluate`, `derivative`, `step` |
| LT | [QuasiStaticLongitudinalLoadTransfer](../../src/apex/models/vehicle/load_transfer.py) |
| LI / GR | [LinearAxleTire](../../src/apex/models/tire/linear.py) / [SmoothCombinedGripTire](../../src/apex/models/tire/grip.py) |
| TP / FA | [TirePhysics](../../src/apex/models/tire/config.py) / [NormalLoadProportionalAllocation](../../src/apex/models/vehicle/force_allocation.py) |
| X / F | [Canonical vectors](../../src/apex/state.py) / [Frenet rates/domain](../../src/apex/models/frenet.py) |
| I / R | [RK4](../../src/apex/models/integration.py) / [SimulationRunner, RunConfig](../../src/apex/simulation/runner.py) |
| DEMO | [Task004 entry point](../../scripts/run_dynamic_bicycle_demo.py): factories, fixed seed, `command`, `main` |
| W | [V0.1 configuration](../../tools/apex_workbench/configuration.py): input allowlists/defaults and explicitly nonphysical UI/resource bounds |
| LQR | [Task005 construction](../../scripts/run_lqr_baseline.py), [linear design](../../src/apex/control/baseline/lqr.py), [references](../../src/apex/control/baseline/references.py), [controller](../../src/apex/control/baseline/controller.py) |
| TC | [test_config.py](../../tests/unit/test_config.py): `test_invalid_mass`, `test_geometry_consistency`, loader/unknown-field/readiness cases |
| TD | [test_dynamic_bicycle.py](../../tests/unit/test_dynamic_bicycle.py): readiness, force/moment oracle, exact slips, input semantics, bounds, low speed, RK stages, immutable deterministic outputs |
| TL | [test_dynamic_components.py](../../tests/unit/test_dynamic_components.py): asymmetric static loads, load direction/conservation/unloading, linear law, no saturation |
| TG | [test_grip_tire.py](../../tests/unit/test_grip_tire.py): explicit selection, force domain, allocation, small-slip/high-demand behavior and NumPy/CasADi parity |
| TX / TR | [test_state.py](../../tests/unit/test_state.py) / [test_runner.py](../../tests/unit/test_runner.py): vectors; hold/rates, failure/corridor/termination |
| TA | [dynamic accuracy regression](../../tests/regression/test_dynamic_accuracy.py), [dynamic track integration](../../tests/integration/test_dynamic_track.py) |
| TB | [baseline tests](../../tests/unit/test_baseline.py): design matrices/references, scheduling, configured command/rate limits |

Coverage means source/tests were inspected. They were **not run in V0.2-A**. Existing tested fixtures
and force/integration checks do not qualify every possible override or a real vehicle.

## A. Meaning, defaults and actual constraints

`L` below denotes `lf+lr`, as used by canonical loads/references. All constraints remain enforced
again by canonical construction/evaluation; a UI must not coerce, clip or silently repair them.

| ID / field | Meaning and SI unit | Source / existing default | Existing enforced contract | Dependencies and coupled constraints |
|---|---|---|---|---|
| P1 `mass` | Vehicle mass [kg] | P.mass; D/LT; YAML **2.0** | Finite real, excluding bool, >0; no upper bound or physical interval specified | Changes lateral specific force and loads. At fixed `a_cmd`, `Fx_total=m*a_cmd` also changes; it is not a fixed-force experiment. No specified rule links mass to inertia/stiffness. |
| P2 `yaw_inertia` | Yaw moment of inertia about modeled CG vertical axis [kg m²] | P.yaw_inertia; D.derivative; YAML **0.025** | Finite real >0; no physical interval or shape-based consistency law | Divides net yaw moment. No automatic change of mass/geometry or equilibrium; small inertia can make the selected fixed timestep inadequate. |
| P3 `lf` | CG-to-front-axle distance [m] | P.lf; D/LT; YAML **0.15** | Finite real >0 | Front slip arm, yaw arm, static load split and transfer length; must satisfy P5 with P4. Changing it is not only changing a moment arm. |
| P4 `lr` | CG-to-rear-axle distance [m] | P.lr; D/LT; YAML **0.15** | Finite real >0 | Rear slip/yaw arm and static load split; coupled to P3/P5. |
| P5 `wheelbase` | Axle separation [m] | P.wheelbase; YAML **0.30** | Finite real >0; equals `lf+lr` with existing `rel_tol=1e-6`, `abs_tol=1e-9 m` | Dynamic loads/slips use axle distances; independently changing this field cannot create a different dynamic geometry while leaving both distances fixed. Geometry editing policy needs review. |
| P6 `front_cornering_stiffness` | Nominal **front axle aggregate** stiffness [N/rad] | P; LI/GR; YAML **45.0** | Finite real >0; no physically credible slip/stiffness range specified | Effective value is canonical load-scaled stiffness; depends on actual/static front load. No per-tire factor-of-two conversion. |
| P7 `rear_cornering_stiffness` | Nominal **rear axle aggregate** stiffness [N/rad] | P; LI/GR; YAML **45.0** | Same constructor contract as P6 | Rear load scaling and slip; front/rear edits must be declared independently or as an explicitly approved composite factor. |
| P8 `cg_height` | CG height for provisional longitudinal load transfer [m] | P/LT; YAML **0.04** | Finite real **≥0** | Coupled to command and geometry through axle loads. Actual and static loads must each exceed canonical `1e-9 N`; no roll/pitch/suspension model. |
| P9 `tire_road_friction_coefficient` | Axle friction coefficient μ [dimensionless] | P/D/GR; YAML **1.0** | P permits None or finite >0. GR requires explicit finite >0 | Linear: diagnostics only. Grip: changes capacity/domain, coupled to allocation and `a_cmd`; these uses are not interchangeable. |
| X1 initial `vx` | Body-longitudinal CG velocity [m/s] | DEMO **2.0**; X/D | Canonical state finite; D default minimum **0.5 m/s**, roundoff tolerance **1e-10 m/s**; fixture maximum **6.0 m/s**, same tolerance | Forward-only validity; checked at input, RK stages and final output. Neither the model floor nor fixture ceiling is an identified physical range. LQR's 1–3 m/s design domain is a different contract. |
| X2 initial `vy` | Body-lateral CG velocity [m/s] | DEMO **0.024**; X/D | Finite; no independent magnitude bound specified | Changes both slips and longitudinal `r*vy` coupling. Do not reconstruct it algebraically as in the kinematic model. |
| X3 initial `r` | Yaw rate [rad/s] | DEMO **0.4**; X/D | Finite; no independent magnitude bound specified | Changes both axle slips, body coupling and Frenet heading dynamics. All six dynamic channels are independent differential states. |
| X4 initial `e_psi`, `s_abs`, `e_y` | Track-relative heading [rad], unwrapped progress [m], lateral offset [m] | DEMO `-atan2(0.024,2)`, `track.length-0.5`, **0** | X finite/shape; `s_abs≥0`; F requires `1-kappa*e_y>1e-3` | Track length/curvature come from canonical spline geometry. Step wraps heading after integration, not progress. Corridor membership is a separate sampled CG condition. No pose recomputation when X1–X3 change unless explicitly declared. |
| U1 `delta(t)` | Front steering input [rad] | DEMO constant **0.06** | Finite; fixture `abs(delta)≤0.4`, rejection without clipping | Dynamic slip uses atan2, not a steering tangent singularity limit. Large allowed steering can still violate low-slip credibility. No physical steering actuator/rate state. |
| U2 `a_cmd(t)` | Commanded total longitudinal tire force divided by mass [m/s²] | DEMO **0** for 0–2 s, **+0.5** for 2–4 s, **0** for 4–6 s, **−0.5** for 6–8 s, then **0** | Finite; fixture **−3≤a_cmd≤2**. Positive/braking magnitudes are stored separately. No clipping in D | `dvx/dt=a_cmd+r*vy`, not `a_cmd`. LT uses `a_cmd`; positive load and, for GR, longitudinal friction reserve can impose tighter coupled limits. |
| N1 `dt`, duration | Numerical step and duration [s] | D/DEMO/W **0.005**, Workbench dynamic duration **10.0** | Model dt finite >0. V0.1 UI guards dt **0.001–0.01**, duration **0.01–20** are resource/numerical safeguards, not accuracy guarantees | R additionally requires duration/control periods to align to integer plant ticks. Changes in stiffness/inertia may need qualified dt; no automatic solver or timestep repair. |

DEMO input transitions use the original `1e-12 s` comparisons and a final shortened step when
duration is off-grid. That is historical behavior to preserve in the old adapter, not a new
schedule tolerance to copy into an unrelated clock profile.

## B. Effect, adapter work, coverage and readiness

**Scope:** the proposed lab is open-loop. Every exposed vehicle override affects its plant;
there is **no controller prediction/design model** to mutate. The existing LQR adapter stays fixed.
The last column records canonical consumers if a later, separately authorized LQR adapter were
to pass altered parameters there; it does not grant such authority.

| IDs | Proposed first-lab treatment / adapter work | Existing verification coverage and gaps | Readiness / approval | Other canonical controller-model consumers |
|---|---|---|---|---|
| P1 | Immutable override merged into full effective P snapshot | TC mass-specific invalid cases; TD hand force/moment and command semantics; TL/TA. No mass operating-range sweep or physical calibration | Canonical interface ready; synthetic cases/envelope pending decision D1 | LQR lateral matrices and cornering references use mass; changing a shared P there would change design as well as plant |
| P2 | Same, no inferred geometry/mass relationship | TD force/moment oracle/readiness; TB transient matrices. No arbitrary-inertia timestep/handling qualification | Canonical ready; D1 approved inertia cases and dt qualification required | LQR transient matrices/gains use inertia; steady reference force balance cancels it |
| P3–P5 | **Fixed initially**; future geometry contract must derive/reject explicitly, never edit YAML | TC geometry-consistency rejection; TL asymmetric loads; TB asymmetric references; TG asymmetric parity fixtures. Not a geometry envelope | Supported constructor fields; coupling policy D2 required before enabling | LQR matrices/references use axle geometry; plant/design effects must later be independently declared |
| P6–P7 | Independent immutable overrides; each approved sweep varies one field | TL linear law; TD force/moment/load scaling; TG small-slip/parity. No measured stiffness/slip domain | Canonical ready; D1 axle-aggregate case sets and D3 low-slip interpretation pending | LQR lateral matrices/gains and references consume both nominal stiffnesses |
| P8 | **Fixed initially** | TL zero-height/gravity/load-conservation/unloading; TD load failures and effective stiffness | Supported; changing transfer physics or envelope requires separate review | LQR linear design neglects command-induced load variation; no automatic matched design effect should be claimed |
| P9 | **Fixed initially**, always label tire selection | TD `test_mu_diagnostic_only`; TG explicit μ/domain/allocation checks | Linear diagnostic behavior ready; grip extension separately gated | Linear LQR ignores friction; a grip-aware controller/prediction is different work, not provided here |
| X1–X3 | Explicit independent initial values in canonical full-state snapshot; no equilibrium solve or hidden edits to X4 | TX finite vectors; TD low-speed/slip/coupling/pure propagation; TA. No bound for every `vy/r` or arbitrary combination | Supported APIs; initial-state/envelope contract D3 pending | Initial state is not a design parameter. Existing LQR would respond/schedule from state if used, but is not used by this lab |
| X4 | Show full canonical pose, **fixed initially** | TX nonnegative unwrapped progress; TD Frenet rejection/heading wrap; TA seam equivalence | Supported state fields; pose-edit policy/domain review before enabling | Track/heading error feed existing feedback; no feedback exists in new lab |
| U1–U2 | Strict finite constant/step ZOH schedule, serialize resolved applied inputs; no user code or free-form functions | TD signs, slips, command semantics/control bounds/stage checks; TR hold/rates/failures; TG force rejection | Canonical inputs ready; schedule levels/events/validity D3 and clock D4 pending | Prescribed inputs bypass feedback only in the new open-loop adapter; existing LQR/PI still generates its own bounded commands |
| N1 | Keep existing resource caps; explicit versioned integer-tick lab clock; no adaptive integration | TR rates/config/failure tests; TD evaluated-stage checks; TA RK4/reference accuracy; V0.1 byte parity | Runner available; lab case-specific convergence and clock/export contract D4 required | Existing LQR retains 200 Hz plant/100 Hz control; no rate change in V0.1 |

## C. Audited fixed/unsupported properties

| Field/component | Existing value/interface | Actual effect and readiness |
|---|---|---|
| `maximum_steering_angle`, `maximum_acceleration`, `maximum_braking_deceleration`, `maximum_speed` | Fixture **0.4 rad, 2 m/s², 3 m/s² magnitude, 6 m/s** | Plant rejection limits; LQR also clips relevant commands. Keep fixed in the minimum lab; never remove a limit by replacing it with None. These fixture limits are not real-vehicle certification. |
| `maximum_steering_rate` | None in dynamic fixture; P can store positive rad/s | DynamicBicycle does **not** enforce it. Existing BaselineController can rate-limit (TB). Exposing it as an open-loop actuator limit would be false; a new actuator/rate contract is separate work. |
| `vehicle_width`, `vehicle_length` | None in dynamic fixture/generic unknown template | Not used in this bicycle force model or a swept-body collision check. Do not enable ineffective fields or infer body size from wheelbase. |
| `v_dynamic_min` | D constructor default **0.5 m/s** | Configurable model-domain guard, not a new low-speed model. Keep fixed; changing it does not authorize standstill/reversing. |
| Gravity/load model | LT default **9.81 m/s²**; custom `AxleLoadModel` protocol | Existing gravity injection and positive-load checks; no suspension/roll/pitch implementation. Keep fixed. Protocol availability is not an implemented alternative model. |
| Track | DEMO radius-5 m, 128-point closed spline, widths 0.6/0.9 m | Actual numerical arc length/curvature from canonical track. Fixed profile; no analytic-circle substitution, new track or VIS work. |

## D. Tire alternatives — separate composition audit

| Selection | Actual canonical behavior | Construction/coupling and evidence | Minimum-lab disposition |
|---|---|---|---|
| `LinearAxleTire`, default `TirePhysics()` | Load-scaled axle-linear lateral force; unsaturated. μ only changes diagnostics | `DynamicBicycle(P,track)` defaults to this law, no longitudinal allocator. TD/TL/TA cover declared fixture behavior. Large-slip credibility has no numeric cutoff in code | **Explicit first-lab choice**, preserving the legacy model identity; not a measured tire |
| Linear reference plus `normal_load_proportional` | Same lateral law, explicit longitudinal split enables combined-force diagnostics; does not saturate Fy | [linear_reference_tires.yaml](../../configs/models/linear_reference_tires.yaml) selects an allocator unlike the default Task004 constructor. Combined utilization may exceed one | Supported alternate composition, **not** a silent substitute for the default. Not needed initially |
| `SmoothCombinedGripTire` + explicit allocation | Smooth bounded lateral envelope; positive μ changes physics. Longitudinal demand is rejected outside the reserved domain, never clipped | TP requires explicit allocation; D enforces injected-tire μ matching. FA conserves total Fx. GR reserve **1e-6** and positive axle loads apply; TG and [grip specification](../../docs/GRIP_LIMITED_TIRE_SPEC.md) cover existing synthetic parity | Defer selector/μ edits. Requires separate reviewed composition, domain and comparison contract; no NMPC/async work follows from this audit |
| Pacejka/Fiala/Dugoff, wheel slip/relaxation, left/right suspension, new drive/brake allocation | Not implemented by these components | Protocol injection alone supplies no equations, parameters or verification. KinematicBicycle is another vehicle model, not a tire alternative or automatic low-speed fallback | Not ready; requires new scientific specification/implementation authorization |

A grip comparison must declare the same allocation, loads, vehicle and inputs on both sides if it
aims to isolate only the force law. Even then it is a different-model illustrative comparison, not
proof that either tire matches APEX hardware. Never transfer a linear-law operating claim to grip
or treat the grip envelope as a real-tire fit.
