# APEX Workbench V0.2 — Vehicle Dynamics Laboratory design and parameter contract

**V0.2_PARAMETER_CONTRACT_PENDING_SCIENTIFIC_ACCEPTANCE.** 28 October 2026.
V0.2-A2 finalizes proposed finite numerical cases under user-approved D1–D5. No implementation,
numerical/model import, test/collection, simulation, sweep or launcher execution occurred.

A2 design/source pin: `d975a1141ae94d836b31d0ed8457870fbe9c98b6`.
Original A1 audit baseline: `c26782da2a9b94187a070ed5d9f72106a093d27e`.
Accepted V0.1 implementation: `77d018b11bbbfc39ab81d98c9bef70e90ab82725`.
The baseline differs from that implementation only in documentation/evidence records. Design branch:
`codex/apex-workbench-v0-2-a-design`. The containing documentation commit is the delivery revision;
its exact SHA/URL is supplied after push. [audit_record.json](audit_record.json) is unchanged A1
historical evidence; its then-pending policies are superseded below, not newly executed A2 evidence.

## Recommendation

Add one **open-loop `dynamic_lab` adapter**, reusing canonical `VehicleParameters`, `DynamicBicycle`,
fixed-step integration through the existing `SimulationRunner`, canonical track/Frenet APIs and the
verified Workbench worker/lifecycle/storage pipeline. The lab uses prescribed inputs, not a new
feedback controller. It adds no physics equations, integrator, simulation engine or solver.

The first release proposes **five selectable finite cases**, sharing one seed and steering step:
baseline, increased Iz, increased steering amplitude, increased Cf and increased Cr. Four one-factor
comparisons reuse that baseline. D1/D3 approve independent synthetic parameter/state/input semantics;
they do not imply an arbitrary slider range or qualification of other combinations. Mass and further
initial-state cases are deferred from this minimum workload. Geometry, CG height, friction, canonical
guards, actuator limits, track and tire/load choice stay fixed. New numerical/filter proposals still
need Primary acceptance and later execution qualification.

The original `dynamic_demo` and `lqr_baseline` adapters remain unchanged, including exact V0.1 default
inputs, execution paths, exports and parity. The new lab has an explicitly versioned runner profile;
it is not advertised as byte-identical to the legacy demo. Its nominal and perturbed cases share
that profile. See the [clock/parity distinction](ADAPTER_DESIGN.md#execution-and-default-preservation).

## Deliverables

| Document | Purpose |
|---|---|
| [Proposed cases](PROPOSED_CASES.md) | Five full parameter snapshots, common state/schedule, origins and analytical immediate expectations |
| [Numerical contract](NUMERICAL_CONTRACT.md) | Integer-grid/export semantics, proposed three-grid criteria and bounded future workload |
| [Validity contract](VALIDITY_CONTRACT.md) | Separate configuration/execution/evidence/numerics/model/comparison decisions and proposed sampled filters |
| [Implementation contract](IMPLEMENTATION_CONTRACT.md) | Small versioned request, fixed composition, telemetry/provenance, integrity and independent future acceptance oracles |
| [Decision summary](DECISION_SUMMARY.md) | Only unresolved consequential numerical/scientific proposals and next gate |

The A1 documents remain the source audit and architectural rationale, with A2 supersession notes:

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

**D1–D5 are settled by the user's A2 instruction.** Do not reopen these policy decisions:

| Approved policy | Required meaning |
|---|---|
| D1 — Synthetic sensitivity | Independent mass, Iz, Cf and Cr counterfactuals; no measured-vehicle claim or invented coupling law |
| D2 — Geometry | lf, lr, wheelbase and CG height fixed; canonical consistency preserved |
| D3 — State/inputs | Independent initial vx/vy/r, prescribed constant/step delta/a_cmd, fixed track-relative pose; reject invalid combinations without clamping/equilibrium reconstruction |
| D4 — Numerics | Existing SimulationRunner, fixed RK4/integer ticks/held inputs, separately versioned lab profile; exact V0.1 original-entry-point parity preserved |
| D5 — Comparison | One declared changed parameter per otherwise identical pair; provenance/integrity/compatibility retained; multi-factor illustrative |

Only concrete case/seed/excitation values, numerical resolution/thresholds and sampled interpretation
filters await [Primary scientific acceptance](DECISION_SUMMARY.md). No trajectory or convergence
claim is supplied. A2 does not choose between the already approved runner and a legacy-loop refactor.

Alternative smooth combined-grip tires need their own later composition/domain authorization; they
are unnecessary for the three initial linear-tire experiments. No tire selector, new friction value,
NMPC/async adapter, hardware work or frozen Performance/Efficiency/Safety/VIS work is opened here.

## Current permitted changes and stop

Only the five A2 contract files, this design index/concise A1 supersession notes, appended ADR-172 in
`docs/DECISIONS.md` and a prepended `docs/CODEX_HANDOFF.md` entry change in A2. ADR-171 and the A1
audit record remain historical.
No Workbench source/README/launcher, canonical code/tests/configuration, dependencies or historical
result is changed. Documentation checks are static; the earlier V0.1 855-pass/17-skip result is
historical context, not a newly executed result or evidence for arbitrary V0.2 parameters.

**Stop: V0.2_PARAMETER_CONTRACT_PENDING_SCIENTIFIC_ACCEPTANCE.** Primary parameter-contract
acceptance precedes a separately authorized V0.2-B implementation stage. Proposed paths, tests and
experiments grant no execution authority.
