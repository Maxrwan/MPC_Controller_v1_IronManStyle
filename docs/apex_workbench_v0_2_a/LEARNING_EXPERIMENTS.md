# Three controlled learning experiments — designs only

**Not executed.** This A1 rationale is now paired with A2's concrete
[proposed numerical cases](PROPOSED_CASES.md), [clock/qualification](NUMERICAL_CONTRACT.md) and
[validity contract](VALIDITY_CONTRACT.md). D1–D5 are approved; case values/thresholds still need
Primary acceptance. Statements below about no selected values describe the A1 design stage only.
The expectations below are conditional inferences from the existing canonical equations, not
predicted empirical results or additional vehicle-model assumptions.

## Shared experimental contract

Use the explicit linear/no-allocation lab composition, fixed synthetic base geometry/mass except
the named factor, default quasi-static loads, fixed existing track and one reviewed clock/dt.
Keep identical source/environment, horizon, full initial tuple, schedule and every other effective
parameter. Launch serial jobs and retain baseline/perturbed raw files, metadata, prediction and notes.

A useful proposed excitation is an ideal steering step after an optional short coasting prefix,
with common reviewed forward `vx0`, initial `vy=r=0`, initial zero steering and `a_cmd=0`.
The full Frenet pose is explicitly reviewed and identical. This is a proposed zero-slip synthetic
initialization, not the legacy near-steady demo seed or a newly solved equilibrium. The fixed track
can remain curved: the coasting body states are identical before the step, while their track-relative
pose evolves and must remain within the approved domain. No new straight-track implementation is needed.

Choose the horizon/prefix so reviewed cases can be interpreted without unqualified coordinate/corridor
excursions. No value is selected here. Constant `a_cmd=0` holds specific longitudinal force at zero;
after steering begins it **does not hold vx constant**, because canonical `dvx=a_cmd+r*vy`. Show actual
vx histories/ranges and do not introduce speed feedback to enforce a cleaner-looking comparison.

Run two cases per overlay through the same lab profile. A baseline plus reviewed lower/higher levels
can be inspected in separate overlays; no sweep engine or fitted response model is necessary.
One treatment is declared before execution. Numeric completion, retained-evidence validity and
scientific/physical interpretation remain separate labels.

## E1 — Yaw moment of inertia sensitivity

**Question:** how does changing the modeled resistance to yaw acceleration affect the transient
response to the same prescribed steering input, with mass, geometry and tire properties fixed?

| Item | Design |
|---|---|
| Varied factor | Only `yaw_inertia`; reviewed finite positive cases around the synthetic nominal. No mass/geometry rescaling or inferred body-shape relationship. |
| Controlled | Full initial tuple; mass, axle distances/wheelbase, CG height, nominal Cf/Cr, tire/load choice, steering step, a_cmd, track, clock/dt/horizon and limits. |
| Qualified expectation | At the same state/control and identical axle forces, canonical yaw acceleration is net yaw moment divided by Iz. If that moment is nonzero, increasing Iz reduces its instantaneous magnitude; decreasing Iz increases it. With zero moment the initial comparison is uninformative. Subsequent slips/forces/states evolve, so there is no universal claim about peak yaw rate, damping, settling time, stability or final curvature. Iz cancels from a steady body moment-balance equation only under that equation's assumptions; this open-loop finite run is not a constant-speed equilibrium proof. |
| Existing observables | `time`, `r`, `vy`, `vx`, `delta`, `a_cmd`; `alpha_f/r`, `fyf/fyr`, `fzf/fzr`, `cf_eff/cr_eff`, and track-relative state. They are already emitted by the current demo; new lab exports use canonical calls. |
| Not currently observed directly | Yaw acceleration is not a current exported channel. Use r(t) for the teaching plot. A future test may call canonical `derivative` at the shared state; do not label a finite difference of r as measured acceleration. |
| Validity concerns | Small Iz can create a faster/stiffer numerical response for fixed dt; positive finite Iz alone is insufficient. Respect vx/load/Frenet/command checks, approved low-slip interpretation and convergence qualification. No invented safe inertia interval. |

**Required future tests/acceptance:**

- The factory changes only Iz; base YAML and input/state snapshots are unchanged. Canonical P rejects
  invalid values; no synthetic inertia is accepted as a measured vehicle property.
- At a reviewed shared valid state with nonzero yaw moment, an independent oracle from the existing
  documented force balance checks the expected inverse-Iz derivative relation using canonical
  `derivative()`. The oracle must not obtain its expected output from the new adapter.
- Adapter result matches an independently constructed canonical runner with the same profile;
  repeated identical inputs are deterministic under the declared environment.
- Keep full trajectories and diagnostics, actual speed drift, domain failures and any insufficient
  excitation. Do not fail an otherwise correct implementation merely because an unproved long-run
  qualitative trend is absent, or tune the case afterward to force a preferred plot.

## E2 — Steering response sensitivity

**Question:** how do the initial force response and subsequent body yaw/lateral response change
when only the steering-step amplitude changes?

| Item | Design |
|---|---|
| Varied factor | One `delta` amplitude field in an otherwise identical approved piecewise-constant schedule. Same onset tick, prefix and duration. No simultaneous rate, timing or parameter change. |
| Controlled | Vehicle/inertia/Cf/Cr, complete initial state, a_cmd=0 schedule, tire/load/track, dt/horizon, validity limits and export semantics. |
| Qualified expectation | At the same state/load the canonical front slip changes with delta. In the linear law positive Cf_eff gives a same-sign change in Fyf; the rear force is initially unchanged at a fixed state. Thus the instantaneous yaw-moment change has the sign of the steering change for positive lf. Long-run yaw/offset may be nonlinear and coupled to vx/vy; larger steering is not guaranteed to improve tracking or remain credible. |
| Existing observables | Actual applied `delta`/`a_cmd`, `r`, `vy`, `vx`, front/rear slip and lateral forces, loads, `e_psi`, `e_y`, `s_abs`, canonical derived XY. No solver/deadline or reference-tracking claim. |
| Validity concerns | Configured ±0.4 rad is the existing synthetic rejection limit, not an experimentally qualified low-slip range. The plant does not enforce steering rate. An ideal input jump is not a physical actuator response. Large finite unsaturated force is not extra grip. |

**Required future tests/acceptance:**

- Applied control rows equal the resolved tick schedule, including the first tick and transition
  boundaries; terminal control is explicitly informational. Reject off-grid/duplicate/unsorted events,
  unsupported schedule kinds, nonfinite inputs and configured-limit violations without snapping/clipping.
- At the shared reviewed state, verify the sign of the front-slip/force and yaw-derivative difference
  through independent canonical-law oracles; test a zero-amplitude control where meaningful.
- Confirm only the declared amplitude differs in effective metadata/controls; source, state, dt and
  timing are identical. A shifted onset time or changed tire is a different treatment and must not be
  silently classified as the same controlled experiment.
- Display sampled corridor violations and actual vx/slip histories. Numerical finiteness or return
  code zero must not be converted into a handling/safety acceptance claim.

## E3 — Front/rear cornering stiffness sensitivity

**Question:** how do front and rear axle force generation influence yaw/lateral transients under
the same steering excitation, when their nominal axle stiffnesses are varied separately?

| Item | Design |
|---|---|
| Varied factor | Two separate one-factor exercises: Cf-only versus common baseline, then Cr-only versus the same baseline. Each overlay varies one approved nominal axle stiffness. |
| Controlled | The other axle stiffness, mass, Iz, geometry, CG height, full initial state, steering/a_cmd, tire/load model, track, clock/horizon and limits. Do not silently keep a front/rear ratio by changing both. |
| Qualified expectation | At a fixed state/load, each axle's force scales with its nominal stiffness in the unsaturated linear law, with the existing load ratio retained. A positive front-force change contributes a positive yaw moment through lf; a positive rear-force change contributes a negative moment through lr. Signs reverse when the corresponding slip/force is negative. For the proposed zero-rear-slip initial step, Cr alone has no immediate rear-force effect until rear slip develops. Coupled later trajectories do not support a blanket understeer/oversteer, damping or stability conclusion. |
| Existing observables | `cf/cr`, `cf_eff/cr_eff`, `alpha_f/r`, `fyf/fyr`, `fzf/fzr`, `r`, `vy`, `vx`, controls and track-relative/XY channels. Nominal and effective stiffness must not be conflated. |
| Validity concerns | Stiffnesses are axle aggregates [N/rad], not per-tire values. Higher stiffness may increase integration stiffness and violate the reviewed low-slip/use envelope. Linear utilization can exceed one without clipping; it remains a diagnostic, not a force-capacity guarantee. |

**Required future tests/acceptance:**

- Verify independent Cf/Cr overrides, unit/name fidelity, no factor-of-two conversion, canonical
  positivity and full unchanged-parameter snapshots. No stiffness is back-calculated from mass/μ.
- Use existing force/moment/load-scaling contracts for independent same-state checks. Zero-slip
  force remains zero; changing one axle stiffness does not alter the other's same-state law.
- Compare each perturbed case to the same nominal lab composition. Simultaneous Cf/Cr changes are
  illustrative unless a later explicit composite-factor experiment contract is approved.
- Preserve zero/weak excitation, model-domain failures, corridor excursions and non-monotone response.
  Any fitted handling interpretation or stability claim is outside these experiments.

## Common software acceptance and scientific limits

Every future qualification requires reviewed literal case values, timestep candidates, numerical
criteria and an explicit interpretation window before execution. Qualification runs establish whether
the candidate timestep meets those criteria; ordinary qualified teaching runs require that evidence.
No observed result may manufacture the acceptance oracle. A2 proposes new tolerances explicitly for
review; existing fixture-specific tolerances do not silently transfer.

Acceptance requires exact V0.1 path/default preservation; correct effective parameters/full state/
held inputs; canonical-runner parity for the new profile; verified artifacts and visible failure/
coverage; one-factor classification; and no changes to canonical equations or frozen data.
Expected qualitative trends are conditional teaching hypotheses, not fabricated golden trajectories.

Use actual retained time/state/control/diagnostic samples. No interpolation across validity failure,
fictitious terminal samples, missing-data zeros, invented reference channels or automatic learner
explanations. A completed execution, valid evidence, admissible comparison and physically identified
vehicle remain four distinct concepts. No experiment above establishes physical validation.
