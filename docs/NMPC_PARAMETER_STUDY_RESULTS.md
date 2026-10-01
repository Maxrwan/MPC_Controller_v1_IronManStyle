# Task006.2 measured tables

Generated from experiment.json records; SI units unless a column says ms or percent.
Tracking metrics are full-run time-weighted RMS, including startup. Failed runs
retain their shorter observation windows and must not be ranked as completed laps.
Local timings are not deadline guarantees. See NMPC_PARAMETER_STUDY.md.

## Stage A

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | track | mode | duration | laps_completed | effective_update_hz | missed_deadline_fraction | front_utilization | rear_utilization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reference_circle_measured_0d17d93037 | rejected | 0.21933 | 0.392525 | 0.304964 | 0.121321 | 0.234595 | 0.24699 | 4.6919 | 0 | 0.193043 | circle | measured | 5.055 | 0 | 6.92384 | 0.647059 | 0.504752 | 0.511303 |
| reference_circle_zero_9a0b8a0c28 | quality_pass | 0.00022482 | 0.0120695 | 0.00616686 | 0.0852482 | 0.0944853 | 0.108692 | 1.88971 | 0 | 9.09155e-11 | circle | zero | 31.32 | 2 | 20.0192 | 0 | 0.0875673 | 0.0823446 |
| reference_oval_measured_6f2e65d9ac | rejected | 0.299997 | 0.595555 | 0.504743 | 0.150516 | 0.264168 | 0.27703 | 5.28337 | 0 | 0.407338 | oval | measured | 2 | 0 | 5.5 | 0.707317 | 0.638538 | 0.543635 |
| reference_oval_zero_cc84e029b3 | quality_pass | 0.00538274 | 0.0163325 | 0.0148811 | 0.0823868 | 0.0965283 | 0.112882 | 1.93057 | 0 | 9.09179e-11 | oval | zero | 32.58 | 2 | 20.0123 | 0 | 0.526026 | 0.365702 |

## Stage B

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | horizon | variables | equalities | inequalities | solve_time_p50 | solve_time_max | iterations_mean | iterations_max | steering_effort | acceleration_effort | steering_rate_activity | boundary_violations | laps_completed | mean_lap_time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| horizon_10_71cee89501 | quality_pass | 0.0045137 | 0.0185433 | 0.0196841 | 0.0379286 | 0.0412906 | 0.0489564 | 0.825813 | 0 | 9.09185e-11 | 10 | 108 | 66 | 494 | 0.0367006 | 0.100047 | 9.30275 | 22 | 0.109668 | 0.0486213 | 6 | 0 | 1 | 16.3012 |
| horizon_12_0258dcf14b | quality_pass | 0.0049929 | 0.0185818 | 0.0175023 | 0.0482252 | 0.0601089 | 0.0697548 | 1.20218 | 0 | 9.09183e-11 | 12 | 128 | 78 | 592 | 0.0445945 | 0.396951 | 9.37309 | 24 | 0.109493 | 0.0382671 | 6 | 0 | 1 | 16.3036 |
| horizon_15_5f50fcc7c9 | quality_pass | 0.00555113 | 0.0185728 | 0.0155404 | 0.059446 | 0.0717886 | 0.0840899 | 1.43577 | 0 | 9.09169e-11 | 15 | 158 | 96 | 739 | 0.0549775 | 0.230687 | 9.50765 | 24 | 0.109598 | 0.0314526 | 6 | 0 | 1 | 16.3068 |
| horizon_20_866d41ddc8 | quality_pass | 0.00611666 | 0.0184799 | 0.0137632 | 0.0917688 | 0.144987 | 0.166464 | 2.89973 | 0 | 9.09179e-11 | 20 | 208 | 126 | 984 | 0.0819965 | 0.312418 | 9.70948 | 25 | 0.109681 | 0.0282727 | 6 | 0 | 1 | 16.3111 |
| horizon_25_7f57c05d3b | quality_pass | 0.00639295 | 0.0183925 | 0.0127536 | 0.120554 | 0.188928 | 0.215805 | 3.77857 | 0 | 9.09184e-11 | 25 | 258 | 156 | 1229 | 0.108817 | 0.478778 | 9.87462 | 25 | 0.109552 | 0.0274692 | 6 | 0 | 1 | 16.314 |
| horizon_8_1eaed8c5cc | quality_pass | 0.00402081 | 0.0184504 | 0.0230203 | 0.0314934 | 0.0375035 | 0.0440684 | 0.75007 | 0 | 9.09181e-11 | 8 | 88 | 54 | 396 | 0.0298854 | 0.110735 | 9.2546 | 20 | 0.109667 | 0.065602 | 7 | 0 | 1 | 16.298 |

## Stage C

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | horizon | substeps | prediction_error_max_scaled | prediction_accuracy_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| horizon_8_1eaed8c5cc | quality_pass | 0.00402081 | 0.0184504 | 0.0230203 | 0.0314934 | 0.0375035 | 0.0440684 | 0.75007 | 0 | 9.09181e-11 | 8 | 5 | 0.000577821 | True |
| integration_n8_s1_6049f2eae1 | rejected | 0.00400777 | 0.0184293 | 0.023032 | 0.00935295 | 0.0110176 | 0.0179401 | 0.220351 | 0 | 9.09184e-11 | 8 | 1 | 0.628879 | False |
| integration_n8_s2_e81de7cf90 | rejected | 0.00402009 | 0.0184497 | 0.0230226 | 0.0161484 | 0.0214192 | 0.029366 | 0.428383 | 0 | 9.09181e-11 | 8 | 2 | 0.0655278 | False |
| integration_n8_s3_cc2f600cbd | quality_pass | 0.00402063 | 0.0184503 | 0.0230204 | 0.0245676 | 0.0314903 | 0.0389507 | 0.629806 | 0 | 9.09176e-11 | 8 | 3 | 0.00682931 | True |

## Stage D

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | frequency_hz | substeps | mode | effective_update_hz | missed_deadline_fraction | staleness_index_p95 | laps_completed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frequency_10_s3_measured_ddbf59c1eb | rejected | 0.0477036 | 0.063993 | 0.0379129 | 0.03321 | 0.039898 | 0.0500611 | 0.39898 | 0 | 9.09176e-11 | 10 | 3 | measured | 9.79366 | 0.0245399 | 0.335444 | 1 |
| frequency_10_s3_zero_cc5e79f84a | rejected | 0.00633234 | 0.0167343 | 0.0128222 | 0.030796 | 0.0392943 | 0.0587266 | 0.392943 | 0 | 9.09152e-11 | 10 | 3 | zero | 10.0583 | 0 | 0 | 1 |
| frequency_10_s4_measured_e7671fa4af | quality_pass | 0.014658 | 0.0299185 | 0.0143295 | 0.0415859 | 0.0546992 | 0.0678421 | 0.546992 | 0 | 9.09169e-11 | 10 | 4 | measured | 9.7337 | 0.0243902 | 0.177421 | 1 |
| frequency_10_s4_zero_1fdd0016ba | quality_pass | 0.00633635 | 0.0167358 | 0.012816 | 0.0439904 | 0.0616169 | 0.0983515 | 0.616169 | 0 | 9.09152e-11 | 10 | 4 | zero | 10.0583 | 0 | 0 | 1 |
| frequency_15_s3_measured_00b2d485a5 | outside_quality_envelope | 0.0252021 | 0.0474431 | 0.0271336 | 0.0460044 | 0.0661082 | 0.0929817 | 0.991623 | 0 | 9.09181e-11 | 15 | 3 | measured | 14.2726 | 0.0487805 | 0.423027 | 1 |
| frequency_15_s3_zero_4f2bf26d10 | quality_pass | 0.00590544 | 0.0177937 | 0.0133822 | 0.0448813 | 0.0562078 | 0.097303 | 0.843117 | 0 | 9.09183e-11 | 15 | 3 | zero | 15.0215 | 0 | 0 | 1 |
| frequency_20_s3_measured_f7c3875f62 | rejected | 0.223956 | 0.55393 | 0.505531 | 0.122736 | 0.221285 | 0.236647 | 4.42569 | 0 | 0.472721 | 20 | 3 | measured | 6.99708 | 0.628571 | 3.56983 | 0 |
| frequency_20_s3_zero_4e026fa782 | quality_pass | 0.00611652 | 0.0184798 | 0.0137635 | 0.0586348 | 0.0782372 | 0.106074 | 1.56474 | 0 | 9.09176e-11 | 20 | 3 | zero | 20.0429 | 0 | 0 | 1 |
| frequency_25_s3_measured_f7835b0573 | rejected | 0.335897 | 0.419686 | 0.622979 | 0.182879 | 0.27115 | 0.304194 | 6.77876 | 0 | 0.071712 | 25 | 3 | measured | 4.85437 | 0.807692 | 3.57779 | 0 |
| frequency_25_s3_zero_adc1919f02 | quality_pass | 0.00637185 | 0.0189788 | 0.0140078 | 0.0710787 | 0.107193 | 0.154525 | 2.67981 | 0 | 9.09186e-11 | 25 | 3 | zero | 25.0077 | 0 | 0 | 1 |
| integration_n8_s3_cc2f600cbd | quality_pass | 0.00402063 | 0.0184503 | 0.0230204 | 0.0245676 | 0.0314903 | 0.0389507 | 0.629806 | 0 | 9.09176e-11 | 20 | 3 | zero | 20 | 0 | 0 | 1 |
| short_frequency_10_measured_c65b876241 | quality_pass | 0.00515145 | 0.0197015 | 0.0213849 | 0.0149827 | 0.017278 | 0.0215718 | 0.17278 | 0 | 9.09152e-11 | 10 | 4 | measured | 9.9356 | 0.00609756 | 0.0168344 | 1 |
| short_frequency_10_zero_5acc7345ac | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0141911 | 0.0160636 | 0.0198738 | 0.160636 | 0 | 9.09152e-11 | 10 | 4 | zero | 10.0092 | 0 | 0 | 1 |
| short_frequency_15_measured_b8b84b0158 | quality_pass | 0.00580534 | 0.0217083 | 0.0247402 | 0.0167506 | 0.020358 | 0.0254632 | 0.30537 | 0 | 9.09155e-11 | 15 | 3 | measured | 14.8943 | 0.00816327 | 0.0399838 | 1 |
| short_frequency_15_zero_1ca841ab09 | quality_pass | 0.00342334 | 0.0177681 | 0.021998 | 0.017314 | 0.0193719 | 0.0247316 | 0.290579 | 0 | 9.09166e-11 | 15 | 3 | zero | 15.0307 | 0 | 0 | 1 |
| short_frequency_20_measured_a5cf64c0ec | quality_pass | 0.00668919 | 0.0233507 | 0.0264422 | 0.0219647 | 0.0274284 | 0.0340051 | 0.548569 | 0 | 9.09182e-11 | 20 | 3 | measured | 19.5466 | 0.0214067 | 0.0622608 | 1 |
| short_frequency_25_measured_79b3a828d4 | quality_pass | 0.0119851 | 0.0323044 | 0.0413119 | 0.0251862 | 0.0309258 | 0.038883 | 0.773145 | 0 | 9.09186e-11 | 25 | 3 | measured | 24.6182 | 0.0146341 | 0.200714 | 1 |
| short_frequency_25_zero_bda7d948f8 | quality_pass | 0.00449624 | 0.0188941 | 0.023208 | 0.0263186 | 0.0283844 | 0.0360693 | 0.709609 | 0 | 9.09181e-11 | 25 | 3 | zero | 25.0307 | 0 | 0 | 1 |

## Stage E

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | cost_lateral | cost_dynamic | cost_speed | cost_control | cost_rate | iterations_mean | iterations_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| weight_combined_634c8a2d04 | quality_pass | 0.0027873 | 0.0163283 | 0.0173664 | 0.0129335 | 0.0138953 | 0.017362 | 0.138953 | 0 | 9.09154e-11 | 2 | 1 | 2 | 1 | 1 | 9.13497 | 20 |
| weight_control_0.5_e40315bd2a | quality_pass | 0.00300359 | 0.0166854 | 0.0167425 | 0.0129748 | 0.013429 | 0.0166404 | 0.13429 | 0 | 9.09152e-11 | 1 | 1 | 1 | 0.5 | 1 | 9.10976 | 20 |
| weight_control_1_02ce95691a | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0129255 | 0.0132376 | 0.0165284 | 0.132376 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 1 | 9.07362 | 20 |
| weight_control_2_dd10a58359 | quality_pass | 0.00316248 | 0.016555 | 0.0260433 | 0.0127591 | 0.0139363 | 0.0174004 | 0.139363 | 0 | 9.09186e-11 | 1 | 1 | 1 | 2 | 1 | 8.82822 | 20 |
| weight_dynamic_0.5_84ef979bfd | quality_pass | 0.00300461 | 0.0166679 | 0.0196203 | 0.012974 | 0.0132202 | 0.0167628 | 0.132202 | 0 | 9.0918e-11 | 1 | 0.5 | 1 | 1 | 1 | 9.09816 | 20 |
| weight_dynamic_1_e498ee8c0d | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0130029 | 0.0133846 | 0.0168022 | 0.133846 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 1 | 9.07362 | 20 |
| weight_dynamic_2_e9cd1ea181 | quality_pass | 0.00317908 | 0.0165894 | 0.0194726 | 0.0131612 | 0.0140481 | 0.0174329 | 0.140481 | 0 | 9.09152e-11 | 1 | 2 | 1 | 1 | 1 | 9.07975 | 20 |
| weight_lateral_0.5_36ca0f36a9 | quality_pass | 0.00358431 | 0.0169491 | 0.015994 | 0.0132308 | 0.0136037 | 0.0172289 | 0.136037 | 0 | 9.09152e-11 | 0.5 | 1 | 1 | 1 | 1 | 9.06707 | 20 |
| weight_lateral_1_6c9d92eb76 | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0131692 | 0.0139146 | 0.0173971 | 0.139146 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 1 | 9.07362 | 20 |
| weight_lateral_2_6fd76ce77b | quality_pass | 0.0027703 | 0.0161007 | 0.0257455 | 0.013361 | 0.013538 | 0.0170858 | 0.13538 | 0 | 9.09152e-11 | 2 | 1 | 1 | 1 | 1 | 9.08589 | 20 |
| weight_rate_0.25_d0524f3f98 | quality_pass | 0.003053 | 0.016625 | 0.0193159 | 0.0129832 | 0.0133957 | 0.0168142 | 0.133957 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 0.25 | 9.07362 | 20 |
| weight_rate_0.5_ee014ae510 | quality_pass | 0.00305756 | 0.0166272 | 0.0193171 | 0.0129051 | 0.0131072 | 0.0164863 | 0.131072 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 0.5 | 9.07362 | 20 |
| weight_rate_1_f788497f20 | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0128577 | 0.0130488 | 0.0164575 | 0.130488 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 1 | 9.07362 | 20 |
| weight_rate_2_9b1cf1e017 | quality_pass | 0.00308295 | 0.0166385 | 0.019338 | 0.0129899 | 0.0138657 | 0.0172035 | 0.138657 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 2 | 9.14724 | 20 |
| weight_speed_0.5_855b144599 | quality_pass | 0.00305684 | 0.0164823 | 0.0263136 | 0.0131465 | 0.013396 | 0.0170578 | 0.13396 | 0 | 9.09152e-11 | 1 | 1 | 0.5 | 1 | 1 | 9.07975 | 20 |
| weight_speed_1_2b71383a2b | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0134226 | 0.0137231 | 0.0172521 | 0.137231 | 0 | 9.09152e-11 | 1 | 1 | 1 | 1 | 1 | 9.07362 | 20 |
| weight_speed_2_567d914c49 | quality_pass | 0.00309015 | 0.0167928 | 0.0130192 | 0.0131031 | 0.014258 | 0.0178051 | 0.14258 | 0 | 9.09152e-11 | 1 | 1 | 2 | 1 | 1 | 9.12195 | 20 |

## Stage F

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | cost_terminal | iterations_mean | iterations_max | max_primal_residual |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| terminal_0.5_4b6a1e1a7b | quality_pass | 0.00412004 | 0.0157188 | 0.0273185 | 0.0129787 | 0.0134937 | 0.0168384 | 0.134937 | 0 | 9.09152e-11 | 0.5 | 9.11656 | 19 | 7.9921e-09 |
| terminal_0_a5b007e34a | quality_pass | 0.0228416 | 0.0143134 | 0.018325 | 0.0129773 | 0.0139651 | 0.0174421 | 0.139651 | 0 | 9.09156e-11 | 0 | 9.2037 | 21 | 3.21645e-08 |
| terminal_1_361d2a2a8e | quality_pass | 0.0027703 | 0.0161007 | 0.0257455 | 0.0128834 | 0.0131583 | 0.0166327 | 0.131583 | 0 | 9.09152e-11 | 1 | 9.08589 | 20 | 6.29536e-09 |
| terminal_2_5805636299 | quality_pass | 0.002888 | 0.0165458 | 0.0228708 | 0.0134102 | 0.0146176 | 0.018301 | 0.146176 | 0 | 9.09161e-11 | 2 | 9.1227 | 20 | 1.02694e-08 |

## Stage G

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | ipopt_settings | iterations_mean | iterations_max | max_primal_residual |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ipopt_limited_memory_76ed60aa0d | quality_pass | 0.00277028 | 0.0161007 | 0.0257457 | 0.0263153 | 0.0391951 | 0.0425555 | 0.391951 | 0 | 1e-13 | {"error_on_fail":false,"ipopt.acceptable_tol":1e-06,"ipopt.bound_relax_factor":0.0,"ipopt.constr_viol_tol":1e-07,"ipopt.hessian_approximation":"limited-memory","ipopt.honor_original_bounds":"yes","ipopt.max_iter":100,"ipopt.print_level":0,"ipopt.sb":"yes","ipopt.tol":1e-07,"print_time":false} | 20.8037 | 54 | 6.09161e-08 |
| ipopt_max40_ab4e62f3a3 | quality_pass | 0.0027703 | 0.0161007 | 0.0257455 | 0.0130962 | 0.0146992 | 0.0180753 | 0.146992 | 0 | 9.09152e-11 | {"error_on_fail":false,"ipopt.acceptable_tol":1e-06,"ipopt.bound_relax_factor":0.0,"ipopt.constr_viol_tol":1e-07,"ipopt.honor_original_bounds":"yes","ipopt.max_iter":40,"ipopt.print_level":0,"ipopt.sb":"yes","ipopt.tol":1e-07,"print_time":false} | 9.08589 | 20 | 6.29536e-09 |
| ipopt_strict_950ba381a7 | quality_pass | 0.0027703 | 0.0161007 | 0.0257453 | 0.0129142 | 0.0131433 | 0.0167063 | 0.131433 | 0 | 2.50652e-11 | {"error_on_fail":false,"ipopt.acceptable_tol":1e-07,"ipopt.bound_relax_factor":0.0,"ipopt.constr_viol_tol":1e-07,"ipopt.honor_original_bounds":"yes","ipopt.max_iter":100,"ipopt.print_level":0,"ipopt.sb":"yes","ipopt.tol":1e-08,"print_time":false} | 9.09816 | 20 | 6.31138e-09 |
| ipopt_tol1e6_2fb077d040 | quality_pass | 0.00277034 | 0.0161009 | 0.0257488 | 0.01288 | 0.0131467 | 0.0166152 | 0.131467 | 0 | 9.09096e-10 | {"error_on_fail":false,"ipopt.acceptable_tol":1e-06,"ipopt.bound_relax_factor":0.0,"ipopt.constr_viol_tol":1e-07,"ipopt.honor_original_bounds":"yes","ipopt.max_iter":100,"ipopt.print_level":0,"ipopt.sb":"yes","ipopt.tol":1e-06,"print_time":false} | 9.07362 | 20 | 6.11283e-08 |
| ipopt_warm_flag_d5e0d799d8 | quality_pass | 0.0027703 | 0.0161007 | 0.0257455 | 0.0127419 | 0.0130121 | 0.0165856 | 0.130121 | 0 | 9.09152e-11 | {"error_on_fail":false,"ipopt.acceptable_tol":1e-06,"ipopt.bound_relax_factor":0.0,"ipopt.constr_viol_tol":1e-07,"ipopt.honor_original_bounds":"yes","ipopt.max_iter":100,"ipopt.print_level":0,"ipopt.sb":"yes","ipopt.tol":1e-07,"ipopt.warm_start_init_point":"yes","print_time":false} | 9.07975 | 17 | 6.44073e-09 |
| terminal_1_361d2a2a8e | quality_pass | 0.0027703 | 0.0161007 | 0.0257455 | 0.0128834 | 0.0131583 | 0.0166327 | 0.131583 | 0 | 9.09152e-11 | {"error_on_fail":false,"ipopt.acceptable_tol":1e-06,"ipopt.bound_relax_factor":0.0,"ipopt.constr_viol_tol":1e-07,"ipopt.honor_original_bounds":"yes","ipopt.max_iter":100,"ipopt.print_level":0,"ipopt.sb":"yes","ipopt.tol":1e-07,"print_time":false} | 9.08589 | 20 | 6.29536e-09 |

## Stage confirmation

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack | track | mode | injected_latency | duration | laps_completed | effective_update_hz | missed_deadline_fraction | staleness_index_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_A_circle_zero_b27522922a | quality_pass | 0.000634319 | 0.0119379 | 0.0129346 | 0.0268422 | 0.0429565 | 0.0465379 | 0.429565 | 0 | 1e-13 | circle | zero | 0 | 31.21 | 2 | 10.0288 | 0 | 0 |
| candidate_A_disturbance_f9d50832e5 | quality_pass | 0.0101363 | 0.0200898 | 0.0224463 | 0.0263887 | 0.0323422 | 0.03811 | 0.323422 | 0 | 1e-13 | circle | zero | 0 | 12 | 0 | 10 | 0 | 0 |
| candidate_A_measured_00f7022cfe | quality_pass | 0.00687775 | 0.0184924 | 0.0311661 | 0.0306329 | 0.0488012 | 0.0532726 | 0.488012 | 0 | 1e-13 | oval | measured | 0 | 32.42 | 2 | 9.87045 | 0.0123077 | 0.0607482 |
| candidate_A_oval_zero_9bbfa6ffd7 | quality_pass | 0.00277776 | 0.0150523 | 0.0291404 | 0.0290239 | 0.0476228 | 0.0521429 | 0.476228 | 0 | 1e-13 | oval | zero | 0 | 32.425 | 2 | 10.0231 | 0 | 0 |
| candidate_B_circle_zero_33bd204916 | quality_pass | 0.000634376 | 0.0119379 | 0.012935 | 0.0134325 | 0.0143773 | 0.0176814 | 0.143773 | 0 | 9.09155e-11 | circle | zero | 0 | 31.21 | 2 | 10.0288 | 0 | 0 |
| candidate_B_disturbance_4a7e7ce7fe | quality_pass | 0.0101363 | 0.0200898 | 0.0224468 | 0.0139641 | 0.0160764 | 0.0198914 | 0.160764 | 0 | 9.09155e-11 | circle | zero | 0 | 12 | 0 | 10 | 0 | 0 |
| candidate_B_measured_c5766dc5bf | quality_pass | 0.00414709 | 0.0164512 | 0.0293992 | 0.0141145 | 0.0158475 | 0.0198979 | 0.158475 | 0 | 9.09152e-11 | oval | measured | 0 | 32.445 | 2 | 10.017 | 0 | 0.0131653 |
| candidate_B_oval_zero_1995c6026d | quality_pass | 0.00277777 | 0.0150523 | 0.0291406 | 0.0130176 | 0.0137641 | 0.0170967 | 0.137641 | 0 | 9.09152e-11 | oval | zero | 0 | 32.425 | 2 | 10.0231 | 0 | 0 |
| candidate_C_25ms_6cb8ec39a9 | quality_pass | 0.00479736 | 0.0171601 | 0.0291852 | 0.0139715 | 0.014547 | 0.0180174 | 0.14547 | 0 | 9.09171e-11 | oval | injected | 0.025 | 32.45 | 2 | 10.0154 | 0 | 0.0284125 |
| candidate_C_45ms_94e8d0c02f | quality_pass | 0.0069144 | 0.0210387 | 0.0304092 | 0.0142719 | 0.0153294 | 0.0190352 | 0.153294 | 0 | 9.09165e-11 | oval | injected | 0.045 | 32.465 | 2 | 10.0108 | 0 | 0.0692936 |
| candidate_C_60ms_67ad1bbeda | quality_pass | 0.00917411 | 0.0264083 | 0.0325006 | 0.0133191 | 0.0149567 | 0.0183965 | 0.149567 | 0 | 9.09165e-11 | oval | injected | 0.06 | 32.47 | 2 | 10.0092 | 0 | 0.182572 |
| candidate_D_disturbance_3d297cf541 | quality_pass | 0.0125633 | 0.0185815 | 0.00871986 | 0.0867086 | 0.0916291 | 0.104938 | 1.83258 | 0 | 9.09155e-11 | circle | zero | 0 | 12 | 0 | 20 | 0 | 0 |
| reference_circle_zero_9a0b8a0c28 | quality_pass | 0.00022482 | 0.0120695 | 0.00616686 | 0.0852482 | 0.0944853 | 0.108692 | 1.88971 | 0 | 9.09155e-11 | circle | zero | 0 | 31.32 | 2 | 20.0192 | 0 | 0 |
| reference_oval_measured_6f2e65d9ac | rejected | 0.299997 | 0.595555 | 0.504743 | 0.150516 | 0.264168 | 0.27703 | 5.28337 | 0 | 0.407338 | oval | measured | 0 | 2 | 0 | 5.5 | 0.707317 | 4.47779 |
| reference_oval_zero_cc84e029b3 | quality_pass | 0.00538274 | 0.0163325 | 0.0148811 | 0.0823868 | 0.0965283 | 0.112882 | 1.93057 | 0 | 9.09179e-11 | oval | zero | 0 | 32.58 | 2 | 20.0123 | 0 | 0 |

## Nondominated screening configurations

| experiment_id | status | rms_e_y | rms_e_psi | rms_speed_error | solve_time_mean | solve_time_p95 | total_compute_time_p95 | compute_ratio_p95 | solver_failures | max_slack |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| frequency_10_s4_zero_1fdd0016ba | quality_pass | 0.00633635 | 0.0167358 | 0.012816 | 0.0439904 | 0.0616169 | 0.0983515 | 0.616169 | 0 | 9.09152e-11 |
| horizon_25_7f57c05d3b | quality_pass | 0.00639295 | 0.0183925 | 0.0127536 | 0.120554 | 0.188928 | 0.215805 | 3.77857 | 0 | 9.09184e-11 |
| ipopt_limited_memory_76ed60aa0d | quality_pass | 0.00277028 | 0.0161007 | 0.0257457 | 0.0263153 | 0.0391951 | 0.0425555 | 0.391951 | 0 | 1e-13 |
| ipopt_strict_950ba381a7 | quality_pass | 0.0027703 | 0.0161007 | 0.0257453 | 0.0129142 | 0.0131433 | 0.0167063 | 0.131433 | 0 | 2.50652e-11 |
| ipopt_warm_flag_d5e0d799d8 | quality_pass | 0.0027703 | 0.0161007 | 0.0257455 | 0.0127419 | 0.0130121 | 0.0165856 | 0.130121 | 0 | 9.09152e-11 |
| terminal_0.5_4b6a1e1a7b | quality_pass | 0.00412004 | 0.0157188 | 0.0273185 | 0.0129787 | 0.0134937 | 0.0168384 | 0.134937 | 0 | 9.09152e-11 |
| terminal_0_a5b007e34a | quality_pass | 0.0228416 | 0.0143134 | 0.018325 | 0.0129773 | 0.0139651 | 0.0174421 | 0.139651 | 0 | 9.09156e-11 |
| weight_combined_634c8a2d04 | quality_pass | 0.0027873 | 0.0163283 | 0.0173664 | 0.0129335 | 0.0138953 | 0.017362 | 0.138953 | 0 | 9.09154e-11 |
| weight_control_0.5_e40315bd2a | quality_pass | 0.00300359 | 0.0166854 | 0.0167425 | 0.0129748 | 0.013429 | 0.0166404 | 0.13429 | 0 | 9.09152e-11 |
| weight_dynamic_0.5_84ef979bfd | quality_pass | 0.00300461 | 0.0166679 | 0.0196203 | 0.012974 | 0.0132202 | 0.0167628 | 0.132202 | 0 | 9.0918e-11 |
| weight_lateral_0.5_36ca0f36a9 | quality_pass | 0.00358431 | 0.0169491 | 0.015994 | 0.0132308 | 0.0136037 | 0.0172289 | 0.136037 | 0 | 9.09152e-11 |
| weight_rate_0.25_d0524f3f98 | quality_pass | 0.003053 | 0.016625 | 0.0193159 | 0.0129832 | 0.0133957 | 0.0168142 | 0.133957 | 0 | 9.09152e-11 |
| weight_rate_0.5_ee014ae510 | quality_pass | 0.00305756 | 0.0166272 | 0.0193171 | 0.0129051 | 0.0131072 | 0.0164863 | 0.131072 | 0 | 9.09152e-11 |
| weight_rate_1_f788497f20 | quality_pass | 0.00306637 | 0.0166312 | 0.0193217 | 0.0128577 | 0.0130488 | 0.0164575 | 0.130488 | 0 | 9.09152e-11 |
| weight_speed_2_567d914c49 | quality_pass | 0.00309015 | 0.0167928 | 0.0130192 | 0.0131031 | 0.014258 | 0.0178051 | 0.14258 | 0 | 9.09152e-11 |

## Selected configurations

```json
{
  "A": {
    "experiment_id": "ipopt_limited_memory_76ed60aa0d",
    "configuration": {
      "hz": 10.0,
      "n": 4,
      "substeps": 4,
      "costs": {
        "lateral": 2,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1
      },
      "solver": {
        "ipopt.hessian_approximation": "limited-memory"
      },
      "warm_start": true,
      "track": "oval",
      "mode": "zero",
      "latency": 0.0,
      "laps": 1,
      "duration": 45.0,
      "ey": 0.0,
      "epsi": 0.0
    },
    "configuration_hash": "76ed60aa0d141a6a1bc857efd93fdb76ac7029cc9aab0abf5bb43cbc612765ca",
    "effective_solver_options": {
      "print_time": false,
      "error_on_fail": false,
      "ipopt.print_level": 0,
      "ipopt.sb": "yes",
      "ipopt.max_iter": 100,
      "ipopt.tol": 1e-07,
      "ipopt.acceptable_tol": 1e-06,
      "ipopt.constr_viol_tol": 1e-07,
      "ipopt.bound_relax_factor": 0.0,
      "ipopt.honor_original_bounds": "yes",
      "ipopt.hessian_approximation": "limited-memory"
    },
    "mpc_config": {
      "tire_physics": {
        "model": "smooth_combined_grip",
        "longitudinal_allocation": "normal_load_proportional"
      },
      "costs": {
        "lateral": 2,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1
      },
      "horizon": 4,
      "dt": 0.1,
      "substeps": 4,
      "steering_rate": 1.0,
      "minimum_speed": 0.5,
      "denominator_margin": 0.01,
      "minimum_axle_load": 1e-06
    },
    "nlp_dimensions": {
      "variables": 48,
      "equalities": 30,
      "inequalities": 168
    },
    "compute_ratio_p95": 0.39195074391318496,
    "quality_pass": true
  },
  "B": {
    "experiment_id": "ipopt_warm_flag_d5e0d799d8",
    "configuration": {
      "hz": 10.0,
      "n": 4,
      "substeps": 4,
      "costs": {
        "lateral": 2,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1
      },
      "solver": {
        "ipopt.warm_start_init_point": "yes"
      },
      "warm_start": true,
      "track": "oval",
      "mode": "zero",
      "latency": 0.0,
      "laps": 1,
      "duration": 45.0,
      "ey": 0.0,
      "epsi": 0.0
    },
    "configuration_hash": "d5e0d799d8e6960c36365acd15937428f910ac1a8534264dffdcaa50f72b5bf1",
    "effective_solver_options": {
      "print_time": false,
      "error_on_fail": false,
      "ipopt.print_level": 0,
      "ipopt.sb": "yes",
      "ipopt.max_iter": 100,
      "ipopt.tol": 1e-07,
      "ipopt.acceptable_tol": 1e-06,
      "ipopt.constr_viol_tol": 1e-07,
      "ipopt.bound_relax_factor": 0.0,
      "ipopt.honor_original_bounds": "yes",
      "ipopt.warm_start_init_point": "yes"
    },
    "mpc_config": {
      "tire_physics": {
        "model": "smooth_combined_grip",
        "longitudinal_allocation": "normal_load_proportional"
      },
      "costs": {
        "lateral": 2,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1
      },
      "horizon": 4,
      "dt": 0.1,
      "substeps": 4,
      "steering_rate": 1.0,
      "minimum_speed": 0.5,
      "denominator_margin": 0.01,
      "minimum_axle_load": 1e-06
    },
    "nlp_dimensions": {
      "variables": 48,
      "equalities": 30,
      "inequalities": 168
    },
    "compute_ratio_p95": 0.1301214110571891,
    "quality_pass": true
  },
  "C": {
    "experiment_id": "ipopt_warm_flag_d5e0d799d8",
    "configuration": {
      "hz": 10.0,
      "n": 4,
      "substeps": 4,
      "costs": {
        "lateral": 2,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1
      },
      "solver": {
        "ipopt.warm_start_init_point": "yes"
      },
      "warm_start": true,
      "track": "oval",
      "mode": "zero",
      "latency": 0.0,
      "laps": 1,
      "duration": 45.0,
      "ey": 0.0,
      "epsi": 0.0
    },
    "configuration_hash": "d5e0d799d8e6960c36365acd15937428f910ac1a8534264dffdcaa50f72b5bf1",
    "effective_solver_options": {
      "print_time": false,
      "error_on_fail": false,
      "ipopt.print_level": 0,
      "ipopt.sb": "yes",
      "ipopt.max_iter": 100,
      "ipopt.tol": 1e-07,
      "ipopt.acceptable_tol": 1e-06,
      "ipopt.constr_viol_tol": 1e-07,
      "ipopt.bound_relax_factor": 0.0,
      "ipopt.honor_original_bounds": "yes",
      "ipopt.warm_start_init_point": "yes"
    },
    "mpc_config": {
      "tire_physics": {
        "model": "smooth_combined_grip",
        "longitudinal_allocation": "normal_load_proportional"
      },
      "costs": {
        "lateral": 2,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1
      },
      "horizon": 4,
      "dt": 0.1,
      "substeps": 4,
      "steering_rate": 1.0,
      "minimum_speed": 0.5,
      "denominator_margin": 0.01,
      "minimum_axle_load": 1e-06
    },
    "nlp_dimensions": {
      "variables": 48,
      "equalities": 30,
      "inequalities": 168
    },
    "compute_ratio_p95": 0.1301214110571891,
    "quality_pass": true
  },
  "D": {
    "experiment_id": "reference_oval_zero_cc84e029b3",
    "configuration": {
      "hz": 20.0,
      "n": 20,
      "substeps": 5,
      "costs": {
        "lateral": 1.0,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1.0
      },
      "solver": {},
      "warm_start": true,
      "track": "oval",
      "mode": "zero",
      "latency": 0.0,
      "laps": 2,
      "duration": 80.0,
      "ey": 0.0,
      "epsi": 0.0
    },
    "configuration_hash": "cc84e029b3867c894e1e9b8603fef16b0c73e07f8eac5c0e2b471790c4068ed2",
    "effective_solver_options": {
      "print_time": false,
      "error_on_fail": false,
      "ipopt.print_level": 0,
      "ipopt.sb": "yes",
      "ipopt.max_iter": 100,
      "ipopt.tol": 1e-07,
      "ipopt.acceptable_tol": 1e-06,
      "ipopt.constr_viol_tol": 1e-07,
      "ipopt.bound_relax_factor": 0.0,
      "ipopt.honor_original_bounds": "yes"
    },
    "mpc_config": {
      "tire_physics": {
        "model": "smooth_combined_grip",
        "longitudinal_allocation": "normal_load_proportional"
      },
      "costs": {
        "lateral": 1.0,
        "dynamic": 1.0,
        "speed": 1.0,
        "control": 1.0,
        "rate": 1.0,
        "terminal": 1.0
      },
      "horizon": 20,
      "dt": 0.05,
      "substeps": 5,
      "steering_rate": 1.0,
      "minimum_speed": 0.5,
      "denominator_margin": 0.01,
      "minimum_axle_load": 1e-06
    },
    "nlp_dimensions": {
      "variables": 208,
      "equalities": 126,
      "inequalities": 984
    },
    "compute_ratio_p95": 1.9305655819625824,
    "quality_pass": true
  }
}
```

## Rejected observations

| experiment_id | rejection_reasons | duration | laps_completed |
| --- | --- | --- | --- |
| frequency_10_s3_measured_ddbf59c1eb | prediction_accuracy_gate | 16.235 | 1 |
| frequency_10_s3_zero_cc5e79f84a | prediction_accuracy_gate | 16.305 | 1 |
| frequency_20_s3_measured_f7c3875f62 | LowSpeedValidityError: vx=0.499103 m/s is below dynamic-model minimum 0.5 m/s; no low-speed regularization or automatic model switch is implemented / required_laps_incomplete / physical_boundary_violation / material_predicted_slack | 1.715 | 0 |
| frequency_25_s3_measured_f7835b0573 | LowSpeedValidityError: vx=0.495446 m/s is below dynamic-model minimum 0.5 m/s; no low-speed regularization or automatic model switch is implemented / required_laps_incomplete / physical_boundary_violation / material_predicted_slack | 1.03 | 0 |
| integration_n8_s1_6049f2eae1 | prediction_accuracy_gate | 16.3 | 1 |
| integration_n8_s2_e81de7cf90 | prediction_accuracy_gate | 16.3 | 1 |
| reference_circle_measured_0d17d93037 | LowSpeedValidityError: vx=0.49569 m/s is below dynamic-model minimum 0.5 m/s; no low-speed regularization or automatic model switch is implemented / required_laps_incomplete / material_predicted_slack | 5.055 | 0 |
| reference_oval_measured_6f2e65d9ac | LowSpeedValidityError: vx=0.496875 m/s is below dynamic-model minimum 0.5 m/s; no low-speed regularization or automatic model switch is implemented / required_laps_incomplete / physical_boundary_violation / material_predicted_slack | 2 | 0 |
