# Task007C gamma2 retained timing histories

25 analyzed records; 0 pending. Requested history matrix analyzed.

The first counted lap begins at s_abs=1m and is a rolling segment. Finite histories are never padded or cycled. A trace-exhausted record without a lap is censored, not a lap-completion pass. Whole-record boundary failures remain visible even if the matched prefix ends before them. Native endpoints differ by sampling; the final retained endpoint contributes zero forward interval.

## Common progress across every listed record

Shared requested interval: 1.000000–145.939377m. The table uses lap-prefix metrics with lap seams reset. It is deliberately separate from full-lap outcomes and from per-history comparisons below.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2_w0_vy1_r1_n4_fixed_l1 | 1 | 0 | 0 | 145.9 | 11.16 | 7.7362 | 8.16 | 0.32061 | 0.0014763 |
| g2_w0_vy1_r1_n6_fixed_l1 | 1 | 0 | 0 | 145.9 | 8.4796 | 5.2636 | 4.86 | 0.32461 | 0.0012845 |
| g2_w0_vy1_r1_n8_fixed_l1 | 1 | 0 | 0 | 145.92 | 7.1965 | 4.6795 | 3.99 | 0.32917 | 0.0011323 |
| g2_w0_vy0p5_r1_n4_fixed_l1 | 1 | 0 | 0 | 145.92 | 9.8641 | 6.5124 | 6.66 | 0.32103 | 0.0014639 |
| g2_w4_vy1_r1_n4_fixed_l1 | 1 | 0 | 0 | 145.93 | 9.6568 | 6.0233 | 6.22 | 0.32033 | 0.0014569 |
| g2_w0_vy1_r1_n4_smooth_l1 | 1 | 0 | 0 | 145.93 | 10.278 | 6.925 | 3.47 | 0.32057 | 0.0014735 |
| g2_w0_vy1_r1_n6_smooth_l1 | 1 | 0 | 0 | 145.93 | 8.3752 | 5.47 | 2.49 | 0.3248 | 0.0012868 |
| g2_w0_vy1_r1_n8_smooth_l1 | 1 | 0 | 0 | 145.91 | 6.9156 | 4.4072 | 1.76 | 0.32912 | 0.0011108 |
| g2_w0_vy0p5_r1_n4_smooth_l1 | 1 | 0 | 0 | 145.93 | 9.8404 | 6.2788 | 3.04 | 0.32105 | 0.0014609 |
| g2_w4_vy1_r1_n4_smooth_l1 | 1 | 0 | 0 | 145.92 | 9.6204 | 6.0451 | 2.8 | 0.31473 | 0.0014267 |
| g2_w0_vy1_r1_n4_median_l1 | 0 | 0 | 0 | 145.92 | 17.078 | 11.493 | 6.17 | 0.24775 | 0.00203 |
| g2_w0_vy1_r1_n6_median_l1 | 0 | 0 | 0 | 145.91 | 8.4953 | 5.4523 | 2.6 | 0.32442 | 0.0013505 |
| g2_w0_vy1_r1_n8_median_l1 | 0 | 0 | 0 | 145.93 | 7.4964 | 5.0444 | 2.02 | 0.32893 | 0.0012211 |
| g2_w0_vy0p5_r1_n4_median_l1 | 0 | 0 | 0 | 145.91 | 11.406 | 7.9631 | 4.22 | 0.32105 | 0.0016351 |
| g2_w4_vy1_r1_n4_median_l1 | 0 | 0 | 0 | 145.9 | 15.83 | 10.519 | 5.65 | 0.31161 | 0.0019515 |
| g2_w0_vy1_r1_n4_pathological_e_l1 | 0 | 0 | 0 | 145.92 | 28.651 | 19.662 | 11.28 | 0.24654 | 0.0027508 |
| g2_w0_vy1_r1_n6_pathological_e_l1 | 1 | 0 | 0 | 145.93 | 8.2144 | 5.5597 | 2.86 | 0.32407 | 0.0013027 |
| g2_w0_vy1_r1_n8_pathological_e_l1 | 1 | 0 | 0 | 145.92 | 7.0735 | 4.5602 | 2.13 | 0.32856 | 0.001164 |
| g2_w0_vy0p5_r1_n4_pathological_e_l1 | 0 | 59 | 59 | 145.94 | 31.083 | 20.235 | 11.55 | -0.033387 | 0.0029653 |
| g2_w4_vy1_r1_n4_pathological_e_l1 | 0 | 0 | 0 | 145.94 | 28.686 | 18.557 | 10.53 | 0.23433 | 0.0027574 |
| g2_w0_vy1_r1_n4_pathological_f_l1 | 1 | 0 | 0 | 145.91 | 11.935 | 8.0323 | 4.33 | 0.30398 | 0.0016512 |
| g2_w0_vy1_r1_n6_pathological_f_l1 | 1 | 0 | 0 | 145.91 | 8.4197 | 5.5585 | 2.63 | 0.32455 | 0.0012838 |
| g2_w0_vy1_r1_n8_pathological_f_l1 | 1 | 0 | 0 | 145.94 | 7.0299 | 4.4024 | 1.83 | 0.32914 | 0.0011335 |
| g2_w0_vy0p5_r1_n4_pathological_f_l1 | 0 | 0 | 0 | 145.92 | 19.686 | 13.438 | 7.75 | 0.17811 | 0.00219 |
| g2_w4_vy1_r1_n4_pathological_f_l1 | 0 | 100 | 100 | 145.93 | 18.567 | 11.716 | 6.55 | -0.087801 | 0.0022658 |

## Matched fixed prefix

Shared requested end: 154.729884m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2_w0_vy1_r1_n4_fixed_l1 | 1 | 0 | 0 | 154.69 | 11.989 | 8.0008 | 8.55 | 0.32061 | 0.001512 |
| g2_w0_vy1_r1_n6_fixed_l1 | 1 | 0 | 0 | 154.69 | 9.3658 | 5.6601 | 5.35 | 0.32461 | 0.0013614 |
| g2_w0_vy1_r1_n8_fixed_l1 | 1 | 0 | 0 | 154.73 | 8.0091 | 4.9598 | 4.35 | 0.32917 | 0.0012048 |
| g2_w0_vy0p5_r1_n4_fixed_l1 | 1 | 0 | 0 | 154.7 | 10.874 | 6.9311 | 7.26 | 0.32103 | 0.0015326 |
| g2_w4_vy1_r1_n4_fixed_l1 | 1 | 0 | 0 | 154.69 | 10.486 | 6.2889 | 6.63 | 0.32033 | 0.0014953 |

## Matched smooth prefix

Shared requested end: 154.718661m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2_w0_vy1_r1_n4_smooth_l1 | 1 | 0 | 0 | 154.71 | 11.208 | 7.342 | 3.73 | 0.32057 | 0.001522 |
| g2_w0_vy1_r1_n6_smooth_l1 | 1 | 0 | 0 | 154.72 | 9.1283 | 5.6657 | 2.63 | 0.3248 | 0.0013307 |
| g2_w0_vy1_r1_n8_smooth_l1 | 1 | 0 | 0 | 154.68 | 7.7495 | 4.7402 | 1.95 | 0.32912 | 0.0011991 |
| g2_w0_vy0p5_r1_n4_smooth_l1 | 1 | 0 | 0 | 154.69 | 10.688 | 6.5188 | 3.26 | 0.32105 | 0.0014992 |
| g2_w4_vy1_r1_n4_smooth_l1 | 1 | 0 | 0 | 154.68 | 10.57 | 6.5105 | 3.05 | 0.31473 | 0.0014847 |

## Matched median prefix

Shared requested end: 147.978479m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2_w0_vy1_r1_n4_median_l1 | 0 | 0 | 0 | 147.98 | 17.401 | 11.894 | 6.35 | 0.24775 | 0.0020384 |
| g2_w0_vy1_r1_n6_median_l1 | 0 | 0 | 0 | 147.97 | 8.6114 | 5.4942 | 2.62 | 0.32442 | 0.0013436 |
| g2_w0_vy1_r1_n8_median_l1 | 0 | 0 | 0 | 147.94 | 7.605 | 5.0907 | 2.04 | 0.32893 | 0.0012166 |
| g2_w0_vy0p5_r1_n4_median_l1 | 0 | 0 | 0 | 147.95 | 11.555 | 8.0177 | 4.28 | 0.32105 | 0.0016274 |
| g2_w4_vy1_r1_n4_median_l1 | 0 | 0 | 0 | 147.97 | 16.434 | 10.905 | 5.86 | 0.31161 | 0.0019589 |

## Matched pathological_e prefix

Shared requested end: 145.939377m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2_w0_vy1_r1_n4_pathological_e_l1 | 0 | 0 | 0 | 145.92 | 28.651 | 19.662 | 11.28 | 0.24654 | 0.0027508 |
| g2_w0_vy1_r1_n6_pathological_e_l1 | 1 | 0 | 0 | 145.93 | 8.2144 | 5.5597 | 2.86 | 0.32407 | 0.0013027 |
| g2_w0_vy1_r1_n8_pathological_e_l1 | 1 | 0 | 0 | 145.92 | 7.0735 | 4.5602 | 2.13 | 0.32856 | 0.001164 |
| g2_w0_vy0p5_r1_n4_pathological_e_l1 | 0 | 59 | 59 | 145.94 | 31.083 | 20.235 | 11.55 | -0.033387 | 0.0029653 |
| g2_w4_vy1_r1_n4_pathological_e_l1 | 0 | 0 | 0 | 145.94 | 28.686 | 18.557 | 10.53 | 0.23433 | 0.0027574 |

## Matched pathological_f prefix

Shared requested end: 149.148304m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2_w0_vy1_r1_n4_pathological_f_l1 | 1 | 0 | 0 | 149.11 | 12.157 | 8.1235 | 4.4 | 0.30398 | 0.0016389 |
| g2_w0_vy1_r1_n6_pathological_f_l1 | 1 | 0 | 0 | 149.15 | 8.5897 | 5.6246 | 2.65 | 0.32455 | 0.0012751 |
| g2_w0_vy1_r1_n8_pathological_f_l1 | 1 | 0 | 0 | 149.12 | 7.2006 | 4.4786 | 1.87 | 0.32914 | 0.0011271 |
| g2_w0_vy0p5_r1_n4_pathological_f_l1 | 0 | 0 | 0 | 149.13 | 20.777 | 14.132 | 8.14 | 0.17811 | 0.002211 |
| g2_w4_vy1_r1_n4_pathological_f_l1 | 0 | 100 | 100 | 149.15 | 20.043 | 12.831 | 7.12 | -0.087801 | 0.0022745 |

Matched baseline/candidate pairs share the same original availability sequence. These histories are a deliberately selected diagnostic set, not independent random samples. Their ranges describe sensitivity, not population confidence. Fresh measured repetitions and isolated compute cost remain separate acceptance layers.
