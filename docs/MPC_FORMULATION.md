# Tracking NMPC formulation — Task 006 implemented

> Task 006.1 update: racing-development composition now explicitly selects
> `SmoothCombinedGripTire` and normal-load proportional longitudinal allocation in both
> NumPy plant and CasADi prediction. The linear law and its legacy constructor defaults
> remain available for reference regression. Statements below about unlimited force or
> diagnostic-only mu describe that historical linear selection. See
> [GRIP_LIMITED_TIRE_SPEC.md](GRIP_LIMITED_TIRE_SPEC.md) for the current grip physics,
> domain reserve, diagnostics and limitations. No body/Frenet equations changed.


Canonical state [vx,vy,r,e_psi,s_abs,e_y], input [delta,a_cmd]. Independent CasADi Task004
prediction; unchanged NumPy physical plant. Direct multiple shooting with N20,T.05s,
five10ms RK4 substeps per interval. Full equations and decisions: NMPC_BASELINE_SPEC.md.

Minimize sum of Q=diag(4,4,1,100,100) tracking error, R=diag(25,1) input deviation,
W=diag(1,.1) increments, plus linear/quadratic track slack penalties10000/100000 and
provisional scheduled lateral DARE terminal cost with speed quadratic. No s_abs cost,
progress reward, minimum-time objective or terminal equality. epsi_ref=ey_ref=0.

X0 is the sampled state. Shooting defects are equality constraints. Actuator boxes,
synthetic1rad/s steering increments, speed/denominator/load domains are hard. Track
bounds are soft through independently logged nonnegative left/right slacks.

208 variables,126 equalities,944 general inequalities at default settings; box bounds
additional. IPOPT is injected through the existing solver contract. Primal solutions shift
one stage; invalid/failing output is rejected, with eligibility-checked baseline fallback
at APPLICATION time. The controller never calls or mutates the plant.

Computational timing is part of closed-loop dynamics. The generic runner holds the actual
previous command during zero/measured/injected latency, advances the plant, then applies
results. Fixed nominal releases while busy are skipped, including exact completion ties.
No latency compensation is implemented. All future computational controllers must retain
latency tests and comparable physical-time metrics.

Grip selection adds40 longitudinal utilization inequalities and intersects acceleration
bounds with the exact reserved friction/load domain:984 inequalities,1110 total g.
Lateral force is bounded analytically through tanh rather than an extra nonsmooth norm
constraint. All objective weights and terminal/reference choices remain as Task006.


## Task006.2 parameterization

The reference above is retained. `MPCConfig.costs` now provides positive grouped multipliers
for lateral/heading,vy/r,speed,R,W and a nonnegative complete-terminal multiplier. Slack
penalties and all physics/domain constraints remain fixed. Horizon, period and RK4 count
are explicit experiment parameters, with variables=10N+8, equalities=6(N+1), and grip
inequalities=N(9+8*substeps)+4. A change in substeps changes internal-stage validity checks.
The stage cost is not multiplied by dt, and the existing100Hz terminal DARE matrix is not
recomputed from tuned stage weights. See NMPC_PARAMETER_STUDY.md for these limitations,
accuracy gates, measured tradeoffs and selected configurations. No new optimizer or
asynchronous/trajectory-tracking layer is introduced.
