# Geometry regression

`test_geometry_accuracy.py` measures circle-fit error, pose round-trip accuracy and
seam continuity on synthetic circle/oval fixtures. Run with `pytest -q -s` to print metrics.
These tolerances apply to the declared fixtures, not arbitrary physical tracks.


`test_kinematic_accuracy.py` reports analytical straight/accelerating motion errors and
RK4 timestep refinement against an independent closed-form turning trajectory. Its smooth
case excludes braking-stop events and singularity thresholds from the order measurement.


Task 004 test_dynamic_accuracy.py compares hand-computable force/moment balances and
load conservation, then checks fixed-step RK4 against a tight-tolerance DOP853 reference
on a smooth transient. The reference independently checks integration, not the physical
force equations; those are covered by analytical tests. No validity events contaminate it.
