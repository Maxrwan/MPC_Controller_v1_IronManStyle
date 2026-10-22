# CT-1 exact model and tracker audit

**WORK_COMPLETE_PENDING_REVIEW. All proposed numerical evaluations: NOT EXECUTED.**
This is a source derivation, not an evaluated linearization or proof of stability.
All repository links resolve within accepted E4 `48adbdf64d492592d15e23c917aca71fa58aa8a5`.
[Provenance](preservation_and_provenance.json) records SHA256 identities; the E3 scientific
revision is `e603672b209985f11ed26b6f44d3949ffd5675c5`. No code or parameters change.

## Accepted identity and domain

Read the [accepted overlay](../task007e/e4/primary_acceptance.json) together with the
[unchanged historical manifest](../../configs/performance/apex_performance_synthetic_v1.json).
The manifest's proposal/pending flags are historical; E4 is the acceptance authority.
Use `smooth_combined_grip` with `normal_load_proportional`, Architecture A, legacy predictor,
N=8, dt=0.1 s, four symbolic RK4 substeps, lambda_s=0, gamma=2 fixture. Earlier Task006.3
N=4 examples and the separate baseline LQR/PI are not the accepted racing configuration.
[Worker construction](../../scripts/task007dcx/worker.py) and
[VIS worker](../../scripts/task007dvis/worker.py) bind the actual composition.

Canonical x=[v,w,r,theta,s,y]=[vx,vy,r,e_psi,s_abs,e_y]; u=[delta,a]=[delta,a_cmd].
Units are [m/s,m/s,rad/s,rad,m,m] and [rad,m/s^2]. y is left-positive; theta is body heading
minus centerline tangent, counterclockwise positive. s is continuous, nonnegative arc progress;
only geometry lookup uses `track_s = s modulo track.length`. `a=Fx_total/m`, not dv/dt.
The supplied 2 kg, Iz=0.025 kg m^2, lf=lr=0.15 m, h=0.04 m, Cf=Cr=45 N/rad, mu=1,
g=9.81 m/s^2 are synthetic fixture values, not identified APEX parameters.
Vehicle width, length and YAML steering rate remain unknown; the tracker supplies 1 rad/s.

Different validity layers must remain distinct:

- NumPy plant: v in [0.5,6] m/s with 1e-10 m/s roundoff tolerance; actual and static axle
  loads >1e-9 N; D>1e-3; original actuator bounds; finite state/control. Invalid values
  raise rather than being regularized. Every RK4 derivative state and final state is checked.
- NMPC constrained prediction domain: v in [0.5,6], D>=0.01, stage loads >=1e-6 N;
  abs(Fx_i)/(mu*Z_i)<=1-1e-6. delta in [-0.4,0.4], a in [-3,2]. Refer to
  [problem](../../src/apex/control/mpc/problem.py) and
  [application chronology](../../src/apex/simulation/asynchronous.py).
- The legacy actuation predictor checks v and D>=0.01 at its RK4 stages/final
  output, refreshing geometry only at each <=5 ms substep start; it holds that curvature
  inside the substep. It does not add an independent >=1e-6 N load check. Tracker request
  and nominal handoff validation call the NumPy plant diagnostics and its own thresholds;
  they must not be relabeled as the stricter NLP state/load constraints.
- Soft NLP corridor: y<=left_width-0.08+slack_left and -y<=right_width-0.08+slack_right.
  Slacks are nonnegative with no finite upper bound. Retained scientific slack gate 1e-6 m
  is distinct from NLP feasibility. Center corridor is not continuous swept-body safety.
- Two-sided derivatives require an open neighborhood inside all applicable domains;
  acceptance of a boundary state is insufficient. No clipping of perturbations or square roots.

## Exact continuous equations

Sources: [NumPy body model](../../src/apex/models/vehicle/dynamic_bicycle.py),
[loads](../../src/apex/models/vehicle/load_transfer.py),
[allocation](../../src/apex/models/vehicle/force_allocation.py),
[smooth tire](../../src/apex/models/tire/grip.py),
[Frenet rates](../../src/apex/models/frenet.py), and independent
[CasADi transcription](../../src/apex/control/mpc/symbolic_model.py).
With L=lf+lr and axle index i in {f,r}, the exact accepted equations are:

```text
Zf0 = m*g*lr/L                  Zr0 = m*g*lf/L
Zf  = Zf0 - m*a*h/L             Zr  = Zr0 + m*a*h/L
Xf  = m*a*Zf/(Zf+Zr)            Xr  = m*a*Zr/(Zf+Zr)
alpha_f = delta - atan2(w+lf*r, v)
alpha_r =       - atan2(w-lr*r, v)
Ci_eff = Ci*Zi/Zi0
Ti = sqrt((mu*Zi)^2-Xi^2)
zi = Ci_eff*alpha_i/Ti
Yi = Ti*tanh(zi)
D = 1-kappa*y
n = v*cos(theta)-w*sin(theta)
b = v*sin(theta)+w*cos(theta)
p = n/D
f(x,u) = [ a+r*w,
           (Yf+Yr)/m-r*v,
           (lf*Yf-lr*Yr)/Iz,
           r-kappa*p,
           p,
           b ]
```

There are no front-force cos(delta)/sin(delta) body rotations, drag, wheel-speed, suspension,
roll, energy or tire-relaxation states. The bounded tanh tire is an engineering synthetic
law, not an identified physical tire curve. Utilization is hypot(Xi,Yi)/(mu*Zi).
The exported effective stiffness is Ci_eff, not the finite-slip force tangent.

## Analytic local A and B, without evaluating them

All quantities below are evaluated at the same proposed (x,u); parameters are held fixed.
Use d for an arbitrary differential in x,u. Define qf=w+lf*r and qr=w-lr*r:

```text
dalpha_f = ddelta - (v*(dw+lf*dr)-qf*dv)/(v^2+qf^2)
dalpha_r =        - (v*(dw-lr*dr)-qr*dv)/(v^2+qr^2)
dZf = -m*h/L*da                    dZr = +m*h/L*da
dZi0 = 0                           d(Zf+Zr) = 0
dXi = m*Zi/(Zf+Zr)*da + m*a/(Zf+Zr)*dZi
dCi_eff = Ci/Zi0*dZi
dTi = (mu^2*Zi*dZi-Xi*dXi)/Ti
hi = 1-tanh(zi)^2
dYi = hi*(Ci_eff*dalpha_i+alpha_i*dCi_eff)
      + (tanh(zi)-zi*hi)*dTi
```

This retains acceleration-dependent load transfer and combined-grip capacity in B;
setting dYi/da=0 would silently change the model. Write Yi_v, Yi_w, Yi_r, Yi_delta, Yi_a
for the coefficients obtained above. Tire force has no direct theta,s,y dependence.
Define kappa_s=d(kappa)/ds for the physical plant, and kappa_s=0 for frozen exogenous
prediction curvature. The progress partials are:

```text
pv=cos(theta)/D; pw=-sin(theta)/D; pr=0
ptheta=-b/D; ps=n*y*kappa_s/D^2; py=n*kappa/D^2
```

In canonical order the complete continuous matrices are:

```text
A = [ 0,                    r,                  w,                  0,              0,                  0;
      (Yf_v+Yr_v)/m-r,      (Yf_w+Yr_w)/m,      (Yf_r+Yr_r)/m-v,   0,              0,                  0;
      (lf*Yf_v-lr*Yr_v)/Iz, (lf*Yf_w-lr*Yr_w)/Iz,(lf*Yf_r-lr*Yr_r)/Iz,0,           0,                  0;
      -kappa*pv,            -kappa*pw,          1,                 -kappa*ptheta, -kappa*ps-kappa_s*p,-kappa*py;
      pv,                   pw,                 0,                  ptheta,        ps,                 py;
      sin(theta),           cos(theta),         0,                  n,             0,                  0 ]

B = [ 0,                         1;
      (Yf_delta+Yr_delta)/m,     (Yf_a+Yr_a)/m;
      (lf*Yf_delta-lr*Yr_delta)/Iz,(lf*Yf_a-lr*Yr_a)/Iz;
      0,                         0;
      0,                         0;
      0,                         0 ]
```

Yr_delta is exactly zero for this independent rear tire, but is retained in the notation
for transparent force bookkeeping. These are derivatives of f, not of rejection guards.
Physical A equals frozen-curvature A plus `(df/dkappa)*kappa_s` in the s column:
`df/dkappa=[0,0,0,-p-kappa*n*y/D^2,n*y/D^2,0]^T`. B is unchanged at the same x,u,kappa.
Neither statement identifies the physical and prediction models along their different RK4 stages.

## Curvature differentiability and charts

[PeriodicCenterline](../../src/apex/track/centerline.py) fits a periodic cubic in raw chord
parameter q, numerically integrates arc length, and inverts s(q). Let the centerline be
c(q)=(X(q),Y(q)), V=|c'|, N=X'Y''-Y'X''. Within one smooth cubic segment:

```text
kappa = N/V^3
kappa_s = (X'*Y'''-Y'*X''')/V^4
          - 3*N*(X'*X''+Y'*Y'')/V^6
```

This uses d/ds=(1/V)d/dq; differentiating raw chord progress as if it were s is incorrect.
The periodic cubic is C2: curvature is continuous when V>0, but kappa_s can jump at knots,
including the periodic seam. There is no public kappa_s API. Future implementation must
independently differentiate the exact coefficients and arc map, and cross-check geometry-only
differences. At a knot use labeled left/right derivatives or report nondifferentiability;
do not average them into an asserted unique physical A. Map stencils can cross a knot only
with explicit piecewise/event treatment. kappa_ref of the offset racing line is a different
quantity from centerline kappa used by Frenet equations.

Plant step wraps theta to (-pi,pi] after integration; packet construction unwraps headings,
and tracker error wraps the residual. Derivatives use locally lifted theta and unwrapped s.
Never difference wrapped headings across +/-pi; apply differences to the lifted endpoint
chart. Never difference packet IDs, acceptance events or ZOH stage switches. Report those
as discrete events and one-sided/branch-specific behavior. A physical path crossing the lap
seam needs periodic geometry branch qualification, not an artificial s reset.

## Exact discrete maps and proposed derivatives

[Symbolic RK4](../../src/apex/control/mpc/symbolic_model.py) constructs, for each substep h:

```text
k1=f(z,u;kappa)
k2=f(z+h*k1/2,u;kappa)
k3=f(z+h*k2/2,u;kappa)
k4=f(z+h*k3,u;kappa)
R_h(z,u;kappa)=z+h*(k1+2*k2+2*k3+k4)/6
F_tracker = R_0.005 composed twice with identical held u,kappa (dt=0.01)
F_NMPC    = R_0.025 composed four times with identical held u,kappa (dt=0.1)
```

Tracker Jacobians are the full derivatives of F_tracker, then selected rows/columns, not
exp(A*dt), Euler I+dt*A, or the baseline's exact-ZOH linear design discretization.
NMPC has eight different shooting intervals; kappa can change between intervals, held within
each. The independent plant's nominal 10 ms held-input comparison is two 5 ms NumPy RK4 steps,
with kappa(s) recomputed at all derivative states and final validity checks and chart lifting.
Actual event-split physical integration may have shorter steps or an intervening application;
then use the recorded event composition, not the uniform tracker map. The 0.1 s held-input
NumPy comparison uses twenty 5 ms steps, separately labeled; it is not the NMPC map.

To reproduce an analytic discrete derivative independently, propagate tangent sensitivities
through each RK4 stage. For initial-state/input sensitivities Zx,Zu (initially I,0), a stage
f at state z has derivative `(f_x*Zx, f_x*Zu+f_u)`. Apply the same RK4 stage construction to
these sensitivities, including the intermediate stage-state derivatives, then compose all
substeps. Physical f_x includes kappa_s at that stage; frozen symbolic f_x does not.
Ad=dF/dx, Bd=dF/du for all maps above remain NOT EXECUTED.

## Actual finite-horizon feedback and sampling

[TVLQR.compute](../../src/apex/control/trajectory/tracker.py) samples untrimmed packet time
from timestamps[0] to horizon_end-1e-9 in 0.01 s increments. At each sample it uses linear
state interpolation, ZOH nominal controls, and ZOH stored preview curvature. If curvature
is absent only, it samples track geometry at nominal progress, but the symbolic derivative
still treats the resulting scalar as exogenous. Accepted packets retain curvatures.
Let E select [e_y,e_psi,vy,r], with insertion E^T, and bdelta select the steering column:
`A_lat=E*Ad*E^T`, `B_delta=E*Bd*bdelta`. Speed, progress and acceleration are frozen
scheduling quantities for this reduced design. The extracted system is not in general an
invariant subsystem of the full six-state perturbation dynamics; log omitted coupling blocks.

`DesignScales().weights()` supplies Q=diag(1/0.1^2,1/0.1^2,1/0.5^2,1/1^2), R=[1/0.2^2].
Importing these scales does not substitute baseline continuous_matrices or baseline PI.
For M tracker samples, P_M=DARE(A_lat,M-1,B_delta,M-1,Q,R), then backward:

```text
H_k = R+B_k^T*P_(k+1)*B_k
K_k = solve(H_k, B_k^T*P_(k+1)*A_k)
P_k = Q+A_k^T*P_(k+1)*A_k-A_k^T*P_(k+1)*B_k*K_k
P_k = (P_k+P_k^T)/2
```

The terminal DARE is the last frozen lateral map, not a terminal invariant set. The separate
NMPC terminal penalty uses baseline-design DARE P scheduled/clamped at speeds 1,2,3 m/s;
that cost does not replace TVLQR's packet-specific terminal DARE or prove NMPC stability.
Q is positive definite and R positive in the stated design scales; existence of a stabilizing
DARE solution still needs stabilizability/detectability and numerical checks at the actual
terminal map. Symmetrization alone proves no definiteness. Preparation catches ValueError
and LinAlgError and withholds the packet; it is not a full a posteriori Riccati certificate.
Original stored gains are primary evidence. Future recomputation must compare to them and
report mismatch, never overwrite or silently substitute gains.

[Packet.sample/trim](../../src/apex/control/trajectory/packet.py) use linear state
interpolation, ZOH controls and gains, 1e-10 s selection tolerance, no authority beyond expiry;
late acceptance trims without recomputing gains. Trimmed gain-time anchors can be off the
original 10 ms grid. Products must follow actual sample times and gains, not shift arrays
by assuming time starts at zero on each handoff.

For lateral error e_lat=[y-y*,wrap(theta-theta*),w-w*,r-r*]:
`delta_des=delta_nom-K*e_lat`. Longitudinal law: `a_des=a_nom-kp*(v-v_nom)`, kp=1 s^-1.
The command first box-clips both inputs, then clips steering to previous +/-1*0.01 rad.
The asynchronous runner resets tracker.previous to the held applied pair before computing;
a request remains pending through codriver latency and the old command holds. At actual
application it additionally clips steering to held_delta +/-1*(t_apply-t_last_apply).
A pending request retains its original packet provenance across handoff. Busy codriver ticks
are skipped and counted separately from busy planner misses. There is no full revalidation
of all tracker/fallback admission conditions at every delayed physical application.

## What the closed-loop matrices describe

Ideal unsaturated, immediate lateral feedback: `Acl_lat,k=A_lat,k-B_delta,k*K_k`.
For the full map use G rows in canonical order:

```text
G_delta = [0,K_vy,K_r,K_epsi,0,K_ey]
G_a     = [kp,0,0,0,0,0]
Acl_full,k = Ad_k-Bd_k*G_k
```

This exposes speed/lateral coupling. In continuous time the longitudinal perturbation obeys
`dot(ev)=-kp*ev+r_nom*ew+w_nom*er+defect_v` at first order; it is not an independent PI loop.
For the reduced scalar analysis use A_v=A[v,v]=0, B_a=B[v,a]=1 (continuous), and the actual
Ad[v,v],Bd[v,a] for discrete maps. Other errors held zero is a modeling qualification, not
a claim that the coupled loop has that scalar pole.

At fixed exogenous curvature the s column of f_x is zero and G ignores s. The corresponding
unregulated progress-offset direction has unit multiplier in the ideal discrete full feedback
map, a structural statement, not an eigensolve. Control of speed can still affect progress;
do not infer that the full pair lacks controllability. Physical kappa_s coupling can remove
that neutral-direction structure; investigate it explicitly. The regulated error set is
[v, y,theta,w,r] relative to the timed packet, with progress analyzed separately, not claimed
asymptotically regulated by a nonexistent progress feedback.

For a genuinely realizable nominal map `e_(k+1)=Acl_k*e_k+O(||e||^2)` in a fixed smooth
branch. Otherwise define `d_k=F(xnom_k,unom_k)-xnom_(k+1)` and retain this affine defect.
Linear interpolation of 100 ms shooting nodes is not in general a realizable 10 ms trajectory;
preview/plant curvature mismatch and racing pseudo-reference `vy_ref=0`, `r_ref=v_ref*kappa_ref`,
kinematic delta_ff and absent a_ref add distinct defects. Quantify each in CT-1L; do not
attribute forced errors to an unstable homogeneous matrix without examining d_k.

Slew-active feedback depends on the previous applied steering. In an ideal immediate tick,
augment state with delta_prev, differentiate the selected clip branches (interior slope 1,
strict saturation slope 0, ties nondifferentiable), and include the memory update. Actual
asynchronous behavior additionally needs held acceleration, pending request, last-application
time, sample age and event mode; an augmented event map is needed for such a linearization.
No such numerical map is constructed here. At clip ties give one-sided/generalized results
or mark unavailable. Never apply an unrestricted A-BK conclusion to this stateful hybrid law.
