# Task007E-4 — Primary acceptance of APEX Performance Synthetic v1

**Delivery stage: WORK_COMPLETE_PENDING_REVIEW — documentation/status only.**
**Primary decision: ACCEPTED on 2026-10-17, Recommendation B.**

Primary APEX has accepted Architecture A as **APEX Performance Synthetic v1**, a bounded
scientific research baseline with documented nonblocking synthetic limitations. This task records
the granted decision; it does not reconsider it or authorize hardware, production changes,
Efficiency, Safety implementation or further experiments.

The authoritative subsequent decision is the separate
[acceptance record](task007e/e4/primary_acceptance.json), version
`apex-primary-acceptance/1.0.0`, with its
[closed decision schema](task007e/e4/primary_acceptance.schema.json).
The accepted scientific reference is frozen by exact Git/content identity. No controller or
runtime configuration was frozen in place, selected or rewritten by E4.

## Immutable identity and historical status

| Role | Exact identity |
|---|---|
| Formally verified profile/source | `e603672b209985f11ed26b6f44d3949ffd5675c5` |
| E3 verification delivery / E4 starting revision | `ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9` |
| Scientific VIS executable/worker | `8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae` |
| Frozen executable ancestor | `c6990572045e61ee443dc715de9e8c44396e5b41` |
| Later offline VIS report | `d55f203aac1a04be598ebce4c38be51a4883e0ba` |
| Original manifest schema | `apex-performance-profile/1.0.0` |

Manifest: `configs/performance/apex_performance_synthetic_v1.json`.
SHA256: `5299adca29d5c5bd383252cd2c299a392dd6872dc6bb72d1a4dd7ecfb8dd1ebf`.
The manifest at the reviewed revision, E3 delivery and current checkout has identical bytes.
Its historical `frozen=false`, `formal_verification_pending=true` and
`primary_acceptance_pending=true` flags remain unchanged because they describe the reviewed
proposal. The [E3 record at its exact delivery](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9/docs/task007e/e3/verification.json)
records formal verification; this E4 overlay records subsequent Primary acceptance.
Neither record silently edits the other. Earlier reports retain their historical status text.

The Primary-pending portion of historical E3 limitation L12 is now resolved. Its remaining
interface/deployment obligations, all technical limitations and HW01–HW07 remain applicable.
The manifest schema, runtime-loading behavior and production defaults are untouched. No derivative
profile or Git tag was created. The acceptance delivery is identified by its containing commit,
reported after push, without circular self-hashing.

## Accepted scientific scope

Architecture A retains original predictor A and variable-availability handoffs. The complete
[immutable profile](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/e603672b209985f11ed26b6f44d3949ffd5675c5/configs/performance/apex_performance_synthetic_v1.json)
binds N8, dt=0.1 s, H=0.8 s, four RK4 substeps, original Q/R/W/scales, lambda_s=0,
gamma2 Planning, full control sequence, terminal policy, IPOPT/warm starts, 100 Hz TVLQR,
plant/tires, physical validity rules, native SINGLE and exact source/dependency/fixture hashes.
The overlay references those values; it does not define an alternate configuration.

Retained evidence is specific to synthetic_grand_prix_v1 and its recorded conditions.
The VIS replay pattern, 5 ms imposed codriver delay, rolling initial state and two-crossing/80 s
protocol remain evaluation conditions, not promoted controller defaults. No arbitrary track,
latency, vehicle or platform claim follows. E3's **750 passed, zero failed/errors/skipped**
result is inherited from the exact reviewed implementation; it was not rerun in E4.

C70 remains an **experimental future Efficiency candidate**, not an accepted Performance
replacement. Its measured history is censored at 48.670 s with 30 fixed deadline misses,
eight terminal misses and no complete measured lap. The subsequent scientific export remains
incomplete. Primary acceptance of bounded Architecture A does not declare that package complete
or accept Workbench ingestion.

## Limitations retained by Recommendation B

The exact [E3 limitations and safeguard register](https://github.com/Maxrwan/MPC_Controller_v1_IronManStyle/blob/ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9/docs/task007e/e3/remaining_limitations.json)
and E1 domain/safeguard records are hash-bound in the acceptance record. In particular:

- Trajectory availability and recovery are not guaranteed; reserve warnings/critical labels
  provide no proactive reserve-triggered rescue.
- Fallback admission requires **1–3 m/s and vehicle-center corridor containment**. This is not
  a guaranteed nonlinear recovery region. Independent application-time fallback-domain eligibility
  and delayed asynchronous fallback-transition coverage remain incomplete.
- There is no emergency braking-to-standstill capability or independent hardware watchdog.
- There is no continuous swept-body/collision-safety guarantee. Recorded center clearance is
  not physical collision certification.
- Vehicle/tire parameters are synthetic and not physically identified. Hardware dimensions,
  uncertainty and state/actuator assumptions require separate development.
- The measured C70 final package and some runtime observations remain unavailable; its exporter
  was not repaired and no missing data were invented.
- There is no unseen-track generalization or embedded timing certification. Independent historical
  IPOPT/linear-solver build identity remains unavailable; locked dependencies do not establish
  portable binary/timing equivalence.

These are nonblocking within the accepted bounded synthetic research scope. The versioned
`apex-prehardware-gates/1.0.0` HW01–HW07 remain mandatory before physical deployment:
identification/uncertainty, recovery and safe stop, application-time validity, watchdog/fault
handling, swept-body/stopping-distance safety, target hardware timing/fault tests and missing
asynchronous fallback-transition tests. Acceptance does not implement or waive them.

## Reproducibility and archival obligations

The overlay contains commit-qualified GitHub links plus full revisions and SHA256 values for
the manifest, verification/recommendation/limitations, original source inventory, dependency
files, synthetic vehicle, all five Planning constituents and evidence index. Git objects and
current bytes were checked locally; recovery does not depend on future `main` contents.
Read-only recovery examples:

```sh
git show e603672b209985f11ed26b6f44d3949ffd5675c5:configs/performance/apex_performance_synthetic_v1.json | shasum -a 256
git show ecbbc5cdb6d182557dfdd0bca7caa215cc1355c9:docs/task007e/e3/verification.json
git cat-file -e 8dbd1c5fbc09781411fc762e04f9c2c5cf2d99ae^{commit}
```

The first command must yield the manifest hash above. Exact Git revisions preserve source and
committed compact evidence; they do not contain every raw archive. Complete scientific histories
and full verification logs remain in ignored local `results/`, with committed inventories.
Retaining those archives and establishing independently durable backup/retrieval remain archival
obligations. No external backup or full archive upload is claimed by E4. Historical negative
findings, incomplete exports and unexecuted cases remain intact.

## Lightweight verification and next boundary

[Validation](task007e/e4/validation.json) records strict JSON/schema checks, exact Git/reference
and content-hash comparisons, unchanged proposal flags, inherited suite identity/log checks,
source/dependency/fixture preservation, authored-document links/scope and `git diff --check`.
Only documentation/decision records changed. The 750-test suite remains applicable because
no executable, dependency, fixture or test change occurred. No simulation, solver experiment,
benchmark, numerical suite or export repair ran; no tests or assertions were altered.

[ADR-164](DECISIONS.md#adr-164--primary-accepts-apex-performance-synthetic-v1-with-limitations)
records the Primary decision. The [roadmap](PROJECT_ROADMAP.md) now identifies Synthetic v1 as
accepted, Efficiency specification as the next separately authorized planning step, shared
Safety as pending, and Workbench/VIS-2 as deferred. These entries authorize no implementation.
E4 stops for Engineering Review of this acceptance-record delivery.
