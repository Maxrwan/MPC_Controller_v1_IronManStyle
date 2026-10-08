# Task007C sustained confirmation and deterministic repeats

N6 and N8 gamma2 fixed-history repeats exactly match states, controls, physical availability, accepted handoffs, active references, predictions, NLP inputs, warm starts, solutions, objectives and iterations. Full snapshot and state counts match. The first-control offset is derived as 6(N+1), rather than the archived N4 offset.

All eight sustained runs reach three lap-end crossings without boundary, solver, forecast, fallback or deadline failures. The first segment starts at s_abs=1m; only the following two are complete geometric laps. Oscillation metrics use native telemetry samples within each lap and reset at seams; crossing times are interpolated by the existing runner. The finite smooth trace was sufficient in all four cases.

| Case | Lap | Segment | Time s | epsi TV rad | Nominal steering TV rad | Actual steering TV rad | Actual reversals (0.001 rad/s deadband) | Rate-limit s |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| g2_w0_vy1_r1_n4_fixed_l3 | 1 | rolling | 31.26713 | 11.99287 | 8.00079 | 11.17160 | 362.00000 | 8.56000 |
| g2_w0_vy1_r1_n4_fixed_l3 | 2 | full geometric lap | 31.40052 | 10.31219 | 6.16894 | 8.77434 | 403.00000 | 6.14000 |
| g2_w0_vy1_r1_n4_fixed_l3 | 3 | full geometric lap | 31.72887 | 13.62900 | 9.12536 | 11.87830 | 354.00000 | 9.61000 |
| g2_w0_vy1_r1_n4_smooth_l3 | 1 | rolling | 31.20225 | 11.21423 | 7.34203 | 9.93403 | 393.00000 | 3.75000 |
| g2_w0_vy1_r1_n4_smooth_l3 | 2 | full geometric lap | 31.47931 | 9.56193 | 5.81738 | 8.13910 | 412.00000 | 2.78000 |
| g2_w0_vy1_r1_n4_smooth_l3 | 3 | full geometric lap | 31.51137 | 9.85505 | 5.82554 | 8.02303 | 417.00000 | 2.67000 |
| g2_w0_vy1_r1_n6_fixed_l3 | 1 | rolling | 30.93697 | 9.37093 | 5.66012 | 8.04541 | 381.00000 | 5.37000 |
| g2_w0_vy1_r1_n6_fixed_l3 | 2 | full geometric lap | 31.16596 | 8.60689 | 5.06158 | 7.40710 | 397.00000 | 4.67000 |
| g2_w0_vy1_r1_n6_fixed_l3 | 3 | full geometric lap | 31.21779 | 9.93455 | 6.33105 | 8.76219 | 397.00000 | 6.06000 |
| g2_w0_vy1_r1_n6_smooth_l3 | 1 | rolling | 30.85974 | 9.12833 | 5.66573 | 8.04292 | 384.00000 | 2.63000 |
| g2_w0_vy1_r1_n6_smooth_l3 | 2 | full geometric lap | 31.13780 | 8.24356 | 4.89884 | 7.10873 | 420.00000 | 2.32000 |
| g2_w0_vy1_r1_n6_smooth_l3 | 3 | full geometric lap | 31.27764 | 9.99178 | 6.51995 | 8.70160 | 396.00000 | 3.01000 |
| g2_w0_vy1_r1_n8_fixed_l3 | 1 | rolling | 30.94717 | 8.00906 | 4.95982 | 7.08202 | 389.00000 | 4.35000 |
| g2_w0_vy1_r1_n8_fixed_l3 | 2 | full geometric lap | 31.18547 | 8.15867 | 5.03427 | 7.11585 | 390.00000 | 4.39000 |
| g2_w0_vy1_r1_n8_fixed_l3 | 3 | full geometric lap | 31.17344 | 8.86348 | 5.54254 | 7.86403 | 387.00000 | 5.24000 |
| g2_w0_vy1_r1_n8_smooth_l3 | 1 | rolling | 30.92741 | 7.75358 | 4.74022 | 6.55060 | 399.00000 | 1.95000 |
| g2_w0_vy1_r1_n8_smooth_l3 | 2 | full geometric lap | 31.15228 | 8.54143 | 5.39576 | 7.27016 | 403.00000 | 2.28000 |
| g2_w0_vy1_r1_n8_smooth_l3 | 3 | full geometric lap | 31.12308 | 8.68677 | 5.60327 | 7.62684 | 386.00000 | 2.51000 |
| g2p2_w0_vy1_r1_n6_fixed_l3 | 1 | rolling | 29.79256 | 9.27786 | 5.81942 | 8.43954 | 383.00000 | 5.71000 |
| g2p2_w0_vy1_r1_n6_fixed_l3 | 2 | full geometric lap | 30.09116 | 9.89224 | 5.97172 | 8.75599 | 370.00000 | 6.14000 |
| g2p2_w0_vy1_r1_n6_fixed_l3 | 3 | full geometric lap | 29.95754 | 8.89884 | 5.35540 | 8.10582 | 392.00000 | 5.24000 |
| g2p2_w0_vy1_r1_n6_smooth_l3 | 1 | rolling | 29.73597 | 8.75980 | 5.30818 | 7.63219 | 389.00000 | 2.47000 |
| g2p2_w0_vy1_r1_n6_smooth_l3 | 2 | full geometric lap | 30.04377 | 8.95651 | 5.44593 | 7.98144 | 395.00000 | 2.69000 |
| g2p2_w0_vy1_r1_n6_smooth_l3 | 3 | full geometric lap | 30.13666 | 11.52965 | 7.51760 | 10.06302 | 342.00000 | 3.89000 |

The sustained result is not a uniform improvement claim. At gamma2 under fixed timing, N6 and N8 reduce heading/steering variation and rate-limit time on both full laps. Under smooth timing, N6 improves the second lap but slightly worsens heading TV on the third (9.992 versus 9.855 rad), with nominal steering TV 6.520 versus 5.826 rad. N8 improves both full smooth laps. Actual small-amplitude reversal counts do not fall consistently; retain them alongside variation magnitude and rate-limit duration.

At gamma2.2, N6 remains safe through both full laps under both histories, but the third smooth lap grows to heading TV 11.530 rad and nominal steering TV 7.518 rad from 8.957 and 5.446 on the second. This limits any claim of uniform sustained smoothness at the upper point. Fresh measured evidence must precede an envelope decision.

These are sustained controlled-history checks, not fresh measured repetitions. Do not compare three-lap total variation with a one-segment screen. Exact artifacts: `n6_fixed_repeat_parity.json`, `n8_fixed_repeat_parity.json`, `sustained_per_lap.csv` under `results/task007c_resume/`.
