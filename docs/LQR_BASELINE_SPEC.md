# Centerline LQR/PI baseline — Task 005

## Purpose and scope

A transparent, reproducible autonomous centerline-tracking baseline for future MPC.
The validation plant is the unchanged nonlinear Task 004 DynamicBicycle, including exact
atan2 slips, load-scaled linear tires, longitudinal body coupling and nonlinear Frenet rates.
The controller's linear model is separate. No optimizer, racing line, estimation, sensor
noise, actuator dynamics, opponent, energy model or tire saturation is introduced.
All configuration and validation data are synthetic, NOT identified APEX properties.

## Interfaces and modules

- control/baseline/references.py: independently testable nominal cornering references and
  ConstantSpeed; alternatively supply any callable f(track_s)->speed in [1,3] m/s.
- lqr.py: continuous matrices, exact ZOH discretization, Bryson scales and cached gains.
- speed.py: independent PI controller and conditional-integration anti-windup.
- controller.py: BaselineController.compute_control(state,context)->[delta,a_cmd].
  Constructor injects vehicle, track and speed provider. Optional context dt must match
  the constructor's design period; time is available to other controllers but unused here.
- simulation/runner.py: generic DynamicsModel/Controller loop, optional reset/diagnostic
  callbacks; no dependency on any baseline controller type.
- simulation/metrics.py: explicit metric windows, failures, boundaries and lap timing.

Perfect state feedback: estimated_state=true_state. The runner passes copies to avoid
controller mutation of the plant state. Neither canonical vector order nor geometry changes.
Baseline requires configured steering, acceleration and braking limits. Undefined physical
APEX configuration remains null; the synthetic vehicle supplies these limits.

## Cornering reference and feedforward derivation

Let v=current body vx, k=local curvature, m=mass, Iz=yaw inertia, L=lf+lr,
Cf/Cr=nominal static-load axle stiffness in N/rad. Approximate r_ref=v*k and
set lateral/yaw accelerations to zero at fixed v,k. Force and moment balance imply

    Ff + Fr = m*v*r_ref = m*v²*k
    lf*Ff - lr*Fr = 0
    Ff = m*v²*k*lr/L; Fr = m*v²*k*lf/L

Using the small-slip rear relation Fr=Cr*(-vy/v+lr*r/v):

    vy_ref = lr*v*k - m*v³*k*lf/(L*Cr)
    r_ref = v*k
    delta_ff = vy_ref/v + lf*k + Ff/Cf
             = L*k + (m*v²*k/L)*(lr/Cf-lf/Cr)
    delta_ff_kin = atan(L*k)  # logged comparison, not added to delta_ff

These references use actual current v, even if the gain scheduling variable is clamped.
No nonlinear plant solve or online Riccati solve is required. Nominal stiffness ignores
command-induced load transfer in the design; the plant retains it. Iz cancels in the
steady moment balance but is present in the transient design model. vy_ref can change
sign as speed increases; forcing its sign to match curvature would be incorrect.

## Lateral design model and explicit approximation

The requested order is x_lat=[e_y,e_psi,vy-vy_ref,r-r_ref]. Write z=vy-vy_ref,
w=r-r_ref and c=Cr*lr-Cf*lf. The homogeneous low-slip design equations are

    de_y = v*e_psi + z
    de_psi = w
    dz = -(Cf+Cr)/(m*v)*z + (c/(m*v)-v)*w + Cf/m*delta_fb
    dw = c/(Iz*v)*z - (Cf*lf²+Cr*lr²)/(Iz*v)*w + Cf*lf/Iz*delta_fb

    A(v) = [[0,v,1,0],
            [0,0,0,1],
            [0,0,-(Cf+Cr)/(m*v),c/(m*v)-v],
            [0,0,c/(Iz*v),-(Cf*lf²+Cr*lr²)/(Iz*v)]]
    B(v) = [0,0,Cf/m,Cf*lf/Iz]^T

**The homogeneous design is an approximation, not an exact linearization around a
curved-path six-state equilibrium.** With raw e_psi as requested, the physical small-angle
lateral rate is v*e_psi+z+vy_ref. The design neglects that affine vy_ref term, derivatives
of changing references, higher-order Frenet terms, load variation and longitudinal coupling.
Actual zero lateral drift requires e_psi≈-atan(vy/v), rather than zero. Consequently a
small steady lateral bias is expected; it is measured, not hidden by redefining e_psi,
adding an unrequested lateral integrator or shifting the centerline. The reference solve
is a steady body-force solution, not a complete exact nonlinear path-following equilibrium.

Use scipy.signal.cont2discrete with ZOH at dt_control=.01 s. Solve discrete DARE at
v=1,2,3 m/s once on construction:

    P = Ad' P Ad - Ad' P Bd (R+Bd' P Bd)^-1 Bd' P Ad + Q
    K = (R+Bd' P Bd)^-1 Bd' P Ad
    delta_fb = -K(v)*x_lat

Positive lateral/heading errors yield negative feedback steering in the project convention.
Tests check both signs independently. Nominal controllability and frozen-speed poles do
not prove nonlinear or arbitrary time-varying gain-scheduled stability.

## Weights and scheduling

Unchanged requested design scales: [0.10 m,0.10 rad,0.5 m/s,1 rad/s], steering feedback
scale .20 rad. Q=diag(100,100,4,1), R=[25]. They are synthetic design scales, not constraints.
No tuning or automatic optimization was used. Gains in the ordered four-state convention:

| v [m/s] | K_ey | K_epsi | K_vy | K_r |
|---|---:|---:|---:|---:|
| 1 | 1.790490931 | 1.903444760 | .058600607 | .052246783 |
| 2 | 1.670248095 | 2.010154895 | .089575502 | .093194075 |
| 3 | 1.604682376 | 2.228250631 | .105210359 | .116364797 |

Between adjacent nodes vi,vi+1, K=(1-t)*Ki+t*Ki+1 with t=(v-vi)/(vi+1-vi).
Outside [1,3], clamp ONLY the scheduling speed and log scheduling_clamped. No plant-state
clipping, automatic stop, or claim of validity outside that domain. Actual speed must be
positive for reference/design evaluation; the plant independently enforces its .5 m/s floor.
At endpoint target speeds even minute tracking excursions can set the clamp flag. Report
actual speed ranges and clamp magnitude as well as counts when interpreting this diagnostic.

## Longitudinal PI and bounds

Synthetic Kp=1 1/s, Ki=.5 1/s², unchanged initial proposal. At each controller update:

    e = v_ref-vx
    I_candidate = I + dt_control*e
    a_candidate = Kp*e + Ki*I_candidate
    block integration if (a_candidate>a_max and e>0)
                      or (a_candidate<-b_max and e<0)
    I = previous I if blocked, otherwise I_candidate
    a_unsaturated = Kp*e + Ki*I
    a_cmd = clip(a_unsaturated,-b_max,a_max)

Opposite-sign error may unwind an integral even while the output is saturated. Reset sets
I=0. A rejected candidate can prevent integration even when the recomputed output is just
inside the limit; both output saturation and integration_blocked are logged separately.
The dynamic plant uses dvx=a_cmd+r*vy; PI integral absorbs steady coupling, without adding
unrequested feedforward cancellation. Steering delta_raw=delta_ff+delta_fb is clipped to
configured ±.4 rad; acceleration to [-3,+2] m/s² in the synthetic fixture.

If a positive maximum_steering_rate is configured, limit changes from the previous command
to ±rate*dt. Otherwise steering rate is diagnostic only. Reset assumes previous command=0,
so the first reported rate is relative to zero, not a measured actuator position. Angle
saturation and rate limiting have separate flags. No physical steering actuator state exists.

## Runner, rates and logs

Plant 200 Hz (.005 s); controller 100 Hz (.01 s); integer tick scheduling and zero-order
hold for two plant steps. Defaults of existing models are untouched. Other positive rates
are supported when control period and duration are integer plant-step multiples.

RunConfig.duration is a required finite safety cap. target_laps optionally stops after
travelling N*track.length from initial s_abs (not merely crossing N seams). Target stop
occurs at the first completed plant step reaching that distance. Ordinary lap seams never
reset or stop a run. Lap times interpolate seam crossings; omit any initial partial lap.
Only forward crossings are lap events; reverse driving remains outside the baseline domain.

Plant rows include time, all six states, lap index, track_s, curvature, independent widths,
boundary_violation and applied delta/a_cmd. Input at a row acts on its following interval;
final-row input is informational. Controller rows include references, all four gains,
scheduling clamp, feedforward/feedback, raw/final commands, PI integral/error and flags.
Diagnostics callback keys are scalar and should be consistent for CSV serialization.

At each sample monitor -right_width<=e_y<=left_width (CG point, no footprint). By default
log violations and continue; stop_on_boundary explicitly enables early termination. Plant
ModelValidationError/FrenetGeometryError are caught, the last valid sample retained and
failure recorded with type/message; unexpected/controller errors propagate to the caller.
No reset or recovery hides a failure. Sampling cannot detect every between-step violation.

## Metrics, experiments and limitations

Primary nominal criteria at 2 m/s: after fixed t>=5 s, RMS ey<.05 m, peak |ey|<.15 m,
RMS speed error<.10 m/s; zero boundary and validity failures over the ENTIRE run. Also
report full-run errors, RMS heading, steering range/saturation percentage over controller
updates, lap times and travelled laps. Runs must explicitly reach their requested lap target;
the metrics' numeric criteria alone do not imply completion. No valid settling samples
produces null metrics, never a fabricated zero.

Recovery is first time after which |ey|<.02 m, |epsi|<.02 rad, |speed error|<.1 m/s for
all remaining samples, with at least one second remaining. This is an observed finite-run
band, not asymptotic convergence to zero. Four single-axis disturbances run for 12 s on the circle; the combined disturbance continues for two laps.

Validation reuses Task 002 fixtures: radius-5-m circle with 64 waypoints and widths .6/.9 m;
ellipse semiaxes 7/3 m, 72 waypoints and widths .3/.5 m. Two laps at each of 1/2/3 m/s on
both tracks. Initial vy/r use nominal local cornering references; epsi=ey=0 for nominal runs.
Additional oval reference 2+.5*sin(2*pi*track_s/L) exercises changing gains and the callable
interface; it is not optimized and need not meet constant-speed nominal criteria.

Known limitations: raw-heading steady bias; no hard predictive constraints; no lookahead;
static-stiffness design; no grip/saturation/slip validity guarantee; perfect state; no model
uncertainty; no real-time timing qualification. Linear stability is only frozen-speed.
Current synthetic evidence cannot establish physical vehicle safety/performance. See
CODEX_HANDOFF.md and results/lqr_baseline/suite_summary.json for actual measured outcomes.
