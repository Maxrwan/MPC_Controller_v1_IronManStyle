"""Known arithmetic examples for offline diagnostics, not fictional dynamics."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from task007c.metrics import (  # noqa: E402
    prediction_metrics,
    sideslip,
    steering_activity,
    variation,
)


def test_beta_uses_body_velocities():
    x = np.zeros((3, 6))
    x[:, 0], x[:, 1] = [1, 2, 2], [0, 2, -2]
    np.testing.assert_allclose(sideslip(x), [0, np.pi / 4, -np.pi / 4])


def test_variation_and_reversals():
    result = steering_activity([0, 0.1, 0, -0.1, 0], np.arange(5) * 0.1)
    assert result["total_variation"] == pytest.approx(0.4)
    assert result["peak_to_peak"] == pytest.approx(0.2)
    assert result["rate_sign_reversals"] == 2
    assert result["time_at_rate_limit"] == pytest.approx(0.4)
    assert variation([np.pi - 0.1, -np.pi + 0.1], angle=True)["total_variation"] == pytest.approx(
        0.2
    )


def test_deadband_does_not_count_numerical_chatter():
    result = steering_activity([0, 1e-8, 0, 1e-8], np.arange(4) * 0.1)
    assert result["rate_sign_reversals"] == 0
    assert result["time_at_rate_limit"] == 0


def test_prediction_metrics_and_horizon():
    x = np.zeros((5, 6))
    x[:, 0] = 2
    x[:, 4] = [100, 100.2, 100.4, 100.6, 100.8]
    x[:, 3] = [0, 0.1, 0, -0.1, 0]
    u = np.zeros((4, 2))
    u[:, 0] = [0, 0.1, 0, -0.1]
    m = prediction_metrics(x, u, 0.1)
    assert m["predicted_progress_m"] == pytest.approx(0.8)
    assert m["horizon_s"] == pytest.approx(0.4)
    assert m["heading_total_variation"] == pytest.approx(0.4)
    assert m["steering_total_variation"] == pytest.approx(0.3)
    assert m["steering_interval_duration"] == pytest.approx(0.3)


def test_common_window_does_not_confuse_longer_horizon_with_oscillation():
    from task007c.metrics import prediction_diagnostics

    x = np.zeros((9, 6))
    x[:, 0] = 2
    x[:, 4] = np.arange(9) * 0.2
    x[5:, 3] = [0.1, -0.1, 0.1, -0.1]
    u = np.zeros((8, 2))
    short = prediction_diagnostics(x[:5], u[:4], 0.1)
    long = prediction_diagnostics(x, u, 0.1)
    assert long["heading_total_variation"] > short["heading_total_variation"]
    assert long["common_0p4_heading_total_variation"] == short["common_0p4_heading_total_variation"]
    assert long["horizon_s"] == pytest.approx(0.8)
