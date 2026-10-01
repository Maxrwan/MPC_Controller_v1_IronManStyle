# Task006.3 — measured results

Final experiments use the timestamp-boundary fix and explicit command-validation timing. Earlier exploratory runs are retained separately and excluded. Desktop measurements are not hard-real-time guarantees.

## All conditions

| case | completed | completed_without_fallback | rms_e_y | rms_e_psi | rms_speed_error | planner_misses | codriver_misses | fallback_events | boundary_violations | solver_failures |
|---|---|---|---|---|---|---|---|---|---|---|
| async_measured | True | True | 0.0039 | 0.0181 | 0.0302 | 0 | 0.0000 | 0 | 0 | 0 |
| codriver_0ms | True | True | 0.0035 | 0.0172 | 0.0302 | 0 | 0.0000 | 0 | 0 | 0 |
| codriver_100ms | True | True | 0.0036 | 0.0173 | 0.0303 | 0 | 0.0000 | 0 | 0 | 0 |
| codriver_150ms | True | True | 0.0034 | 0.0167 | 0.0317 | 162 | 0.0000 | 0 | 0 | 0 |
| codriver_250ms | True | False | 0.0154 | 0.0165 | 0.0233 | 4 | 0.0000 | 1 | 0 | 0 |
| codriver_25ms | True | True | 0.0034 | 0.0169 | 0.0302 | 0 | 0.0000 | 0 | 0 | 0 |
| codriver_450ms | True | False | 0.0154 | 0.0165 | 0.0232 | 4 | 0.0000 | 1 | 0 | 0 |
| codriver_60ms | True | True | 0.0042 | 0.0186 | 0.0303 | 0 | 0.0000 | 0 | 0 | 0 |
| disturbance_feedback | True | True | 0.0072 | 0.0192 | 0.0313 | 0 | 0.0000 | 0 | 0 | 0 |
| disturbance_playback | True | True | 0.0079 | 0.0200 | 0.0305 | 0 | 0.0000 | 0 | 0 | 0 |
| isolated_150ms | True | True | 0.0034 | 0.0169 | 0.0302 | 1 | 0.0000 | 0 | 0 | 0 |
| isolated_failure | True | True | 0.0034 | 0.0169 | 0.0302 | 0 | 0.0000 | 0 | 0 | 1 |
| open_loop_measured | True | True | 0.0046 | 0.0177 | 0.0292 | 0 | 0.0000 | 0 | 0 | 0 |
| sync_0ms | True | True | 0.0028 | 0.0151 | 0.0291 | 0 | nan | 0 | 0 | 0 |
| sync_100ms | False | False | 0.1057 | 0.2801 | 0.6375 | 7 | nan | 0 | 0 | 0 |
| sync_150ms | False | False | 0.1521 | 0.3581 | 0.6780 | 8 | nan | 0 | 0 | 0 |
| sync_250ms | False | False | 0.3172 | 0.6293 | 0.7822 | 16 | nan | 0 | 58 | 0 |
| sync_25ms | True | True | 0.0048 | 0.0172 | 0.0292 | 0 | nan | 0 | 0 | 0 |
| sync_450ms | False | False | 0.5337 | 0.4236 | 0.5263 | 11 | nan | 0 | 130 | 0 |
| sync_60ms | True | True | 0.0092 | 0.0264 | 0.0325 | 0 | nan | 0 | 0 | 0 |
| sync_measured | True | True | 0.0051 | 0.0182 | 0.0302 | 0 | nan | 0 | 0 | 0 |

Tracking RMS units are metres, radians and metres/second. A completed run with fallback is not uninterrupted operation of the planned architecture.

## Lap times, control activity and tires

| case | lap_times | steering_total_variation | acceleration_total_variation | max_front_utilization | max_rear_utilization |
|---|---|---|---|---|---|
| async_measured | [16.2502531266936, 16.17375965544975] | 2.8312 | 1.7641 | 0.4983 | 0.3941 |
| codriver_0ms | [16.255707070946556, 16.172283232057538] | 2.9878 | 3.1207 | 0.4510 | 0.3667 |
| codriver_100ms | [16.254887979845503, 16.173458831318488] | 2.4051 | 1.5216 | 0.4390 | 0.3669 |
| codriver_150ms | [16.25659677424887, 16.158558945679545] | 2.5882 | 2.0069 | 0.4743 | 0.3702 |
| codriver_250ms | [16.301970533842603, 16.273787758122015] | 2.2062 | 1.2434 | 0.4871 | 0.3849 |
| codriver_25ms | [16.26026272837273, 16.173729595718534] | 2.3914 | 1.4945 | 0.4755 | 0.3710 |
| codriver_450ms | [16.298523320683433, 16.273786654263954] | 2.2052 | 1.2701 | 0.4871 | 0.3851 |
| codriver_60ms | [16.23988400623186, 16.173385815626894] | 2.6974 | 1.6556 | 0.5000 | 0.3987 |
| disturbance_feedback | [16.231735507538755, 16.173626272454836] | 2.6069 | 2.0374 | 0.4755 | 0.3710 |
| disturbance_playback | [16.218669147458698, 16.17683796021732] | 2.5493 | 2.0876 | 0.4768 | 0.3722 |
| isolated_150ms | [16.260230803203175, 16.1737297447587] | 2.3978 | 1.4950 | 0.4755 | 0.3710 |
| isolated_failure | [16.260248045700795, 16.173729664324863] | 2.3933 | 1.4946 | 0.4755 | 0.3710 |
| open_loop_measured | [16.2506600641381, 16.177557349697626] | 2.3446 | 1.5436 | 0.4755 | 0.3864 |
| sync_0ms | [16.245840092021883, 16.174987413174872] | 2.0208 | 1.3194 | 0.6134 | 0.3735 |
| sync_100ms | [] | 0.6677 | 7.6635 | 0.6385 | 0.3633 |
| sync_150ms | [] | 0.7595 | 11.3343 | 0.6385 | 0.3544 |
| sync_250ms | [] | 0.6000 | 12.4634 | 0.6385 | 0.4827 |
| sync_25ms | [16.268091306852167, 16.179959075279445] | 2.2397 | 1.4753 | 0.6385 | 0.3688 |
| sync_450ms | [] | 0.2000 | 2.4634 | 0.6385 | 0.3701 |
| sync_60ms | [16.286039065480264, 16.183363919244375] | 3.2111 | 2.7603 | 0.6385 | 0.4146 |
| sync_measured | [16.28051775717348, 16.17917246392388] | 2.2910 | 1.7594 | 0.6385 | 0.3763 |

## Reserve and update rates

| case | planner_effective_hz | codriver_effective_hz | codriver_computational_exceedances | reserve_min | reserve_mean | reserve_p95 | reserve_time_below_warning | reserve_time_below_critical | urgent_triggers |
|---|---|---|---|---|---|---|---|---|---|
| async_measured | 9.9611 | 100.0119 | 0.0000 | 0.2555 | 0.3490 | 0.3944 | 0.0000 | 0.0000 | 0.0000 |
| codriver_0ms | 9.9907 | 100.0000 | 0.0000 | 0.2830 | 0.3500 | 0.3950 | 0.0000 | 0.0000 | 0.0000 |
| codriver_100ms | 9.9599 | 100.0000 | 0.0000 | 0.2000 | 0.3495 | 0.3950 | 0.0000 | 0.0000 | 0.0000 |
| codriver_150ms | 4.9661 | 100.0000 | 0.0000 | 0.0670 | 0.2991 | 0.3899 | 0.1830 | 0.0000 | 0.0000 |
| codriver_250ms | 0.0614 | 100.0000 | 34.0000 | 0.0000 | 0.0028 | 3.638e-13 | 32.3800 | 32.1130 | 0.0000 |
| codriver_25ms | 9.9892 | 100.0154 | 0.0000 | 0.2750 | 0.3499 | 0.3950 | 0.0000 | 0.0000 | 0.0000 |
| codriver_450ms | 0.0307 | 100.0153 | 8.0000 | 0.0000 | 0.0025 | 3.638e-13 | 32.3750 | 32.2250 | 0.0000 |
| codriver_60ms | 9.9645 | 100.0154 | 0.0000 | 0.2400 | 0.3498 | 0.3950 | 0.0000 | 0.0000 | 0.0000 |
| disturbance_feedback | 9.9969 | 100.0000 | 0.0000 | 0.2750 | 0.3500 | 0.3950 | 0.0000 | 0.0000 | 1.0000 |
| disturbance_playback | 10.0000 | 100.0000 | 1.0000 | 0.2750 | 0.3500 | 0.3950 | 0.0000 | 0.0000 | 1.0000 |
| isolated_150ms | 9.9584 | 100.0154 | 0.0000 | 0.1750 | 0.3492 | 0.3950 | 0.0250 | 0.0000 | 0.0000 |
| isolated_failure | 9.9892 | 100.0154 | 3.0000 | 0.2000 | 0.3496 | 0.3950 | 0.0000 | 0.0000 | 0.0000 |
| open_loop_measured | 9.9599 | 100.0000 | 0.0000 | 0.2528 | 0.3494 | 0.3945 | 0.0000 | 0.0000 | 0.0000 |

Reserve statistics integrate its physical-time linear decay between events, including instantaneous handoff resets and zero reserve after exhaustion. Threshold durations are seconds, not event-count fractions.

Computational exceedances count measured callback durations above 10 ms. Injected planner-delay cases use zero simulated codriver latency, so these can coexist with zero simulated codriver misses. Fallback-case callback costs include the Task005 controller and must not be attributed solely to TVLQR.

## Trajectory tracking envelopes

| case | error | rms | p95 | max |
|---|---|---|---|---|
| async_measured | e_y | 0.0004 | 0.0005 | 0.0064 |
| async_measured | e_psi | 0.0035 | 0.0061 | 0.0369 |
| async_measured | vy | 0.0019 | 0.0035 | 0.0290 |
| async_measured | r | 0.0263 | 0.0484 | 0.3213 |
| codriver_0ms | e_y | 0.0004 | 0.0004 | 0.0050 |
| codriver_0ms | e_psi | 0.0030 | 0.0051 | 0.0340 |
| codriver_0ms | vy | 0.0017 | 0.0034 | 0.0289 |
| codriver_0ms | r | 0.0225 | 0.0461 | 0.3199 |
| codriver_100ms | e_y | 0.0004 | 0.0003 | 0.0087 |
| codriver_100ms | e_psi | 0.0028 | 0.0046 | 0.0351 |
| codriver_100ms | vy | 0.0017 | 0.0033 | 0.0289 |
| codriver_100ms | r | 0.0229 | 0.0448 | 0.3199 |
| codriver_150ms | e_y | 0.0010 | 0.0011 | 0.0121 |
| codriver_150ms | e_psi | 0.0042 | 0.0079 | 0.0403 |
| codriver_150ms | vy | 0.0025 | 0.0053 | 0.0289 |
| codriver_150ms | r | 0.0343 | 0.0784 | 0.3199 |
| codriver_250ms | e_y | 0.0078 | 0.0136 | 0.0157 |
| codriver_250ms | e_psi | 0.0275 | 0.0474 | 0.0483 |
| codriver_250ms | vy | 0.0136 | 0.0259 | 0.0289 |
| codriver_250ms | r | 0.2030 | 0.2882 | 0.3199 |
| codriver_25ms | e_y | 0.0003 | 0.0004 | 0.0050 |
| codriver_25ms | e_psi | 0.0028 | 0.0051 | 0.0356 |
| codriver_25ms | vy | 0.0018 | 0.0034 | 0.0289 |
| codriver_25ms | r | 0.0227 | 0.0470 | 0.3199 |
| codriver_450ms | e_y | 0.0087 | 0.0166 | 0.0167 |
| codriver_450ms | e_psi | 0.0283 | 0.0476 | 0.0483 |
| codriver_450ms | vy | 0.0148 | 0.0270 | 0.0289 |
| codriver_450ms | r | 0.2065 | 0.3284 | 0.3342 |
| codriver_60ms | e_y | 0.0004 | 0.0004 | 0.0062 |
| codriver_60ms | e_psi | 0.0031 | 0.0050 | 0.0336 |
| codriver_60ms | vy | 0.0018 | 0.0035 | 0.0289 |
| codriver_60ms | r | 0.0247 | 0.0470 | 0.3199 |
| disturbance_feedback | e_y | 0.0024 | 0.0004 | 0.0800 |
| disturbance_feedback | e_psi | 0.0031 | 0.0052 | 0.0406 |
| disturbance_feedback | vy | 0.0018 | 0.0034 | 0.0289 |
| disturbance_feedback | r | 0.0232 | 0.0473 | 0.3199 |
| disturbance_playback | e_y | 0.0025 | 0.0008 | 0.0800 |
| disturbance_playback | e_psi | 0.0037 | 0.0075 | 0.0401 |
| disturbance_playback | vy | 0.0018 | 0.0033 | 0.0321 |
| disturbance_playback | r | 0.0225 | 0.0378 | 0.3628 |
| isolated_150ms | e_y | 0.0003 | 0.0004 | 0.0050 |
| isolated_150ms | e_psi | 0.0028 | 0.0051 | 0.0356 |
| isolated_150ms | vy | 0.0018 | 0.0034 | 0.0289 |
| isolated_150ms | r | 0.0227 | 0.0470 | 0.3199 |
| isolated_failure | e_y | 0.0003 | 0.0004 | 0.0050 |
| isolated_failure | e_psi | 0.0028 | 0.0051 | 0.0356 |
| isolated_failure | vy | 0.0018 | 0.0034 | 0.0289 |
| isolated_failure | r | 0.0227 | 0.0470 | 0.3199 |
| open_loop_measured | e_y | 0.0004 | 0.0009 | 0.0056 |
| open_loop_measured | e_psi | 0.0036 | 0.0080 | 0.0327 |
| open_loop_measured | vy | 0.0017 | 0.0028 | 0.0321 |
| open_loop_measured | r | 0.0209 | 0.0312 | 0.3628 |

## Timing

| case | component | mean_ms | p50_ms | p95_ms | p99_ms | max_ms |
|---|---|---|---|---|---|---|
| async_measured | planner_solve_time | 21.0459 | 20.6686 | 22.4351 | 31.4170 | 34.7748 |
| async_measured | planner_preview_time | 4.6229 | 4.5584 | 5.1856 | 5.5670 | 8.0054 |
| async_measured | planner_prediction_time | 8.9315 | 8.6112 | 11.0182 | 13.0124 | 25.8379 |
| async_measured | planner_gain_time | 5.5736 | 5.5354 | 5.8353 | 6.8086 | 8.9606 |
| async_measured | planner_planner_total_time | 40.8767 | 40.0868 | 44.5926 | 53.9717 | 74.2822 |
| async_measured | planner_planner_cpu_time | 40.7458 | 40.0415 | 43.8337 | 53.7960 | 67.2240 |
| async_measured | codriver_interpolation_time | 0.0300 | 0.0285 | 0.0416 | 0.0549 | 0.2271 |
| async_measured | codriver_feedback_time | 0.0324 | 0.0313 | 0.0421 | 0.0568 | 0.2992 |
| async_measured | codriver_total_time | 1.0398 | 0.9691 | 1.1869 | 1.3366 | 7.0582 |
| async_measured | codriver_kernel_time | 0.0635 | 0.0610 | 0.0853 | 0.1131 | 0.3665 |
| async_measured | codriver_command_validation_time | 0.9700 | 0.8890 | 1.0990 | 1.2345 | 6.8378 |
| async_measured | codriver_cpu_time | 1.0368 | 0.9680 | 1.1860 | 1.3217 | 4.0110 |
| codriver_0ms | planner_solve_time | 20.6343 | 20.5296 | 21.3815 | 24.4166 | 31.1701 |
| codriver_0ms | planner_preview_time | 4.6434 | 4.5863 | 5.2519 | 5.4271 | 5.8913 |
| codriver_0ms | planner_prediction_time | 0.0365 | 0.0242 | 0.0263 | 0.0331 | 4.0409 |
| codriver_0ms | planner_gain_time | 5.5322 | 5.5162 | 5.8074 | 5.9189 | 6.4083 |
| codriver_0ms | planner_planner_total_time | 31.5213 | 31.3639 | 32.6771 | 36.0885 | 44.4124 |
| codriver_0ms | planner_planner_cpu_time | 31.5065 | 31.3640 | 32.5778 | 36.0786 | 44.3900 |
| codriver_0ms | codriver_interpolation_time | 0.0281 | 0.0257 | 0.0392 | 0.0464 | 0.1015 |
| codriver_0ms | codriver_feedback_time | 0.0300 | 0.0279 | 0.0391 | 0.0456 | 0.0990 |
| codriver_0ms | codriver_total_time | 1.0360 | 0.9740 | 1.1811 | 1.2844 | 2.6422 |
| codriver_0ms | codriver_kernel_time | 0.0594 | 0.0554 | 0.0798 | 0.0924 | 0.2027 |
| codriver_0ms | codriver_command_validation_time | 0.9714 | 0.8975 | 1.1038 | 1.2107 | 2.4634 |
| codriver_0ms | codriver_cpu_time | 1.0354 | 0.9740 | 1.1800 | 1.2787 | 2.6250 |
| codriver_100ms | planner_solve_time | 22.1860 | 20.6988 | 26.0109 | 42.2613 | 227.8978 |
| codriver_100ms | planner_preview_time | 4.8767 | 4.7055 | 5.7705 | 8.3280 | 33.8702 |
| codriver_100ms | planner_prediction_time | 21.6927 | 20.9370 | 25.7056 | 36.3674 | 180.5080 |
| codriver_100ms | planner_gain_time | 5.8463 | 5.5619 | 6.7891 | 10.1229 | 25.4734 |
| codriver_100ms | planner_planner_total_time | 55.6157 | 52.5026 | 64.7062 | 103.4465 | 559.6045 |
| codriver_100ms | planner_planner_cpu_time | 53.9149 | 52.4125 | 64.0743 | 81.6319 | 139.7670 |
| codriver_100ms | codriver_interpolation_time | 0.0321 | 0.0276 | 0.0492 | 0.0819 | 0.4219 |
| codriver_100ms | codriver_feedback_time | 0.0335 | 0.0301 | 0.0483 | 0.0735 | 1.1437 |
| codriver_100ms | codriver_total_time | 1.0789 | 1.0431 | 1.3296 | 1.9901 | 7.5878 |
| codriver_100ms | codriver_kernel_time | 0.0669 | 0.0593 | 0.0998 | 0.1537 | 1.5678 |
| codriver_100ms | codriver_command_validation_time | 1.0055 | 0.9576 | 1.2284 | 1.8331 | 7.0995 |
| codriver_100ms | codriver_cpu_time | 1.0703 | 1.0320 | 1.3140 | 1.8287 | 4.3540 |
| codriver_150ms | planner_solve_time | 20.5486 | 20.4665 | 21.1601 | 25.8231 | 28.7591 |
| codriver_150ms | planner_preview_time | 4.6486 | 4.5798 | 5.2929 | 5.3425 | 5.6669 |
| codriver_150ms | planner_prediction_time | 30.5521 | 30.3416 | 34.1315 | 34.5536 | 49.3540 |
| codriver_150ms | planner_gain_time | 5.6196 | 5.6040 | 5.8825 | 6.0729 | 6.2536 |
| codriver_150ms | planner_planner_total_time | 62.0121 | 61.7980 | 66.3230 | 69.6380 | 86.0537 |
| codriver_150ms | planner_planner_cpu_time | 61.9613 | 61.7985 | 66.2142 | 69.5723 | 80.0700 |
| codriver_150ms | codriver_interpolation_time | 0.0268 | 0.0241 | 0.0391 | 0.0465 | 2.0095 |
| codriver_150ms | codriver_feedback_time | 0.0282 | 0.0261 | 0.0391 | 0.0463 | 0.3509 |
| codriver_150ms | codriver_total_time | 1.0319 | 0.9543 | 1.1791 | 1.2732 | 6.2642 |
| codriver_150ms | codriver_kernel_time | 0.0561 | 0.0513 | 0.0791 | 0.0950 | 2.0840 |
| codriver_150ms | codriver_command_validation_time | 0.9712 | 0.8917 | 1.1015 | 1.1968 | 5.7126 |
| codriver_150ms | codriver_cpu_time | 1.0300 | 0.9540 | 1.1790 | 1.2666 | 3.9680 |
| codriver_250ms | planner_solve_time | 17.3546 | 17.3546 | 32.9738 | 34.3622 | 34.7093 |
| codriver_250ms | planner_preview_time | 2.6030 | 2.6030 | 4.9456 | 5.1539 | 5.2059 |
| codriver_250ms | planner_prediction_time | 2.1179 | 2.1179 | 4.0240 | 4.1934 | 4.2358 |
| codriver_250ms | planner_gain_time | 5.1224 | 5.1224 | 9.7326 | 10.1424 | 10.2449 |
| codriver_250ms | planner_planner_total_time | 27.7217 | 27.7217 | 52.6168 | 54.8297 | 55.3830 |
| codriver_250ms | planner_planner_cpu_time | 25.9790 | 25.9790 | 49.3106 | 51.3845 | 51.9030 |
| codriver_250ms | codriver_interpolation_time | 0.0013 | 0.0000 | 0.0000 | 0.0437 | 1.0458 |
| codriver_250ms | codriver_feedback_time | 2.1871 | 2.0161 | 3.2663 | 6.7527 | 91.4882 |
| codriver_250ms | codriver_total_time | 3.3101 | 3.0206 | 5.0039 | 10.0665 | 107.8658 |
| codriver_250ms | codriver_kernel_time | 2.1900 | 2.0174 | 3.2691 | 6.7568 | 91.4933 |
| codriver_250ms | codriver_command_validation_time | 1.1178 | 1.0069 | 1.5921 | 3.3129 | 105.7290 |
| codriver_250ms | codriver_cpu_time | 3.1221 | 3.0085 | 4.4450 | 6.5906 | 11.3810 |
| codriver_25ms | planner_solve_time | 20.7503 | 20.6320 | 21.2490 | 26.5215 | 31.3247 |
| codriver_25ms | planner_preview_time | 4.6298 | 4.5662 | 5.2241 | 5.3604 | 5.7728 |
| codriver_25ms | planner_prediction_time | 5.2019 | 4.9299 | 5.8822 | 6.1443 | 6.3918 |
| codriver_25ms | planner_gain_time | 5.5635 | 5.5572 | 5.7814 | 5.9571 | 7.1725 |
| codriver_25ms | planner_planner_total_time | 36.8258 | 36.4490 | 38.5528 | 43.1582 | 48.0487 |
| codriver_25ms | planner_planner_cpu_time | 36.8035 | 36.4325 | 38.5105 | 43.0794 | 48.0340 |
| codriver_25ms | codriver_interpolation_time | 0.0279 | 0.0252 | 0.0390 | 0.0453 | 0.1377 |
| codriver_25ms | codriver_feedback_time | 0.0298 | 0.0275 | 0.0387 | 0.0455 | 0.1271 |
| codriver_25ms | codriver_total_time | 1.0328 | 0.9697 | 1.1778 | 1.2586 | 1.7364 |
| codriver_25ms | codriver_kernel_time | 0.0588 | 0.0543 | 0.0790 | 0.0925 | 0.1728 |
| codriver_25ms | codriver_command_validation_time | 0.9686 | 0.8960 | 1.1000 | 1.1892 | 1.6622 |
| codriver_25ms | codriver_cpu_time | 1.0323 | 0.9700 | 1.1770 | 1.2490 | 1.4370 |
| codriver_450ms | planner_solve_time | 18.0156 | 18.0156 | 18.0156 | 18.0156 | 18.0156 |
| codriver_450ms | planner_preview_time | 3.2195 | 3.2195 | 3.2195 | 3.2195 | 3.2195 |
| codriver_450ms | planner_prediction_time | 2.5134 | 2.5134 | 2.5134 | 2.5134 | 2.5134 |
| codriver_450ms | planner_gain_time | 3.3329 | 3.3329 | 3.3329 | 3.3329 | 3.3329 |
| codriver_450ms | planner_planner_total_time | 27.5201 | 27.5201 | 27.5201 | 27.5201 | 27.5201 |
| codriver_450ms | planner_planner_cpu_time | 27.5200 | 27.5200 | 27.5200 | 27.5200 | 27.5200 |
| codriver_450ms | codriver_interpolation_time | 0.0002 | 0.0000 | 0.0000 | 0.0148 | 0.0323 |
| codriver_450ms | codriver_feedback_time | 1.4589 | 1.3541 | 1.9840 | 4.1200 | 81.1833 |
| codriver_450ms | codriver_total_time | 2.1959 | 2.0345 | 3.0150 | 5.8570 | 101.2959 |
| codriver_450ms | codriver_kernel_time | 1.4603 | 1.3550 | 1.9854 | 4.1244 | 81.1987 |
| codriver_450ms | codriver_command_validation_time | 0.7340 | 0.6761 | 0.9842 | 1.8946 | 45.8270 |
| codriver_450ms | codriver_cpu_time | 2.0939 | 2.0340 | 2.9322 | 4.5056 | 9.3500 |
| codriver_60ms | planner_solve_time | 20.8857 | 20.5658 | 22.2919 | 30.5766 | 33.1644 |
| codriver_60ms | planner_preview_time | 4.6346 | 4.5550 | 5.1901 | 5.7927 | 15.9835 |
| codriver_60ms | planner_prediction_time | 12.3222 | 11.8086 | 13.7899 | 15.1236 | 39.0047 |
| codriver_60ms | planner_gain_time | 5.4801 | 5.4286 | 5.6836 | 7.0248 | 10.4353 |
| codriver_60ms | planner_planner_total_time | 44.0064 | 43.1456 | 47.4099 | 59.4645 | 98.9507 |
| codriver_60ms | planner_planner_cpu_time | 43.8888 | 43.1260 | 47.2536 | 56.6677 | 80.8060 |
| codriver_60ms | codriver_interpolation_time | 0.0285 | 0.0255 | 0.0407 | 0.0505 | 0.1375 |
| codriver_60ms | codriver_feedback_time | 0.0301 | 0.0276 | 0.0396 | 0.0500 | 0.2155 |
| codriver_60ms | codriver_total_time | 1.0330 | 0.9663 | 1.1869 | 1.3762 | 4.0176 |
| codriver_60ms | codriver_kernel_time | 0.0598 | 0.0546 | 0.0812 | 0.1001 | 0.3098 |
| codriver_60ms | codriver_command_validation_time | 0.9678 | 0.8888 | 1.0992 | 1.2735 | 3.9627 |
| codriver_60ms | codriver_cpu_time | 1.0312 | 0.9660 | 1.1860 | 1.3497 | 2.1300 |
| disturbance_feedback | planner_solve_time | 13.6135 | 12.9757 | 16.5809 | 20.9015 | 26.3074 |
| disturbance_feedback | planner_preview_time | 2.9842 | 2.9470 | 3.5878 | 3.9335 | 4.1700 |
| disturbance_feedback | planner_prediction_time | 3.4331 | 3.3518 | 4.2452 | 4.5161 | 14.9853 |
| disturbance_feedback | planner_gain_time | 3.6035 | 3.3933 | 4.4588 | 5.5999 | 18.6733 |
| disturbance_feedback | planner_planner_total_time | 24.1117 | 23.1032 | 29.4760 | 34.5958 | 54.6791 |
| disturbance_feedback | planner_planner_cpu_time | 23.9434 | 23.0720 | 29.0496 | 34.0340 | 39.1460 |
| disturbance_feedback | codriver_interpolation_time | 0.0195 | 0.0160 | 0.0330 | 0.0419 | 0.1041 |
| disturbance_feedback | codriver_feedback_time | 0.0204 | 0.0172 | 0.0315 | 0.0377 | 0.4862 |
| disturbance_feedback | codriver_total_time | 0.6732 | 0.6589 | 0.8339 | 1.0079 | 4.2791 |
| disturbance_feedback | codriver_kernel_time | 0.0406 | 0.0339 | 0.0655 | 0.0806 | 0.5823 |
| disturbance_feedback | codriver_command_validation_time | 0.6288 | 0.6120 | 0.7687 | 0.9222 | 4.0872 |
| disturbance_feedback | codriver_cpu_time | 0.6700 | 0.6580 | 0.8290 | 0.9830 | 2.4870 |
| disturbance_playback | planner_solve_time | 15.4402 | 13.9117 | 21.5955 | 39.1382 | 64.9614 |
| disturbance_playback | planner_preview_time | 3.4254 | 3.1964 | 4.5308 | 7.1278 | 16.3416 |
| disturbance_playback | planner_prediction_time | 3.7644 | 3.5702 | 4.9761 | 7.6649 | 13.2770 |
| disturbance_playback | planner_gain_time | 4.0594 | 3.6010 | 5.8549 | 9.9652 | 16.5851 |
| disturbance_playback | planner_planner_total_time | 27.2478 | 24.8954 | 37.6389 | 64.0388 | 100.8015 |
| disturbance_playback | planner_planner_cpu_time | 26.5909 | 24.8100 | 34.9115 | 49.9023 | 69.5250 |
| disturbance_playback | codriver_interpolation_time | 0.0242 | 0.0180 | 0.0417 | 0.0839 | 1.6320 |
| disturbance_playback | codriver_feedback_time | 0.0168 | 0.0144 | 0.0236 | 0.0599 | 0.5038 |
| disturbance_playback | codriver_total_time | 0.7498 | 0.7070 | 1.0288 | 1.6188 | 12.9211 |
| disturbance_playback | codriver_kernel_time | 0.0418 | 0.0331 | 0.0662 | 0.1447 | 1.7158 |
| disturbance_playback | codriver_command_validation_time | 0.7033 | 0.6719 | 0.9494 | 1.4436 | 12.4630 |
| disturbance_playback | codriver_cpu_time | 0.7364 | 0.7070 | 0.9891 | 1.4026 | 2.9400 |
| isolated_150ms | planner_solve_time | 13.9243 | 12.7548 | 16.8493 | 29.5550 | 79.5599 |
| isolated_150ms | planner_preview_time | 3.0427 | 2.8805 | 3.9807 | 5.0234 | 5.8279 |
| isolated_150ms | planner_prediction_time | 3.4154 | 3.2540 | 4.5856 | 6.1030 | 7.4712 |
| isolated_150ms | planner_gain_time | 3.5819 | 3.3541 | 4.3340 | 5.7849 | 17.1264 |
| isolated_150ms | planner_planner_total_time | 24.4221 | 22.7307 | 29.7723 | 45.6149 | 93.6168 |
| isolated_150ms | planner_planner_cpu_time | 23.9239 | 22.7240 | 29.5352 | 38.0107 | 52.1070 |
| isolated_150ms | codriver_interpolation_time | 0.0190 | 0.0154 | 0.0337 | 0.0466 | 0.2442 |
| isolated_150ms | codriver_feedback_time | 0.0200 | 0.0168 | 0.0319 | 0.0416 | 0.6658 |
| isolated_150ms | codriver_total_time | 0.6835 | 0.6230 | 0.8963 | 1.2818 | 6.6635 |
| isolated_150ms | codriver_kernel_time | 0.0397 | 0.0330 | 0.0666 | 0.0925 | 0.7743 |
| isolated_150ms | codriver_command_validation_time | 0.6402 | 0.5750 | 0.8260 | 1.1434 | 5.8651 |
| isolated_150ms | codriver_cpu_time | 0.6777 | 0.6220 | 0.8920 | 1.1804 | 3.2540 |
| isolated_failure | planner_solve_time | 18.5558 | 15.5685 | 25.0842 | 38.0122 | 575.5863 |
| isolated_failure | planner_preview_time | 3.8840 | 3.4746 | 5.7704 | 13.1292 | 30.2148 |
| isolated_failure | planner_prediction_time | 4.5001 | 3.9574 | 6.5463 | 10.0544 | 73.0828 |
| isolated_failure | planner_gain_time | 5.0443 | 4.0731 | 7.0017 | 35.3588 | 72.1925 |
| isolated_failure | planner_planner_total_time | 32.6996 | 27.5487 | 45.0369 | 90.4767 | 690.8940 |
| isolated_failure | planner_planner_cpu_time | 29.4494 | 27.3225 | 43.2444 | 61.1503 | 91.2940 |
| isolated_failure | codriver_interpolation_time | 0.0302 | 0.0244 | 0.0466 | 0.1189 | 1.5455 |
| isolated_failure | codriver_feedback_time | 0.0291 | 0.0255 | 0.0446 | 0.0997 | 1.2563 |
| isolated_failure | codriver_total_time | 0.8757 | 0.7769 | 1.2509 | 2.9198 | 36.5705 |
| isolated_failure | codriver_kernel_time | 0.0603 | 0.0510 | 0.0955 | 0.2200 | 2.5794 |
| isolated_failure | codriver_command_validation_time | 0.8094 | 0.7193 | 1.1372 | 2.6754 | 36.4407 |
| isolated_failure | codriver_cpu_time | 0.8276 | 0.7755 | 1.1848 | 1.9794 | 3.5050 |
| open_loop_measured | planner_solve_time | 20.7144 | 20.5833 | 21.6482 | 24.5561 | 31.2347 |
| open_loop_measured | planner_preview_time | 4.5925 | 4.5364 | 5.1853 | 5.2558 | 5.3424 |
| open_loop_measured | planner_prediction_time | 8.7564 | 8.5085 | 10.4241 | 11.2846 | 11.3678 |
| open_loop_measured | planner_gain_time | 5.5641 | 5.5604 | 5.8274 | 5.9349 | 5.9995 |
| open_loop_measured | planner_planner_total_time | 40.3077 | 39.9722 | 42.9938 | 46.8595 | 49.6540 |
| open_loop_measured | planner_planner_cpu_time | 40.2763 | 39.9320 | 42.9233 | 46.6939 | 49.6370 |
| open_loop_measured | codriver_interpolation_time | 0.0284 | 0.0258 | 0.0393 | 0.0464 | 0.1429 |
| open_loop_measured | codriver_feedback_time | 0.0219 | 0.0212 | 0.0250 | 0.0301 | 0.1602 |
| open_loop_measured | codriver_total_time | 1.0262 | 0.9628 | 1.1648 | 1.2422 | 1.9366 |
| open_loop_measured | codriver_kernel_time | 0.0514 | 0.0488 | 0.0654 | 0.0765 | 0.3047 |
| open_loop_measured | codriver_command_validation_time | 0.9689 | 0.8980 | 1.0982 | 1.1770 | 1.7450 |
| open_loop_measured | codriver_cpu_time | 1.0257 | 0.9620 | 1.1649 | 1.2316 | 1.6920 |

## Cpu Memory

| case | final_rss_mib | peak_rss_mib | construction_rss_delta_mib | planner_core_demand | codriver_core_demand | total_core_demand |
|---|---|---|---|---|---|---|
| async_measured | 145.4531 | 180.0625 | 9.5781 | 0.4071 | 0.1037 | 0.5108 |
| codriver_0ms | 213.1094 | 213.3281 | 16.9375 | 0.3148 | 0.1035 | 0.4183 |
| codriver_100ms | 110.8906 | 187.5938 | 16.9531 | 0.5386 | 0.1070 | 0.6457 |
| codriver_150ms | 213.0469 | 213.0469 | 16.9375 | 0.3096 | 0.1030 | 0.4126 |
| codriver_250ms | 79.5781 | 180.6719 | 15.8594 | 0.0016 | 0.3122 | 0.3138 |
| codriver_25ms | 214.5469 | 214.8438 | 16.7656 | 0.3676 | 0.1032 | 0.4709 |
| codriver_450ms | 86.9531 | 174.2812 | 17.1406 | 0.0008 | 0.2094 | 0.2103 |
| codriver_60ms | 180.1094 | 188.3438 | 16.9219 | 0.4387 | 0.1031 | 0.5418 |
| disturbance_feedback | 136.2500 | 172.0469 | 16.7500 | 0.2401 | 0.0670 | 0.3071 |
| disturbance_playback | 121.1875 | 179.6719 | 17.2344 | 0.2659 | 0.0736 | 0.3395 |
| isolated_150ms | 128.6562 | 187.2500 | 17.0000 | 0.2382 | 0.0678 | 0.3060 |
| isolated_failure | 107.8750 | 179.9062 | 15.5625 | 0.2942 | 0.0828 | 0.3769 |
| open_loop_measured | 146.7812 | 193.9688 | 16.9688 | 0.4024 | 0.1026 | 0.5050 |

## Handoff Statistics

| case | accepted | component | rms | p95_abs | max_abs |
|---|---|---|---|---|---|
| async_measured | True | vx | 0.0001 | 1.207e-05 | 0.0023 |
| async_measured | True | vy | 0.0005 | 4.615e-05 | 0.0037 |
| async_measured | True | r | 0.0070 | 0.0004 | 0.0509 |
| async_measured | True | e_psi | 0.0007 | 0.0003 | 0.0112 |
| async_measured | True | s_abs | 2.024e-05 | 5.343e-06 | 0.0003 |
| async_measured | True | e_y | 3.661e-05 | 1.560e-05 | 0.0004 |
| codriver_0ms | True | vx | 8.431e-05 | 0.0000 | 0.0015 |
| codriver_0ms | True | vy | 0.0001 | 0.0000 | 0.0026 |
| codriver_0ms | True | r | 0.0018 | 0.0000 | 0.0326 |
| codriver_0ms | True | e_psi | 1.712e-05 | 0.0000 | 0.0003 |
| codriver_0ms | True | s_abs | 1.126e-06 | 0.0000 | 2.027e-05 |
| codriver_0ms | True | e_y | 1.533e-06 | 0.0000 | 2.759e-05 |
| codriver_100ms | True | vx | 0.0005 | 0.0001 | 0.0079 |
| codriver_100ms | True | vy | 0.0005 | 0.0003 | 0.0043 |
| codriver_100ms | True | r | 0.0085 | 0.0030 | 0.0716 |
| codriver_100ms | True | e_psi | 0.0011 | 0.0002 | 0.0177 |
| codriver_100ms | True | s_abs | 2.056e-05 | 1.892e-05 | 0.0003 |
| codriver_100ms | True | e_y | 0.0002 | 0.0001 | 0.0024 |
| codriver_150ms | True | vx | 0.0008 | 3.497e-05 | 0.0104 |
| codriver_150ms | True | vy | 0.0003 | 0.0002 | 0.0040 |
| codriver_150ms | True | r | 0.0077 | 0.0030 | 0.0870 |
| codriver_150ms | True | e_psi | 0.0023 | 0.0004 | 0.0291 |
| codriver_150ms | True | s_abs | 0.0001 | 3.414e-06 | 0.0013 |
| codriver_150ms | True | e_y | 0.0005 | 4.844e-05 | 0.0062 |
| codriver_250ms | True | vx | 0.0097 | 0.0097 | 0.0097 |
| codriver_250ms | True | vy | 0.0183 | 0.0183 | 0.0183 |
| codriver_250ms | True | r | 0.2050 | 0.2050 | 0.2050 |
| codriver_250ms | True | e_psi | 0.0222 | 0.0222 | 0.0222 |
| codriver_250ms | True | s_abs | 0.0035 | 0.0035 | 0.0035 |
| codriver_250ms | True | e_y | 0.0114 | 0.0114 | 0.0114 |
| codriver_25ms | True | vx | 2.596e-05 | 8.119e-06 | 0.0004 |
| codriver_25ms | True | vy | 0.0004 | 8.289e-05 | 0.0033 |
| codriver_25ms | True | r | 0.0045 | 0.0014 | 0.0421 |
| codriver_25ms | True | e_psi | 0.0002 | 5.363e-05 | 0.0034 |
| codriver_25ms | True | s_abs | 8.908e-06 | 6.901e-07 | 0.0002 |
| codriver_25ms | True | e_y | 6.397e-06 | 3.073e-06 | 5.828e-05 |
| codriver_60ms | True | vx | 0.0002 | 9.590e-06 | 0.0040 |
| codriver_60ms | True | vy | 0.0006 | 7.432e-05 | 0.0043 |
| codriver_60ms | True | r | 0.0095 | 0.0012 | 0.0609 |
| codriver_60ms | True | e_psi | 0.0009 | 0.0002 | 0.0152 |
| codriver_60ms | True | s_abs | 1.943e-05 | 1.554e-06 | 0.0003 |
| codriver_60ms | True | e_y | 6.343e-05 | 7.262e-06 | 0.0008 |
| disturbance_feedback | True | vx | 2.597e-05 | 8.248e-06 | 0.0004 |
| disturbance_feedback | True | vy | 0.0004 | 8.319e-05 | 0.0033 |
| disturbance_feedback | True | r | 0.0051 | 0.0014 | 0.0424 |
| disturbance_feedback | True | e_psi | 0.0002 | 5.591e-05 | 0.0034 |
| disturbance_feedback | True | s_abs | 8.909e-06 | 6.950e-07 | 0.0002 |
| disturbance_feedback | True | e_y | 7.252e-06 | 3.094e-06 | 6.021e-05 |
| disturbance_playback | True | vx | 1.097e-05 | 4.441e-16 | 0.0001 |
| disturbance_playback | True | vy | 0.0003 | 1.249e-16 | 0.0032 |
| disturbance_playback | True | r | 0.0041 | 1.776e-15 | 0.0417 |
| disturbance_playback | True | e_psi | 0.0002 | 0.0001 | 0.0034 |
| disturbance_playback | True | s_abs | 7.463e-06 | 7.530e-07 | 0.0001 |
| disturbance_playback | True | e_y | 6.735e-06 | 2.491e-06 | 5.639e-05 |
| isolated_150ms | True | vx | 2.604e-05 | 8.228e-06 | 0.0004 |
| isolated_150ms | True | vy | 0.0004 | 8.361e-05 | 0.0033 |
| isolated_150ms | True | r | 0.0045 | 0.0014 | 0.0421 |
| isolated_150ms | True | e_psi | 0.0002 | 5.427e-05 | 0.0034 |
| isolated_150ms | True | s_abs | 8.922e-06 | 6.992e-07 | 0.0002 |
| isolated_150ms | True | e_y | 6.810e-06 | 3.139e-06 | 5.828e-05 |
| isolated_failure | True | vx | 2.600e-05 | 8.119e-06 | 0.0004 |
| isolated_failure | True | vy | 0.0004 | 8.293e-05 | 0.0033 |
| isolated_failure | True | r | 0.0045 | 0.0014 | 0.0421 |
| isolated_failure | True | e_psi | 0.0002 | 5.363e-05 | 0.0034 |
| isolated_failure | True | s_abs | 8.922e-06 | 6.920e-07 | 0.0002 |
| isolated_failure | True | e_y | 6.407e-06 | 3.074e-06 | 5.828e-05 |
| open_loop_measured | True | vx | 0.0002 | 1.392e-05 | 0.0042 |
| open_loop_measured | True | vy | 0.0003 | 0.0001 | 0.0036 |
| open_loop_measured | True | r | 0.0047 | 0.0016 | 0.0504 |
| open_loop_measured | True | e_psi | 0.0007 | 0.0003 | 0.0122 |
| open_loop_measured | True | s_abs | 1.409e-05 | 3.614e-06 | 0.0003 |
| open_loop_measured | True | e_y | 3.461e-05 | 2.111e-05 | 0.0005 |

## Prediction Statistics

| case | component | rms | p95_abs | max_abs |
|---|---|---|---|---|
| async_measured | vx | 0.0005 | 0.0002 | 0.0084 |
| async_measured | vy | 0.0010 | 0.0001 | 0.0133 |
| async_measured | r | 0.0116 | 0.0028 | 0.1382 |
| async_measured | e_psi | 0.0012 | 0.0002 | 0.0197 |
| async_measured | s_abs | 0.0070 | 0.0083 | 0.0688 |
| async_measured | e_y | 0.0002 | 3.587e-05 | 0.0033 |
| codriver_0ms | vx | 0.0004 | 0.0000 | 0.0077 |
| codriver_0ms | vy | 6.113e-05 | 0.0000 | 0.0011 |
| codriver_0ms | r | 0.0008 | 0.0000 | 0.0141 |
| codriver_0ms | e_psi | 0.0008 | 0.0000 | 0.0139 |
| codriver_0ms | s_abs | 0.0018 | 0.0000 | 0.0330 |
| codriver_0ms | e_y | 9.108e-05 | 0.0000 | 0.0016 |
| codriver_100ms | vx | 0.0015 | 0.0001 | 0.0262 |
| codriver_100ms | vy | 0.0022 | 0.0003 | 0.0393 |
| codriver_100ms | r | 0.0269 | 0.0030 | 0.4648 |
| codriver_100ms | e_psi | 0.0025 | 0.0002 | 0.0432 |
| codriver_100ms | s_abs | 0.0089 | 1.892e-05 | 0.1591 |
| codriver_100ms | e_y | 0.0006 | 0.0001 | 0.0113 |
| codriver_150ms | vx | 0.0024 | 3.497e-05 | 0.0307 |
| codriver_150ms | vy | 0.0048 | 0.0002 | 0.0614 |
| codriver_150ms | r | 0.0611 | 0.0030 | 0.7735 |
| codriver_150ms | e_psi | 0.0035 | 0.0004 | 0.0444 |
| codriver_150ms | s_abs | 0.0200 | 3.414e-06 | 0.2536 |
| codriver_150ms | e_y | 0.0015 | 4.844e-05 | 0.0185 |
| codriver_250ms | vx | 0.0254 | 0.0280 | 0.0283 |
| codriver_250ms | vy | 0.1007 | 0.1019 | 0.1021 |
| codriver_250ms | r | 1.4677 | 1.5392 | 1.5474 |
| codriver_250ms | e_psi | 0.0417 | 0.0556 | 0.0580 |
| codriver_250ms | s_abs | 0.4640 | 0.4826 | 0.4847 |
| codriver_250ms | e_y | 0.0307 | 0.0346 | 0.0351 |
| codriver_25ms | vx | 7.590e-05 | 8.119e-06 | 0.0013 |
| codriver_25ms | vy | 0.0005 | 8.289e-05 | 0.0055 |
| codriver_25ms | r | 0.0055 | 0.0014 | 0.0583 |
| codriver_25ms | e_psi | 0.0003 | 5.363e-05 | 0.0058 |
| codriver_25ms | s_abs | 0.0009 | 6.901e-07 | 0.0155 |
| codriver_25ms | e_y | 4.788e-05 | 3.073e-06 | 0.0009 |
| codriver_450ms | vx | 0.0164 | 0.0164 | 0.0164 |
| codriver_450ms | vy | 0.0189 | 0.0189 | 0.0189 |
| codriver_450ms | r | 0.3214 | 0.3214 | 0.3214 |
| codriver_450ms | e_psi | 0.1307 | 0.1307 | 0.1307 |
| codriver_450ms | s_abs | 0.8269 | 0.8269 | 0.8269 |
| codriver_450ms | e_y | 0.0015 | 0.0015 | 0.0015 |
| codriver_60ms | vx | 0.0008 | 9.590e-06 | 0.0135 |
| codriver_60ms | vy | 0.0013 | 7.432e-05 | 0.0207 |
| codriver_60ms | r | 0.0155 | 0.0012 | 0.2263 |
| codriver_60ms | e_psi | 0.0016 | 0.0002 | 0.0284 |
| codriver_60ms | s_abs | 0.0046 | 1.554e-06 | 0.0829 |
| codriver_60ms | e_y | 0.0003 | 7.262e-06 | 0.0054 |
| disturbance_feedback | vx | 7.590e-05 | 8.248e-06 | 0.0013 |
| disturbance_feedback | vy | 0.0005 | 8.319e-05 | 0.0055 |
| disturbance_feedback | r | 0.0060 | 0.0014 | 0.0583 |
| disturbance_feedback | e_psi | 0.0003 | 5.591e-05 | 0.0058 |
| disturbance_feedback | s_abs | 0.0009 | 6.950e-07 | 0.0155 |
| disturbance_feedback | e_y | 4.800e-05 | 3.094e-06 | 0.0009 |
| disturbance_playback | vx | 7.365e-05 | 4.441e-16 | 0.0013 |
| disturbance_playback | vy | 0.0004 | 1.249e-16 | 0.0057 |
| disturbance_playback | r | 0.0053 | 1.776e-15 | 0.0632 |
| disturbance_playback | e_psi | 0.0003 | 0.0001 | 0.0055 |
| disturbance_playback | s_abs | 0.0009 | 7.530e-07 | 0.0155 |
| disturbance_playback | e_y | 4.771e-05 | 2.491e-06 | 0.0009 |
| isolated_150ms | vx | 7.606e-05 | 8.228e-06 | 0.0013 |
| isolated_150ms | vy | 0.0005 | 8.361e-05 | 0.0055 |
| isolated_150ms | r | 0.0056 | 0.0014 | 0.0583 |
| isolated_150ms | e_psi | 0.0003 | 5.427e-05 | 0.0058 |
| isolated_150ms | s_abs | 0.0139 | 6.992e-07 | 0.2502 |
| isolated_150ms | e_y | 4.798e-05 | 3.139e-06 | 0.0009 |
| isolated_failure | vx | 7.590e-05 | 8.119e-06 | 0.0013 |
| isolated_failure | vy | 0.0005 | 8.288e-05 | 0.0055 |
| isolated_failure | r | 0.0055 | 0.0014 | 0.0583 |
| isolated_failure | e_psi | 0.0003 | 5.363e-05 | 0.0058 |
| isolated_failure | s_abs | 0.0009 | 6.901e-07 | 0.0155 |
| isolated_failure | e_y | 4.788e-05 | 3.073e-06 | 0.0009 |
| open_loop_measured | vx | 0.0005 | 0.0002 | 0.0092 |
| open_loop_measured | vy | 0.0009 | 5.471e-05 | 0.0150 |
| open_loop_measured | r | 0.0099 | 0.0009 | 0.1645 |
| open_loop_measured | e_psi | 0.0011 | 0.0002 | 0.0199 |
| open_loop_measured | s_abs | 0.0041 | 0.0050 | 0.0582 |
| open_loop_measured | e_y | 0.0002 | 5.312e-05 | 0.0036 |

## Handoff Input Jumps

| case | accepted | rejected | max_abs_nominal_delta_jump | max_abs_nominal_acceleration_jump |
|---|---|---|---|---|
| async_measured | 323 | 0 | 0.0952 | 0.1172 |
| codriver_0ms | 324 | 0 | 0.0900 | 0.0984 |
| codriver_100ms | 323 | 0 | 0.0998 | 0.1263 |
| codriver_150ms | 161 | 0 | 0.0991 | 0.0533 |
| codriver_250ms | 1 | 0 | 0.0852 | 0.0074 |
| codriver_25ms | 324 | 0 | 0.0995 | 0.1231 |
| codriver_450ms | 0 | 1 | nan | nan |
| codriver_60ms | 323 | 0 | 0.1001 | 0.1432 |
| disturbance_feedback | 324 | 0 | 0.0995 | 0.2447 |
| disturbance_playback | 324 | 0 | 0.1000 | 0.2447 |
| isolated_150ms | 323 | 0 | 0.0995 | 0.1231 |
| isolated_failure | 323 | 0 | 0.0995 | 0.1231 |
| open_loop_measured | 323 | 0 | 0.1000 | 0.1255 |

## Disturbance Recovery

| case | trajectory_settling_seconds | centerline_settling_seconds | post5s_lateral_tracking_rms | post5s_max_abs_steering_correction | urgent_triggers |
|---|---|---|---|---|---|
| disturbance_feedback | 0.0300 | 0.4500 | 0.0050 | 0.0491 | 1 |
| disturbance_playback | 0.0300 | 0.4500 | 0.0050 | 0.0000 | 1 |

CPU-core demand excludes simulation integration, logging and transport. Codriver total includes command validation; its interpolation/feedback kernel is reported separately. RSS includes imports, NLP, gains and logs; it is not isolated tracker allocation.

Prediction error compares intended-handoff forecast with actual-completion state, so it includes delay-estimation error. Handoff mismatch uses aligned nominal state.

Disturbance settling is a diagnostic measured from the perturbation to the first 100 consecutive codriver samples within 0.01 m lateral and 0.05 rad heading trajectory error, searched in the following five seconds. Replanning changes that reference; this is not an isolated fixed-reference disturbance-rejection claim.

Centerline settling separately requires physical lateral error within 0.02 m and heading error within 0.05 rad continuously for one second, within the same window.

## Reproduction

Use scripts/run_async_planner_tracker.py run/suite/analyze/audit. Select fresh case names or a fresh output directory; existing evidence is never silently overwritten.
