# Task 007A measured results

Errors use SI units. Primary comparison uses complete laps 2 and 3; lap 1 is the s=1m rolling-launch transient. Zero/injected runs are supporting checks.

## Lap metrics

| case | lap | phase | racing_lateral_error_rms | racing_heading_error_rms | racing_speed_error_rms | racing_lateral_error_max_abs |
|---|---|---|---|---|---|---|
| injected | 1 | startup_transient | 0.0063 | 0.0157 | 0.1354 | 0.0373 |
| measured | 1 | startup_transient | 0.0062 | 0.0157 | 0.1359 | 0.0378 |
| measured | 2 | comparable | 0.0063 | 0.0157 | 0.1359 | 0.0375 |
| measured | 3 | comparable | 0.0065 | 0.0158 | 0.1360 | 0.0376 |
| zero | 1 | startup_transient | 0.0062 | 0.0155 | 0.1381 | 0.0381 |

## Comparable-lap sector errors

| sector | racing_lateral_error_rms | racing_heading_error_rms | racing_speed_error_rms | racing_lateral_error_max_abs |
|---|---|---|---|---|
| long_straight | 0.0040 | 0.0087 | 0.1656 | 0.0211 |
| hairpin | 0.0181 | 0.0516 | 0.2173 | 0.0376 |
| acceleration_zone | 0.0041 | 0.0019 | 0.1830 | 0.0057 |
| medium_corner | 0.0043 | 0.0082 | 0.1475 | 0.0081 |
| fast_sweeper | 0.0008 | 0.0061 | 0.0435 | 0.0041 |
| direction_change | 0.0022 | 0.0042 | 0.1383 | 0.0036 |
| second_straight | 0.0009 | 0.0030 | 0.0766 | 0.0024 |
| technical_section | 0.0082 | 0.0147 | 0.1524 | 0.0284 |
| return_complex | 0.0028 | 0.0053 | 0.1109 | 0.0095 |

## Sector actuator, tire and corridor use

| sector | delta_max_abs | steering_rate_utilization_max_abs | acceleration_max | braking_min | front_utilization_max_abs | rear_utilization_max_abs | boundary_clearance_min | margin_activity_seconds |
|---|---|---|---|---|---|---|---|---|
| long_straight | 0.0922 | 1.0000 | 0.2819 | -0.7850 | 0.1670 | 0.1588 | 0.4292 | 0.0000 |
| hairpin | 0.3751 | 1.0000 | 0.3051 | -1.1267 | 0.3824 | 0.3012 | 0.3366 | 0.0000 |
| acceleration_zone | 0.0487 | 0.4420 | 0.3505 | -0.0519 | 0.0987 | 0.0969 | 0.4343 | 0.0000 |
| medium_corner | 0.1303 | 1.0000 | 0.3405 | -0.3833 | 0.2328 | 0.2143 | 0.3351 | 0.0000 |
| fast_sweeper | 0.0448 | 0.5500 | 0.2644 | -0.2015 | 0.1313 | 0.1309 | 0.3403 | 0.0000 |
| direction_change | 0.0945 | 1.0000 | 0.3018 | -0.4780 | 0.2241 | 0.2066 | 0.4549 | 0.0000 |
| second_straight | 0.0813 | 0.5856 | 0.0172 | -0.4266 | 0.2012 | 0.1954 | 0.5476 | 0.0000 |
| technical_section | 0.3232 | 1.0000 | 0.3469 | -0.6567 | 0.3804 | 0.3013 | 0.3475 | 0.0000 |
| return_complex | 0.1019 | 1.0000 | 0.2821 | -0.4583 | 0.2325 | 0.2055 | 0.3350 | 0.0000 |

## Sector timing and reserve

| sector | solve_time_mean | solve_time_p95 | planner_total_time_mean | planner_total_time_p95 | codriver_time_mean | codriver_time_p95 | reserve_min |
|---|---|---|---|---|---|---|---|
| long_straight | 0.0110 | 0.0141 | 0.0228 | 0.0265 | 0.0008 | 0.0009 | 0.2969 |
| hairpin | 0.0147 | 0.0175 | 0.0277 | 0.0305 | 0.0008 | 0.0009 | 0.2976 |
| acceleration_zone | 0.0125 | 0.0131 | 0.0255 | 0.0263 | 0.0010 | 0.0009 | 0.2994 |
| medium_corner | 0.0121 | 0.0132 | 0.0247 | 0.0265 | 0.0009 | 0.0010 | 0.2987 |
| fast_sweeper | 0.0105 | 0.0109 | 0.0218 | 0.0228 | 0.0008 | 0.0009 | 0.2953 |
| direction_change | 0.0109 | 0.0119 | 0.0231 | 0.0247 | 0.0008 | 0.0009 | 0.2969 |
| second_straight | 0.0108 | 0.0113 | 0.0233 | 0.0244 | 0.0008 | 0.0009 | 0.2318 |
| technical_section | 0.0124 | 0.0148 | 0.0267 | 0.0339 | 0.0010 | 0.0012 | 0.2938 |
| return_complex | 0.0115 | 0.0120 | 0.0241 | 0.0249 | 0.0009 | 0.0010 | 0.1514 |

Sector timing values interpolate logged work onto physical state times and use time-weighted means; p95 uses samples. Raw timing distributions follow.

## Raw measured timing distributions, milliseconds

| component | measurement | mean | p50 | p95 | p99 | max | std |
|---|---|---|---|---|---|---|---|
| planner | solve_time | 11.6468 | 10.8049 | 14.6766 | 17.9346 | 61.2505 | 2.6938 |
| planner | preview_time | 4.1440 | 4.0541 | 5.7988 | 6.2225 | 21.3336 | 0.7602 |
| planner | prediction_time | 4.6067 | 4.2647 | 7.4527 | 8.5950 | 23.2529 | 1.2675 |
| planner | gain_time | 3.4637 | 3.3757 | 3.5916 | 4.1539 | 42.2618 | 1.1460 |
| planner | planner_total_time | 24.3246 | 23.0963 | 31.1507 | 34.8501 | 105.3560 | 4.6160 |
| planner | planner_cpu_time | 24.1305 | 23.0710 | 31.1082 | 34.4688 | 55.0590 | 3.0435 |
| codriver | interpolation_time | 0.0186 | 0.0173 | 0.0270 | 0.0353 | 0.2087 | 0.0050 |
| codriver | feedback_time | 0.0202 | 0.0190 | 0.0276 | 0.0339 | 0.4365 | 0.0059 |
| codriver | command_validation_time | 0.8152 | 0.7979 | 1.1500 | 1.2028 | 26.8793 | 0.2817 |
| codriver | kernel_time | 0.0397 | 0.0372 | 0.0552 | 0.0694 | 0.6468 | 0.0105 |
| codriver | total_time | 0.8588 | 0.8387 | 1.1915 | 1.2503 | 27.1045 | 0.2853 |
| codriver | cpu_time | 0.8545 | 0.8390 | 1.1890 | 1.2420 | 3.3460 | 0.1455 |

## Candidate supervisor signal ranges (observations only)

| signal | min | max |
|---|---|---|
| abs_trajectory_ey | 0.0000 | 0.0051 |
| abs_trajectory_epsi | 0.0000 | 0.0439 |
| trajectory_vy_error | -0.0096 | 0.0115 |
| trajectory_r_error | -0.1153 | 0.1362 |
| centerline_curvature | -1.0933 | 1.0271 |
| racing_curvature | -1.2136 | 0.9185 |
| lateral_acceleration | -3.2214 | 3.1569 |
| steering_utilization | 2.613e-05 | 0.9533 |
| steering_rate_utilization | 0.0000 | 1.0000 |
| front_utilization | 0.0003 | 0.3827 |
| rear_utilization | 0.0003 | 0.3051 |
| trajectory_age | 0.0000 | 0.2709 |
| reserve | 0.1514 | 0.4000 |

Lateral acceleration estimates d(vy)/dt+vx*r by finite differences. No switching. Difficulty logs also retain completed-plan lateral/heading prediction errors.

## Local APEX-packet tracking

| channel | rms | p95 | max |
|---|---|---|---|
| e_y | 0.0004 | 0.0007 | 0.0051 |
| e_psi | 0.0028 | 0.0041 | 0.0439 |
| vy | 0.0013 | 0.0026 | 0.0115 |
| r | 0.0169 | 0.0330 | 0.1362 |

## Offline reference-state model residual

At 310 sampled nominal points, propagate the independent nonlinear plant for 10ms with the geometric nominal state/feedforward and compare with the next supplied nominal. Maximum absolute residuals by canonical channel:

| vx | vy | r | e_psi | s_abs | e_y |
|---|---|---|---|---|---|
| 0.0067 | 0.0417 | 0.0230 | 0.0001 | 4.112e-05 | 0.0002 |

These diagnose the approximation, not optimizer violations. The reference is not claimed dynamically exact; APEX still enforces its local shooting dynamics.

## Combined turning and longitudinal demand

| braking_while_turning_seconds | acceleration_while_turning_seconds |
|---|---|
| 37.8544 | 45.4758 |

Thresholds: absolute estimated lateral acceleration >0.3 m/s² and absolute a_cmd >0.1 m/s².

## Interpretation

The baseline completes two comparable measured laps after launch. Review the interface and reference-state approximation before Task 007B. Timing tails, synthetic parameters and perfect state preclude a deployment or near-limit guarantee.
