This isolated tooling assignment separately authorizes V0.1. Earlier Workbench/VIS-2 deferrals
remain historical; VIS-2/new tracks, VIS exports, frozen Performance and Efficiency work are not reopened.

All vehicle/track values are **synthetic**, not measured or identified. Status describes this UI.

| Parameter / capability | Source | Unit | Allowed range | Execution adapter | Validation | Provenance | Status |
|---|---|---|---|---|---|---|---|
| Duration | Dynamic CLI; LQR run_case | s | 0.01–20 (UI resource safeguard) | Both | Finite; LQR integer 0.005 s multiple | Request source/effective + hashes | Ready |
| Integration timestep | Dynamic CLI --dt | s | 0.001–0.01 (UI numerical/resource safeguard, not validated accuracy) | Dynamic demo | Finite, bounded | Request + original summary | Ready |
| Initial/reference speed | LQR run_case speed; LQR_BASELINE_SPEC | m/s | 1–3 (design/reference domain) | LQR/PI | Finite, bounded; plant independently validates | Request + states/controls | Ready |
| Track | LQR make_track | — | Existing circle / oval only | LQR/PI | Enum | Source hashes + exported geometry | Ready |
| Initial lateral error | LQR run_case ey | m | ±0.1 (UI safeguard from disturbance examples) | LQR/PI | Finite, bounded | Request + first state | Ready |
| Initial heading error | LQR run_case epsi | rad | ±0.05 (UI safeguard from disturbance examples) | LQR/PI | Finite, bounded | Request + first state | Ready |
| Controller | Existing experiment composition | — | Open loop or scheduled LQR/PI, chosen by experiment | Both | Adapter allowlist | Entry point/model/controller identity | Ready |
| Vehicle mass/inertia/axles/stiffness | Synthetic YAML; VehicleParameters | SI | Read-only fixture; constructor contracts exist | Neither original runner exposes overrides | Would require a new composition/parity adapter | YAML copied into request; hashes retained | Requires a minimal adapter |
| Initial speed / input schedule in dynamic demo | Fixed seed and command() | m/s, rad, m/s² | Read-only original values | Dynamic demo | Original model validity | Source hashes + CSV | Requires a minimal adapter |
| Tire law | Current demos: LinearAxleTire | — | Unsaturated linear only | Both | Original model checks; mu diagnostic only | Request identity | Requires a minimal adapter for other existing laws |
| LQR weights/gains/PI constants | Baseline constructors and Task005 spec | Mixed SI scales | Read-only existing defaults | LQR/PI | No tuning advertised | Source hashes | Requires later scientific authorization for a tuning study |
| Rates/timing | Original Task005 runner | Hz, s | Plant 200 / control 100; ideal zero modeled delay | LQR/PI | Existing scheduler | Request + original summary | Ready (fixed) |
| NMPC / async / latency modes | run_mpc_baseline.py; run_async_planner_tracker.py | s, steps | Existing CLI has zero/injected/measured, tire choices and fixed configs | Deferred | Needs prerequisite gates, timing isolation, bounded solver acceptance and parity | Existing CSV/JSON formats | Requires a minimal adapter and applicable execution authorization |
| Accepted Performance / Efficiency / VIS-2 campaigns | Frozen profiles and staged specifications | — | No editing/execution through V0.1 | None | Review boundaries retained | Historical evidence unchanged | Requires later scientific authorization |
| Measured vehicle parameters, suspension, SI, opponents | Future specifications | SI | No invented values/physics | None | Unimplemented | Explicitly unavailable | Unsupported |

Existing result formats: the dynamic demo emits states.csv and summary.json; LQR emits states.csv,
controls.csv and summary.json. NMPC/async additionally emit solver events/predictions/timing, but
those are not exposed by these adapters. No fake solver, constraint or timing series is generated.

R1–R6 corrections add no editable parameters or experiments. Runs now use worker-owned execution
leases, atomic publication, separate execution/evidence outcomes, verified selected artifacts and
controlled/illustrative/invalid comparison eligibility. Historical records and the original failed
review are preserved. See [CORRECTIONS.md](CORRECTIONS.md); a new Engineering Review is required.
