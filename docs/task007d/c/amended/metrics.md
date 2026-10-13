# Task007D-C compact numerical tables

All C3 runs: recorded states 0–1.995 s, codriver samples 0–1.990 s; physical run ends at 2 s.
Canonical state units: vx/vy m/s, r rad/s, e_psi rad, s_abs/e_y m. Heading residuals wrapped.
TV is sum of absolute changes; world heading uses track heading plus Frenet heading.
Nominal TV is the sequence actually sampled by TVLQR; actual steering is physically applied.
Rate magnitudes divide actual applied increments by elapsed application time; the startup command is prepositioned.
Rate occupancy uses the unchanged 1 rad/s bound; reversals ignore magnitudes below 1e-10 rad/s.

## Active APEX-to-vehicle tracking

| Run | State | RMS | Maximum absolute |
| --- | --- | --- | --- |
| C3_g1.8_fixed70 | vx | 0.00064643491 | 0.0038343296 |
| C3_g1.8_fixed70 | vy | 0.0090013704 | 0.050291696 |
| C3_g1.8_fixed70 | r | 0.021865475 | 0.10255724 |
| C3_g1.8_fixed70 | e_psi | 0.0028286034 | 0.018883608 |
| C3_g1.8_fixed70 | s_abs | 0.00036701942 | 0.00099028684 |
| C3_g1.8_fixed70 | e_y | 0.00042307961 | 0.0015120047 |
| C3_g1.8_fixed80 | vx | 0.00068833819 | 0.0038426195 |
| C3_g1.8_fixed80 | vy | 0.009282887 | 0.050426872 |
| C3_g1.8_fixed80 | r | 0.020250114 | 0.108958 |
| C3_g1.8_fixed80 | e_psi | 0.0030109148 | 0.018924975 |
| C3_g1.8_fixed80 | s_abs | 0.00036505154 | 0.00098881547 |
| C3_g1.8_fixed80 | e_y | 0.00046083773 | 0.0019759626 |
| C3_g1.8_variable | vx | 0.00090342283 | 0.0044128507 |
| C3_g1.8_variable | vy | 0.010324193 | 0.050499466 |
| C3_g1.8_variable | r | 0.027151373 | 0.14417583 |
| C3_g1.8_variable | e_psi | 0.0032369311 | 0.016141092 |
| C3_g1.8_variable | s_abs | 0.00038045242 | 0.0010136047 |
| C3_g1.8_variable | e_y | 0.00052913163 | 0.0025884633 |
| C3_g2.0_fixed70 | vx | 0.0010440316 | 0.0064816176 |
| C3_g2.0_fixed70 | vy | 0.014124392 | 0.070524627 |
| C3_g2.0_fixed70 | r | 0.032387978 | 0.14309025 |
| C3_g2.0_fixed70 | e_psi | 0.0037105233 | 0.023530956 |
| C3_g2.0_fixed70 | s_abs | 0.000405825 | 0.0010951021 |
| C3_g2.0_fixed70 | e_y | 0.00049368713 | 0.002168311 |
| C3_g2.0_fixed80 | vx | 0.0011179265 | 0.0066793537 |
| C3_g2.0_fixed80 | vy | 0.01454528 | 0.071442133 |
| C3_g2.0_fixed80 | r | 0.029958294 | 0.11470673 |
| C3_g2.0_fixed80 | e_psi | 0.0039896154 | 0.024228154 |
| C3_g2.0_fixed80 | s_abs | 0.00040421432 | 0.0010886745 |
| C3_g2.0_fixed80 | e_y | 0.0005454671 | 0.0027811226 |
| C3_g2.0_variable | vx | 0.001512598 | 0.0072171419 |
| C3_g2.0_variable | vy | 0.016645326 | 0.073222673 |
| C3_g2.0_variable | r | 0.042905629 | 0.31147413 |
| C3_g2.0_variable | e_psi | 0.0044779614 | 0.02166057 |
| C3_g2.0_variable | s_abs | 0.00041981279 | 0.001133236 |
| C3_g2.0_variable | e_y | 0.00067468833 | 0.0038598565 |

## Physical and rate metrics

| Run | max_front_utilization | max_rear_utilization | max_abs_beta | steering_utilization | minimum_frenet_denominator |
| --- | --- | --- | --- | --- | --- |
| C3_g1.8_fixed70 | 0.2971804 | 0.3166462 | 0.05038606 | 0.14146327 | 0.99999841 |
| C3_g1.8_fixed80 | 0.2971804 | 0.3166462 | 0.05038606 | 0.14146327 | 0.9999981 |
| C3_g1.8_variable | 0.2971804 | 0.3166462 | 0.050369669 | 0.14146327 | 0.99999721 |
| C3_g2.0_fixed70 | 0.33734855 | 0.36460087 | 0.062662412 | 0.14075652 | 0.99998099 |
| C3_g2.0_fixed80 | 0.33734855 | 0.36460087 | 0.062662412 | 0.14075652 | 0.99998462 |
| C3_g2.0_variable | 0.33734855 | 0.36460087 | 0.062638282 | 0.14993126 | 0.99997616 |

| Run | steering_rate_max_abs_rad_s | steering_rate_rms_rad_s | rate_reversals | rate_limit_occupancy |
| --- | --- | --- | --- | --- |
| C3_g1.8_fixed70 | 1 | 0.24960974 | 22 | 0.055 |
| C3_g1.8_fixed80 | 1 | 0.26779575 | 20 | 0.06 |
| C3_g1.8_variable | 1 | 0.25248003 | 34 | 0.04 |
| C3_g2.0_fixed70 | 1 | 0.281886 | 20 | 0.06 |
| C3_g2.0_fixed80 | 1 | 0.29648202 | 20 | 0.07 |
| C3_g2.0_variable | 1 | 0.32393654 | 34 | 0.09 |

| Run | nominal_heading_tv | nominal_steering_tv | nominal_acceleration_tv | applied_acceleration_tv |
| --- | --- | --- | --- | --- |
| C3_g1.8_fixed70 | 0.27275922 | 0.11830546 | 0.83401325 | 0.841036 |
| C3_g1.8_fixed80 | 0.27824882 | 0.11666219 | 0.83107555 | 0.83656657 |
| C3_g1.8_variable | 0.27029543 | 0.096885619 | 1.0205404 | 1.0358233 |
| C3_g2.0_fixed70 | 0.30393049 | 0.1457563 | 1.1446521 | 1.1571239 |
| C3_g2.0_fixed80 | 0.31173516 | 0.14426485 | 1.1431679 | 1.1537635 |
| C3_g2.0_variable | 0.29525403 | 0.11687725 | 1.3042635 | 1.3284504 |

## Physical coverage / validity

| Run | progress_reached | minimum_center_clearance | minimum_reserve | max_predicted_slack | accepted_handoffs |
| --- | --- | --- | --- | --- | --- |
| C3_g1.8_fixed70 | 11.339566 | 0.43731382 | 0.635 | 9.0918165e-11 | 19 |
| C3_g1.8_fixed80 | 11.339284 | 0.43731382 | 0.625 | 9.091829e-11 | 19 |
| C3_g1.8_variable | 11.339268 | 0.43731382 | 0.667 | 9.0917512e-11 | 19 |
| C3_g2.0_fixed70 | 12.495381 | 0.43731382 | 0.635 | 9.0915253e-11 | 19 |
| C3_g2.0_fixed80 | 12.494988 | 0.43731382 | 0.625 | 9.0915253e-11 | 19 |
| C3_g2.0_variable | 12.494015 | 0.43731382 | 0.667 | 9.0915253e-11 | 19 |

Progress differences are millimetres or less over this short trace, not established racing gains.

## First common-event divergence

Difference threshold is 1e-12 for reporting, not a physics error tolerance. Comparisons also retain bitwise equality flags.

| Pair | First physical state difference [s] | First command generation difference [s] | First reference difference [s] |
| --- | --- | --- | --- |
| C1 | 0.125 | 0.13 | 0.27 |
| C2 | 0.48 | 0.47 | 0.47 |
| C3_g2.0_vs_70 | 0.15 | 0.14 | 0.14 |
| C3_g2.0_vs_80 | 0.15 | 0.14 | 0.14 |
| C3_g1.8_vs_70 | 0.15 | 0.14 | 0.14 |
| C3_g1.8_vs_80 | 0.15 | 0.14 | 0.14 |

## C2 state difference versus matched no-miss history

| State | RMS | Maximum absolute |
| --- | --- | --- |
| vx | 0.0008984085 | 0.0021475855 |
| vy | 0.00043495661 | 0.0019750071 |
| r | 0.002038037 | 0.012769484 |
| e_psi | 0.00010862631 | 0.00051378375 |
| s_abs | 0.00082161608 | 0.0012746151 |
| e_y | 7.8687401e-05 | 0.00019173615 |

## Same-time accepted-handoff continuity

These are actual-minus-new-nominal errors at accepted handoff, not the readiness-state diagnostic.

| Run | State | RMS | Maximum absolute |
| --- | --- | --- | --- |
| C3_g1.8_fixed70 | vx | 0.00016517427 | 0.00071992249 |
| C3_g1.8_fixed70 | vy | 0.00058387587 | 0.0025013227 |
| C3_g1.8_fixed70 | r | 0.012939493 | 0.056341103 |
| C3_g1.8_fixed70 | e_psi | 0.00046285689 | 0.0019872867 |
| C3_g1.8_fixed70 | s_abs | 1.0167604e-05 | 4.3892648e-05 |
| C3_g1.8_fixed70 | e_y | 5.0825983e-05 | 0.00021368035 |
| C3_g1.8_fixed80 | vx | 0.00019712569 | 0.00085860867 |
| C3_g1.8_fixed80 | vy | 0.00091361503 | 0.003779834 |
| C3_g1.8_fixed80 | r | 0.013991167 | 0.060665759 |
| C3_g1.8_fixed80 | e_psi | 0.00059494064 | 0.0025269668 |
| C3_g1.8_fixed80 | s_abs | 1.2543108e-05 | 5.4602541e-05 |
| C3_g1.8_fixed80 | e_y | 7.0900495e-05 | 0.00028789726 |
| C3_g1.8_variable | vx | 0.00054609837 | 0.0021548551 |
| C3_g1.8_variable | vy | 0.0060431625 | 0.024367225 |
| C3_g1.8_variable | r | 0.0059486752 | 0.019779291 |
| C3_g1.8_variable | e_psi | 0.0017782488 | 0.0077332094 |
| C3_g1.8_variable | s_abs | 0.00021777639 | 0.00065583779 |
| C3_g1.8_variable | e_y | 0.00012748805 | 0.00046633106 |
| C3_g2.0_fixed70 | vx | 0.00022650378 | 0.00098674734 |
| C3_g2.0_fixed70 | vy | 0.0012682197 | 0.0040854039 |
| C3_g2.0_fixed70 | r | 0.013344068 | 0.058052768 |
| C3_g2.0_fixed70 | e_psi | 0.00053639535 | 0.0019901948 |
| C3_g2.0_fixed70 | s_abs | 1.1892809e-05 | 5.1178737e-05 |
| C3_g2.0_fixed70 | e_y | 6.2026014e-05 | 0.00020590988 |
| C3_g2.0_fixed80 | vx | 0.00027264566 | 0.0011880411 |
| C3_g2.0_fixed80 | vy | 0.0017353613 | 0.0053499154 |
| C3_g2.0_fixed80 | r | 0.014567091 | 0.063029976 |
| C3_g2.0_fixed80 | e_psi | 0.00068492711 | 0.0025471981 |
| C3_g2.0_fixed80 | s_abs | 1.4730436e-05 | 6.3433103e-05 |
| C3_g2.0_fixed80 | e_y | 8.5037601e-05 | 0.00027880265 |
| C3_g2.0_variable | vx | 0.00086311261 | 0.0031838779 |
| C3_g2.0_variable | vy | 0.0093978555 | 0.033848584 |
| C3_g2.0_variable | r | 0.025490974 | 0.099075719 |
| C3_g2.0_variable | e_psi | 0.0023105046 | 0.0093822265 |
| C3_g2.0_variable | s_abs | 0.00024007361 | 0.00071111264 |
| C3_g2.0_variable | e_y | 8.2221888e-05 | 0.00025993555 |

## Event partitions

Counts are overlapping event-boundary classifications; coincident events must not be summed.

| Run | count | minimum_dt | maximum_dt | non_grid_readiness | readiness_boundaries | handoff_boundaries | application_boundaries | readiness_only_boundaries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1_jitter | 419 | 0.001 | 0.005 | 19 | 19 | 19 | 200 | 19 |
| C1_steady | 400 | 0.005 | 0.005 | 0 | 19 | 19 | 200 | 0 |
| C2_miss | 400 | 0.005 | 0.005 | 1 | 19 | 18 | 200 | 0 |
| C3_g1.8_fixed70 | 400 | 0.005 | 0.005 | 19 | 19 | 19 | 200 | 0 |
| C3_g1.8_fixed80 | 400 | 0.005 | 0.005 | 19 | 19 | 19 | 200 | 0 |
| C3_g1.8_variable | 400 | 0.005 | 0.005 | 19 | 19 | 19 | 200 | 0 |
| C3_g2.0_fixed70 | 400 | 0.005 | 0.005 | 19 | 19 | 19 | 200 | 0 |
| C3_g2.0_fixed80 | 400 | 0.005 | 0.005 | 19 | 19 | 19 | 200 | 0 |
| C3_g2.0_variable | 400 | 0.005 | 0.005 | 19 | 19 | 19 | 200 | 0 |
