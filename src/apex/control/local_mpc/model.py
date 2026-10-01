"""Discrete approved-model Jacobians and the interpolated-reference affine defect."""

import casadi as ca
import numpy as np
from scipy.linalg import solve_discrete_are

from apex.control.trajectory.tracker import LATERAL
from apex.coordinates.angles import wrap_angle


class LocalModel:
    def __init__(self, model, dt=0.01):
        self.dt = dt
        x, u, k = ca.SX.sym("x", 6), ca.SX.sym("u", 2), ca.SX.sym("k")
        step, _ = model.rk4(dt, 2)(x, u, k)
        self.step = ca.Function("local_nominal_step", [x, u, k], [step])
        self.evaluate = ca.Function(
            "local_discrete_model",
            [x, u, k],
            [step, ca.jacobian(step, x), ca.jacobian(step, u)],
        )
        self.q, self.r = np.diag([100.0, 100.0, 4.0, 1.0]), 25.0

    def matrices(self, reference, nominal, curvature, next_reference):
        step, a, b = map(np.asarray, self.evaluate(reference, nominal, curvature))
        residual = step.ravel() - next_reference
        residual[3] = wrap_angle(residual[3])
        return a[np.ix_(LATERAL, LATERAL)], b[LATERAL, :1], residual[LATERAL]

    def horizon(self, packet, time, count, varying=True):
        matrices, nominal = [], []
        for i in range(count):
            t = time + i * self.dt
            x, u, _ = packet.sample(t)
            future = packet.sample(t + self.dt)[0]
            if not varying and matrices:
                a, b = matrices[0][:2]
                residual = np.asarray(self.step(x, u, packet.curvature(t))).ravel() - future
                residual[3] = wrap_angle(residual[3])
                c = residual[LATERAL]
            else:
                a, b, c = self.matrices(x, u, packet.curvature(t), future)
            matrices.append((a, b, c))
            nominal.append(u[0])
        a, b, _ = matrices[-1]
        terminal = solve_discrete_are(a, b, self.q, np.array([[self.r]]))
        return matrices, np.array(nominal), terminal
