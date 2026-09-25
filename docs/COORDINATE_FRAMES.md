# Frozen coordinate conventions

The global inertial plane is X/Y. Vehicle heading psi is measured counterclockwise
from global +X. The right-handed body frame has +x forward, +y left, and +z upward.

| Quantity | Positive direction |
|---|---|
| Yaw / psi | Counterclockwise, left turn |
| Yaw rate r | Left turn |
| Steering delta | Left |
| Body lateral velocity vy | Motion toward body-left |
| Track lateral error e_y | Left of centerline, looking along track travel direction |
| Heading error e_psi | Vehicle heading rotated left from track tangent |
| Track curvature kappa | Left-hand bend |

Waypoint order defines track direction; the first waypoint defines start/finish progress zero.
Lengths use metres; time seconds; mass kilograms; angles radians; velocity m/s;
acceleration m/s^2; inertia kg m^2; forces newtons; stiffness N/rad.
Task 002 implements the canonical angle interval (-pi, pi], mapping -pi to +pi.
All wrapping uses `apex.coordinates.angles.wrap_angle`. Heading errors use the same
interval. Positive e_y uses left normal [-sin(psi_t), cos(psi_t)]; global heading is
wrap_angle(psi_t + e_psi). See TRACK_MODEL_SPEC.md for transformations and validity limits.
Changes to these frame/sign conventions require explicit instruction.
