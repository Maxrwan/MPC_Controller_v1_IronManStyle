# Integration tests

`test_kinematic_track.py` couples the CG kinematic model to real periodic spline geometry,
verifies algebraic state consistency and crosses L and 2L without wrapping race progress.
The fixed ideal-circle steering is not feedback; bounded spline approximation drift is expected.


Task 004 test_dynamic_track.py couples dynamic forces to the actual spline, verifies
finite valid evolution across L and 2L, and checks equivalent-lap propagation invariance.

Task 005 test_baseline_tracking.py validates the actual nonlinear DynamicBicycle on circle
and oval periodic splines at 1/2/3 m/s for two laps, initial-error recovery, deterministic
repetition, and progress-varying speed references. Full runs take several minutes because
geometry retains its established numerical arc-length inversion; no faster approximate
track or linear validation plant is substituted.
