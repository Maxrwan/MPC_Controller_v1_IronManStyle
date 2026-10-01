# Task 006.4 measured comparison

RMS values use SI units. Full-loop summaries include measured codriver latency. Replay uses identical offered packets, with unchanged acceptance gates. Raw timing tails and local replacement events are retained.

## Experiment outcomes

| case | completed | rms_e_y | tracking_e_y_rms | tracking_e_y_max | steering_total_variation | steering_rate_limit_seconds | recovery_seconds | planner_misses | codriver_misses | qp_local_fallbacks | fallback_events | boundary_violations | compute_ratio_p95 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mpc_100ms | True | 0.0025 | 0.0003 | 0.0054 | 2.1980 | 0.5300 | nan | 0 | 0 | 0 | 0 | 0 | 0.3073 |
| mpc_150ms | True | 0.0026 | 0.0005 | 0.0053 | 2.4326 | 0.7300 | nan | 162 | 0 | 0 | 0 | 0 | 0.3011 |
| mpc_60ms | True | 0.0025 | 0.0002 | 0.0049 | 2.2082 | 0.5500 | nan | 0 | 0 | 0 | 0 | 0 | 0.3056 |
| mpc_disturbance | True | 0.0071 | 0.0034 | 0.0800 | 2.3989 | 0.3779 | 0.4627 | 1 | 3 | 2 | 0 | 0 | 0.3126 |
| mpc_nominal | True | 0.0027 | 0.0003 | 0.0054 | 2.1773 | 0.2695 | nan | 0 | 0 | 2 | 0 | 0 | 0.3090 |
| mpc_qp_failure | True | 0.0027 | 0.0003 | 0.0054 | 2.1937 | 0.2890 | nan | 1 | 3 | 3 | 0 | 0 | 0.3124 |
| mpc_spike | True | 0.0026 | 0.0002 | 0.0033 | 2.2770 | 0.5800 | nan | 1 | 0 | 2 | 0 | 0 | 0.3086 |
| mpc_stress | True | 0.0064 | 0.0027 | 0.0650 | 2.6730 | 0.6761 | 0.5331 | 1 | 3 | 3 | 0 | 0 | 0.3136 |
| replay_N10 | True | 0.0032 | 0.0012 | 0.0156 | 2.6383 | 0.4242 | nan | 0 | 11 | 7 | 0 | 0 | 0.4174 |
| replay_N15 | True | 0.0034 | 0.0013 | 0.0166 | 2.6741 | 0.4540 | nan | 0 | 7 | 11 | 0 | 0 | 0.4579 |
| replay_N3 | True | 0.0035 | 0.0011 | 0.0147 | 2.6176 | 0.4255 | nan | 0 | 12 | 6 | 0 | 0 | 0.2765 |
| replay_N5 | True | 0.0033 | 0.0012 | 0.0154 | 2.6140 | 0.3824 | nan | 0 | 14 | 2 | 0 | 0 | 0.2945 |
| replay_N8 | True | 0.0034 | 0.0011 | 0.0143 | 2.7325 | 0.3657 | nan | 0 | 9 | 8 | 0 | 0 | 0.3509 |
| replay_N8_LTI | True | 0.0033 | 0.0012 | 0.0146 | 2.7040 | 0.3956 | nan | 0 | 3 | 4 | 0 | 0 | 0.3145 |
| replay_N8_W05 | True | 0.0033 | 0.0012 | 0.0150 | 2.6823 | 0.3671 | nan | 0 | 0 | 2 | 0 | 0 | 0.3384 |
| replay_N8_W1 | True | 0.0035 | 0.0012 | 0.0156 | 2.6639 | 0.4514 | nan | 0 | 1 | 4 | 0 | 0 | 0.3391 |
| replay_N8_W2 | True | 0.0033 | 0.0013 | 0.0167 | 2.6537 | 0.3472 | nan | 0 | 7 | 6 | 0 | 0 | 0.3365 |
| replay_tvlqr | True | 0.0038 | 0.0004 | 0.0064 | 2.8273 | 0.7391 | nan | 0 | 6 | 0 | 0 | 0 | 0.1805 |
| tvlqr_100ms | True | 0.0036 | 0.0004 | 0.0087 | 2.4051 | 0.9800 | nan | 0 | 0 | 0 | 0 | 0 | 0.1141 |
| tvlqr_150ms | True | 0.0034 | 0.0010 | 0.0121 | 2.5882 | 1.0900 | nan | 162 | 0 | 0 | 0 | 0 | 0.1164 |
| tvlqr_60ms | True | 0.0042 | 0.0004 | 0.0062 | 2.6974 | 1.3100 | nan | 0 | 0 | 0 | 0 | 0 | 0.1180 |
| tvlqr_disturbance | True | 0.0076 | 0.0031 | 0.0800 | 3.0237 | 0.7360 | 0.4700 | 1 | 0 | 0 | 0 | 0 | 0.1167 |
| tvlqr_nominal | True | 0.0039 | 0.0004 | 0.0064 | 2.7294 | 0.5765 | nan | 0 | 2 | 0 | 0 | 0 | 0.1200 |
| tvlqr_qp_failure | True | 0.0039 | 0.0004 | 0.0055 | 2.7946 | 0.6960 | nan | 0 | 0 | 0 | 0 | 0 | 0.1158 |
| tvlqr_spike | True | 0.0034 | 0.0003 | 0.0050 | 2.3978 | 0.9600 | nan | 1 | 0 | 0 | 0 | 0 | 0.1210 |
| tvlqr_stress | True | 0.0071 | 0.0025 | 0.0640 | 3.2477 | 0.8893 | 0.5162 | 0 | 0 | 0 | 0 | 0 | 0.1167 |

## QP work (seconds except iteration/count fields)

| case | qp_update_time_mean | qp_update_time_p95 | qp_solver_time_mean | qp_solver_time_p95 | qp_solver_update_time_mean | qp_model_assembly_time_mean | qp_iterations_mean | qp_iterations_p95 | qp_non_deadline_fallbacks |
|---|---|---|---|---|---|---|---|---|---|
| mpc_100ms | 3.465e-05 | 4.988e-05 | 1.247e-05 | 1.742e-05 | 7.069e-06 | 0.0016 | 20.0031 | 30.0000 | 0.0000 |
| mpc_150ms | 3.317e-05 | 4.738e-05 | 1.235e-05 | 1.754e-05 | 6.823e-06 | 0.0016 | 19.9599 | 30.0000 | 0.0000 |
| mpc_60ms | 3.483e-05 | 4.992e-05 | 1.240e-05 | 1.742e-05 | 7.107e-06 | 0.0016 | 20.0555 | 30.0000 | 0.0000 |
| mpc_disturbance | 3.589e-05 | 5.381e-05 | 1.528e-05 | 2.055e-05 | 7.226e-06 | 0.0016 | 25.1684 | 30.0000 | 1.0000 |
| mpc_nominal | 3.557e-05 | 5.363e-05 | 1.508e-05 | 2.050e-05 | 7.417e-06 | 0.0016 | 24.8936 | 30.0000 | 2.0000 |
| mpc_qp_failure | 3.616e-05 | 5.418e-05 | 1.515e-05 | 2.042e-05 | 7.341e-06 | 0.0016 | 24.7128 | 30.0000 | 2.0000 |
| mpc_spike | 3.522e-05 | 5.050e-05 | 1.215e-05 | 1.625e-05 | 7.244e-06 | 0.0016 | 19.4479 | 20.0000 | 2.0000 |
| mpc_stress | 3.593e-05 | 5.206e-05 | 1.351e-05 | 1.683e-05 | 7.276e-06 | 0.0016 | 22.1336 | 20.0000 | 2.0000 |
| replay_N10 | 5.641e-05 | 7.454e-05 | 2.121e-05 | 2.912e-05 | 1.225e-05 | 0.0022 | 21.7667 | 30.0000 | 1.0000 |
| replay_N15 | 6.078e-05 | 7.497e-05 | 3.916e-05 | 5.227e-05 | 1.813e-05 | 0.0029 | 28.0501 | 30.0000 | 7.0000 |
| replay_N3 | 4.997e-05 | 6.375e-05 | 7.115e-06 | 9.666e-06 | 5.773e-06 | 0.0011 | 15.3853 | 20.0000 | 0.0000 |
| replay_N5 | 4.826e-05 | 6.184e-05 | 1.060e-05 | 1.408e-05 | 7.186e-06 | 0.0014 | 20.7216 | 30.0000 | 0.0000 |
| replay_N8 | 5.359e-05 | 6.783e-05 | 1.514e-05 | 1.771e-05 | 9.945e-06 | 0.0018 | 21.0297 | 20.0000 | 6.0000 |
| replay_N8_LTI | 5.270e-05 | 6.925e-05 | 1.486e-05 | 1.809e-05 | 1.004e-05 | 0.0015 | 20.5432 | 20.0000 | 3.0000 |
| replay_N8_W05 | 4.990e-05 | 6.317e-05 | 1.392e-05 | 1.604e-05 | 9.455e-06 | 0.0018 | 19.6053 | 20.0000 | 2.0000 |
| replay_N8_W1 | 5.053e-05 | 6.400e-05 | 1.761e-05 | 2.345e-05 | 9.653e-06 | 0.0018 | 26.1999 | 30.0000 | 3.0000 |
| replay_N8_W2 | 5.032e-05 | 6.347e-05 | 1.618e-05 | 2.144e-05 | 9.678e-06 | 0.0018 | 23.7608 | 30.0000 | 4.0000 |

OSQP update time includes numerical matrix-update/refactorization work; an isolated factorization timer is not exposed by this Python interface.

## Full-update timing, milliseconds

| case | component | mean | p50 | p95 | p99 | max | std |
|---|---|---|---|---|---|---|---|
| mpc_100ms | total_time | 2.8477 | 2.8223 | 3.0725 | 3.2396 | 6.2975 | 0.1538 |
| mpc_150ms | total_time | 2.7967 | 2.7729 | 3.0108 | 3.1730 | 3.6217 | 0.1312 |
| mpc_60ms | total_time | 2.8315 | 2.8107 | 3.0565 | 3.2324 | 5.9173 | 0.1491 |
| mpc_disturbance | total_time | 2.8615 | 2.8374 | 3.1260 | 3.3782 | 31.4756 | 0.5286 |
| mpc_nominal | total_time | 2.8375 | 2.8250 | 3.0903 | 3.3452 | 5.1945 | 0.1576 |
| mpc_qp_failure | total_time | 2.8723 | 2.8387 | 3.1242 | 3.5194 | 38.1280 | 0.6535 |
| mpc_spike | total_time | 2.8409 | 2.8132 | 3.0856 | 3.2898 | 6.1265 | 0.1622 |
| mpc_stress | total_time | 2.8869 | 2.8616 | 3.1356 | 3.3688 | 33.2968 | 0.5657 |
| replay_N10 | total_time | 3.5432 | 3.4198 | 4.1738 | 5.8727 | 43.1948 | 1.0415 |
| replay_N15 | total_time | 4.2343 | 4.1739 | 4.5787 | 5.7902 | 34.2787 | 0.7287 |
| replay_N3 | total_time | 2.4591 | 2.3791 | 2.7654 | 3.7166 | 34.5836 | 1.0440 |
| replay_N5 | total_time | 2.7167 | 2.6435 | 2.9450 | 3.4014 | 118.6850 | 2.1354 |
| replay_N8 | total_time | 3.1939 | 3.1337 | 3.5093 | 4.0437 | 53.9822 | 1.1954 |
| replay_N8_LTI | total_time | 2.7713 | 2.7168 | 3.1452 | 4.2724 | 34.6492 | 0.6397 |
| replay_N8_W05 | total_time | 3.1028 | 3.0814 | 3.3837 | 3.7130 | 6.0588 | 0.1935 |
| replay_N8_W1 | total_time | 3.1138 | 3.0868 | 3.3906 | 3.9129 | 14.1798 | 0.3106 |
| replay_N8_W2 | total_time | 3.1145 | 3.0676 | 3.3650 | 3.7202 | 57.7709 | 1.0826 |
| replay_tvlqr | total_time | 1.1979 | 1.0565 | 1.8046 | 3.4113 | 38.8100 | 0.8951 |
| tvlqr_100ms | total_time | 1.0105 | 0.9395 | 1.1412 | 1.1986 | 2.0225 | 0.1034 |
| tvlqr_150ms | total_time | 1.0308 | 0.9505 | 1.1643 | 1.3320 | 5.5998 | 0.1664 |
| tvlqr_60ms | total_time | 1.0484 | 0.9688 | 1.1802 | 1.3049 | 15.3462 | 0.3137 |
| tvlqr_disturbance | total_time | 1.0408 | 0.9645 | 1.1666 | 1.3815 | 4.8815 | 0.1764 |
| tvlqr_nominal | total_time | 1.0574 | 0.9842 | 1.1996 | 1.3482 | 22.8038 | 0.4238 |
| tvlqr_qp_failure | total_time | 1.0294 | 0.9555 | 1.1585 | 1.2358 | 2.7971 | 0.1174 |
| tvlqr_spike | total_time | 1.0729 | 0.9956 | 1.2099 | 1.2606 | 2.0875 | 0.1076 |
| tvlqr_stress | total_time | 1.0364 | 0.9576 | 1.1669 | 1.3631 | 5.3848 | 0.1811 |

## Four-state trajectory error distributions

| case | error | rms | p95 | max |
|---|---|---|---|---|
| mpc_100ms | e_y | 0.0003 | 0.0003 | 0.0054 |
| mpc_100ms | e_psi | 0.0019 | 0.0040 | 0.0179 |
| mpc_100ms | vy | 0.0017 | 0.0032 | 0.0274 |
| mpc_100ms | r | 0.0202 | 0.0425 | 0.3009 |
| mpc_150ms | e_y | 0.0005 | 0.0009 | 0.0053 |
| mpc_150ms | e_psi | 0.0027 | 0.0071 | 0.0177 |
| mpc_150ms | vy | 0.0023 | 0.0054 | 0.0274 |
| mpc_150ms | r | 0.0298 | 0.0720 | 0.3009 |
| mpc_60ms | e_y | 0.0002 | 0.0003 | 0.0049 |
| mpc_60ms | e_psi | 0.0019 | 0.0042 | 0.0183 |
| mpc_60ms | vy | 0.0016 | 0.0032 | 0.0274 |
| mpc_60ms | r | 0.0201 | 0.0430 | 0.3009 |
| mpc_disturbance | e_y | 0.0034 | 0.0005 | 0.0800 |
| mpc_disturbance | e_psi | 0.0029 | 0.0051 | 0.0440 |
| mpc_disturbance | vy | 0.0017 | 0.0034 | 0.0275 |
| mpc_disturbance | r | 0.0211 | 0.0455 | 0.3020 |
| mpc_nominal | e_y | 0.0003 | 0.0005 | 0.0054 |
| mpc_nominal | e_psi | 0.0023 | 0.0050 | 0.0213 |
| mpc_nominal | vy | 0.0016 | 0.0033 | 0.0273 |
| mpc_nominal | r | 0.0201 | 0.0430 | 0.2989 |
| mpc_qp_failure | e_y | 0.0003 | 0.0004 | 0.0054 |
| mpc_qp_failure | e_psi | 0.0023 | 0.0049 | 0.0214 |
| mpc_qp_failure | vy | 0.0016 | 0.0033 | 0.0274 |
| mpc_qp_failure | r | 0.0202 | 0.0434 | 0.3006 |
| mpc_spike | e_y | 0.0002 | 0.0004 | 0.0033 |
| mpc_spike | e_psi | 0.0022 | 0.0045 | 0.0250 |
| mpc_spike | vy | 0.0016 | 0.0031 | 0.0274 |
| mpc_spike | r | 0.0197 | 0.0427 | 0.3009 |
| mpc_stress | e_y | 0.0027 | 0.0005 | 0.0650 |
| mpc_stress | e_psi | 0.0039 | 0.0057 | 0.0568 |
| mpc_stress | vy | 0.0018 | 0.0034 | 0.0274 |
| mpc_stress | r | 0.0220 | 0.0465 | 0.3009 |
| replay_N10 | e_y | 0.0012 | 0.0010 | 0.0156 |
| replay_N10 | e_psi | 0.0035 | 0.0058 | 0.0372 |
| replay_N10 | vy | 0.0025 | 0.0035 | 0.0286 |
| replay_N10 | r | 0.0348 | 0.0440 | 0.4693 |
| replay_N15 | e_y | 0.0013 | 0.0015 | 0.0166 |
| replay_N15 | e_psi | 0.0034 | 0.0057 | 0.0343 |
| replay_N15 | vy | 0.0026 | 0.0035 | 0.0287 |
| replay_N15 | r | 0.0354 | 0.0446 | 0.4795 |
| replay_N3 | e_y | 0.0011 | 0.0012 | 0.0147 |
| replay_N3 | e_psi | 0.0035 | 0.0060 | 0.0341 |
| replay_N3 | vy | 0.0023 | 0.0035 | 0.0272 |
| replay_N3 | r | 0.0307 | 0.0441 | 0.3795 |
| replay_N5 | e_y | 0.0012 | 0.0011 | 0.0154 |
| replay_N5 | e_psi | 0.0034 | 0.0059 | 0.0316 |
| replay_N5 | vy | 0.0025 | 0.0034 | 0.0274 |
| replay_N5 | r | 0.0328 | 0.0424 | 0.4383 |
| replay_N8 | e_y | 0.0011 | 0.0010 | 0.0143 |
| replay_N8 | e_psi | 0.0031 | 0.0057 | 0.0322 |
| replay_N8 | vy | 0.0021 | 0.0035 | 0.0274 |
| replay_N8 | r | 0.0286 | 0.0445 | 0.3014 |
| replay_N8_LTI | e_y | 0.0012 | 0.0013 | 0.0146 |
| replay_N8_LTI | e_psi | 0.0032 | 0.0057 | 0.0305 |
| replay_N8_LTI | vy | 0.0024 | 0.0035 | 0.0274 |
| replay_N8_LTI | r | 0.0319 | 0.0438 | 0.3949 |
| replay_N8_W05 | e_y | 0.0012 | 0.0012 | 0.0150 |
| replay_N8_W05 | e_psi | 0.0033 | 0.0058 | 0.0335 |
| replay_N8_W05 | vy | 0.0025 | 0.0034 | 0.0279 |
| replay_N8_W05 | r | 0.0334 | 0.0431 | 0.4559 |
| replay_N8_W1 | e_y | 0.0012 | 0.0013 | 0.0156 |
| replay_N8_W1 | e_psi | 0.0033 | 0.0055 | 0.0327 |
| replay_N8_W1 | vy | 0.0023 | 0.0034 | 0.0271 |
| replay_N8_W1 | r | 0.0311 | 0.0432 | 0.2968 |
| replay_N8_W2 | e_y | 0.0013 | 0.0013 | 0.0167 |
| replay_N8_W2 | e_psi | 0.0035 | 0.0059 | 0.0340 |
| replay_N8_W2 | vy | 0.0026 | 0.0035 | 0.0294 |
| replay_N8_W2 | r | 0.0354 | 0.0439 | 0.4856 |
| replay_tvlqr | e_y | 0.0004 | 0.0005 | 0.0064 |
| replay_tvlqr | e_psi | 0.0035 | 0.0061 | 0.0363 |
| replay_tvlqr | vy | 0.0019 | 0.0036 | 0.0290 |
| replay_tvlqr | r | 0.0261 | 0.0483 | 0.3216 |
| tvlqr_100ms | e_y | 0.0004 | 0.0003 | 0.0087 |
| tvlqr_100ms | e_psi | 0.0028 | 0.0046 | 0.0351 |
| tvlqr_100ms | vy | 0.0017 | 0.0033 | 0.0289 |
| tvlqr_100ms | r | 0.0229 | 0.0448 | 0.3199 |
| tvlqr_150ms | e_y | 0.0010 | 0.0011 | 0.0121 |
| tvlqr_150ms | e_psi | 0.0042 | 0.0079 | 0.0403 |
| tvlqr_150ms | vy | 0.0025 | 0.0053 | 0.0289 |
| tvlqr_150ms | r | 0.0343 | 0.0784 | 0.3199 |
| tvlqr_60ms | e_y | 0.0004 | 0.0004 | 0.0062 |
| tvlqr_60ms | e_psi | 0.0031 | 0.0050 | 0.0336 |
| tvlqr_60ms | vy | 0.0018 | 0.0035 | 0.0289 |
| tvlqr_60ms | r | 0.0247 | 0.0470 | 0.3199 |
| tvlqr_disturbance | e_y | 0.0031 | 0.0005 | 0.0800 |
| tvlqr_disturbance | e_psi | 0.0037 | 0.0060 | 0.0426 |
| tvlqr_disturbance | vy | 0.0019 | 0.0037 | 0.0290 |
| tvlqr_disturbance | r | 0.0255 | 0.0496 | 0.3213 |
| tvlqr_nominal | e_y | 0.0004 | 0.0005 | 0.0064 |
| tvlqr_nominal | e_psi | 0.0033 | 0.0059 | 0.0366 |
| tvlqr_nominal | vy | 0.0018 | 0.0036 | 0.0290 |
| tvlqr_nominal | r | 0.0250 | 0.0486 | 0.3211 |
| tvlqr_qp_failure | e_y | 0.0004 | 0.0005 | 0.0055 |
| tvlqr_qp_failure | e_psi | 0.0032 | 0.0059 | 0.0363 |
| tvlqr_qp_failure | vy | 0.0019 | 0.0036 | 0.0290 |
| tvlqr_qp_failure | r | 0.0251 | 0.0488 | 0.3213 |
| tvlqr_spike | e_y | 0.0003 | 0.0004 | 0.0050 |
| tvlqr_spike | e_psi | 0.0028 | 0.0051 | 0.0356 |
| tvlqr_spike | vy | 0.0018 | 0.0034 | 0.0289 |
| tvlqr_spike | r | 0.0227 | 0.0470 | 0.3199 |
| tvlqr_stress | e_y | 0.0025 | 0.0006 | 0.0640 |
| tvlqr_stress | e_psi | 0.0044 | 0.0069 | 0.0559 |
| tvlqr_stress | vy | 0.0020 | 0.0038 | 0.0290 |
| tvlqr_stress | r | 0.0277 | 0.0503 | 0.3211 |

## Actuator activity

| case | steering_total_variation | acceleration_total_variation | steering_rate_rms | steering_rate_max | steering_rate_limit_seconds | steering_correction_rms | steering_correction_max | applied_steering_correction_rms | applied_steering_correction_max |
|---|---|---|---|---|---|---|---|---|---|
| mpc_100ms | 2.1980 | 1.4210 | 0.1791 | 1.0000 | 0.5300 | 0.0036 | 0.0612 | 0.0036 | 0.0612 |
| mpc_150ms | 2.4326 | 1.9920 | 0.1951 | 1.0000 | 0.7300 | 0.0046 | 0.0612 | 0.0046 | 0.0612 |
| mpc_60ms | 2.2082 | 1.3644 | 0.1797 | 1.0000 | 0.5500 | 0.0036 | 0.0612 | 0.0036 | 0.0612 |
| mpc_disturbance | 2.3989 | 1.9886 | 0.1947 | 1.0000 | 0.3779 | 0.0044 | 0.0618 | 0.0044 | 0.0620 |
| mpc_nominal | 2.1773 | 1.3903 | 0.1787 | 1.0000 | 0.2695 | 0.0040 | 0.0622 | 0.0041 | 0.0622 |
| mpc_qp_failure | 2.1937 | 1.4010 | 0.1796 | 1.0000 | 0.2890 | 0.0041 | 0.0621 | 0.0041 | 0.0621 |
| mpc_spike | 2.2770 | 1.4130 | 0.1846 | 1.0000 | 0.5800 | 0.0044 | 0.0681 | 0.0046 | 0.0700 |
| mpc_stress | 2.6730 | 2.7966 | 0.2231 | 1.0000 | 0.6761 | 0.0058 | 0.0757 | 0.0058 | 0.0757 |
| replay_N10 | 2.6383 | 1.7690 | 0.2096 | 1.0000 | 0.4242 | 0.0076 | 0.0776 | 0.0076 | 0.0775 |
| replay_N15 | 2.6741 | 1.7703 | 0.2126 | 1.0000 | 0.4540 | 0.0078 | 0.0909 | 0.0078 | 0.0909 |
| replay_N3 | 2.6176 | 1.7627 | 0.2136 | 1.0000 | 0.4255 | 0.0067 | 0.0770 | 0.0067 | 0.0772 |
| replay_N5 | 2.6140 | 1.7642 | 0.2106 | 1.0000 | 0.3824 | 0.0071 | 0.0727 | 0.0071 | 0.0727 |
| replay_N8 | 2.7325 | 1.7658 | 0.2134 | 1.0000 | 0.3657 | 0.0071 | 0.0905 | 0.0071 | 0.0905 |
| replay_N8_LTI | 2.7040 | 1.7663 | 0.2111 | 1.0000 | 0.3956 | 0.0074 | 0.0839 | 0.0074 | 0.0839 |
| replay_N8_W05 | 2.6823 | 1.7671 | 0.2096 | 1.0000 | 0.3671 | 0.0074 | 0.0799 | 0.0074 | 0.0799 |
| replay_N8_W1 | 2.6639 | 1.7686 | 0.2087 | 1.0000 | 0.4514 | 0.0069 | 0.0775 | 0.0070 | 0.0782 |
| replay_N8_W2 | 2.6537 | 1.7678 | 0.2075 | 1.0000 | 0.3472 | 0.0075 | 0.0822 | 0.0075 | 0.0824 |
| replay_tvlqr | 2.8273 | 1.7642 | 0.2350 | 1.0000 | 0.7391 | 0.0081 | 0.0920 | 0.0078 | 0.0996 |
| tvlqr_100ms | 2.4051 | 1.5216 | 0.2086 | 1.0000 | 0.9800 | 0.0066 | 0.0917 | 0.0067 | 0.0991 |
| tvlqr_150ms | 2.5882 | 2.0069 | 0.2198 | 1.0000 | 1.0900 | 0.0088 | 0.1116 | 0.0077 | 0.0991 |
| tvlqr_60ms | 2.6974 | 1.6556 | 0.2303 | 1.0000 | 1.3100 | 0.0070 | 0.0832 | 0.0081 | 0.0991 |
| tvlqr_disturbance | 3.0237 | 2.3521 | 0.2457 | 1.0000 | 0.7360 | 0.0076 | 0.0875 | 0.0079 | 0.0993 |
| tvlqr_nominal | 2.7294 | 1.6389 | 0.2292 | 1.0000 | 0.5765 | 0.0075 | 0.0934 | 0.0077 | 0.0993 |
| tvlqr_qp_failure | 2.7946 | 1.6247 | 0.2327 | 1.0000 | 0.6960 | 0.0072 | 0.0911 | 0.0076 | 0.0995 |
| tvlqr_spike | 2.3978 | 1.4950 | 0.2074 | 1.0000 | 0.9600 | 0.0059 | 0.0928 | 0.0065 | 0.0991 |
| tvlqr_stress | 3.2477 | 3.0902 | 0.2644 | 1.0000 | 0.8893 | 0.0120 | 0.2124 | 0.0090 | 0.0995 |

Correction columns are requested pre-clipping corrections; applied columns use actual steering minus nominal feedforward.

## CPU demand and process memory

| case | planner_core_demand | codriver_core_demand | total_core_demand | effective_cores | final_rss_mib | peak_rss_mib | construction_rss_delta_mib |
|---|---|---|---|---|---|---|---|
| mpc_100ms | 0.6790 | 0.2848 | 0.9638 | 0.9999 | 220.4688 | 220.4688 | 19.7031 |
| mpc_150ms | 0.4275 | 0.2797 | 0.7072 | 1.0000 | 239.5938 | 239.5938 | 19.8750 |
| mpc_60ms | 0.5272 | 0.2831 | 0.8103 | 0.9999 | 221.6875 | 221.6875 | 19.6562 |
| mpc_disturbance | 0.5168 | 0.2858 | 0.8026 | 0.9998 | 148.1406 | 183.2500 | 20.0938 |
| mpc_nominal | 0.5156 | 0.2837 | 0.7993 | 0.9998 | 153.2500 | 190.8125 | 19.7188 |
| mpc_qp_failure | 0.5187 | 0.2861 | 0.8048 | 0.9969 | 153.1875 | 190.5000 | 19.8281 |
| mpc_spike | 0.4043 | 0.2841 | 0.6884 | 1.0000 | 220.1250 | 220.1250 | 19.7812 |
| mpc_stress | 0.5206 | 0.2884 | 0.8090 | 0.9998 | 153.3125 | 194.2188 | 19.7969 |
| replay_N10 | 0.0000 | 0.3493 | 0.3493 | 0.9892 | 144.9375 | 198.9219 | 31.1250 |
| replay_N15 | 0.0000 | 0.4202 | 0.4202 | 0.9944 | 144.6406 | 199.8594 | 31.2344 |
| replay_N3 | 0.0000 | 0.2420 | 0.2420 | 0.9877 | 116.4375 | 191.5000 | 31.1406 |
| replay_N5 | 0.0000 | 0.2666 | 0.2666 | 0.9855 | 144.9531 | 186.7188 | 23.7188 |
| replay_N8 | 0.0000 | 0.3164 | 0.3164 | 0.9933 | 144.8750 | 198.7812 | 31.1406 |
| replay_N8_LTI | 0.0000 | 0.2762 | 0.2762 | 0.9976 | 117.7344 | 192.0312 | 29.0312 |
| replay_N8_W05 | 0.0000 | 0.3095 | 0.3095 | 0.9973 | 145.2344 | 195.4688 | 30.0469 |
| replay_N8_W1 | 0.0000 | 0.3105 | 0.3105 | 0.9976 | 144.9375 | 175.2656 | -1.6094 |
| replay_N8_W2 | 0.0000 | 0.3091 | 0.3091 | 0.9946 | 144.4844 | 199.0156 | 31.3125 |
| replay_tvlqr | 0.0000 | 0.1149 | 0.1149 | 0.9607 | 105.3906 | 187.2344 | 12.9531 |
| tvlqr_100ms | 0.5134 | 0.1010 | 0.6144 | 1.0000 | 214.3281 | 214.4531 | 17.0000 |
| tvlqr_150ms | 0.3085 | 0.1028 | 0.4113 | 0.9970 | 133.7188 | 187.2812 | 17.0000 |
| tvlqr_60ms | 0.4385 | 0.1041 | 0.5426 | 0.9925 | 137.1562 | 179.8281 | -1.3750 |
| tvlqr_disturbance | 0.4055 | 0.1039 | 0.5094 | 0.9977 | 146.9688 | 187.5781 | 16.8438 |
| tvlqr_nominal | 0.4104 | 0.1044 | 0.5149 | 0.9882 | 146.7500 | 182.1250 | 14.6719 |
| tvlqr_qp_failure | 0.4003 | 0.1029 | 0.5032 | 0.9995 | 146.8125 | 195.0000 | 16.9062 |
| tvlqr_spike | 0.3651 | 0.1073 | 0.4724 | 1.0001 | 212.7969 | 213.0000 | 16.9844 |
| tvlqr_stress | 0.4041 | 0.1033 | 0.5075 | 0.9970 | 146.6719 | 187.4844 | 17.0938 |

CPU-core-seconds per second excludes plant integration/logging/transport. Replay does not execute the planner and its planner CPU demand is zero. In full replanning, forecasting the MPC codriver executes cloned QPs; that cost belongs to the planner pipeline. Process RSS includes imports, planner and logs, not an isolated QP workspace.

## Constraint and deadline behavior

| case | solver_failures | planner_failures | qp_local_fallbacks | codriver_computational_exceedances | max_front_utilization | max_rear_utilization |
|---|---|---|---|---|---|---|
| mpc_100ms | 0 | 0 | 0 | 0 | 0.4449 | 0.3490 |
| mpc_150ms | 0 | 0 | 0 | 0 | 0.4404 | 0.3511 |
| mpc_60ms | 0 | 0 | 0 | 0 | 0.4443 | 0.3495 |
| mpc_disturbance | 0 | 0 | 2 | 1 | 0.4410 | 0.3514 |
| mpc_nominal | 0 | 0 | 2 | 0 | 0.4420 | 0.3509 |
| mpc_qp_failure | 0 | 0 | 3 | 1 | 0.4421 | 0.3509 |
| mpc_spike | 0 | 0 | 2 | 0 | 0.4339 | 0.3540 |
| mpc_stress | 0 | 0 | 3 | 1 | 0.5858 | 0.4966 |
| replay_N10 | 0 | 0 | 7 | 6 | 0.4362 | 0.3518 |
| replay_N15 | 0 | 0 | 11 | 4 | 0.4180 | 0.3509 |
| replay_N3 | 0 | 0 | 6 | 6 | 0.4325 | 0.3676 |
| replay_N5 | 0 | 0 | 2 | 2 | 0.4218 | 0.3576 |
| replay_N8 | 0 | 0 | 8 | 2 | 0.4697 | 0.3688 |
| replay_N8_LTI | 0 | 0 | 4 | 1 | 0.4564 | 0.3580 |
| replay_N8_W05 | 0 | 0 | 2 | 0 | 0.4329 | 0.3551 |
| replay_N8_W1 | 0 | 0 | 4 | 1 | 0.4513 | 0.3653 |
| replay_N8_W2 | 0 | 0 | 6 | 2 | 0.4223 | 0.3506 |
| replay_tvlqr | 0 | 0 | 0 | 3 | 0.4977 | 0.3937 |
| tvlqr_100ms | 0 | 0 | 0 | 0 | 0.4390 | 0.3669 |
| tvlqr_150ms | 0 | 0 | 0 | 0 | 0.4743 | 0.3702 |
| tvlqr_60ms | 0 | 0 | 0 | 1 | 0.5000 | 0.3987 |
| tvlqr_disturbance | 0 | 0 | 0 | 0 | 0.4983 | 0.3942 |
| tvlqr_nominal | 0 | 0 | 0 | 1 | 0.4979 | 0.3940 |
| tvlqr_qp_failure | 0 | 0 | 0 | 0 | 0.4979 | 0.3937 |
| tvlqr_spike | 0 | 0 | 0 | 0 | 0.4755 | 0.3710 |
| tvlqr_stress | 0 | 0 | 0 | 0 | 0.6059 | 0.5161 |

## Fixed-input repeated timing benchmark

| controller | mean | p50 | p95 | p99 | max | std | iterations_mean | iterations_p95 | core_demand_100hz | deadline_exceedances |
|---|---|---|---|---|---|---|---|---|---|---|
| mpc_cold | 2.7841 | 2.7679 | 3.0024 | 3.2009 | 3.6748 | 0.1397 | 26.4250 | 40.0000 | 0.2783 | 0 |
| mpc_warm | 2.8367 | 2.7862 | 3.0604 | 3.3117 | 32.9498 | 0.6823 | 28.9667 | 50.0000 | 0.2832 | 2 |
| tvlqr | 1.0285 | 0.9609 | 1.1747 | 1.2278 | 1.5217 | 0.1079 | 0.0000 | 0.0000 | 0.1028 | 0 |

Three rotated controller-order replicates use identical sampled states, packets and previous controls. Warm/cold modes share matrix-update structure; cold mode zeros primal and dual starts; this is not a cold process per tick.

## Hardware-independent QP dimensions

| nx | nu | horizon | dt | decision_variables | equalities | two_sided_constraint_rows | scalar_inequalities | hessian_shape | hessian_full_structural_nonzeros | hessian_upper_stored_nonzeros | constraint_shape | constraint_nonzeros | kkt_shape |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1 | 8 | 0.0100 | 8 | 0 | 16 | 32 | [8, 8] | 64 | 36 | [16, 8] | 23 | [24, 24] |

## Pi portability

| controller | m1_p95_seconds | rho_required_10ms | rho_required_5ms | interpretation |
|---|---|---|---|---|
| mpc_cold | 0.0030 | 0.3002 | 0.6005 | Target single-core throughput / M1 throughput; not Pi utilization |
| mpc_warm | 0.0031 | 0.3060 | 0.6121 | Target single-core throughput / M1 throughput; not Pi utilization |
| tvlqr | 0.0012 | 0.1175 | 0.2349 | Target single-core throughput / M1 throughput; not Pi utilization |

These are throughput requirements, not measured Pi performance. On both Pi 4 and Pi 5, benchmark the complete callback and concurrent planner under the intended OS, thermal policy and native-library build. Small matrices make single-core latency and Python/validation overhead material; tiny matrix storage does not imply tiny process RSS. Direct target measurement is necessary before deployment.

OSQP numerical updates and warm starts follow its [official Python interface](https://osqp.org/docs/interfaces/python.html).
