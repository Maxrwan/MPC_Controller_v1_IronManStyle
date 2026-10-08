# Task007C C2 fixed-history screen — interim evidence

All nine approved alpha pairs at gamma1.8 and2.0 have completed under fixed35ms/1ms timing.
The smooth-history grid is still running; no formulation is selected from this table alone.
Nonlinear states, equations, Planning intent, TVLQR, dt0.1/N4 and lambda0 remain unchanged.
Only stage importance and the corresponding DARE design Q change. The regenerated P can
retain dynamic-state and cross terms even when a Q multiplier is zero: this is not removal
of vy/r from the nonlinear model or manual zeroing of terminal P rows.

| Gamma | alpha_vy | alpha_r | Heading TV rad | Nominal steering TV rad | Rate-limit s | p95 abs beta rad | Min clearance m | Max slack m | Lap s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|1.8000|0.0000|0.0000|25.9994|17.4092|17.8260|0.1533|0.2117|0.0000|34.9728|
|1.8000|0.0000|1.0000|11.6332|7.9607|7.7900|0.1044|0.3048|0.0000|33.7287|
|1.8000|0.2500|0.2500|15.9267|11.1506|11.4100|0.1039|0.1461|0.0000|34.5201|
|1.8000|0.2500|1.0000|11.1322|7.5851|7.2110|0.1001|0.3268|0.0000|33.8708|
|1.8000|0.5000|1.0000|12.0279|7.9269|7.5960|0.0962|0.3267|0.0000|33.8543|
|1.8000|1.0000|0.0000|25.2326|17.1472|17.7000|0.1470|0.2503|0.0000|35.5704|
|1.8000|1.0000|0.2500|20.6952|14.3440|14.5600|0.1354|0.2966|0.0000|34.7778|
|1.8000|1.0000|0.5000|13.6327|9.5614|9.7100|0.1077|0.2989|0.0000|33.9953|
|1.8000|1.0000|1.0000|9.6472|6.0848|5.4900|0.0939|0.3264|0.0000|33.8014|
|2.0000|0.0000|0.0000|38.0302|23.4129|25.1000|0.2112|0.0855|0.0000|35.4383|
|2.0000|0.0000|1.0000|12.9723|8.8609|9.7000|0.1517|0.3215|0.0000|31.0072|
|2.0000|0.2500|0.2500|43.5292|27.0020|28.9300|0.2131|-0.2644|0.3406|35.7865|
|2.0000|0.2500|1.0000|15.6233|11.3828|12.3800|0.1672|0.3212|0.0000|31.1576|
|2.0000|0.5000|1.0000|10.8932|7.0455|7.2600|0.1414|0.3210|0.0000|31.0436|
|2.0000|1.0000|0.0000|46.9485|29.6098|31.7400|0.2174|0.2097|0.0000|35.7572|
|2.0000|1.0000|0.2500|43.2094|28.4747|30.8700|0.2209|0.0696|0.0197|34.7848|
|2.0000|1.0000|0.5000|15.6258|9.6672|9.9400|0.1449|0.2323|0.0000|31.8887|
|2.0000|1.0000|1.0000|11.9929|8.0008|8.5600|0.1459|0.3206|0.0000|31.2671|

At gamma2, the combined(.25,.25) case crosses the physical boundary at the technical entrance:
159 samples from21.546–22.071s, s97.574–98.715m, max ey0.814420m. Minimum clearance−0.264420m,
maximum predicted slack0.3406m, heading TV43.529rad. It has no solver/fallback/deadline failures.
Local ey RMS remains0.00324m, so the large global excursion is predominantly upstream of the
codriver. The exact synthetic-model consistency export is retained with this rejected case.

Reducing yaw importance strongly worsens smoothness in this screen, even when no boundary is
crossed. Complete removal of both tracking weights does not improve the oscillatory behavior;
its lack of a crossing cannot outweigh heading TV38.030rad and25.10s at the rate limit.

At gamma2, halving vy importance reduces heading TV11.993→10.893rad, nominal steering TV
8.001→7.046rad and rate-limit activity8.56→7.26s. At gamma1.8 the same change worsens those
metrics. It remains only a candidate for cross-history comparison, not a robust improvement.
Larger beta is interpreted together with oscillation, margins and tracking rather than ranked
as good or bad in isolation. All27 DARE node solutions passed the consistency/stability audit.

The disk-capacity interruption affected a derived export, not the controller outcomes.
After the user freed space, all38 completed raw JSON cases passed structural checks and39
asynchronous cases (including the baseline parity run) passed the physical chronology audit.
Interrupted derived files were regenerated. No prior B/C/CR evidence was removed or modified.

Recovered physics export for the failed(.25,.25) case confirms independent derivative maxima
vx0, vy1.78e-15m/s² and r2.66e-14rad/s²; smooth-stencil ay discrepancy RMS0.00334m/s².
The technical-section dashboard was rendered and visually checked. See
`results/task007c_resume/g2_w0_vy0p25_r0p25_n4_fixed_l1/dashboard_technical_section.png`.

## Emerging matched-history evidence (C2 still running)

At gamma2, alpha_vy0.5/alpha_r1 improves both controlled histories. Smooth-history heading TV
11.214→10.692rad, steering TV7.342→6.519rad and rate-limit time3.746→3.260s; min clearance
remains about0.321m. The fixed-history improvement is tabulated above. At gamma1.8 every
single-channel ablation worsens heading/steering variation under both histories. Thus the
half-vy candidate is operating-point dependent and requires representative-history and fresh
measured validation; it is not yet a selected production setting.

Solver success does not certify physical boundary safety: the existing track constraints are
softened by penalized slack, while the0.08m tracking margin remains unchanged. The rejected
case therefore can return a valid optimization result with material slack and then closely
track a trajectory outside the physical boundary. No hard vehicle/model constraint or tire law
was relaxed for the ablation. This distinction is central to the robustness-first ranking.
