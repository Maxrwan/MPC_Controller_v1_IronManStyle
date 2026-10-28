# V0.2-A2 — Consequential scientific decisions still pending

**V0.2_PARAMETER_CONTRACT_PENDING_SCIENTIFIC_ACCEPTANCE.** 28 October 2026.
Design/source revision inspected: `d975a1141ae94d836b31d0ed8457870fbe9c98b6` on
`codex/apex-workbench-v0-2-a-design`. D1–D5 are approved and are not reopened.
All new numbers below are proposals for Primary APEX review, not Codex-approved assumptions.

| Decision requiring acceptance or amendment | Concrete proposal | Remaining uncertainty |
|---|---|---|
| Finite cases, seed and excitation window | [Five cases](PROPOSED_CASES.md): nominal, Iz=0.030 kg m², steering=0.025 rad, Cf-only=54 or Cr-only=54 N/rad. Common [2,0,0,0,0,0] seed; zero a_cmd; steering 0→0.020/0.025 rad at 0.100 s; horizon 0.500 s. Fixed existing spline track/geometry. Mass excluded from minimum workload. | Synthetic counterfactuals only. Whole-path domain/low-slip containment and a useful rear-stiffness signal remain untested; existing fixture magnitudes do not qualify this combined experiment. No continuous slider range. |
| Numerical resolution and useful-signal criteria | [Nominal 5 ms input/plant grid](NUMERICAL_CONTRACT.md); refinements 2.5/1.25 ms; each channel nominal/finest difference≤1e-5 in its own SI unit, refinement contraction≤1/2 plus 1e-12 roundoff floor. Four peak yaw differences≥10×max(tolerance, each pair member's grid discrepancy). Analytical fixture tolerance 1e-12 per quantity SI unit. | New teaching-resolution criteria, not a proven global-error/physical-accuracy bound. Are these thresholds adequate for the intended comparisons? 15 grid trajectories + baseline repeat + direct-runner oracle=17 bounded future lab trajectories; no execution now. |
| Sampled interpretation filters and qualification eligibility | [Full-horizon, all-grid filters](VALIDITY_CONTRACT.md): both abs(slip)≤0.050 rad, synthetic lateral utilization≤1, zero sampled CG corridor violations, complete guard-valid coverage/evidence plus numerical/signal qualification. Preserve permanent synthetic/linear/instantaneous-input limitations. | The 0.050 rad cutoff is newly proposed and unmeasured; utilization/corridor filters do not prove real grip, continuous containment or vehicle-body clearance. Any failure remains visible and unqualified, with no favorable subwindow or retuning. |

Scalar algebra establishes initial admissibility and conditional immediate body-force/moment values,
including the initially zero rear-stiffness effect. It does not establish trajectory results,
convergence, timing performance or physical validation. No scientific/numerical module was imported;
no tests (including collection), simulations, sweeps or launcher execution were performed.

After Primary acceptance of this version or an explicitly amended contract, **a separately authorized
V0.2-B implementation can begin** using [IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md).
No canonical scientific implementation change is identified as necessary. Qualification execution
and formal Verification retain their explicit later gates. An inconclusive authorized qualification
returns its preserved evidence for review; it does not authorize adding cases or changing thresholds.

Permissible A2 changes: these five new contract documents; the existing V0.2 design index and concise
supersession notes in its four source-audit/design documents; appended ADR-172 and prepended repository
handoff. The A1 audit record remains historical and unchanged. Scientific/Workbench/launcher source,
tests, configurations, frozen profiles, dependencies and old results stay untouched. The containing
documentation commit is the delivery revision; its exact SHA/URL is reported after normal push.

**Stop: V0.2_PARAMETER_CONTRACT_PENDING_SCIENTIFIC_ACCEPTANCE.**
