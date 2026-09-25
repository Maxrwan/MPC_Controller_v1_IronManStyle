"""Explicit lateral bicycle design model; never used as the validation plant."""

from dataclasses import dataclass

import numpy as np
from scipy.linalg import solve_discrete_are
from scipy.signal import cont2discrete

from apex.models.vehicle.parameters import VehicleParameters


@dataclass(frozen=True)
class DesignScales:
    e_y: float = 0.10
    e_psi: float = 0.10
    vy_error: float = 0.5
    r_error: float = 1.0
    delta_feedback: float = 0.20

    def weights(self):
        scales = np.array([self.e_y, self.e_psi, self.vy_error, self.r_error, self.delta_feedback])
        if not np.all(np.isfinite(scales)) or np.any(scales <= 0):
            raise ValueError("Design scales must be finite and positive")
        return np.diag(1 / scales[:4] ** 2), np.array([[1 / scales[4] ** 2]])


def continuous_matrices(p: VehicleParameters, speed: float):
    """State order: [e_y, e_psi, vy_error, r_error]; input delta_feedback."""
    p.validate_for_dynamic()
    if not np.isfinite(speed) or speed <= 0:
        raise ValueError("Design speed must be finite and positive")
    m, iz, lf, lr = p.mass, p.yaw_inertia, p.lf, p.lr
    cf, cr = p.front_cornering_stiffness, p.rear_cornering_stiffness
    coupling = cr * lr - cf * lf
    a = np.array(
        [
            [0, speed, 1, 0],
            [0, 0, 0, 1],
            [0, 0, -(cf + cr) / (m * speed), coupling / (m * speed) - speed],
            [0, 0, coupling / (iz * speed), -(cf * lf**2 + cr * lr**2) / (iz * speed)],
        ],
        dtype=float,
    )
    b = np.array([[0], [0], [cf / m], [cf * lf / iz]])
    return a, b


def discrete_matrices(p: VehicleParameters, speed: float, dt: float = 0.01):
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("Controller dt must be finite and positive")
    a, b = continuous_matrices(p, speed)
    ad, bd, _, _, _ = cont2discrete((a, b, np.eye(4), np.zeros((4, 1))), dt)
    return ad, bd


class ScheduledLQR:
    """Solve three DAREs once; interpolate gains, clamping only scheduling speed."""

    def __init__(
        self, parameters: VehicleParameters, dt: float = 0.01, scales: DesignScales = DesignScales()
    ):
        self.nodes = np.array([1.0, 2.0, 3.0])
        self.q, self.r = scales.weights()
        gains, poles = [], []
        for speed in self.nodes:
            a, b = discrete_matrices(parameters, speed, dt)
            p = solve_discrete_are(a, b, self.q, self.r)
            gain = np.linalg.solve(self.r + b.T @ p @ b, b.T @ p @ a)
            gains.append(gain.ravel())
            poles.append(np.linalg.eigvals(a - b @ gain))
        self.gains = np.array(gains)
        self.poles = np.array(poles)
        for array in (self.nodes, self.q, self.r, self.gains, self.poles):
            array.setflags(write=False)

    def gain(self, speed: float):
        if not np.isfinite(speed) or speed <= 0:
            raise ValueError("Scheduling speed must be finite and positive")
        scheduled = float(np.clip(speed, self.nodes[0], self.nodes[-1]))
        gain = np.array([np.interp(scheduled, self.nodes, self.gains[:, i]) for i in range(4)])
        return gain, scheduled, scheduled != speed
