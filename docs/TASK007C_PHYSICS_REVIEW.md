# Task007C internal synthetic physics review

These checks verify the configured synthetic model and its independent NumPy/CasADi implementations. They do not validate an APEX physical vehicle or identified tire parameters. The physical plant and controller prediction remain separate.

## Gamma2 horizon comparison

Baseline weights, lambda0, dt0.1s. All primary horizon statistics below use accepted packets, include only observed future times, and keep heading interpolation wrapped consistently.

| N | History | Same-input vy derivative max m/s² | Same-input r derivative max rad/s² | Lateral force-balance max m/s² | Smooth-stencil finite-difference RMS m/s² | Stencil count |
|---|---|---|---|---|---|---|
| 4 | fixed | 1.77636e-15 | 3.10862e-14 | 4.44089e-16 | 0.00172444 | 3127 |
| 4 | smooth | 1.77636e-15 | 2.66454e-14 | 4.44089e-16 | 0.00142564 | 3558 |
| 6 | fixed | 1.77636e-15 | 3.10862e-14 | 4.44089e-16 | 0.00127525 | 3094 |
| 6 | smooth | 1.77636e-15 | 2.22045e-14 | 4.44089e-16 | 0.00116233 | 3519 |
| 8 | fixed | 1.77636e-15 | 2.66454e-14 | 2.22045e-16 | 0.0011302 | 3095 |
| 8 | smooth | 2.66454e-15 | 2.66454e-14 | 2.22045e-16 | 0.00095607 | 3526 |

The independent derivative transcriptions agree to floating-point precision. The force-balance equality is an algebraic consistency check; finite differences provide a separate numerical reconstruction. The primary finite-difference subset excludes stencils crossing command changes and adjacent intervals of1μs or less. Event-grid differentiation is not a sensor measurement.

| N | History | One-step ey RMS m | Realized step4 vx RMS m/s | vy RMS m/s | r RMS rad/s | epsi RMS rad | ey RMS m |
|---|---|---|---|---|---|---|---|
| 4 | fixed | 1.45206e-07 | 0.152145 | 0.152611 | 0.510317 | 0.0675019 | 0.0245191 |
| 4 | smooth | 1.42641e-07 | 0.151356 | 0.1359 | 0.461592 | 0.0678592 | 0.0265095 |
| 6 | fixed | 1.38018e-07 | 0.082076 | 0.0544605 | 0.304349 | 0.0357588 | 0.0231585 |
| 6 | smooth | 1.35272e-07 | 0.07838 | 0.0513467 | 0.29902 | 0.0363087 | 0.0231775 |
| 8 | fixed | 1.33794e-07 | 0.0483885 | 0.0375757 | 0.22912 | 0.02989 | 0.0199856 |
| 8 | smooth | 1.3144e-07 | 0.0466675 | 0.0366503 | 0.203639 | 0.0247739 | 0.0174361 |

The one-step diagnostic uses the actual held input and physical event-step duration. Its symbolic RK4 freezes interval-start curvature, whereas the plant reevaluates curvature at intermediate RK4 states; these residuals are not expected to be exactly zero.

The common0.4s realized prediction error becomes smaller with the longer horizons in these six cases, especially yaw rate. This combines preview/availability error, later replanning and TVLQR feedback with model approximation. It must not be interpreted as a change in the physical tire law or as pure open-loop identification accuracy.

## Required plots and reading limits

Each principal case has `physics_review.png`, `physics_telemetry.csv`, `horizon_prediction_error.csv` and `physics_validation.json`. Slip/force panels show a configured-law slice at the middle sample load/Fx alongside the observed cloud, whose normal load and longitudinal force vary. The slice demonstrates the linear low-slip regime and smooth saturation. Friction-plane plots include the unit boundary.

Low-slip yaw comparison uses max(|alpha_f|,|alpha_r|)<0.03rad as a descriptive split, not a new safety threshold. High-slip/transient yaw rate need not equal vx times racing-reference curvature. Beta is reported alongside normalized lateral demand; a nonzero beta is not automatically a defect.

Primary horizon curves exclude rejected and pending packets. The tagged CSV and `horizon_errors_all_prepared` summary retain them for diagnosis. No packet or unfavorable outcome is removed from raw evidence.

Principal folders:

- `results/task007c_resume/g2_w0_vy1_r1_n4_fixed_l1/`
- `results/task007c_resume/g2_w0_vy1_r1_n4_smooth_l1/`
- `results/task007c_resume/g2_w0_vy1_r1_n6_fixed_l1/`
- `results/task007c_resume/g2_w0_vy1_r1_n6_smooth_l1/`
- `results/task007c_resume/g2_w0_vy1_r1_n8_fixed_l1/`
- `results/task007c_resume/g2_w0_vy1_r1_n8_smooth_l1/`

Representative histories and measured validation are now complete. The initial six cells above are the controlled comparison; measured worst cases are listed below. Final limitations and the review recommendation are in `TASK007C_RESUMED_RESULTS.md`.

## Measured worst-heading and failed-case consistency

Selection is the largest completed heading TV in each of four measured groups, plus the incomplete N6 record. The incomplete record has shorter coverage and is not ranked as a full-lap accuracy improvement.

| Case | Derivative max abs (SI/channel) | Smooth ay FD RMS m/s² | One-step ey RMS m | Accepted step4 ey RMS m | Accepted step4 r RMS rad/s |
|---|---:|---:|---:|---:|---:|
| g2_w0_vy1_r1_n4_measured_l1_rep02 | 2.664535e-14 | 0.002306449 | 1.379371e-07 | 0.0369515 | 0.721315 |
| g2_w0_vy1_r1_n6_measured_l1_rep02 | 2.664535e-14 | 0.001215844 | 1.343007e-07 | 0.02492261 | 0.31731 |
| g2_w0_vy1_r1_n8_measured_l1_rep04 | 2.220446e-14 | 0.001107607 | 1.31606e-07 | 0.0192426 | 0.2496894 |
| g2p2_w0_vy1_r1_n6_measured_l1_rep03 | 2.664535e-14 | 0.001465053 | 1.582655e-07 | 0.02563347 | 0.3580114 |
| g2_w0_vy1_r1_n6_measured_l1_rep00 | 2.131628e-14 | 0.001144206 | 1.164519e-07 | 0.01999539 | 0.2651835 |

The measured comparison figure, N8 primary/technical and physics panels, failed N6 primary dashboard and measured phase portraits were visually inspected. Smooth saturation, bounded friction-plane clouds and matched lateral-acceleration traces are visible. Repeated loops and steering corrections remain; no claim of perfectly smooth behavior follows. Pending preparation is marked at its source progress even when it never becomes an active packet.
