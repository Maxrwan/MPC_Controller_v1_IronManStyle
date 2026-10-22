# APEX-CT-1 independent control-theoretic methodology

**WORK_COMPLETE_PENDING_REVIEW — read-only analysis and documentation only.**
**Every new numerical matrix, rank, eigenvalue, Riccati check, response and sensitivity evaluation:
NOT EXECUTED.** No numerical package initialization, solver construction, test collection/execution,
simulation or new parameter study occurred. Static extraction of archived scalar values is
not a new dynamical experiment. The accepted controller is not tuned, replaced or modified.

## Scientific identity and review package

Accepted E4: `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
Verified source: `e603672b209985f11ed26b6f44d3949ffd5675c5`.
Manifest SHA256: `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
Isolated branch: `research/control-theory-ct1`, created directly from E4.
Original Efficiency/Safety worktrees and Performance/main refs remain protected.

- [Exact equations, analytic derivatives, discrete maps and actual tracker audit](model_and_linearization_audit.md).
- [Twelve archived candidate anchors, selection contract and missing qualification](operating_point_selection.json).
- [Separate local, nonlinear and robustness designs with enumerated trial IDs](test_matrix.json).
- [Metrics, thresholds, censoring and interpretation](metrics_and_interpretation.json).
- [Resources, prerequisites and separate authorization requests](resource_and_review_gates.json).
- [Source/evidence hashes and preservation boundaries](preservation_and_provenance.json).
- [Static validation, schema and explicit unexecuted work](validation.json),
  [documentation schema](ct1_documentation.schema.json).

## Source-bound operating-point protocol

The deterministic archived-value selection rule was written before extraction and is embedded
verbatim in operating_point_selection.json. It uses only controlled_A, whose successful retained
stop gate is empty, and only its recorded complete lap. Samples in the first/last 0.3 s of that
lap are excluded. Sample times must match a recorded command computation and native state;
accepted trajectory authority, valid packet, unexpired reserve, available reference and no
recorded boundary violation are required. Three neighboring packet preview curvatures at
(t-0.1,t,t+0.1) define straight (all abs<=0.02 1/m), sustained corner (all same-sign abs>=0.08,
range<=0.01 1/m), and entry/exit (endpoint change abs>=0.03 1/m). High speed is vx>=5.5 m/s.

Category priority is entry/exit, corner, straight, high speed. Within each eligible list sorted
by time choose the nearest still-available index to fractions 1/6,1/2,5/6, ties earlier. Reject
candidates within 0.5 m unwrapped progress of any already selected point. Never relax thresholds
or change run after seeing a rank/eigenvalue. Missing slots remain missing. This yields twelve
archived anchors, not twelve newly certified linearization domains. Their complete source IDs,
rows, state, held/nominal/requested/applied inputs, gains, beta/utilization, authority and
available clearances are recorded. Exact physical curvature, axle loads and strict two-sided
stencil validity remain null pending separate CT-1L qualification. Preview curvature can jump
at packet replacement; an entry label here is a nominal-geometry screening label. CT-1L must
confirm physical geometry and classify packet-only changes; it must report any missing category,
not select a favorable replacement. Straight anchors span one straight, not three independent
tracks/cars/straight sectors. High-speed categories can overlap geometrically but selected
records are distinct. Measured_A_1 is retained supporting evidence, not a replacement pool.

The actual tracker gain is evaluated about packet nominal x,u, whereas the archived physical
anchor is actual x and held u, which can come from an older packet. CT-1L reports these distinct
operating tuples and their mismatch; do not attach K to a different nominal point silently.
Four nonlinear representatives are the middle-ranked anchor of each category, fixed by ID.
No exact accepted-load, physical-curvature or strict-interior value is fabricated from a missing
export. E3 validity is inherited evidence, not a fresh CT-1 derivative qualification.

## CT-1L: continuous/discrete local matrix methodology

At each of the twelve qualified anchors evaluate separate full 6x6/6x2 pairs for:
(1) continuous frozen-preview model, (2) continuous geometry-dependent plant,
(3) tracker 10 ms symbolic RK4 at nominal tuple, (4) NMPC 100 ms symbolic RK4,
and independently held-input NumPy 10/100 ms maps. Compare like maps/tuples/curvature
contracts; model differences are not automatically differentiation errors.
Within the same distinct anchor count, also evaluate the remaining original gain-grid nominal
samples through that packet's expiry for finite-horizon products (at most 80 per packet,
<=960 total samples before deduplication); this is not an unbounded trajectory campaign.
For current trimmed authority use its original gain indexing and actual sample durations.
If resource caps prevent this, retain the completed prefix and censor remaining products.

For each map analyze full pair, lateral pair selected in [e_y,e_psi,vy,r], and scalar speed pair.
Report omitted coupling blocks and full-loop feedback separately. Normalize perturbations by
Dx=diag(0.5,0.5,1,0.1,0.75,0.1) in canonical SI state units and Du=diag(0.2,1) in input units.
Lateral Dx=[0.1,0.1,0.5,1], Du=[0.2]. Speed scales=[0.5],[1]. These are diagnostic scales,
not new weights, admissible disturbances or physical uncertainty estimates. Set tau=1 s for
continuous dimensionless comparison: Abar=tau*Dx^-1*A*Dx, Bbar=tau*Dx^-1*B*Du.
For discrete pairs omit tau. Kbar=Du^-1*K*Dx. Also publish dimensional raw matrices and units.

Construct C=[B,AB,...,A^(n-1)B], n=6,4,1. Use SVD of normalized C (never C*C^T for rank),
record every singular value, sigma_min/sigma_max, numerical rank and condition number
(infinite when deficient). Threshold is max(1e-12, t_rel*sigma_max), with
 t_rel in [1e-12,1e-10,1e-8,1e-6], default 1e-10. Repeat with each one of the n+m
normalization scales individually multiplied by 0.1 then 10, keeping all others fixed.
Show changes of numerical rank/conditioning; do not infer physical controllability from
one floating-point tolerance. For continuous C the chosen tau matters; show tau=0.1,1,10 s
sensitivity as well. Powers at short dt can be ill-conditioned despite theoretical rank;
use a rank-revealing staircase/PBH cross-check before concluding a physical deficiency.

PBH/Hautus: compute singular spectra of [lambda*I-A,B] at every eigenvalue, using complex
arithmetic and the same declared rank tolerances. Continuous stabilizability requires full
row rank for Re(lambda)>=0; discrete requires it for abs(lambda)>=1. Include marginal modes.
Use uncertainty band 1e-8 around these boundaries and label unresolved cases indeterminate,
not stable. For repeated/ill-conditioned eigenvalues use Schur/staircase diagnostics and
residuals; eigenvector inversion is not a reliable uncontrollable-subspace test. Retain all
modes and identify the progress-offset direction separately. Exact rank conditions concern
unconstrained local linear pairs; they are not constrained nonlinear controllability proofs.

Independent finite differences must call a separately transcribed NumPy implementation of
the same frozen-curvature equations/map, then the actual plant separately. No CasADi function
may be hidden inside the independent check. Central differences use normalized step multipliers
[2e-5,1e-5,5e-6] times Dx/Du column scales. Scale outputs by Dx (and tau for f) before comparison.
For analytic J versus D_h require each entry's abs error<=1e-7+1e-4*max(abs(J),abs(D_h)); adjacent
step estimates must satisfy the same bound on at least the two smallest declared steps.
Log max absolute/relative errors, numerator errors, all columns/steps, and finite-precision
cancellation. No adaptive tolerance/step relaxation after results. At a boundary or a stencil
crossing a nondifferentiable knot/chart/clip branch report unavailable or an explicit one-sided
result; do not clamp the point to manufacture a central derivative. If tolerance fails, stop
the affected quantitative conclusion and preserve evidence. Complex-step is not a substitute
for real atan2/wrap/guarded branches. Separately compare physical kappa_s with within-segment
geometry differences using s steps [2e-5,1e-5,5e-6] m, abs tolerance 1e-5 1/m^2 plus relative
1e-3; this looser geometry inversion check is declared, not retroactively chosen.

## CT-1L: closed-loop and time-varying interpretation

Using original stored K_k, calculate Acl_lat,k=A_lat,k-B_delta,k*K_k. Report spectral radius,
complex eigenvalues, distance to the unit circle, singular values/norms in normalized coordinates,
and eigensolver residuals. Stable classification needs rho<1-1e-8; unstable rho>1+1e-8;
the boundary band is indeterminate. This applies only to each frozen, immediate, unsaturated
reduced map. For Phi(k,j)=Acl_(k-1)...Acl_j (Phi(j,j)=I), evaluate all original-grid subintervals
within the remaining packet, and report ||Phi||_2, maximum transient gain, time to peak, and
endpoint gain, in raw SI and scaled norms. Stream products to avoid unnecessary storage;
QR/SVD or rescaling must log factors and overflow/underflow rather than replacing a failure.
Report selected durations 0.01,0.05,0.1,0.2,0.4 s and remaining horizon only where covered.

A sequence of Schur-stable frozen matrices need not have decaying products. Growth over a
finite packet is transient evidence, not proof of asymptotic instability; apparent finite
contraction is not uniform exponential stability. A stronger time-varying result would require
verified bounds ||Phi(k,j)||<=C*rho^(k-j), C finite and rho<1 over the claimed domain/time range,
or a positive-definite uniformly bounded Lyapunov sequence with a certified decrease. Neither
is established by twelve points or a finite horizon. Do not apply Floquet theory unless a
periodic closed-loop sequence and repeated authority/timing actually exist.

Audit terminal DARE residual (relative Frobenius<=1e-8), symmetry (relative<=1e-10), normalized
P eigenvalues (>1e-12 required for asserted positive definiteness), H positivity (>1e-12),
condition number (flag >1e10), and recursion residuals (relative<=1e-8). Report normalized
residual denominator `max(1, norms of all equation terms summed)`; store unsymmetrized
recursion skew before symmetrization. Q/R positivity follows from scales, not an evaluated
P. For normalized Riccati audits use Pbar=Dx_lat^T*P*Dx_lat, Qbar=Dx_lat^T*Q*Dx_lat
and Rbar=Du_lat^T*R*Du_lat, with normalized A/B; do not mix raw P with scaled A/B. DARE stabilizability/detectability and finite computation remain separate prerequisites.
Recomputed gain disagreement threshold is abs<=1e-9+1e-7*abs(original K); flag/stop quantitative
reproduction if exceeded. Do not retune or use a recomputed gain to hide disagreement.

Quantify nominal defects d_k in normalized state units and forced response
`sum_i Phi(k,i+1)*d_i`, using symbolic and physical maps separately, plus track/reference
curvature discrepancies. State interpolation, imperfect pseudo-reference realizability,
remaining packet timing, handoff jumps, speed coupling and limits all qualify conclusions.
Compute full 6-state Acl with both actual feedback rows; also report the projected 5 regulated
errors with the progress coupling exposed, not simply deleted. Scalar P speed analysis is
conditional on frozen lateral channels; no baseline PI substitution.

Report each limit branch and the actual steering-memory/pending-control state. Active slew,
input clipping, delayed actuation, skipped ticks, packet replacement and validity rejection
invalidate direct application of the ideal A-BK result. A branch-specific augmented event map
would be a separately reviewed extension; CT-1L may mark it unavailable. No local unsaturated
claim is promoted to a theorem about accepted asynchronous hybrid operation.

## CT-1N: nonlinear disturbance plan

Four representatives x five one-channel increments x both signs x two modes = 80 proposed
trials exactly; there are no extra baseline, pilot, repeat or timing-sweep runs hidden in the
cap. Proposed increments: e_y=0.02 m, e_psi=0.02 rad, vy=0.10 m/s, r=0.10 rad/s,
vx=0.10 m/s. They are review candidates, not reviewed uncertainty bounds or authorization.
Apply the selected channel once to the archived actual state; other channels, physical clock,
held input, tracker memory and packet timeline are not reset. Inject before the next tracker
computation following the accepted coincident-event order. Reject an initially invalid
perturbation as an observation, not replace it with a smaller amplitude. s_abs is not perturbed.
The static scalar screen already shows straight_2 vx+0.10 would exceed 6 m/s
(archived vx=5.956184909815748 m/s); its two mode entries remain predeclared invalid initial
observations unless Primary reviews a new version before execution. They are not replaced
by another anchor or reduced amplitude. Consequently the 80 entries do not promise 80 valid responses.

**Mode A:** fixed original accepted packet and original gain sequence, no replanning or gain
regeneration; preserve nominal controls and acceptance-trimmed time. Horizon is the remaining
original packet validity, never extrapolated, up to 0.8 s. At expiry terminate the observation
and censor settling; do not count fallback as TVLQR recovery. Log original authority replacement
as a counterfactual difference from the recorded run. This harness does not currently exist.

**Mode B:** original Architecture A NMPC preparation, rolling delay estimator, acceptance,
urgent demand, TVLQR, limits and validity logic. Fixed maximum simulated observation 2 s;
preserve plant motion during preparation, held commands during codriver delays, stale state
and skipped ticks. Track accepted packet replacement; recovery after replacement is system
response, not evidence solely about the original local feedback. The existing runner's disturbance
hook simultaneously modifies only e_y/heading; it does not support five one-channel trials or
arbitrary mid-run checkpoint restoration. Separate harness implementation/review and tests are
prerequisites. Preserve original parameters/configuration, solver options and source hashes.

The four representatives receive predetermined timing blocks: straight_2 ZERO (planner and
codriver physical delay 0, measured compute costs still logged); corner_2 INJECTED_ACCEPTED
(planner cycle [35,55,45,25] ms, codriver 5 ms); entry_exit_2 INJECTED_MISS (planner cycle
[35,125,45,25] ms, codriver 15 ms); high_speed_2 MEASURED (measured preparation and codriver
validation time). Mode A ignores planner timing because no solve is performed, but uses that
block's codriver timing and records skips. This covers zero/injected/measured timing and a
fixed-grid miss condition without exceeding 80 trials. It is not a crossed design: geometry
and timing are confounded, so do not compare blocks as isolated latency effects or claim a
complete latency acceptance gate. No exact timing pass/fail assertion on measured costs.

There is no new unperturbed counterfactual trial in this cap. Report absolute tracking errors,
original pre-injection error and perturbation increments; archived run comparisons after the
first authority/timing divergence are descriptive only. Without paired unperturbed runs,
nominal defects and changing references prevent a causal incremental-disturbance rejection
claim. Additional baselines require a separately reconciled cap and Primary authorization.
Trial order is listed representative-major, channel [e_y,e_psi,vy,r,vx], sign [-,+], mode [A,B];
partial budget coverage remains explicit. Metrics/censoring are predeclared in the metric record.
No requirement of monotonic componentwise error decrease is imposed.

## CT-1R: bounded offline mismatch plan

Four representatives x [Cf,Cr,mu,Iz] x multipliers [0.9,1.1] = 32 proposed trials; Mode B,
2 s maximum each. One plant-only parameter varies per trial; all others remain nominal.
Controller prediction parameters, gain-generation assumptions, reference and geometry remain
the accepted nominal configuration. Original packet gains remain fixed for any active retained
packet; newly prepared packets use the original nominal gain builder and weights, never the
varied plant parameters. Freeze the nominal construction configuration, not one gain array
across all future packets. Distinct plant/controller parameter objects and hashes are required.
Use the original accepted injected planner [35,55,45,25] ms cycle/codriver 5 ms for all 32;
no added state disturbance and no gain/model retuning. This is sensitivity analysis, not online
identification or a new nominal-model validation. Proposed +/-10% is a bounded synthetic
scenario, not an identified physical confidence interval; Primary must review magnitudes.
The 32-trial total includes no nominal baseline, repeats or multi-parameter interaction.
Without matched unperturbed trials, interpret comparisons with retained nominal evidence
conditionally; no causal timing-equivalent sensitivity estimate is claimed.

Estimation delay, uncertainty and biased states are deferred: the exact accepted architecture
uses perfect state and has no versioned estimator/error injection model. Neither delaying
plant truth silently nor reusing planner latency as estimation delay is valid. A separate
versioned measurement contract, timestamps, channel correlation/noise seeds, queue/hold law,
checkpoint state and sample count/cap reconciliation must be reviewed first. Alternative
matched-model or gain-regeneration studies are separate modes, not mixed into these 32.
Parameter domains require finite positive Cf/Cr/mu/Iz; retained geometry/mass/loads, sqrt reserve,
actuator/speed/denominator/corridor gates apply unchanged. No clipping/regularizing an invalid
state or new fallback plant can be used to finish a trial. Preserve unstable/infeasible/censored
observations and unmatched future packet-acceptance outcomes.

## Claims and exit gates

Level 1: future local mathematical/numerical evidence under explicit charts, scaling,
conditioning, reference and actuator assumptions. Current work contains symbolic derivations
only; no evaluated rank, pole or stability finding is available.
Level 2: future empirical synthetic finite-horizon observations, with partial coverage,
non-realizable references, changing packets and censoring exposed.
Level 3: formal guarantees only with an actual proof and explicit hypotheses. No such proof is
supplied here. Levels 1/2 cannot establish global asymptotic stability, invariant nonlinear
reachable sets, guaranteed disturbance rejection, physical collision safety or hardware robustness.

[Resource and review gates](resource_and_review_gates.json) reserve <=1500 s aggregate future
host allocation, <=1 GiB worker RSS, <=1 GiB new outputs and >=2 GiB initially free. These are
ceilings, not measured runtimes or permission. Native SINGLE and isolated sequential workers
are mandatory. STOP for Secondary Engineering Review; Primary must authorize CT-1L, CT-1N
and CT-1R independently, after remaining prerequisites are resolved. No follow-on work is implied.

## Mathematical references

The original source code above defines the APEX model and control law. General derivation
references, not evidence that APEX satisfies their hypotheses:
[Boyd, discrete finite-horizon LQR](https://ee363.stanford.edu/archive/lectures/dlqr.pdf),
[Boyd, basic Lyapunov theory](https://ee363.stanford.edu/archive/lectures/lyap.pdf),
[Tedrake, local/trajectory LQR](https://underactuated.csail.mit.edu/lqr.html), and
[Yang, discrete controllability/PBH](https://hankyang.seas.harvard.edu/OptimalControlReinforcementLearning/model-based-plan-optimize.html).


## Reproducing the static identity audit

A reviewer can inspect the exact containing CT1 commit without importing APEX. Check the diff
against E4; its only paths must be docs/ct1 and a prepend-only docs/CODEX_HANDOFF.md. The
ct1_documentation.schema.json `$defs` entries are schemas named after each JSON record stem;
use an independent Draft 2020-12 validator, or implement the listed small vocabulary. Our
current checks used a standard-library recursive reader, not a numerical/test runtime.
The record roots and operating-point/trial structures are closed; nested free-form planning
objects are intentionally not a runtime experiment schema. validation.json records eight
negative document mutations rejected and the semantic checks applied in addition to schema.

For a portable content and diff check, set CT1_ROOT to the isolated checkout and
CT1_ARCHIVE_ROOT to the original root containing ignored results, then use standard-library
Python with `-I -S` (the two shell variables below are passed as explicit argv paths):

```sh
CT1_ROOT=/path/to/ct1-checkout
CT1_ARCHIVE_ROOT=/path/to/retained-original-checkout
python3 -I -S - "$CT1_ROOT" "$CT1_ARCHIVE_ROOT" <<'PY_STATIC'
from pathlib import Path
import hashlib, json, subprocess, sys
root, archives = map(Path, sys.argv[1:])
record = json.loads((root/'docs/ct1/preservation_and_provenance.json').read_text())
for group, location in [('source_files',root), ('evidence_files',archives)]:
    for item in record[group]:
        assert hashlib.sha256((location/item['path']).read_bytes()).hexdigest() == item['sha256']
base = record['accepted_E4_revision']
changed = subprocess.check_output(['git','-C',str(root),'diff','--name-only',base,'HEAD'],text=True).splitlines()
assert changed and all(p.startswith('docs/ct1/') or p=='docs/CODEX_HANDOFF.md' for p in changed)
old = subprocess.check_output(['git','-C',str(root),'show',base+':docs/CODEX_HANDOFF.md'])
assert (root/'docs/CODEX_HANDOFF.md').read_bytes().endswith(old)
subprocess.run(['git','-C',str(root),'diff','--check',base,'HEAD'],check=True)
print('STATIC source/evidence hashes and documentation diff passed; no mathematical result evaluated')
PY_STATIC
```

Whole-worktree preservation needs the before-inventory named in preservation_and_provenance.json,
or independent before/after Git-object comparison; a later clone cannot reconstruct local ignored
archive metadata retrospectively. GitHub contains compact evidence and inventories, not all raw
files. The copied two-drive archive has no path in this request and remains independently
unqualified. No coverage, restoration, durability or complete-archive rehash is inferred from
these static checks. Fresh numerical environment qualification remains deferred to each
separately authorized execution stage; the current static reader's Python version is not the
accepted numerical environment identity.
