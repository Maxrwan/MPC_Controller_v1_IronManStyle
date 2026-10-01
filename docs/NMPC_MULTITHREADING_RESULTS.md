# Task 006.2.2 — generated measurements

Generated from retained CSV/JSON/logs. All n values are requested ceilings; actual sampled NMPC thread count was one. Solver/controller timing columns are milliseconds; lap times are seconds.

## Candidate C

| threads | samples | solve_time_mean | solve_time_p50 | solve_time_p95 | solve_time_p99 | solve_time_max | solve_time_std | solve_time_cv | total_compute_time_mean | total_compute_time_p95 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 360 | 13.2880 | 13.0052 | 13.5704 | 22.9231 | 35.1667 | 2.2350 | 0.1682 | 16.6799 | 17.1751 |
| 2 | 360 | 13.2101 | 12.9096 | 13.6818 | 19.8782 | 34.8328 | 2.1238 | 0.1608 | 16.6827 | 17.2636 |
| 4 | 360 | 13.4170 | 13.1315 | 13.7033 | 19.9134 | 35.7282 | 2.1544 | 0.1606 | 16.7621 | 17.3013 |
| 8 | 360 | 13.3750 | 13.0385 | 13.9723 | 23.1386 | 36.2275 | 2.3044 | 0.1723 | 16.7815 | 17.5189 |

Efficiencies are percentages of requested count, not CPU utilization.

| threads | speedup_mean | speedup_p95 | efficiency_mean | efficiency_p95 | backend_cpu_time_mean | controller_cpu_time_mean | controller_cpu_time_p95 | effective_cores | planner_core_demand | rss_mean_mib | rss_max_mib |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0000 | 1.0000 | 100.0000 | 100.0000 | 13.2224 | 16.6026 | 17.0877 | 0.9953 | 0.1660 | 181.8144 | 189.7344 |
| 2 | 1.0059 | 0.9919 | 50.2948 | 49.5928 | 13.1590 | 16.6229 | 17.0984 | 0.9964 | 0.1662 | 189.2961 | 189.8125 |
| 4 | 0.9904 | 0.9903 | 24.7596 | 24.7576 | 13.3432 | 16.6937 | 17.1653 | 0.9947 | 0.1669 | 189.1894 | 189.6875 |
| 8 | 0.9935 | 0.9712 | 12.4187 | 12.1405 | 13.2979 | 16.7010 | 17.3892 | 0.9945 | 0.1670 | 185.6951 | 189.7344 |

Callback times are accumulated per solve, not per callback.

| threads | iterations_mean | n_call_nlp_f_mean | n_call_nlp_g_mean | n_call_nlp_grad_mean | n_call_nlp_grad_f_mean | n_call_nlp_hess_l_mean | n_call_nlp_jac_g_mean | t_wall_nlp_f_mean | t_wall_nlp_g_mean | t_wall_nlp_grad_mean | t_wall_nlp_grad_f_mean | t_wall_nlp_hess_l_mean | t_wall_nlp_jac_g_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9.1417 | 11.3333 | 12.3333 | 0.0000 | 11.1417 | 9.1417 | 11.1417 | 0.0458 | 0.3308 | 0.0000 | 0.0640 | 6.4070 | 2.9345 |
| 2 | 9.1417 | 11.3333 | 12.3333 | 0.0000 | 11.1417 | 9.1417 | 11.1417 | 0.0455 | 0.3283 | 0.0000 | 0.0644 | 6.3506 | 2.9278 |
| 4 | 9.1417 | 11.3333 | 12.3333 | 0.0000 | 11.1417 | 9.1417 | 11.1417 | 0.0463 | 0.3358 | 0.0000 | 0.0642 | 6.4561 | 2.9590 |
| 8 | 9.1417 | 11.3333 | 12.3333 | 0.0000 | 11.1417 | 9.1417 | 11.1417 | 0.0462 | 0.3316 | 0.0000 | 0.0653 | 6.4127 | 2.9677 |

## Candidate D

| threads | samples | solve_time_mean | solve_time_p50 | solve_time_p95 | solve_time_p99 | solve_time_max | solve_time_std | solve_time_cv | total_compute_time_mean | total_compute_time_p95 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 360 | 81.0985 | 74.7692 | 97.5831 | 104.4413 | 223.1124 | 15.3510 | 0.1893 | 94.3085 | 112.4103 |
| 2 | 360 | 82.3808 | 75.4512 | 98.1492 | 185.1346 | 224.7130 | 17.2675 | 0.2096 | 95.8153 | 112.8975 |
| 4 | 360 | 82.5780 | 75.1016 | 99.1137 | 166.5381 | 273.4246 | 18.7554 | 0.2271 | 95.6206 | 113.6698 |
| 8 | 360 | 81.7665 | 74.8850 | 98.0792 | 122.1070 | 222.9453 | 15.8174 | 0.1934 | 95.4187 | 112.7112 |

Efficiencies are percentages of requested count, not CPU utilization.

| threads | speedup_mean | speedup_p95 | efficiency_mean | efficiency_p95 | backend_cpu_time_mean | controller_cpu_time_mean | controller_cpu_time_p95 | effective_cores | planner_core_demand | rss_mean_mib | rss_max_mib |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.0000 | 1.0000 | 100.0000 | 100.0000 | 80.7275 | 93.8910 | 111.7738 | 0.9955 | 1.8778 | 204.8944 | 206.7344 |
| 2 | 0.9844 | 0.9942 | 49.2217 | 49.7116 | 81.6649 | 94.9690 | 112.2072 | 0.9914 | 1.8994 | 138.8867 | 206.9688 |
| 4 | 0.9821 | 0.9846 | 24.5521 | 24.6139 | 81.5624 | 94.5388 | 112.6525 | 0.9878 | 1.8908 | 160.6855 | 207.3438 |
| 8 | 0.9918 | 0.9949 | 12.3979 | 12.4368 | 81.1823 | 94.3772 | 112.0852 | 0.9929 | 1.8875 | 168.1683 | 206.6562 |

Callback times are accumulated per solve, not per callback.

| threads | iterations_mean | n_call_nlp_f_mean | n_call_nlp_g_mean | n_call_nlp_grad_mean | n_call_nlp_grad_f_mean | n_call_nlp_hess_l_mean | n_call_nlp_jac_g_mean | t_wall_nlp_f_mean | t_wall_nlp_g_mean | t_wall_nlp_grad_mean | t_wall_nlp_grad_f_mean | t_wall_nlp_hess_l_mean | t_wall_nlp_jac_g_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 9.9000 | 12.2083 | 12.2083 | 0.0000 | 11.9000 | 9.9000 | 11.9000 | 0.1868 | 1.9034 | 0.0000 | 0.2923 | 42.4998 | 19.5124 |
| 2 | 9.9000 | 12.2083 | 12.2083 | 0.0000 | 11.9000 | 9.9000 | 11.9000 | 0.1946 | 1.9514 | 0.0000 | 0.3089 | 42.9744 | 19.8869 |
| 4 | 9.9000 | 12.2083 | 12.2083 | 0.0000 | 11.9000 | 9.9000 | 11.9000 | 0.1912 | 1.9528 | 0.0000 | 0.3113 | 43.1399 | 19.9329 |
| 8 | 9.9000 | 12.2083 | 12.2083 | 0.0000 | 11.9000 | 9.9000 | 11.9000 | 0.1907 | 1.9223 | 0.0000 | 0.3006 | 42.7264 | 19.7501 |

## Controller phases and lifetime memory

Nested adapter/backend timers must not be added twice.

| workload | threads | preview_time_mean_ms | warm_start_preparation_time_mean_ms | parameter_update_time_mean_ms | solve_time_mean_ms | solver_adapter_time_mean_ms | postprocessing_time_mean_ms | total_compute_time_mean_ms | lifetime_peak_rss_mib |
|---|---|---|---|---|---|---|---|---|---|
| C | 1 | 3.0104 | 0.0463 | 0.0227 | 13.2880 | 13.4294 | 0.1401 | 16.6799 | 190.4688 |
| C | 2 | 3.0859 | 0.0468 | 0.0230 | 13.2101 | 13.3522 | 0.1432 | 16.6827 | 190.5156 |
| C | 4 | 2.9654 | 0.0441 | 0.0216 | 13.4170 | 13.5588 | 0.1420 | 16.7621 | 190.4219 |
| C | 8 | 3.0235 | 0.0464 | 0.0231 | 13.3750 | 13.5161 | 0.1414 | 16.7815 | 190.4062 |
| D | 1 | 12.5241 | 0.0511 | 0.0263 | 81.0985 | 81.3198 | 0.3544 | 94.3085 | 207.3750 |
| D | 2 | 12.7304 | 0.0530 | 0.0281 | 82.3808 | 82.6085 | 0.3620 | 95.8153 | 206.9688 |
| D | 4 | 12.3479 | 0.0528 | 0.0273 | 82.5780 | 82.8031 | 0.3568 | 95.6206 | 207.3438 |
| D | 8 | 12.9492 | 0.0516 | 0.0269 | 81.7665 | 81.9920 | 0.3623 | 95.4187 | 207.5156 |

## Supplementary IPOPT timing-print probes

Two calls per condition, no warmup; 1 ms printed precision. Zero means rounded below precision, not free computation. Not a scaling benchmark; these nested timers overlap. Primary callback timings above are stronger evidence.

| workload | threads | component | cpu_ms | wall_ms |
|---|---|---|---|---|
| C | 1 | LinearSystemBackSolve | 1.5000 | 2.0000 |
| C | 1 | LinearSystemFactorization | 0.0000 | 0.0000 |
| C | 1 | LinearSystemSymbolicFactorization | 1.5000 | 2.0000 |
| C | 1 | PDSystemSolverTotal | 7.0000 | 9.0000 |
| C | 1 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| C | 2 | LinearSystemBackSolve | 1.5000 | 1.5000 |
| C | 2 | LinearSystemFactorization | 0.0000 | 0.0000 |
| C | 2 | LinearSystemSymbolicFactorization | 1.0000 | 1.0000 |
| C | 2 | PDSystemSolverTotal | 6.0000 | 6.0000 |
| C | 2 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| C | 4 | LinearSystemBackSolve | 2.0000 | 2.0000 |
| C | 4 | LinearSystemFactorization | 0.0000 | 0.0000 |
| C | 4 | LinearSystemSymbolicFactorization | 1.0000 | 1.0000 |
| C | 4 | PDSystemSolverTotal | 6.5000 | 6.5000 |
| C | 4 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| C | 8 | LinearSystemBackSolve | 1.5000 | 1.5000 |
| C | 8 | LinearSystemFactorization | 0.0000 | 0.0000 |
| C | 8 | LinearSystemSymbolicFactorization | 1.0000 | 1.0000 |
| C | 8 | PDSystemSolverTotal | 6.0000 | 6.0000 |
| C | 8 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| D | 1 | LinearSystemBackSolve | 14.5000 | 18.5000 |
| D | 1 | LinearSystemFactorization | 0.0000 | 0.0000 |
| D | 1 | LinearSystemSymbolicFactorization | 2.0000 | 2.0000 |
| D | 1 | PDSystemSolverTotal | 40.0000 | 46.0000 |
| D | 1 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| D | 2 | LinearSystemBackSolve | 16.0000 | 16.5000 |
| D | 2 | LinearSystemFactorization | 0.0000 | 0.0000 |
| D | 2 | LinearSystemSymbolicFactorization | 2.0000 | 2.0000 |
| D | 2 | PDSystemSolverTotal | 43.5000 | 45.0000 |
| D | 2 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| D | 4 | LinearSystemBackSolve | 15.0000 | 15.0000 |
| D | 4 | LinearSystemFactorization | 0.0000 | 0.0000 |
| D | 4 | LinearSystemSymbolicFactorization | 2.0000 | 2.0000 |
| D | 4 | PDSystemSolverTotal | 40.0000 | 40.5000 |
| D | 4 | UpdateBarrierParameter | 0.0000 | 0.0000 |
| D | 8 | LinearSystemBackSolve | 15.0000 | 15.0000 |
| D | 8 | LinearSystemFactorization | 0.0000 | 0.0000 |
| D | 8 | LinearSystemSymbolicFactorization | 2.0000 | 2.0000 |
| D | 8 | PDSystemSolverTotal | 39.5000 | 39.5000 |
| D | 8 | UpdateBarrierParameter | 0.0000 | 0.0000 |

## Fresh two-lap measured-latency confirmations

| threads | success | rms_e_y | rms_e_psi | rms_speed_error | lap_times | solver_failures | fallbacks | boundary_violations | max_slack | front_utilization | rear_utilization |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | True | 0.0041 | 0.0165 | 0.0293 | [16.266544338476308, 16.17799050876271] | 0 | 0 | 0 | 9.092e-11 | 0.6385 | 0.3697 |
| 2 | True | 0.0041 | 0.0165 | 0.0293 | [16.26715036002055, 16.1778870916361] | 0 | 0 | 0 | 9.092e-11 | 0.6385 | 0.3699 |
| 4 | True | 0.0043 | 0.0169 | 0.0296 | [16.270543165008824, 16.177887121998197] | 0 | 0 | 0 | 9.092e-11 | 0.6385 | 0.3694 |
| 8 | True | 0.0041 | 0.0165 | 0.0294 | [16.267102941856315, 16.17799594358975] | 0 | 0 | 0 | 9.092e-11 | 0.6385 | 0.3694 |

| threads | missed_deadlines | effective_update_hz | solve_time_mean | solve_time_p50 | solve_time_p95 | solve_time_p99 | solve_time_max | solve_time_std | solve_time_cv | total_compute_time_mean | total_compute_time_p50 | total_compute_time_p95 | total_compute_time_p99 | total_compute_time_max | total_compute_time_std | total_compute_time_cv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | 10.0170 | 13.5242 | 13.3851 | 14.4033 | 18.0400 | 34.8234 | 1.4952 | 0.1106 | 16.8471 | 16.6975 | 17.7443 | 21.6369 | 38.8843 | 1.5362 | 0.0912 |
| 2 | 0 | 10.0154 | 12.9678 | 12.8024 | 13.5010 | 17.2810 | 23.8426 | 1.0649 | 0.0821 | 16.1787 | 16.0318 | 16.9781 | 20.6408 | 30.1628 | 1.2249 | 0.0757 |
| 4 | 1 | 9.9846 | 13.8270 | 13.4104 | 14.5042 | 20.0554 | 108.7037 | 5.4725 | 0.3958 | 17.3442 | 16.6538 | 17.9758 | 23.6303 | 170.8213 | 8.6666 | 0.4997 |
| 8 | 0 | 10.0154 | 13.8269 | 13.3908 | 15.0179 | 22.6673 | 78.2420 | 4.2139 | 0.3048 | 17.2915 | 16.6862 | 18.6134 | 26.7989 | 115.8904 | 5.9360 | 0.3433 |
