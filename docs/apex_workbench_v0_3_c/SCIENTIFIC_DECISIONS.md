# V0.3-C Primary scientific decisions

**PENDING PRIMARY REVIEW — NO SCENARIO EXECUTION AUTHORIZED.** Design inspected at
`ccd19549a9b3e25d1a5bd2c037a27090eda8dccf`, 29 October 2026. The authoritative
[handoff](../CODEX_HANDOFF.md) records B Verification with user acceptance pending.
These decisions concern the [scenario proposals](RACING_SCENARIO_PROPOSALS.md), not routine
layout, catalog wording, replay controls or pairwise presentation. Those engineering choices
do not require scientific permission when existing semantics and source protections hold.

| Decision | Consequence / recommendation | Approval boundary |
|---|---|---|
| **S1 — minimal scientific expansion and interpretation** | Approve the proposed direction: existing 2 m/s oval LQR/PI as the immediate varying-curvature example; one original GP history for retained hairpin/direction-change/sector investigation; separately specified rolling acceleration/braking and turn-in **open-loop response** as the next new experiment family. Defer standalone new tracks, high-demand variants and additional presets. This distinguishes plant excitation from a closed-loop racing benchmark. | Direction approval permits preparation of an exact next contract. It does not qualify a preset, authorize new numerical runs, or turn successful nominal tracking into a robustness/stability claim. Existing supported workflows remain available under their existing scope. |
| **S2 — source-bound racing profile before any new execution adapter** | For the first future racing execution contract, recommend the historical conservative **G** composition in the proposals: original Task007A full GP reference, Candidate C N4/gamma1/progress0, smooth combined grip with explicit allocation, unchanged APEX→TVLQR and rolling launch. Bind the exact Candidate-C configuration dependency, source, fixtures, timing and evidence contract before implementation. Keep **P**, the separately accepted N8/gamma2 Performance Synthetic v1, as its exact immutable reference/evidence; using P instead is an explicit alternate profile decision. | No current Workbench NMPC/TVLQR adapter exists. G's historical scientific composition, P's acceptance and the Workbench's current source identity are distinct. Approve one exact profile and its provenance/qualification disposition before adapter WORK; do not merge profiles, migrate accepted source identity silently or transfer VDL Q. Any indispensable change to a frozen dependency requires the separate source-identity migration proposal described in V0.3-A. |
| **S3 — exact domain, excitation and qualification contract for the new response family** | Before authorizing that experiment, decide its Track asset and what “straight” means, literal initial state, rolling speed, steering/acceleration/braking segments and integer transition ticks, finite duration/stop rule, diagnostic coverage, componentwise refinement/oracle criteria and sampled model window. Retain the canonical dynamic floor and guards, synthetic parameters and explicit failure preservation. The production straight asset and these scenario-specific choices are currently unspecified; this design supplies no invented values or bounds. | Approve a concrete versioned protocol and its bounded execution budget separately. Existing actuator/domain checks are necessary but do not qualify the new coupled speed/curvature/load/grip trajectory. V0.2's five-case slip/utilization filters and tolerances are not universal acceptance limits. A new metric/window/deadband or causal comparison requires its mathematical meaning and criteria in that protocol before use. |

**Recommended Primary disposition:** approve S1's three-part design direction; approve G as
the profile to specify under S2 while retaining P separately; require a concrete S3 protocol
and separately authorized qualification before any new scientific execution. If Primary
prefers P or an exact-zero-curvature straight representation, return that amendment for contract preparation.
No launch-at-standstill, hybrid low-speed model, new controller behavior, tire/vehicle model,
physical parameter identification, physical telemetry or Safety authority is proposed.

Retained-GP inspection first still requires an explicit archive profile with known producer,
schema, clocks, units, source and original partial/failure semantics. That is bounded evidence
engineering under an approved contract; it must not silently reconstruct unavailable events,
interpolate new samples, recompute new sector scores, or claim admission by the initial
fixed-grid V0.2 replay profile. B final user acceptance, V0.3-C exact-revision Engineering
Review/Verification and scenario approval remain separate dispositions.
