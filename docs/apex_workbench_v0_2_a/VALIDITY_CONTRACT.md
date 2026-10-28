# V0.2-A2 — Proposed validity and interpretation contract

**Design, not qualification.** Approved D1–D5 do not supply a measured parameter envelope.
The finite [cases](PROPOSED_CASES.md), [numerical thresholds](NUMERICAL_CONTRACT.md) and new filters
below remain subject to Primary scientific acceptance. Keep these distinct axes in records and UI.

## Decision hierarchy

Evaluate in this order; retain all reasons and lower-level unknowns rather than collapse into PASS.

| Axis | Proposed labels | Meaning and consequence |
|---|---|---|
| Configuration | admissible / configuration-invalid | Accepted contract/case, strict schema, complete snapshot, canonical constructor/readiness, initial-state and schedule checks. Positivity alone is insufficient. Unsupported values/case versions, ill-typed/nonfinite inputs, altered fixed fields, inconsistent geometry or invalid initial/domain conditions reject before execution. No clamp/repair. |
| Execution | existing lifecycle and scientific outcome, plus runner stop reason/failure and horizon reached | Queued/running/finalizing/completed/failed/cancelled/interrupted/timed_out remain existing process states. Horizon reached and a completed receipt are execution evidence only. A handled runner failure must propagate to non-success even if Python returns normally. |
| Evidence | existing pending / valid / failed or quarantined state, with explicit reason | Verify required artifacts and all manifest entries on consumption. Missing/corrupt/unknown evidence prohibits scientific plots or comparison and makes numerical conclusions **unverifiable**; it does not prove the integrator wrong. A completed execution can have invalid retained evidence. |
| Numerics | not qualified / grid-qualified / inconclusive / invalid / unverifiable | Nonfinite state/required numeric diagnostics or model/integration failure invalidates the affected numerical result; failed refinement or inadequate coverage is inconclusive. No runs means not qualified. Evidence failure means unverifiable. Excitation is separately assessed per comparison. |
| Model interpretation | permanent limitations + within proposed sampled window / outside window / unknown | Always show synthetic parameters, unsaturated linear tire, provisional loads and ideal instantaneous steering. Passing filters does not remove these limitations or establish physical validity. Missing required observations makes window status unknown. |
| Comparison | incompatible/illustrative / controlled candidate / qualified synthetic comparison / invalid | Metadata invariants establish a candidate, never qualification by themselves. Only complete verified, numerically qualified, sufficiently excited, same-contract one-factor pairs within the reviewed sampled window may receive the final label. Failed/incomplete/corrupt/unknown-contract runs are invalid for qualification. Known multi-factor/cross-profile data remain illustrative, without causal ranking. |

Configuration validation occurs again against the effective composition in the worker. File integrity
is enforced before reading telemetry; invalid evidence must not be displayed as a merely amber
physical warning. Record software correctness and numerical comparison qualification separately.

## Existing hard mathematical guards

Reuse the [canonical dynamic/Frenet specification](../DYNAMIC_BICYCLE_SPEC.md#integration-and-validity)
and implementation unchanged:

- Finite six-state/two-input vectors, s_abs≥0; independent dynamic vy and r. Forward vx≥0.5 m/s and
  vx≤6 m/s with existing 1e-10 m/s roundoff allowance, without changing the state value.
- Finite configured commands: abs(delta)≤0.4 rad, −3≤a_cmd≤2 m/s². No steering-rate model is present.
- All actual/static axle normal loads finite and >1e-9 N; no wheel unloading/clamping.
- Frenet D=1−kappa*e_y>1e-3; canonical track query/curvature at evaluated RK4 stages and final state.
  Finite derivatives, forces and integrated states. Do not invent a low-speed fallback.

The existing guards operate at evaluated stages/final states, not at every continuous instant.
An actual coordinate-domain failure is a numerical/model failure with partial retention; it is not
a completed trajectory with a warning. Finite D just above its floor may still be poorly conditioned;
refinement and sampled-D extrema must be inspected. No new D floor is proposed in this contract.

## Proposed sampled teaching window

The following are **new interpretation/qualification filters**, not canonical physics changes or
experimentally validated safety bounds. Apply to every retained native state/diagnostic row, including
prefix/onset/terminal, on each qualification grid. The terminal held input is informational.

| Filter | Proposed criterion | Basis and limitation |
|---|---|---|
| Low slip | max(abs(alpha_f),abs(alpha_r))≤0.050 rad | New engineering teaching cutoff, chosen to keep angles small for the axle-linear law; no measured tire data or canonical numeric slip boundary supports this specific value. Primary may amend before execution. |
| Lateral utilization | Both abs(Fy)/(mu*Fz)≤1 | Uses the existing synthetic diagnostic unity reference. Above unity means demanded lateral force exceeds the stated synthetic mu*Fz; the linear law remains unsaturated and execution may complete. Below unity does not establish real grip or account for missing tire physics. |
| Sampled CG corridor | Zero `boundary_violation` rows; −right_width≤e_y≤left_width | Existing inclusive corridor definition, with fixed 0.9/0.6 m half-widths. Requiring zero violations for this teaching window is a proposed qualification rule. It is not a vehicle-footprint or continuous collision test. |
| Domain/coverage | All canonical evaluated-stage/final guards satisfied and full prescribed horizon retained | Initial D=1 and positive schedule loads are analytically established, but entire trajectories are unqualified. Native sampled diagnostics supplement, not replace, stage checks. |

Slip >0.050, utilization >1 or a sampled corridor excursion may be **mathematically executed but
physically limited/outside the proposed window**, provided the hard guards did not fail. Retain the
raw run and extrema/timestamps; prohibit the qualified comparison label. Do not clip forces, stop
physics at a fabricated boundary or truncate to a favorable subwindow. Missing diagnostic coverage
is unknown, never zero. A different approved window would require a versioned scientific amendment.

Even all filters passing means only that this synthetic run satisfies the reviewed **sampled**
interpretation rules. There is no physical validation, real-vehicle safe operating envelope,
hard real-time guarantee, actuator feasibility or new controller capability. For this linear/no-
allocator composition, combined-slip/allocation channels may be null; they are unavailable, not zero.

## Presentation and failure retention

Show a compact row such as **Execution: completed · Evidence: valid · Numerics: not qualified ·
Window: unknown · Comparison: controlled candidate** with the permanent synthetic/linear/ideal-input
badges. When qualified, use the literal **Qualified synthetic comparison**, followed by “sampled
model window; no physical validation.” Never display an unqualified generic green PASS.

For every nonqualification show the actual reason, last retained time, intended horizon and which
criterion failed or remains untested. Insufficient post-step yaw excitation is an inconclusive
comparison under [the proposed signal criterion](NUMERICAL_CONTRACT.md#excitation-and-repetition),
even when both runs individually execute correctly. No required trend is fabricated.

Keep original failed/partial/cancelled/interrupted records, immutable receipt and evidence status,
logs and written samples. A worker kill during an in-memory runner may leave only logs/metadata.
Export failure after integration can produce a failed worker result; integration-horizon evidence,
where retained, stays separate. Manifest failure after worker success keeps completed-execution/
evidence-failed semantics. No reconstruction, resealing old artifacts, automatic favorable rerun,
hidden state change, threshold tuning or promotion from stale UI status.
