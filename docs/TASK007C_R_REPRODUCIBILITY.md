# Task007C-R — reproducibility and timing causality

Status: implementation and validation before serialized experiments. Task007C C1–C4 remain gated.
No controller, plant, cost, constraint, terminal schedule, warm-start policy or solver option change.
The only runtime extension is an optional availability schedule injected into AsyncRunner.
Default timing dispatch is preserved when no diagnostic schedule is supplied.

## Physical timing semantics

For each nonstartup planner launch, tau_plan is logged `physical_delay`, checked against
completion_time minus release_time. It includes the physical delay imposed on the full prepared
result, not only IPOPT time. Startup remains gated at t=0 and consumes no replay entry.
A future-dated packet can still wait for its timestamp, or be rejected by the unchanged buffer;
therefore completion availability and actual accepted handoff are logged separately.

For each launched/applied codriver update, tau_codriver is logged `physical_latency`, checked
against application_time minus release time. Trace indices count launched jobs, not nominal
releases; skipped deadlines never consume an entry. Historical unapplied in-flight codriver
work, if present at termination, is not retained and is not fabricated. Exhaustion explicitly
stops the replay with `diagnostic_trace_exhausted`. Cross-replays compare their supported prefix.

Actual computation always executes and is timed. Diagnostic fixed/replay schedules alone set
physical availability; physics continues under active TVLQR and previously applied commands.
Fixed primary schedule: planner 35 ms, codriver 1 ms. Same startup and rolling-delay estimator.

## Historical evidence and preservation

Original Task007B and Task007C artifact manifests were verified before edits. All original files
are read-only inputs. `historical_audit.json` records file hashes, available channels and missing
exact historical NLP guesses/parameters. New equivalent snapshots are therefore captured.
E/F current and historical runtime hashes matched before instrumentation. The older A loader
variant is outside the primary E/F/C matrix and will be checked explicitly, not dismissed.

## Exact snapshot semantics

An opt-in solver decorator copies initial guess, parameter vector, previous solution and returned
solution without altering them. Capture overhead contributes to measured planner timing and is
reported. Disk serialization occurs only after simulation. Every optimizer call is retained,
allowing retrospective selection before onset, divergence, strong oscillation, slack and smooth
matched progress. Parameter vector layout: predicted application x0[6], predicted application previous command[2],
column-major preview
[11,N+1], terminal P[4,4]. The serialized CasADi f/g graph, all bounds and exact solver options
reconstruct the identical NLP; metadata retains vehicle/config/fixture/native/backend identity.
The actual command applied at planner release is a separate physical-history quantity, available
from the same-time states.csv row. Do not confuse it with the forecast command in the NLP.

## Experiment order

Validate opt-in timing and exact reconstruction first. R1 ten fixed repeats each E/F plus stable C;
R2 five original-history repeats each E/F plus stable C; R3 cross histories; R4 ten fresh measured
runs each E/F, all sequential fresh SINGLE workers. R5 snapshot selection and R6 twenty exact
solves per selected snapshot follow, with separate deterministic warm-start/state perturbations.
Single-event timing perturbations follow identification of an important divergence update.
No bulk numerical analysis or tests overlap R4 measured benchmarking.

## Descriptive outcome labels (declared before measured-repeat analysis)

Report each independently: sweeper heading TV >3 rad; whole-lap planned steering TV >20 rad;
sweeper rate-limit activity >1 s; predicted slack >1e-6 m; physical clearance <0.08 m;
front/rear utilization >=0.97; max abs(beta) >=0.35 rad. These are transparent descriptive
inspection thresholds, not validated safety limits or a combined bad-run score. Include event
frequency sensitivity with each threshold multiplied by 0.8 and 1.2. Geometry and traversal
length affect variation, so report all raw metrics and sector coverage alongside labels.
Additional separately reported activity labels: technical-section heading TV >6 rad and
whole-run steering-rate-limit fraction >20%, with the same threshold sensitivity reporting.
Solver iteration distributions use actual planner calls, not repeated telemetry-held values.

## Frozen cost and exact snapshot decoding

For all primary runs, stage Q is diag(4,4,1,200,200) in [vx,vy,r,epsi,ey]; input-reference
R is diag(25,1); input-increment W is diag(1,0.1). Slack linear/quadratic weights remain
1e4/1e5 and terminal multiplier remains 1. Terminal P is captured numerically in every parameter
vector; its unchanged source schedules 100 Hz DARE matrices at speeds 1/2/3 m/s, interpolated
with speed clamped to [1,3]. State/preview/bound values are decoded into a companion index;
raw capture files remain intact. IEEE double values round-trip through Python JSON; bound
infinities use Python JSON's explicit Infinity representation. The serialized graph is tied to
the captured CasADi version. Raw warm starts are decision-vector guesses, not dual warm starts;
the unchanged production solver does not supply dual initialization.

The vehicle's effective trajectory availability can be later than result readiness. Report
`tau_ready = completion_time - release_time` separately from
`tau_vehicle = accepted_handoff_time - release_time`; the latter is undefined for rejected or
unfinished packets. Replay injects recorded tau_ready and retains the original timestamp/buffer
policy, thereby reproducing both readiness and accepted handoff history. Feeding handoff delay
back into the completion estimator instead would change the experiment and is not done here.

## Numerical interpretation limits

First-divergence reports explicitly distinguish timing metadata at release, actual availability,
optimizer forecast state, initial guess, prior optimum, solver output and sampled active packet.
A changed application timestamp for an unchanged held command need not change the plant;
therefore report the first nontrivial command transition as well. Physical-state comparisons use
common exact sample timestamps rather than interpolating across different integration grids.
The first observed state split is limited by that common sampling resolution.

Availability events also partition the frozen RK4 plant integration. This is part of the simulator
being reproduced. The study does not independently separate integration-discretization effects
from command-timing effects in every counterfactual, and must not label sensitivity as chaos.

## Randomness and ordering audit

The active NumPy plant, NMPC preparation/solver, preview, trajectory buffer and TVLQR path
contain no Python/NumPy RNG draws, noise, randomized initialization or shuffled execution.
`results/task007cr/randomness_search.txt` retains the source search. The simulator base-class
comment describes a future stochastic seed API; it does not implement random dynamics.
Diagnostic workers explicitly seed Python and NumPy with 0 and use PYTHONHASHSEED=0.
Numerical arrays retain canonical state/control ordering. File lists are sorted, planner/codriver
releases are deterministic event sequences under imposed delays, and the OS wall clock is
only a source of variability in normal measured mode. Seeds do not make wall-clock timing
constant. Offline plotting/analysis order cannot affect the completed physical runs.

## Snapshot-selection and sensitivity scope

Nine retained requests cover E/F before visible oscillation, strong sector predictions, maximum
slack (including E's negligible-slack negative control), E's first optimizer-input divergence,
and matched-progress measured comparisons. E's smooth comparator minimizes measured sweeper
heading TV; F's minimizes technical-section heading TV. These are sector-specific descriptive
selections, not claims that the selected entire lap is safe or smooth. All measured runs remain
in the outcome tables and overlays.

The separate state probes use the absolute differences between the two E optimizer states
at their first detected input divergence. They keep the captured initial decision vector fixed
and change one physical input channel at a time. They test local NLP sensitivity; they are not
new closed-loop state-perturbation experiments. Failed/infeasible solves must remain labeled
and cannot establish alternative valid local solutions. The raw unscaled stationarity infinity
norm is computed from the saved objective/constraint derivatives and returned bound/constraint
multipliers; it is reported separately from IPOPT's own scaled diagnostics.
