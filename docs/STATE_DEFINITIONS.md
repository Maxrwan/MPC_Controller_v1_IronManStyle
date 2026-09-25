# Canonical state and control

Ordering is frozen and requires explicit authorization to change. Use `StateIndex`
and `ControlIndex` from `apex.state`; never scatter numeric indices through algorithms.
Validated vectors are independent NumPy float64 arrays of shape `(6,)` and `(2,)`.
Column-vector notation below is mathematical notation, not the Python storage shape.

x = [vx, vy, r, e_psi, s_abs, e_y]^T

| Index | Enum | Symbol | Meaning and frame | SI unit |
|---|---|---|---|---|
| 0 | VX | vx | Longitudinal body-frame velocity, forward positive | m/s |
| 1 | VY | vy | Lateral body-frame velocity, left positive | m/s |
| 2 | YAW_RATE | r | Yaw rate, counterclockwise positive | rad/s |
| 3 | E_PSI | e_psi | Heading error relative to track tangent, left positive | rad |
| 4 | S_ABS | s_abs | Continuous unwrapped track progress, nonnegative | m |
| 5 | E_Y | e_y | Displacement left of track centerline | m |

u = [delta, a_cmd]^T

| Index | Enum | Symbol | Meaning | SI unit |
|---|---|---|---|---|
| 0 | DELTA | delta | Front-wheel steering angle, left positive | rad |
| 1 | A_CMD | a_cmd | Commanded longitudinal acceleration, braking negative | m/s^2 |

No actuator saturation, heading wrapping, or dynamics is implemented by these helpers.
Future global pose, battery state, and opponent state belong in separate representations;
they must not silently reorder or extend the canonical six-state interface.

## Closed-circuit progress

`s_abs` is continuous and belongs to [0, infinity). For positive track length L,
geometry queries use `track_s = s_abs mod L` in [0, L). `track_s` is the Task 002 API
spelling of the previously documented `s_track`. Lap index follows `floor(s_abs / L)`
with exact represented multiples recognized explicitly at floating-point boundaries.
L is numerical arc length of the periodic spline, not raw waypoint polygon perimeter.
Crossing start/finish never resets s_abs or terminates simulation. Projection returns
wrapped progress separately and can recover continuous s_abs from a previous-progress
hint when successive changes are less than half a lap. Reverse driving and ambiguous
geometric branches remain outside the initial forward-racing assumptions.
Canonical state ordering and units are unchanged.

## Task 003 kinematic interpretation

vx and vy are body-frame velocities at the CG. For the kinematic model only, a_cmd is
exactly d(vx)/dt. Independent channels are [vx,e_psi,s_abs,e_y]; vy=vx*tan(beta) and
r=(vx/lr)*tan(beta) are algebraic reconstructions, not independent differential states.
Incoming finite vy/r are ignored by this model; output channels use final vx and applied
delta. Instantaneous steering may instantly change vy/r. Total CG speed is hypot(vx,vy),
not vx. Later dynamic models will propagate lateral/yaw channels through specified physics.
The ordering remains unchanged; post-step e_psi uses the canonical (-pi,pi] interval.

## Task 004 dynamic interpretation — explicit model distinction

DynamicBicycle independently propagates vx,vy,r together with e_psi,s_abs,e_y. It does not
reconstruct lateral/yaw channels algebraically. Its a_cmd requests Fx_total/m, giving
**dvx/dt=a_cmd+r*vy**, hence a_cmd=dvx/dt-r*vy. This body-axis inertial acceleration also
drives its quasi-static load-transfer approximation. Task 003's a_cmd=dvx/dt is unchanged.
The same vector shape does not imply identical longitudinal semantics in the two models;
future controllers/model comparisons must account for this documented distinction.
