# CT-1L bounded implementation-assignment request

**WORK_COMPLETE_PENDING_REVIEW — L0 assignment preparation only.**
No implementation, numerical packages, executable tests, model/matrix functions, solvers or
experiments ran. All future modules, tests and fixtures below are **PROPOSED, NOT CREATED**.
All tests remain **UNEXECUTED**. Primary's current instruction accepts CT-1's methodology,
interpretation boundaries and candidate panel; historical accepted CT-1 files retain their
original bytes/status. This is a new implementation assignment, not an acceptance-status rewrite.

## Exact source and authority

Start: `b22e24c13f76ea2e265d54a423825f8b15ea7b37`, `research/control-theory-ct1`.
Performance E4 ancestor: `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Verified scientific source: `e603672b209985f11ed26b6f44d3949ffd5675c5`.
Manifest SHA256: `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
Repository remote: `Maxrwan/MPC_Controller_v1_IronManStyle`.
The isolated CT-1 checkout was clean at exactly the authorized starting SHA. Original Efficiency
has unrelated in-progress source/untracked work and is preserved, not used as scientific source.
Safety, Performance/main and the annotated Performance tag are outside the writable assignment.
No SID or other-research source is imported. Every future worker checks actual module origins
against this isolated CT-1 checkout before analysis, rather than trusting a shared working directory.

Accepted sources are the unchanged [methodology](../CT1_CONTROL_THEORY_METHODOLOGY.md),
[mathematical audit](../model_and_linearization_audit.md),
[candidate panel](../operating_point_selection.json), [test matrix](../test_matrix.json),
[criteria](../metrics_and_interpretation.json), [provenance](../preservation_and_provenance.json)
and [resource gates](../resource_and_review_gates.json). No CT-1N/R identities or plans change.

## Reviewable implementation scope

The [future allowlist](future_source_allowlist.json) declares every proposed module, public
signature, type, dependency, test and fixture path. New research code lives only in scripts/ct1;
future tests and literal fixtures live only in tests/ct1l. There are no permitted edits to
existing controller, optimizer, plant, tracker, simulation, accepted fixtures, dependencies or
pytest configuration. No implementation framework, new library or solver backend is needed.
The read-only source adapter calls accepted DynamicBicycle, SymbolicBicycle and TVLQR Jacobian
construction only after numerical authorization. It never calls make_mpc, constructs an NMPC
problem/solver, instantiates TrajectoryPlanner or runs AsyncRunner. A separate value-only NumPy
transcription is a cross-check, not a replacement plant or controller.

Imports are staged deliberately: contracts/inputs/CLI/supervisor remain standard-library-only;
worker verifies explicit L3 authorization and immutable sources, sets native SINGLE in a fresh
process, then imports numerical packages. Future pytest collection is numerical execution and
must occur only after that bootstrap. Root tests/conftest.py imports APEX eagerly; the exact
future test command must use --confcutdir=tests/ct1l and the reviewed CT-1 test-file selection.
No tests are collected or run during L0, L1 code creation or L2 static Engineering Review.

## Twelve-point qualification

[Qualification contract](point_qualification_contract.json) preserves all twelve accepted
candidate IDs and exact original candidate-object hashes, packet IDs, gain indices and raw rows.
Two distinct tuples are retained at each candidate: ACTUAL_HELD (actual x, physically held u)
and PACKET_NOMINAL (original packet x/u/gain/preview at that time). Latest actual application,
command-source packet, active authority, pending request and expiry are separate facts. Nominal
packet input is never assumed to be held physical input.

Qualification checks accepted diagnostics, true track curvature and arc-length derivative,
speed/load/square-root/grip/actuator/Frenet domains, local heading chart, C2 curvature-knot
sides and every original/perturbed RK4 stage. An admissible boundary is not automatically a
smooth open central-difference neighborhood. Return QUALIFIED, QUALIFIED_BRANCH_SPECIFIC,
UNAVAILABLE or INVALID per tuple/map with reasons; retain poorly conditioned candidates.
No point shift, regularization, threshold relaxation, replacement or reduced panel denominator.
Physical geometry uses the exact accepted periodic spline and numerical arc map; private
coefficient/arc access is proposed read-only and requires explicit review (D01). Ambiguous
inversion/knot stencils stay unavailable rather than receiving an invented derivative.

## Exact local analysis

[Derivative contract](linearization_and_derivative_contract.json) fixes the six maps:
continuous frozen curvature; continuous physical kappa(s); symbolic tracker RK4 at 10 ms/two
substeps; symbolic NMPC RK4 at 100 ms/four substeps; physical held-input RK4 at 10 ms/two 5 ms
steps; physical held-input RK4 at 100 ms/twenty 5 ms steps. Canonical state/input order and SI
units remain fixed. Analytical A/B retain acceleration-dependent load transfer, effective
stiffness and combined-grip capacity derivatives. Physical A additionally includes kappa_s in
the progress column. Tangent propagation follows every exact RK4 stage with input sensitivity;
it is not Euler or an LTI matrix exponential.

Compare analytical derivatives, accepted CasADi AD, independent value-only NumPy real finite
differences and RK4 tangent propagation only for identical tuples, curvature policies and maps.
The exact accepted scales, central steps and tolerances are copied from the hash-bound CT-1
criteria; none are loosened. All future matrices retain tuple identity, map, method, units,
validity, source hashes and branch/chart. A method/tuple mismatch is not a derivative failure.

[Linear-systems contract](controllability_stability_contract.json) specifies full 6x2,
lateral 4x1 [e_y,e_psi,vy,r], and scalar speed analyses with original/scaled A/B/C, all SVD
singular values, rank thresholds, condition numbers and state/input/time-scale sensitivities.
PBH includes continuous unstable/marginal and discrete outside/on-unit-circle modes, with
accepted ambiguity bands and residual/Schur handling. Poor numerical conditioning is distinct
from exact deficient controllability. Full rank implies no constrained nonlinear reachability.

## Original gains, defects and applicability

Original archived gains are the controller evidence. Recomputed terminal DARE and backward
Riccati values verify them under the accepted residual/symmetry/positivity/conditioning/gain
criteria; they never replace the archived values. Audit only the bound original suffix needed
for each point, capped at 80 original slots per candidate and 960 total before deduplication.
Original DARE/backward design support through packet expiry is labeled DESIGN_SUPPORT_ONLY;
it is not accepted authority after packet replacement. Products over actual observed authority
truncate at replacement/expiry/coverage. Conditional original design-grid products may be
reported separately inside the packet's original nominal/gain validity. Unsupported off-grid
actual-duration maps remain unavailable instead of being approximated with a 10 ms map (D02).

Compute ideal lateral Acl=Alat-Bdelta*K and full Ad-Bd*G with the original proportional speed
row and all coupling. Products multiply newest factors on the left; report scaled/raw norms,
transient peak/time and endpoint only for covered intervals. Stable frozen poles alone do not
prove stable varying products or full asynchronous stability. Progress is not an artificially
regulated error: the frozen-curvature ideal full map has a structural neutral progress-offset
direction, while physical kappa_s coupling must be retained.

Nominal defects d=F(xnom,unom)-xnom_next retain interpolation, preview/plant curvature and
reference-realizability effects with matching timestamps/maps and local heading chart. Report
forced affine response and packet discontinuities; do not attribute every error to feedback.
Box saturation, slew-active/tie branches, previous applied steering, pending/delayed commands,
skipped ticks, invalid/superseded authority and nominal/actual mismatch limit A-BK applicability.
The augmented hybrid/event-map analysis remains unavailable and is not hidden in this allowlist.

## Independent tests and evidence

[Independent oracle specification](independent_test_oracles.json) declares hand-derived literal
load/force slopes, analytic arc-curvature jets and one-sided knots, exact double-integrator/scalar
RK4 maps, literal C/SVD/rank/PBH cases, scalar radical DARE, noncommuting products, normalized
norms, affine defects and progress/coupling identities. They are reference declarations, not
executed results. Expectations must never be obtained by running the future implementation.
At L1 create tiny literal fixtures with separate derivation/review hashes; at L2 inspect oracle
independence; at separately authorized L3 evaluate the exact reviewed tests before panel analysis.
No analysis-generated result may become its own oracle or replace an unfavorable observation.

[Scientific output schema](scientific_evidence.schema.json) defines exact closed record shapes
for qualification, matrices/units, singular values/ranks/conditioning, complex eigenvalues,
residuals, original/recomputed gains, products/defects, coverage, resources and run manifests.
[Evidence controls](evidence_and_resource_gates.json) map each exact output filename to its schema
and require semantic shape/identity/interval checks in addition to JSON validation. Every invalid,
unavailable, failed, unexecuted or censored candidate remains in the twelve-point panel. Never
emit NaN/Infinity, invent a missing norm/pole, or relabel toy oracles as scientific evidence.

## Resources and independent stage gates

CT-1L retains provisional ceilings: twelve candidates, 960 gain slots before deduplication,
300 seconds total proposed host allocation, native SINGLE, one sequential isolated worker,
1 GiB proposed worker RSS ceiling, 1 GiB total new outputs and at least 2 GiB initially free.
All authorized tests, package initialization, qualification, calculations, monitoring and export
must fit the eventual reviewed allocation; these ceilings are not measured runtimes or
current execution permission. Existing measurement guards and competing workers must be
checked at L3, not removed. Sampled RSS monitoring cannot establish a hard memory cap.
Time/output truncation preserves completed prefixes, missing ranges, failed checks and raw logs.

L0 is this documentation delivery. **L1 code creation requires Secondary review plus explicit
Primary authorization.** L2 reviews the exact implementation diff, hashes and independent oracle
code. **L3 numerical execution requires a separate explicit Primary grant after L2**, with final
tests/budget/resource policy. L4 reviews all outcomes; L5 is Primary's bounded scientific
acceptance. No stage authorizes the next. CT-1N/R experiments, controller optimization, solver
migration, physical testing and frozen Performance changes remain excluded.

Before L1, review the proposed private geometry binding. Before L2/L3, resolve the design-support
versus authority reporting convention, conservative missing knot/off-grid coverage, exact
prerequisite test selection within 300 seconds, sampled-memory enforcement limitation, incomplete
pending-tail evidence and ambiguous PBH treatment. These decisions are enumerated as D01-D07;
the assignment does not manufacture the missing scientific or environment evidence.

## Current static verification and requested decision

[Validation](validation.json) records exact starting/source bindings, the immutable accepted CT-1
records, file/scope/schema/AST/link checks, protected Git identities and before/after preservation.
Only this new docs/ct1/ct1l package and a prepended docs/CODEX_HANDOFF.md entry are allowed now.
No future source/test/fixture path is created, imported, collected or executed. Original archives,
failed/censored observations and CT-1N/R plans remain untouched. No copied-drive restoration or
whole-archive content verification is claimed.

**Requested next decision:** Secondary Engineering Review of this exact documentation commit,
then explicit Primary authorization for L1 only, if accepted. Do not authorize or begin L3 by
inference. The current exit is WORK_COMPLETE_PENDING_REVIEW.
