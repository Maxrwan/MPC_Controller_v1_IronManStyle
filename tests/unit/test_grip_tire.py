"""Physical envelope, independent symbolic parity and derivative domain gates."""

from dataclasses import replace

import casadi as ca
import numpy as np
import pytest

from apex.control.mpc.problem import MPCConfig, MPCProblem
from apex.control.mpc.symbolic_model import SymbolicBicycle
from apex.models.tire.config import RACING_TIRE_PHYSICS, TirePhysics
from apex.models.tire.grip import (
    LONGITUDINAL_MARGIN,
    SmoothCombinedGripTire,
    TireForceValidityError,
)
from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
from apex.models.vehicle.force_allocation import NormalLoadProportionalAllocation
from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer


def test_small_slip_zero_symmetry():
    tire = SmoothCombinedGripTire(1)
    for fx in (0, 3, -6):
        zero = tire.evaluate_combined(0, 45, 10, 10, fx)
        assert zero.lateral_force == 0
        for alpha in (1e-7, 1e-5, 0.1, 1):
            pos = tire.evaluate_combined(alpha, 45, 10, 10, fx)
            neg = tire.evaluate_combined(-alpha, 45, 10, 10, fx)
            assert pos.lateral_force == -neg.lateral_force
            if alpha <= 1e-5:
                # |z| <= 5.625e-5, tanh(z)/z=1-z²/3+O(z⁴): loss <1.06e-9.
                assert pos.lateral_force == pytest.approx(45 * alpha, rel=1.1e-9)


def test_saturation_tradeoff_load_and_bound():
    tire = SmoothCombinedGripTire(1)
    for load in (4, 9.81, 16):
        forces = []
        for ratio in (0, 0.3, 0.8, 1 - LONGITUDINAL_MARGIN):
            for alpha in (-3, -0.5, 0, 0.5, 3):
                d = tire.evaluate_combined(alpha, 45, load, 9.81, ratio * load)
                assert d.combined_utilization <= 1 + 3e-15
                assert abs(d.lateral_force) <= d.lateral_capacity
                if abs(alpha) == 3:
                    assert abs(d.lateral_force) == pytest.approx(d.lateral_capacity, rel=3e-11)
            forces.append(tire.evaluate_combined(0.2, 45, load, 9.81, ratio * load).lateral_force)
        assert np.all(np.diff(forces) < 0)
    assert (
        tire.evaluate_combined(0.2, 45, 16, 9.81, 0).lateral_force
        > tire.evaluate_combined(0.2, 45, 4, 9.81, 0).lateral_force
    )


@pytest.mark.parametrize("fx", [10, -10, 11, -11, float("nan"), 10 * (1 - LONGITUDINAL_MARGIN / 2)])
def test_invalid_longitudinal(fx):
    with pytest.raises(TireForceValidityError):
        SmoothCombinedGripTire(1).evaluate_combined(0.1, 45, 10, 10, fx)


@pytest.mark.parametrize("mu", [None, 0, -1, float("nan")])
def test_missing_grip(mu):
    with pytest.raises(ValueError):
        SmoothCombinedGripTire(mu)


def test_load_transfer_allocation(dynamic_vehicle):
    allocation = NormalLoadProportionalAllocation()
    loads = QuasiStaticLongitudinalLoadTransfer()
    baseline = loads.evaluate(dynamic_vehicle, 0)
    for a in (-2, 2):
        d = loads.evaluate(dynamic_vehicle, a)
        front, rear = allocation.allocate(dynamic_vehicle.mass * a, d.front, d.rear)
        assert front + rear == pytest.approx(dynamic_vehicle.mass * a)
        assert front / d.front == pytest.approx(rear / d.rear)
        assert np.sign(d.front - baseline.front) == -np.sign(a)
        assert np.sign(d.rear - baseline.rear) == np.sign(a)


def test_selection_and_invalid_plant(dynamic_vehicle, straight_geometry):
    with pytest.raises(ValueError):
        TirePhysics("smooth_combined_grip")
    with pytest.raises(ValueError):
        DynamicBicycle(
            replace(dynamic_vehicle, tire_road_friction_coefficient=None),
            straight_geometry,
            tire_physics=RACING_TIRE_PHYSICS,
        )
    p = replace(dynamic_vehicle, maximum_acceleration=12, maximum_braking_deceleration=12)
    model = DynamicBicycle(p, straight_geometry, tire_physics=RACING_TIRE_PHYSICS)
    with pytest.raises(TireForceValidityError):
        model.derivative(np.array([2, 0, 0, 0, 0, 0]), np.array([0, 10]))


def test_symbolic_jacobians_boundary_and_transition(dynamic_vehicle):
    p = replace(dynamic_vehicle, maximum_acceleration=12, maximum_braking_deceleration=12)
    model = SymbolicBicycle(p, RACING_TIRE_PHYSICS)
    x, u = ca.SX.sym("x", 6), ca.SX.sym("u", 2)
    expression = model.derivative(x, u, 0.2)
    jac = ca.Function("grip_jacobian", [x, u], [ca.jacobian(expression, ca.vertcat(x, u))])
    for a in (-9.81 * (1 - 2e-6), 0, 9.81 * (1 - 2e-6)):
        for delta in (0, 0.05, 0.15, 0.3):
            values = np.asarray(jac([2, 0.02, 0.4, 0, 0, 0], [delta, a]))
            assert np.isfinite(values).all()
    state = np.array([2, 0.02, 0.4, 0, 0, 0])
    for delta in np.linspace(-0.3, 0.3, 25):
        command = np.array([delta, 1.0])
        h = 1e-6
        finite = (
            np.asarray(model.derivative(state, command + [h, 0], 0.2))
            - np.asarray(model.derivative(state, command - [h, 0], 0.2))
        ) / (2 * h)
        np.testing.assert_allclose(
            finite.ravel(), np.asarray(jac(state, command))[:, 6], rtol=1e-7, atol=1e-7
        )


def test_grip_nlp_dimensions_and_interior_bounds(dynamic_vehicle):
    p = replace(dynamic_vehicle, tire_road_friction_coefficient=0.1)
    problem = MPCProblem(p, MPCConfig(tire_physics=RACING_TIRE_PHYSICS))
    assert problem.equality_count == 126 and problem.inequality_count == 984
    _, lo, _ = problem.unpack(problem.lbx)
    _, hi, _ = problem.unpack(problem.ubx)
    assert np.max(hi[1]) < 0.981 and np.min(lo[1]) > -0.981
    for a in (lo[1, 0], hi[1, 0]):
        assert np.isfinite(
            np.asarray(problem.model.derivative([2, 0, 0, 0, 0, 0], [0.2, a], 0))
        ).all()


def test_seeded_independent_grip_parity(monkeypatch):
    import runpy
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    report = runpy.run_path(str(scripts / "check_grip_parity.py"))["check_parity"](100)
    assert max(report["force_max_abs"].values()) < 1e-12


def test_many_valid_combined_forces():
    rng = np.random.default_rng(6101)
    for _ in range(2000):
        mu = rng.uniform(0.1, 1.5)
        load = rng.uniform(1, 25)
        fx = rng.uniform(-1 + 1e-6, 1 - 1e-6) * mu * load
        d = SmoothCombinedGripTire(mu).evaluate_combined(
            rng.uniform(-2, 2), rng.uniform(10, 80), load, 9.81, fx
        )
        assert np.hypot(fx, d.lateral_force) <= mu * load * (1 + 5e-15)


def test_tire_configuration_files_and_generic_unchanged():
    from pathlib import Path

    from apex.config import load_tire_physics, load_vehicle_parameters

    root = Path(__file__).resolve().parents[2]
    assert (
        load_tire_physics(root / "configs/models/synthetic_racing_tires.yaml")
        == RACING_TIRE_PHYSICS
    )
    assert load_tire_physics(root / "configs/models/linear_reference_tires.yaml").model == "linear"
    assert (
        load_vehicle_parameters(
            root / "configs/vehicles/generic_1_10_racecar.yaml"
        ).tire_road_friction_coefficient
        is None
    )


def test_application_rejects_force_outside_grip(dynamic_vehicle, circle):
    from apex.control.mpc.controller import ControllerApplicationError, MPCController

    p = replace(dynamic_vehicle, tire_road_friction_coefficient=0.1)
    problem = MPCProblem(p, MPCConfig(tire_physics=RACING_TIRE_PHYSICS))
    controller = MPCController(p, circle, None, problem)
    controller.last_diagnostics = {"success": True}
    with pytest.raises(ControllerApplicationError, match="longitudinal force"):
        controller.finalize_control([0, 2], [2, 0, 0, 0, 0, 0], {"previous_control": [0, 0]})
