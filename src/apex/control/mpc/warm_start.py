"""Primal multiple-shooting warm starts; no hidden state-latency prediction."""

import numpy as np


def shift_solution(states, controls, slacks, sampled_state):
    x = np.column_stack((states[:, 1:], states[:, -1]))
    u = np.column_stack((controls[:, 1:], controls[:, -1]))
    e = np.column_stack((slacks[:, 1:], slacks[:, -1]))
    x[:, 0] = sampled_state
    return x, u, e
