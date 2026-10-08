# Task 007A — completed

User brief: attachment a85f5e36-e474-4649-891f-04ea6fd0868a/Pasted text.txt.
Completed ONLY offline racing-reference interface and conservative synthetic GP baseline.
Task 007B, adaptive switching and direct-tracker architecture comparison remain deferred.
Previous completed handoff: TASK006_4_HANDOFF.md.

Planning owns the OFFLINE global racing line and velocity profile. The temporary generator
scripts/task007a/generate.py creates configs/planning/synthetic_grand_prix_v1 artifacts.
Runtime apex/planning_reference loads, validates, interpolates or rejects them; no generator
runs while the car moves. Reference and track geometry schemas are documented in
TASK007A_RACING_REFERENCE_INTERFACE.md; exact commands in TASK007A_REPRODUCTION.md.

Circuit: 154.763454927m, width1.1m, 43 documented spline control points, 3097 reference rows.
Principal nominal radii1.2/3/8m, sampled minimum0.915m. Closed, sampled crossing-free,
periodic tangent/curvature. Reference uses periodic Gaussian offset lobes and offline curvature
speed bound plus cyclic acceleration/braking passes, approximately1.115–3.001m/s.

MPCConfig.racing_reference is opt-in; old7-row preview unchanged, racing11-row preview adds
lateral/heading/reference-curvature/acceleration targets. Dynamics and packet curvature remain
CENTERLINE. Explicit geometric nominal vx=v,vy=0,r=v*kappa_ref,delta=atan(L*kappa_ref) is
an approximation, not dynamic equilibrium. Full residual diagnostics are exported.
Candidate C and 100Hz TVLQR weights/rates/limits/policies and0.08m margin remain fixed.

Measured3-lap baseline:58.632885s partial startup from s=1m, then59.019681/59.009765s
complete comparable laps. No model/planner failure, boundary violation or global fallback.
One planner release and four codriver releases missed; three codriver computations exceeded10ms.
Comparable racing-line lateral RMS6.412mm/max37.621mm, heading RMS0.015781rad,
speed RMS0.135966m/s. Local packet lateral RMS0.391mm. Hairpin sector RMS18.136mm.
Minimum physical-time reserve149.376ms, front/rear utilization maxima0.382725/0.305076.
Planner full mean/p95 24.325/31.151ms; codriver0.859/1.191ms. CPU0.326516core-s/s total.

Official zero and60ms injected supporting runs each complete one lap. All three physical
chronology audits pass. Initial s=0 smoke encountered the existing optimizer-negative-roundoff
state-domain check; use the documented s=1m rolling launch, not a changed state validator.
Pilots remain under /private/tmp and are excluded from primary results.

479 full regression tests passed in507.22s;23 focused interface tests passed in27.73s,
including exact fixture regeneration. Ruff lint/format pass for157 active Python files.
20 plots generated; circuit and speed-tracking figures visually checked. Full results and
sector tables: TASK007A_RESULTS.md and results/task007a. Final source_snapshot.zip,
provenance.json and validation logs preserve measured source/fixture hashes and prior artifacts.

No work remains for Task007A. Next: review this interface/baseline before authorizing Task007B.
Priorities are the geometric nominal-state approximation, hairpin speed lag,95.3% peak steering
usage and timing tails. Do not automatically increase aggressiveness or implement switching.
Final user response must use the exact30 headings in the brief. No subagents were used.
