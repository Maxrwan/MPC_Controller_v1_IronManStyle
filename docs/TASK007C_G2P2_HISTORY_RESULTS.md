# Task007C gamma2.2 retained timing histories

7 analyzed records; 0 pending. Requested history matrix analyzed.

The first counted lap begins at s_abs=1m and is a rolling segment. Finite histories are never padded or cycled. A trace-exhausted record without a lap is censored, not a lap-completion pass. Whole-record boundary failures remain visible even if the matched prefix ends before them. Native endpoints differ by sampling; the final retained endpoint contributes zero forward interval.

## Common progress across every listed record

Shared requested interval: 1.000000–154.712823m. The table uses lap-prefix metrics with lap seams reset. It is deliberately separate from full-lap outcomes and from per-history comparisons below.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2p2_w0_vy1_r1_n4_fixed_l1 | 1 | 44 | 44 | 154.7 | 24.801 | 15.267 | 16.67 | -0.019739 | 0.0025221 |
| g2p2_w0_vy1_r1_n6_fixed_l1 | 1 | 0 | 0 | 154.7 | 9.2718 | 5.8194 | 5.69 | 0.31566 | 0.0014096 |
| g2p2_w0_vy1_r1_n4_smooth_l1 | 1 | 0 | 0 | 154.71 | 21.914 | 14.848 | 7.81 | 0.10003 | 0.0022553 |
| g2p2_w0_vy1_r1_n6_smooth_l1 | 1 | 0 | 0 | 154.69 | 8.7479 | 5.3058 | 2.47 | 0.31558 | 0.0013422 |
| g2p2_w0_vy1_r1_n6_median_l1 | 1 | 0 | 0 | 154.7 | 8.8887 | 5.6076 | 2.92 | 0.31524 | 0.0014314 |
| g2p2_w0_vy1_r1_n6_pathological_e_l1 | 1 | 0 | 0 | 154.71 | 9.2737 | 5.7377 | 2.95 | 0.31453 | 0.0014693 |
| g2p2_w0_vy1_r1_n6_pathological_f_l1 | 1 | 0 | 0 | 154.67 | 9.2077 | 5.5226 | 2.71 | 0.31552 | 0.0014497 |

## Matched fixed prefix

Shared requested end: 154.737200m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2p2_w0_vy1_r1_n4_fixed_l1 | 1 | 44 | 44 | 154.74 | 24.807 | 15.267 | 16.68 | -0.019739 | 0.0025223 |
| g2p2_w0_vy1_r1_n6_fixed_l1 | 1 | 0 | 0 | 154.7 | 9.2718 | 5.8194 | 5.69 | 0.31566 | 0.0014096 |

## Matched smooth prefix

Shared requested end: 154.734291m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2p2_w0_vy1_r1_n4_smooth_l1 | 1 | 0 | 0 | 154.71 | 21.914 | 14.848 | 7.81 | 0.10003 | 0.0022553 |
| g2p2_w0_vy1_r1_n6_smooth_l1 | 1 | 0 | 0 | 154.73 | 8.7598 | 5.3082 | 2.47 | 0.31558 | 0.001342 |

## Matched median prefix

Shared requested end: 154.747497m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2p2_w0_vy1_r1_n6_median_l1 | 1 | 0 | 0 | 154.75 | 8.8927 | 5.6076 | 2.92 | 0.31524 | 0.0014317 |

## Matched pathological_e prefix

Shared requested end: 154.712823m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2p2_w0_vy1_r1_n6_pathological_e_l1 | 1 | 0 | 0 | 154.71 | 9.2737 | 5.7377 | 2.95 | 0.31453 | 0.0014693 |

## Matched pathological_f prefix

Shared requested end: 154.716623m. This may be longer than the all-history intersection.

| Case | Lap-end crossings | Whole-record boundary samples | Common-prefix boundary samples | Native end m | epsi TV rad | Nominal steering TV rad | Rate-limit s | Prefix clearance min m | Prefix ey RMS m |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| g2p2_w0_vy1_r1_n6_pathological_f_l1 | 1 | 0 | 0 | 154.72 | 9.2145 | 5.5226 | 2.71 | 0.31552 | 0.0014497 |

Matched baseline/candidate pairs share the same original availability sequence. These histories are a deliberately selected diagnostic set, not independent random samples. Their ranges describe sensitivity, not population confidence. Fresh measured repetitions and isolated compute cost remain separate acceptance layers.
