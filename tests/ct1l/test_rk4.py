"""O06/O07 exact nilpotent and quartic references; no implementation-generated oracle."""

import numpy as np
import pytest


@pytest.mark.parametrize(
    "T,n,Ad,Bd",
    [
        (0.01, 2, [[1, 1 / 100], [0, 1]], [[1 / 20000], [1 / 100]]),
        (0.1, 4, [[1, 1 / 10], [0, 1]], [[1 / 200], [1 / 10]]),
        (0.1, 20, [[1, 1 / 10], [0, 1]], [[1 / 200], [1 / 10]]),
    ],
)
def test_double_integrator_tangent(T, n, Ad, Bd):
    from ct1.rk4 import rk4_tangent

    A = np.array([[0.0, 1.0], [0.0, 0.0]])
    B = np.array([[0.0], [1.0]])
    X = np.eye(2)
    U = np.zeros((2, 1))
    x = np.array([1.0, 2.0])
    u = np.array([0.5])
    for _ in range(n):
        z = rk4_tangent(
            x, u, h_s=T / n, f=lambda x, u: np.array([x[1], u[0]]), df=lambda x, u: (A, B)
        ).unwrap()
        U = z.Jx @ U + z.Ju
        X = z.Jx @ X
        x = z.value
    np.testing.assert_allclose(X, Ad, atol=1e-7, rtol=1e-4)
    np.testing.assert_allclose(U, Bd, atol=1e-7, rtol=1e-4)


@pytest.mark.parametrize("T,n", [(0.01, 2), (0.1, 4), (0.1, 20)])
def test_scalar_quartic_not_euler(T, n):
    from ct1.rk4 import rk4_tangent

    h = T / n
    z = -h
    expected = (1 + z + z * z / 2 + z**3 / 6 + z**4 / 24) ** n
    X = 1.0
    U = 0.0
    x = np.array([0.0])
    for _ in range(n):
        step = rk4_tangent(
            x,
            np.array([1.0]),
            h_s=h,
            f=lambda x, u: -x + u,
            df=lambda x, u: (np.array([[-1.0]]), np.array([[1.0]])),
        ).unwrap()
        U = float(step.Jx[0, 0]) * U + float(step.Ju[0, 0])
        X = float(step.Jx[0, 0]) * X
        x = step.value
    assert abs(X - expected) <= 1e-7 + 1e-4 * abs(expected)
    assert abs(U - (1 - expected)) <= 1e-7 + 1e-4 * abs(1 - expected)
