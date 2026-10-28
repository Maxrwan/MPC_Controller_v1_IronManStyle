# V0.2-A2 — Proposed numerical contract

**Not executed; new numerical criteria require Primary review.** D4 already selects the canonical
[SimulationRunner/RunConfig](../../src/apex/simulation/runner.py) and
[RK4](../../src/apex/models/integration.py). No new integrator, adaptive step or legacy-loop rewrite.
Case values: [PROPOSED_CASES.md](PROPOSED_CASES.md).

## Clock, events and export

Proposed runner profile `apex-vdl-rk4-zoh-v1` has nominal h=dt_plant=dt_input=0.005 s,
duration=0.500 s; dt_input is passed as `dt_control` through the existing protocol. This is a
prescribed input provider, not a feedback controller. `latency=None`, `target_laps=None`,
`stop_on_boundary=False`. Construct model default_dt=h and also pass h explicitly through the runner.
The 5 ms value is an existing default, **not demonstrated convergence for these new cases**.

- Use integer plant ticks k=0…N, physical time k*h, N=duration/h. Input update period and event onset
  must be exact integer multiples at the contract level; preserve canonical RunConfig's numerical
  ratio check (absolute 1e-9, zero relative tolerance). No tolerance-based snapping of user events.
- Ordered segments begin at tick zero. At each nonterminal tick the provider selects the segment
  whose start tick is the last ≤k; its command is held for [k*h,(k+1)*h), including all RK4 stages.
  Do not switch the last RK4 stage to the next interval's input. The step starts at k=20 on the
  nominal grid; [0.095,0.100) s still uses zero steering and [0.100,0.105) uses the treatment.
- The provider may keep its own integer call counter, reset per run, and cross-check the runner's
  `time=k*h`/`dt` context. Do not accumulate floating time or copy the legacy demo's 1e-12 transition
  comparisons. Reject off-grid, unsorted, duplicate, negative and terminal event ticks.
- A successful run exports N+1 state rows at 0…N and N actual applied-control rows at 0…N−1.
  The initial state row precedes any integration and records the command for the next interval.
  At the onset row the state is continuous while its associated command is the new one.
- The terminal state is at exactly the nominal N*h representation. There is no terminal provider
  call or newly applied terminal command. Its retained last command and recomputed diagnostics
  are **informational**; no extra interval is simulated. Row counts describe successful runs only.
- A handled model/Frenet failure returns the last valid sample and failure reason; unexpected
  exceptions may propagate. Never fill a missing terminal row or reconstruct an unwritten path.

Keep V0.1 dynamic-demo/LQR original-entry-point byte parity unchanged. The lab's fixed-grid and
terminal semantics differ from the demo's final shortened step and terminal command re-evaluation;
they have no cross-profile byte-identity claim. The prior
[architecture distinction](ADAPTER_DESIGN.md#execution-and-default-preservation) remains applicable.

## Minimal future convergence qualification

**Only after separate execution authorization**, run the five finite cases serially on three grids.
Refinement is a numerical qualification exercise, not an extra physical treatment or UI timestep
slider. Keep the same physical onset/horizon, inputs, seed, parameters, track and environment.

| Qualification grid ID | h=dt_input [s] | Onset tick | Steps N | State rows | Control rows | Post-step intervals |
|---|---:|---:|---:|---:|---:|---:|
| nominal | 0.00500 | 20 | 100 | 101 | 100 | 80 |
| half | 0.00250 | 40 | 200 | 201 | 200 | 160 |
| quarter | 0.00125 | 80 | 400 | 401 | 400 | 320 |

The initial qualification is **15 trajectories, 3,500 plant steps, 7.5 simulated seconds aggregate**.
Reuse the nominal baseline output for all four pair comparisons. One additional nominal baseline
adapter repeat in a fresh worker and one independently assembled nominal baseline canonical-runner
reference provide repeatability and adapter parity: **17 short lab trajectories total, 3,700 plant
steps, 8.5 simulated seconds**, excluding separate existing regression tests. Preserve all attempts;
these are bounded planned counts, not execution or wall-time measurements. Unit-level canonical
derivative checks need no additional trajectories. No sweep, timing benchmark or automatic refinement.

### Proposed componentwise criteria

The following **new engineering thresholds** are proposed numerical teaching-resolution criteria,
not inherited accuracy bounds, measurement uncertainty or physical tolerances:

| Canonical channel j | Unit | T_j: nominal versus quarter-grid tolerance | R_j: refinement roundoff floor |
|---|---|---:|---:|
| vx, vy | m/s each | 1e-5 | 1e-12 |
| r | rad/s | 1e-5 | 1e-12 |
| e_psi | rad | 1e-5 | 1e-12 |
| s_abs, e_y | m each | 1e-5 | 1e-12 |

Compare at all shared nominal ticks, including onset and terminal, using stored rows by exact tick
index (no interpolation). Use the canonical wrapped angular difference for e_psi; do not wrap r or
s_abs. For each channel define:

    d0_j = max difference between nominal and half at shared ticks
    d1_j = max difference between half and quarter at the same shared ticks
    E_j  = max difference between nominal and quarter at those ticks

Propose E_j≤T_j and d1_j≤d0_j/2+R_j for every channel, with finite complete outputs on all grids and
the model-window requirements on every grid. A factor-two reduction is a conservative detectable
refinement requirement, below smooth RK4's ideal factor 16; R avoids imposing an order on roundoff.
Report all d0/d1/E and diagnostic extrema. Report a ratio only when both differences exceed R.
The quarter grid is a **numerical reference, not truth**; these checks do not prove a global error
bound, continuous-time domain compliance, or accurate model physics. Shared-tick comparisons alone
can miss intersample behavior; inspect slip/domain/corridor diagnostics at every retained native tick.

The existing [dynamic accuracy regression](../../tests/regression/test_dynamic_accuracy.py) compares
a different smooth held-input straight-track fixture with DOP853 (rtol=2e-13, atol=2e-14), expects
12–22 refinement ratios and finest endpoint error <1e-7. Those are inspected historical assertions,
**not results rerun here**, and not transferable acceptance thresholds for switched spline-track
cases. Existing stage/final validity checks still apply. An independent high-accuracy integration
reference or further grids are possible escalations only after review of inconclusive evidence and
separate authorization; do not add them automatically to make a case pass.

### Excitation and repetition

For each of four nominal baseline/treatment pairs, propose a resolvable signal criterion:

    max over shared ticks 0.100≤t≤0.500 of abs(r_treatment−r_baseline)
        ≥ 10 * max(T_r, E_baseline,r, E_treatment,r)

The factor 10 is a **new proposed separation margin**, not statistical confidence. With the proposed
T_r it requires at least 1e-4 rad/s in addition to qualified convergence. It establishes a visible
yaw-rate teaching signal; it does not require an unproved sign/peak/settling trend. Keep actual vy,
slip and forces to interpret it. A weak rear response is retained as insufficient excitation, not
fixed by changing the initial state, horizon or thresholds after viewing it.

Repeatability requires byte-identical scientific state/control/diagnostic CSVs under the same
source/profile/numerical environment, excluding separately recorded run IDs, wall times and process
metadata. Direct nominal-runner parity uses an independently specified literal schedule and canonical
construction; expected data must not come from the adapter's configuration/provider functions.
Any failure remains evidence for review, not permission for favorable reruns or auto-tuning.
