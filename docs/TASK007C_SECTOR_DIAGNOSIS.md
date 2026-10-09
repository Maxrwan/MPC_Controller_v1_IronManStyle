# Task007C gamma2 sector diagnosis

Baseline weights, lambda0; fixed and smooth initial histories. Reversal counts use the existing1e-4rad/s deadband and the telemetry sampling grid. Other exported deadbands1e-5/1e-3 remain available. Heading here is Frenet epsi.

| History | N | Sector | Planned heading TV rad | Planned steering TV rad | Actual steering TV rad | Planned reversals | Actual reversals | Rate-limit s |
|---|---|---|---|---|---|---|---|---|
| fixed | 4 | hairpin | 1.7727 | 1.6159 | 1.9478 | 7 | 16 | 1.8 |
| fixed | 4 | fast_sweeper | 0.28364 | 0.061425 | 0.11861 | 6 | 75 | 0 |
| fixed | 4 | technical_section | 4.3041 | 3.1949 | 4.0374 | 18 | 55 | 3.51 |
| fixed | 6 | hairpin | 1.6516 | 1.4816 | 1.7208 | 5 | 21 | 1.61 |
| fixed | 6 | fast_sweeper | 0.28348 | 0.072369 | 0.13123 | 8 | 79 | 0.01 |
| fixed | 6 | technical_section | 3.4615 | 2.4236 | 3.0183 | 16 | 59 | 2.5 |
| fixed | 8 | hairpin | 1.7677 | 1.7526 | 1.9709 | 6 | 11 | 1.85 |
| fixed | 8 | fast_sweeper | 0.2862 | 0.063703 | 0.1279 | 6 | 76 | 0.01 |
| fixed | 8 | technical_section | 2.1822 | 1.5713 | 2.0523 | 13 | 70 | 1.42 |
| smooth | 4 | hairpin | 2.253 | 2.0077 | 2.1252 | 9 | 13 | 0.98 |
| smooth | 4 | fast_sweeper | 0.28212 | 0.075888 | 0.12452 | 10 | 67 | 0 |
| smooth | 4 | technical_section | 3.7834 | 2.463 | 3.0899 | 24 | 69 | 1.34 |
| smooth | 6 | hairpin | 2.0465 | 1.8513 | 2.0362 | 11 | 9 | 0.91 |
| smooth | 6 | fast_sweeper | 0.28858 | 0.061603 | 0.11468 | 6 | 67 | 0 |
| smooth | 6 | technical_section | 2.6901 | 1.909 | 2.4649 | 18 | 69 | 0.98 |
| smooth | 8 | hairpin | 1.7045 | 1.6624 | 1.8338 | 8 | 13 | 0.83 |
| smooth | 8 | fast_sweeper | 0.28671 | 0.068404 | 0.13148 | 8 | 72 | 0.01 |
| smooth | 8 | technical_section | 1.9474 | 1.3704 | 1.6644 | 14 | 77 | 0.54 |

The technical section shows the largest consistent reduction in planned heading and steering variation with horizon extension. For example, fixed technical heading TV drops4.304→3.462→2.182rad for N4/6/8; smooth3.783→2.690→1.947rad. Hairpin changes are smaller and not uniformly monotonic; N8 fixed steering TV is slightly higher than N4. The fast sweeper is already comparatively smooth in the planned steering channel.

Actual steering reversal counts do not uniformly decrease with planned variation. In the fixed technical section they rise55→59→70, while planned reversals fall18→16→13. These are distinct measurements and both remain in the evidence. Small feedback corrections, sampling and the chosen deadband can produce many reversals even when total angular variation falls. Reversal count alone cannot establish the amplitude or harmfulness of oscillation; inspect its companion TV, rate-limit time, tracking residual and phase portrait. No finalist is accepted from a single smoothness scalar.

The phase portraits retain loops through changing corner demand; they are not autonomous limit-cycle proofs. Compare growing excursion size, repeated turns, steering activity and spatial context. Separate sector and lap boundaries avoid drawing lines between unrelated traversals.

Figure: `results/task007c_resume/c3_gamma2_phase_portraits.png`. The four N6/N8 fixed/smooth case folders include primary dashboards and hairpin/technical/sweeper zooms. Baseline N4 dashboards are retained alongside them. These are synthetic diagnostics; completed measured timing and the bounded review recommendation are in `TASK007C_RESUMED_RESULTS.md`.
