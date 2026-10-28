# APEX Workbench V0.2-A — Vehicle Dynamics Laboratory design

**V0.2_DESIGN_COMPLETE_PENDING_SCIENTIFIC_REVIEW.** 28 October 2026.
Read-only scientific audit and proposed implementation design; **no V0.2 code, numerical test,
simulation, parameter sweep or scientific implementation change was executed**.

Audit baseline: `c26782da2a9b94187a070ed5d9f72106a093d27e`.
Accepted V0.1 implementation: `77d018b11bbbfc39ab81d98c9bef70e90ab82725`.
The baseline differs from that implementation only in documentation/evidence records. Design branch:
`codex/apex-workbench-v0-2-a-design`. The containing documentation commit is the delivery revision;
its exact SHA/URL is supplied after push. Source hashes are in [audit_record.json](audit_record.json).

## Recommendation

Add one **open-loop `dynamic_lab` adapter**, reusing canonical `VehicleParameters`, `DynamicBicycle`,
fixed-step integration through the existing `SimulationRunner`, canonical track/Frenet APIs and the
verified Workbench worker/lifecycle/storage pipeline. The lab uses prescribed inputs, not a new
feedback controller. It adds no physics equations, integrator, simulation engine or solver.

The smallest useful first implementation exposes reviewed synthetic mass, yaw inertia and independent
front/rear axle stiffness overrides; independent initial `vx`, `vy`, `r`; and constant/step,
piecewise-constant steering and `a_cmd`. Values/presets and an operating envelope must first be
approved. Geometry, CG height, friction, validity thresholds, actuator limits, track and tire/load
selection stay visible but fixed initially. Their capability is audited, not silently enabled.

The original `dynamic_demo` and `lqr_baseline` adapters remain unchanged, including exact V0.1 default
inputs, execution paths, exports and parity. The new lab has an explicitly versioned runner profile;
it is not advertised as byte-identical to the legacy demo. Its nominal and perturbed cases share
that profile. See the [clock/parity distinction](ADAPTER_DESIGN.md#execution-and-default-preservation).

## Deliverables

| Document | Purpose |
|---|---|
| [Parameter capability matrix](PARAMETER_CAPABILITY_MATRIX.md) | Source/defaults, mathematical checks, couplings, plant/design-model effects, existing coverage and readiness |
| [Adapter design](ADAPTER_DESIGN.md) | Construction, strict validation, provenance, preserved lifecycle/integrity, clock/export semantics and scoped comparison |
| [Three learning experiments](LEARNING_EXPERIMENTS.md) | Inertia, steering and front/rear stiffness questions, qualified expectations, observables and acceptance |
| [Implementation/regression plan](IMPLEMENTATION_PLAN.md) | Smallest stages, future file scope and review/Verification gates |
| [Audit record](audit_record.json) | Pinned source identity, inspected paths, documentation allowlist and preservation evidence |

The constructor already supports the required synthetic parameterization. There is no missing
canonical equation to invent. The original demo lacks injection arguments, but the generic runner
already accepts a model, controller-protocol input provider, initial state and explicit rates.
Tooling seams need changes only after authorization: adapter dispatch/validation, actual-composition
provenance, artifact expectations, geometry/diagnostic export and comparison treatment semantics.

## Scientific decisions requiring review

These are proposed contracts, not questions blocking this documentation task:

1. **Synthetic counterfactuals and permitted cases.** Approve which mass/inertia/stiffness values or
   finite case sets may be explored, and their qualified operating envelope. Existing positivity
   checks are not physical validity ranges. Do not infer an inertia–mass–geometry law or stiffness
   calibration that the repository does not specify.
2. **Geometry coupling.** Keep `lf`, `lr`, wheelbase and CG height fixed in the minimum lab. Before
   exposing geometry, approve whether changing CG position preserves total wheelbase or changing
   axle distances derives wheelbase. Always retain canonical `wheelbase≈lf+lr` validation; no silent
   correction of an inconsistent triple.
3. **Initial state, input and validity contract.** Approve the full initial-state presets, independent
   velocity/yaw edits, steering/acceleration levels, tick-aligned event times, durations, and the
   interpretation/rejection policy for low-slip credibility, coordinate-domain and corridor limits.
   No automatic equilibrium reconstruction, constant-speed assumption or new numerical limit.
4. **Lab clock and export semantics.** Approve the existing runner profile with integer ticks,
   held inputs and informational terminal control, while preserving the legacy demo exactly. If
   byte-identical legacy stepping/export is required *inside the new lab as well*, separately review
   an injectable original-entry-point extraction; do not duplicate its loop or patch module globals.
5. **Controlled sensitivity classification.** Approve the explicit single-factor treatment contract
   for same-profile lab runs. This permits a declared vehicle/input change without relaxing V0.1
   compatibility rules or treating arbitrary different vehicles as a controlled comparison.

Alternative smooth combined-grip tires need their own later composition/domain authorization; they
are unnecessary for the three initial linear-tire experiments. No tire selector, new friction value,
NMPC/async adapter, hardware work or frozen Performance/Efficiency/Safety/VIS work is opened here.

## Current permitted changes and stop

Only new `docs/apex_workbench_v0_2_a/` design/audit files, an appended **proposed** ADR-171 in
`docs/DECISIONS.md`, and a prepended `docs/CODEX_HANDOFF.md` entry are permitted in this delivery.
No Workbench source/README/launcher, canonical code/tests/configuration, dependencies or historical
result is changed. Documentation checks are static; the earlier V0.1 855-pass/17-skip result is
historical context, not a newly executed result or evidence for arbitrary V0.2 parameters.

**Stop here.** Scientific parameter-contract review precedes a separately authorized implementation
stage. Proposed paths, tests and experiments in these documents grant no execution authority.
