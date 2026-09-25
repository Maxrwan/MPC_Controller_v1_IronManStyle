# APEX architecture

> Task 006.1 update: racing-development composition now explicitly selects
> `SmoothCombinedGripTire` and normal-load proportional longitudinal allocation in both
> NumPy plant and CasADi prediction. The linear law and its legacy constructor defaults
> remain available for reference regression. Statements below about unlimited force or
> diagnostic-only mu describe that historical linear selection. See
> [GRIP_LIMITED_TIRE_SPEC.md](GRIP_LIMITED_TIRE_SPEC.md) for the current grip physics,
> domain reserve, diagnostics and limitations. No body/Frenet equations changed.


Status: Task 006 adds constrained tracking NMPC, an IPOPT adapter and latency-aware
simulation atop the unchanged Task 004 plant and Task 005 baseline. Racing objectives,
estimation, energy and tactical algorithms remain unimplemented.

```text
physical plant -> simulated sensors / estimator -> estimated vehicle state
      ^                                                   |
      |                                                   v
actuator commands <- controller <- references/constraints <- planning / strategy
```

## Subsystem boundaries

| Package | Responsibility |
|---|---|
| models/vehicle, models/tire | Physical plant and reusable prediction model components |
| models/battery | Future battery/motor power and energy state |
| models/opponent | Future opponent state and motion representations |
| coordinates | Global/body/track coordinate transformations |
| track | Closed-circuit geometry and later boundary queries |
| estimation | Sensor-to-state estimates, including future opponent estimation |
| identification | Parameter/model identification from trajectory data |
| planning/racing, planning/defensive | References and tactical objectives/constraints |
| control | Baseline, MPC, LMPC, and energy-aware control orchestration |
| optimization | Solver-neutral contract and future backend adapters |
| simulation | Action-driven stepping and orchestration, independent of controller |
| logging | Future telemetry, completed laps, energy and analysis data |
| utils | Small shared utilities when justified |

`DynamicsModel.step(state, control, dt)` permits separate plant and prediction
instances, parameters, and integration schemes. Neither model is embedded in MPC.
`Controller.compute_control(state, context)` consumes an estimated canonical state;
context is a minimal mapping pending concrete requirements. `Track.sample(s)` accepts
arbitrary geometric progress and returns wrapped `track_s`, while race state preserves
`s_abs`. Track geometry owns neither lap completion nor termination. `Solver.solve`
has opaque problem/result payloads until a concrete optimization specification exists.
Controllers must receive a solver rather than directly hardcode IPOPT calls.

Current simulation orchestration composes a physical plant, controller, track and logging
with perfect-state feedback. Sensors/estimation remain future work. Required vehicle and
controller configuration must pass their model-specific validation before a run.

## Future extensions

Opponent prediction supplies predicted occupancy/trajectories to tactical planning
and collision constraints. Energy management supplies energy estimates, constraints,
and objectives before defensive strategy is introduced. Identification learns models
from logged trajectories; LMPC adds completed-lap storage, local safe sets, learned
cost-to-go, and local affine time-varying prediction models. Their schemas remain TODO.
Logging and analysis must consume data without becoming dependencies of vehicle equations.

## RL compatibility

`Simulation.reset(initial_state)` returns an observation, and `step(action)` returns
`StepResult(observation, terminated, truncated, reward, info)`. Reward defaults to None
because no reward is specified. Future adapters may add seeding, spaces, and reset info.
Termination is a specified terminal condition; truncation is an external run limit.
Lap crossing is neither. No Gymnasium dependency or RL environment is implemented.
Classical feedback, MPC, LMPC, RL, and hybrid controllers can all provide actions.

## Implemented geometry layer (Task 002)

`track/centerline.py` owns periodic spline construction, numerical arc-length mapping,
and bounded closest-point projection. `track/closed_track.py` combines centerline and
independent explicit widths. `track/io.py` reads CSV; `track/progress.py` owns wrapping,
lap index and unwrapping. `coordinates/angles.py` owns angle wrapping and
`coordinates/frenet.py` owns immutable poses/projection results and signed transforms.
`track/synthetic.py` provides explicitly synthetic circle fixtures.

The Track protocol now exposes width queries and point projection in addition to
samples and length. TrackSample includes wrapped progress and widths. Geometry/coordinate
modules do not import vehicle dynamics, controllers, simulation or solver backends.
See TRACK_MODEL_SPEC.md for equations, tolerances, assumptions, and limitations.

## Implemented kinematic propagation (Task 003)

`models/vehicle/kinematic.py` consumes an injected Track and geometry-validated
VehicleParameters. Its step(state,control,dt) satisfies the unchanged DynamicsModel
protocol. Separate instances can be used as plant and prediction model. Only four
channels are integrated; canonical vy/r are reconstructed algebraically. Model-domain
exceptions live in models/errors.py. The existing full vehicle readiness gate is retained
alongside validate_for_kinematic. Model-specific readiness is the propagation entry gate.

`scripts/run_kinematic_demo.py` supplies predetermined time-only commands and logs CSV,
JSON summary and a headless plot. This is not a controller, estimator or generic simulator.
Neither the geometry layer nor controller interfaces depend on the concrete kinematic class.

## Dynamic propagation and component boundaries (Task 004)

DynamicBicycle independently integrates all six channels. It orchestrates an injected
AxleTireModel and AxleLoadModel, shared Frenet validity/kinematics, and a pure RK4 integrator.
Track receives wrapped queries only. derivative(state,control) is deterministic NumPy f(x,u).
The kinematic denominator check now calls the shared helper with its existing behavior,
threshold, default timestep and stop policy preserved. No controller imports are added.

The tire law supplies axle lateral forces; load transfer supplies actual/static axle loads;
the vehicle owns body balances. Geometry and numerical integration do not own force laws.
Input interpretation is explicitly model-dependent: dynamic a_cmd=Fx/m, kinematic a_cmd=dvx/dt.
Mu is diagnostic only and no component applies saturation. See DYNAMIC_BICYCLE_SPEC.md.

## Baseline control and simulation orchestration (Task 005)

A generic simulation/runner.py composes Controller and DynamicsModel protocols, runs integer control
and plant ticks, logs states and optional controller diagnostics, and monitors track bounds
and lap targets. Optional reset/diagnostic callbacks keep it independent of LQR.
Perfect state feedback is explicit; no estimator is implemented. simulation/metrics.py
analyzes fixed windows and complete lap times without changing the plant.

control/baseline separates nominal cornering references, lateral linear design/gain schedule,
longitudinal PI and command composition. The design model is not the nonlinear validation
plant. All Task 004 physics, canonical state conventions and track algorithms are unchanged.
No solver or MPC implementation was added. See LQR_BASELINE_SPEC.md.

## Tracking NMPC and computational clocks (Task 006)

Independent CasADi prediction and direct multiple shooting live in control/mpc; the IPOPT
adapter lives behind optimization/base.py. SolverResult adds statistics and NLPRequest
supplies numeric parameters/initial guesses. Physical plant code remains independent.

SimulationRunner preserves its Task005 path by default. Explicit latency configuration
selects generic event scheduling with held previous input, exact completion-time plant-step
splitting, fixed nominal releases and skipped-deadline accounting. Optional application and
prediction-log callbacks add no MPC type dependency. Full state-staleness and physical-time
metrics are available. Future estimation/LMPC/RL can use the same timing interface.
