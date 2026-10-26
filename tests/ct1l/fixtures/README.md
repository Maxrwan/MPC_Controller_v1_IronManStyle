# CT-1L L1 implementation handoff

Status: **WORK_COMPLETE_PENDING_REVIEW**. This is code creation and non-executing
static review only. Every numerical path and every test body is **UNEXECUTED**.
No L3 execution grant exists. No measured runtime, controller result, new numerical
qualification, physical stability or safety claim is made.

The exact reviewed assignment is `3898704102e7570bcaff9b1654b7b345db1f9b6f` on
`research/control-theory-ct1`. `source_bindings.json` contains the approved public
signatures, actual acyclic internal import graph, immutable input hashes,
independent oracle mapping, and hashes of the 34 source/test/literal files.
Its own hash and this evolving handoff are deliberately excluded to avoid a
self-referential digest. The implementation SHA is the Git commit containing this file.

## Implementation and dependency boundaries

Contracts and immutable inputs use the standard library. Source adapters construct
owned accepted vehicle, symbolic and tracker objects only in a granted L3 worker.
Geometry copies the hash-bound private spline/arc representation. Analytical and
independent NumPy value transcriptions share contracts, not derivative code.
RK4 tangents and fixed finite differences have independent paths; both source
values and independent values are compared. Linear systems, Riccati and closed-loop
modules consume matched records. Evidence uses the reviewed closed JSON schema.
Guards supervise one sequential fresh worker with supported SINGLE controls before
numerical imports. CLI/worker imports alone perform no numerical initialization.
No optimizer, solver plugin, simulator, Safety, Efficiency or SID research code is
used. No dependencies or accepted files are changed.

All six map IDs, both actual-held/packet-nominal roles and the exact twelve
candidate IDs are retained. Frozen preview and physical curvature are explicit.
All full, lateral and speed matrices retain omitted coupling blocks. Original
packet gains stay primary; DARE/recursion gains are independent checks. Products
multiply chronologically on the left and retain incomplete prefixes. Dimensional,
nominal scaled and one-scale sensitivity cases are labeled. Forced affine defects
use matching full design Acl and a zero initial error at the suffix start.

## D01-D07 disposition

| Decision | Implementation / limitation |
|---|---|
| D01 | `geometry.py` reads source-hash-bound `_spline.c`, `_q`, `_arc`, `_parameter`; copied read-only coefficients and true-arc derivatives. Unsupported representation returns unavailable. |
| D02 | Original gain suffixes are `DESIGN_SUPPORT_ONLY`/`DESIGN_CONDITIONAL`; `OBSERVED_AUTHORITY` contains only complete original 10 ms intervals inside recorded authority and expiry after the candidate anchor. No off-grid approximation or post-replacement authority extension. |
| D03 | Exact knot sides remain separate; near-root branch uncertainty and unqualified map/stencil crossings return unavailable. Automatic qualification does not invent a one-sided event map. L2 must assess conservative missing coverage. |
| D04 | Exact 13 test paths, initialization, analysis and export share the future 300 s supervisor allocation, with final 5 s reserved. Runtime/coverage feasibility is unmeasured, pending L3. |
| D05 | RSS/CPU/thread observations are sampled; proposed 1 GiB RSS/output and 2 GiB initial free-disk guards are code targets. No hard memory guarantee or backend qualification has been demonstrated. |
| D06 | Missing unapplied-command-tail evidence is explicit. Ideal A-BK remains conditional; open-loop derivative qualification remains separate. No checkpoint or augmented hybrid model. |
| D07 | PBH boundary/repeated/tolerance-sensitive cases remain INDETERMINATE; scoped complex Schur and rank-revealing reachable-subspace crosschecks are retained as events. No favorable threshold changes. |

## Independent oracle inventory

O00 canonical/schema/shape identities; O01 immutable candidate/held-input lineage;
O02 arc-length line/parabola and circle differential jet; O03 C2 knot/seam and
heading charts; O04 load slopes; O05 force/body derivatives including acceleration;
O06 double-integrator RK4; O07 scalar quartic RK4; O08 fixed stencil refusal;
O09 literal controllability; O10 rank/scale sensitivity; O11 stable/unstable/marginal
PBH; O12 scalar radical DARE; O13 finite Riccati and corrupted gains; O14
noncommuting left products; O15 normalized transient norms; O16 nominal defect
sign and forced convolution; O17 unregulated frozen progress; O18 actuator,
steering-memory, pending, expiry and supersession branches; O19 strict closed
schema, censored products and truncated JSONL; O20 fake-clock/RSS/disk/output,
foreign-owner guard and missing/expired/wrong-SHA grant negatives.

Literal expectations are hand-derived assignment expressions, not generated model
results. The circle fixture is a local third-order differential jet, not a global
cubic circle or replacement Performance track. Geometry inversion tolerances are
source metadata, not certified error bounds. Synthetic parameters are not measured
APEX physics. Unresolvable causal history cannot support a physical hybrid claim.

## Static review and remaining gates

Only stdlib source/JSON reads, hashes, AST/symbol-table parsing, structural public
API/import checks and Git diff/preservation checks are permitted at L1. AST checks
do not establish behavior. No pytest collection, numerical import, propagation,
Jacobian evaluation, SVD/eigensolve/PBH/Riccati calculation, resource probe or
experiment has run. Full static results and hashes are in `source_bindings.json`.

L2 Engineering Review of this exact revision is next. L3 requires explicit Primary
authorization, exact reviewed SHA/tests/budget/output grant, backend/native controls,
resource policy and all relevant independent tests. Numerical/scientific checks,
host resource feasibility and complete coverage remain **PENDING L3**. CT-1N,
CT-1R, controller optimization and further experiments remain unauthorized.

The newest exact-36 authorization leaves `docs/CODEX_HANDOFF.md` unchanged; this
approved support README is the scoped handoff. Original CT1 documents, accepted
Performance sources and historical evidence remain immutable.

## Exact changed-file list

- `scripts/ct1/__init__.py`
- `scripts/ct1/contracts.py`
- `scripts/ct1/inputs.py`
- `scripts/ct1/source_adapter.py`
- `scripts/ct1/geometry.py`
- `scripts/ct1/qualification.py`
- `scripts/ct1/analytic.py`
- `scripts/ct1/crosscheck_numpy.py`
- `scripts/ct1/rk4.py`
- `scripts/ct1/finite_difference.py`
- `scripts/ct1/linear_systems.py`
- `scripts/ct1/riccati.py`
- `scripts/ct1/closed_loop.py`
- `scripts/ct1/evidence.py`
- `scripts/ct1/guards.py`
- `scripts/ct1/worker.py`
- `scripts/ct1/cli.py`
- `tests/ct1l/conftest.py`
- `tests/ct1l/test_contracts.py`
- `tests/ct1l/test_inputs.py`
- `tests/ct1l/test_geometry.py`
- `tests/ct1l/test_analytic.py`
- `tests/ct1l/test_rk4.py`
- `tests/ct1l/test_derivative_parity.py`
- `tests/ct1l/test_qualification.py`
- `tests/ct1l/test_linear_systems.py`
- `tests/ct1l/test_riccati.py`
- `tests/ct1l/test_closed_loop.py`
- `tests/ct1l/test_applicability.py`
- `tests/ct1l/test_evidence.py`
- `tests/ct1l/test_guards.py`
- `tests/ct1l/fixtures/literal_oracles.json`
- `tests/ct1l/fixtures/geometry_cases.json`
- `tests/ct1l/fixtures/causal_packets.json`
- `tests/ct1l/fixtures/source_bindings.json`
- `tests/ct1l/fixtures/README.md`

## Recorded static result

PASS_STATIC_ONLY: 31 Python ASTs; 45 exact public functions and 8 exact frozen
constructor signatures; 21 retained oracle declarations; four fixture JSON files;
14 scientific record types; acyclic allowlisted imports; Ruff E9/F/I and whitespace
checks. No research or numerical import, pytest collection/test, numerical
evaluation or resource probe executed. Preservation counts and protected SHA
bindings are recorded in `source_bindings.json`. All numerical behavior remains
PENDING L3.

Concurrent activity: the independent Efficiency branch advanced from `c99b9dfdc981cb13ccd2e5ff53af98a3b568f70a` to `b53d92f8284e5f1c87c86b05916ea3019bba859f` with five clock-only authorization documents. All preexisting tracked file hashes remained unchanged. CT1 did not modify that branch or use those documents as source dependencies.
