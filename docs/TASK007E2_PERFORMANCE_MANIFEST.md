# Task007E-2 — exact proposed synthetic Performance profile

**WORK_COMPLETE_PENDING_REVIEW**

**PROPOSED SYNTHETIC APEX PERFORMANCE PROFILE — AWAITING PRIMARY ACCEPTANCE**

The [manifest](../configs/performance/apex_performance_synthetic_v1.json), schema
`apex-performance-profile/1.0.0`, describes the tested Architecture A formulation. It is an
inert research record: nothing loads it into a controller, changes defaults or freezes a profile.
E-1's accepted audit permits preparation with explicit limitations, not a claim of safe recovery.
No simulation, solver call, numerical constructor, timing experiment or full regression ran in E-2.

## Configuration identity

| Layer | Exact proposed formulation |
|---|---|
| State/input | `[vx,vy,r,e_psi,s_abs,e_y]`; `[delta,a_cmd]`; SI. Dynamic `a_cmd=Fx/m`, not `dvx/dt`; the latter includes `r*vy`. |
| Coordinates | Body forward/left, world x/y, CCW radians; e_y left-positive; heading residuals wrapped to (-pi,pi]; s_abs unwrapped. NLP heading remains locally unwrapped. |
| Vehicle/tires | Hashed synthetic 2 kg vehicle, wheelbase 0.30 m, Iz=0.025 kg m², lf=lr=0.15 m, cg=0.04 m, axle stiffnesses 45 N/rad, mu=1. NumPy dynamic plant and independently transcribed CasADi prediction; smooth combined grip with normal-load proportional longitudinal allocation. |
| NMPC | N=8, dt=0.1 s, H=0.8 s, four RK4 substeps per interval. Full eight-stage two-input ZOH sequence; no separate shortened control horizon. 54 state, 16 control, 18 slack variables. |
| Cost | Error order `[vx,vy,r,e_psi,e_y]`; Q=diag(4,4,1,200,200), R=diag(25,1), W=diag(1,0.1). Lateral scale=2; dynamic/speed/control/rate/terminal and alpha_vy/alpha_r=1; lambda_s=0. Input increment penalty has no dt division; stage sum has no dt multiplier. |
| Terminal | 100 Hz lateral DARE P schedule at speeds 1/2/3 m/s, interpolated/clamped to that interval, plus speed-error weight 4. Lateral scale=2 does not rescale terminal P. No terminal set/equality. Stored design weights preserve floating evaluation of `1/DesignScales**2`. |
| Reference | Existing gamma2 package, 154.76345492731022 m synthetic_grand_prix_v1. Advisory feasibility loader; geometry and serialized speed remain unchanged. vy_ref=0, r_ref=v_ref*kappa_ref, delta_ff=atan(L*kappa_ref); absent a_ref channel resolves to zero. |
| Solver | CasADi3.8.1 IPOPT plugin; max_iter=100, tol=1e-7, acceptable_tol=1e-6, constr_viol_tol=1e-7, bound_relax_factor=0, honor_original_bounds=yes, warm_start_init_point=yes. All explicit options, including output/error settings, are in the manifest. No custom early/suboptimal termination or wall-time limit. |
| Warm start | Shift primal states, inputs and slacks; duplicate last columns and overwrite initial state. No supplied dual warm start. Failure clears the retained solution. |
| Constraints | vx 0.5–6 m/s; s_abs>=0; denominator>=0.01 at nodes/internal stages; axle load>=1e-6 N; hard longitudinal grip fraction<=1-1e-6; steering ±0.4 rad, a_cmd [-3,2] m/s²; steering increment ±0.1 rad per NMPC stage. |
| Slack | Two nonnegative, unbounded-above corridor slacks per node, including terminal; linear penalty 1e4 and quadratic 1e5. The 0.08 m margin is a soft NMPC corridor/reference margin, not independently enforced swept-body safety. Scientific slack gate 1e-6 m belongs to evaluation. |
| Acceptance | Backend success plus finite output and infeasibility<=1e-6; controller independently checks shape, constraints within 1e-6 and variable bounds within 1e-8. Successful nominal solve alone does not guarantee packet/gain preparation or handoff. |
| TVLQR | 100 Hz; lateral order `[e_y,e_psi,vy,r]`, nominal-trajectory Jacobians of two-substep symbolic RK4, backward Riccati recursion from final DARE. Longitudinal correction is proportional with kp=1, not PI. Steering slew 1 rad/s at request and elapsed-time application. |

Values are taken from [CX construction](../scripts/task007dcx/worker.py),
[VIS construction](../scripts/task007dvis/worker.py), retained A summaries and the hashed
implementation. The manifest includes all `MPCConfig`/`CostScales`/`TrackerConfig` values,
not just overrides. Vehicle width, length and YAML steering-rate parameter remain **unknown**;
the controller/tracker supply the explicit 1 rad/s rate. No physical parameters were invented.

## Architecture A policy versus evaluation conditions

The profile uses variable handoff and original predictor A: forecast to release plus the rolling
delay estimate (initial 17 ms, median of last ten observed completions, clipped to 0–300 ms).
The cap bounds the estimate, not solver duration. Prediction clones the active-trajectory tracker,
uses the existing RK4 map and ideal future feedback timing, omits the committed pending prefix,
and refuses to extend beyond available authority. No future actual duration or plant truth enters it.

Nominal release cadence is 100 ms. One pending solve prevents overlap; nominal busy misses are
recorded. Urgent demand requires two consecutive lateral >0.05 m or heading >0.10 rad samples;
it latches while busy, nominal release has priority, and A may release off-grid. It is not
reserve-triggered rescue. Early preparation waits for the nominal start; later preparation can
accept if valid, newer, continuous and with at least 50 ms reserve. The original timeline is
not shifted to actual readiness. Warning and critical reserve thresholds remain 0.20 and 0.05 s; exhaustion uses
the existing 1e-10 s numerical tolerance. Authority is accepted-packet authority, separate from
old commands physically pending across handoff. The manifest retains the exact event order.

The `evaluation_protocol` section records **conditions**, not controller properties:

- Controlled planner availability repeats 35/55/45/25 ms; measured mode uses observed complete
  preparation duration. Their differing prediction estimates and event partitions remain real.
- Both accepted VIS modes impose 5 ms codriver delay. No arbitrary latency robustness is claimed.
- The exact initial six-state vector, two requested seam crossings, 80 s cap, 2 s parity duration,
  disabled disturbances/failure injection and complete AsyncConfig records are retained.
- Startup is launch-gated with prepositioned control; its unmodelled prelaunch time is separate.
  The first seam crossing from s_abs=1 m is a partial traversal, not a complete lap.

## Source and dependency provenance

| Role | Revision |
|---|---|
| Manifest preparation base reviewed by Engineering | `835eefb0aafe2f982a0ba05847d4e731079ff52d` |
| Scientific VIS worker/in-worker export | `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae` |
| Frozen executable ancestor | `c6990572045e61ee443dc715de9e8c44396e5b41` |
| Later offline VIS report tools | `d55f203aac1a04be598ebce4c38be51a4883e0ba` |
| Earlier CX formal test revision | `935e98b7af6c2fda8458551f1fbcbddb3bf8932d` |

All **294** paths in the scientific source inventory match current file SHA256 values. The
frozen ancestor→worker comparison is empty in the inspected implementation scope. Worker→E-2
base adds two offline long-report tools in that scope; it changes no controller, solver, model,
tracker, predictor, scheduling, fixture or dependency file. Later report/test provenance remains
separately recorded in VIS-1L. E-2 adds a manifest and read-only validator, not a newly tested
scientific executable. The historical launcher's complete source-inventory guard must not be
bypassed or treated as renewed execution authorization after these additions.

`uv.lock` SHA256:
`8cf85868a456415a898643dbb226d146b0b90e5c98982136cf2abf2465fa16ec`.
`pyproject.toml` SHA256:
`c8ea69a3a486c9794b6cf88ac26566211c6f1bb7b7286d86dbaa36a191353d41`.
The lock preserves all package versions/platform resolutions and distribution hashes; no install
or dependency update occurred. Recorded Python3.12.14, macOS26.5.1 arm64, NumPy2.5.3,
SciPy1.18.1, CasADi3.8.1, pandas3.0.6, pytest9.1.1, psutil7.2.2 and threadpoolctl3.7.0 match.

The tested SINGLE process uses `environment(1)` then `configure_accelerate(1)` before numerical
imports. Both A runs record Accelerate mode=1/status=0 and sampled process counts [1]. Empty
threadpoolctl inventory does not measure continuously active BLAS threads. This is Mac host
evidence, not embedded timing certification. The independently recorded IPOPT plugin/linear-solver
build version is unavailable; no undocumented default or build identity is invented. Explicit
options and locked CasADi distribution are supplied instead.

| Fixture constituent | SHA256 |
|---|---|
| Synthetic vehicle YAML | `df1b853d21a1d3efaf858f7e58401151f2c5237793c40e16bb4189ed651f9cf3` |
| planning_manifest.json | `5e7bccf1a300fb6737fc6b6b6e0c9aa921c110b11ffc5762a73f57f830a8660c` |
| planning_reference.csv | `6206e18ce3cb105d58d0923564336e28c00ec44aee3fd8a06ff7a37bcf84e2df` |
| planning_validation.json | `279582d2dcf37fdf4008ddc7f926109ef3d730a0e64c188d7003755d08871fa7` |
| speed_polynomial.json | `f335e78fc6c735c952f49078077a573ee989dd2be71497e90451e34a79f2c7ea` |
| track_source.json | `5f4d1734d7fec7de56d346e8f90bf272a3de9c05ac42f76cd49004e7f9183e55` |

No arrays are duplicated. Hash references point to immutable existing artifacts. The manifest
has no self-hash: [validation](task007e/e2/manifest_validation.json) hashes it and its evidence
index/schema/validator; Git identifies the delivery. No containing-commit SHA is embedded in
itself, and that commit is not relabeled as a tested worker revision.

## Demonstrated operating point and preserved comparative limitations

| Recorded metric, own whole observed run | Controlled A | Measured A1 |
|---|---:|---:|
| Complete-lap time (s), crossing reconstruction | 31.171900 | 31.317756 |
| Physical coverage end (s) | 62.235 | 62.285 |
| Runtime releases / accepted handoffs | 622 / 621 | 620 / 620 |
| Minimum recorded center clearance (m) | 0.328796 | 0.329424 |
| Minimum sampled reserve (s) | 0.667000 | 0.565171 |
| Maximum predicted slack (m) | 9.092e-11 | 9.092e-11 |
| Applied steering total variation (rad) | 17.424009 | 17.760724 |
| Actual world-heading total variation (rad) | 45.662093 | 46.092791 |
| Boundary / solver / handoff rejection counts | 0 / 0 / 0 | 0 / 0 / 0 |
| Planner busy misses / codriver busy ticks | 0 / 0 | 2 / 0 |
| Causal release forecast matches | 622 / 622 | 620 / 620 |

Both retained acceptance records report no chronology/scientific gate issues. The final controlled
A preparation has unobserved physical completion; 621 accepted is not a lost recorded failure.
Measured A preparation mean/p95/max is 57.629/70.253/193.324 ms. One host history is not a worst-case
bound. [Evidence links](task007e/e2/evidence_links.json) preserve six-state tracking and physical/tire
metrics, exact timings, counts and original sources. Historical event-summary metrics and later
native/endpoint, left-held time-weighted metrics are separately labeled; they must not be mixed.
Own-reference tracking is not equivalent to racing performance. Comparisons of different coverage
must use the existing common-window tables, not this per-run descriptive table.

C70 remains **comparative evidence only**: controlled lap 31.172038 s (difference from A below
5 ms crossing reconstruction brackets); measured run censored at 48.670 s with 30 fixed misses,
eight terminal misses and no completed lap. Its later failed export remains incomplete, with
missing observations explicitly absent. Measured C70_2 and A_2 remain unexecuted. E0's endpoint
speed correction remains authoritative. No comparative C70 setting selects the proposed profile.
See [VIS-1L](TASK007D_VIS1L_RESULTS.md), [E0 closure](TASK007E0_VIS1_CLOSURE.md) and
[E1 fallback audit](TASK007E1_FALLBACK_DOMAIN_AUDIT.md). Full raw histories remain ignored local
evidence under `results/task007d/vis/vis1r_c699057/`; GitHub compact evidence is not a replacement.

## Safety and acceptance boundaries

Shared asynchronous fallback admission requires vx in [1,3] m/s and vehicle-center corridor
containment. It targets centerline/2 m/s; it neither guarantees recovery nor brakes to standstill.
No separate fallback eligibility check occurs at every delayed application, and no continuous
corridor/swept-body guarantee exists. Finite reserve can exhaust after timing/failure/rejection
sequences in A, although that was not observed in these A runs. Simulation termination is not
physical fail-safe actuation. The exact E-1 guard and model-check register are hash-bound.

The versioned `apex-prehardware-gates/1.0.0` list contains future requirements only: identified
models/uncertainty, recovery/safe-stop domain, application-time freshness and held-input validity,
pending-command ownership, watchdog/braking/communications faults, continuous swept-body clearance
and target-hardware fault/timing tests. No hardware functionality was added. Arbitrary tracks,
vehicles, latencies, unseen-track generalization, guaranteed recovery/deadlines/collision avoidance
and production deployment are expressly excluded.

## Validation, reuse and reproduction

The [profile schema](task007e/e2/performance_profile.schema.json) defines required top-level fields,
types and immutable proposal/status flags. `profile` holds controller/model policy;
`evaluation_protocol` holds recorded experimental conditions; `provenance` binds revisions and
hash references; `environment`, `verification`, `exclusions` and `hardware_gates` constrain claims.
Paths are repository-relative; JSON null means unavailable/not applicable, never invented zero.
The schema version is independent of profile designation and scientific acceptance.

The [read-only validator](../scripts/task007e2/validate_manifest.py) checks the exact JSON Schema
vocabulary used here (type/const/required/properties/additionalProperties; unknown keywords fail),
static Python AST construction/defaults, numerical literals, retained JSON values, dependency
metadata and SHA256 references. It is not a general schema engine, dynamics test or runtime loader.
No external schema dependency was installed. Ten altered-input checks reject changed horizon,
weights, order, freeze status, predictor selection, fallback claims, solver options, fixtures,
thread observations and evidence hashes. These are new manifest checks, **not pytest/regression
passes**. Ruff lint/format and scoped documentation/preservation checks passed. An initial lint
formatting issue was corrected only in the new validator; no scientific gate failed or assertion
was relaxed.

Reproduce only the offline manifest checks from repository root, with the recorded environment:

```sh
task_e2_check_dir=$(mktemp -d /tmp/apex-e2-check.XXXXXX)
.venv/bin/python scripts/task007e2/validate_manifest.py \
  --output "$task_e2_check_dir/manifest_validation.json"
.venv/bin/ruff check scripts/task007e2/validate_manifest.py
.venv/bin/ruff format --check scripts/task007e2/validate_manifest.py
git diff --check
```

Output creation is exclusive; preserve previous logs. No APEX/numerical module is imported.
The historical scientific construction is `geometry()`/`frozen_config()` from CX, the explicit
`make_mpc(..., warm_start=True, solver_options={"ipopt.warm_start_init_point":"yes"})` and
VIS `availability(case)`. Full source-bound scientific reproduction instructions remain in
[VIS-1L reproduction](TASK007D_VIS1L_REPRODUCTION.md); executing them requires new authorization
and their original source/prerequisite/resource guards. Do not bypass them to load this manifest.

**Inherited only:** CX 709-pass formal evidence covers unchanged components; VIS-1R has 414
applicable prerequisites and A parity 19/19 exact C3 groups plus 19/19 forecasts; VIS-1L has 41
unique final focused passes. These overlapping counts are not added. Old CX verification predates
VIS additions. No old scientific experiment or failed package was rerun, repaired or replaced.
The [E0 applicability matrix](task007e/e0/verification_applicability.json) retains exact prior
revisions/logs and unresolved coverage.

**E-3 recommendation:** ready for Engineering Review to authorize exact-revision formal
verification of the proposed manifest, required current mathematical/chronology/physical/analysis
regression and acceptance checks. Review fallback transition coverage and known exporter limitations
explicitly; do not reinterpret an expected-error test as successful export. Independent plugin-build
identity and hardware geometry remain unavailable, not silently repaired. No runtime ambiguity
requires parameter invention. Primary APEX acceptance and any freeze remain later decisions.
ADR-163 already records these separate gates; no new architectural decision is made here.
**Stop after E-2.**
