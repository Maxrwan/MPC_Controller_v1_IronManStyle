"""Post-run attribution and oscillation measurements; never feedback signals."""

import numpy as np
import pandas as pd


def tracking_cost_channels(predictions, configuration, folder):
    scales = configuration["costs"]
    weights = np.array(
        [
            4 * scales["speed"],
            4 * scales["dynamic"] * scales.get("alpha_vy", 1.0),
            scales["dynamic"] * scales.get("alpha_r", 1.0),
            100 * scales["lateral"],
            100 * scales["lateral"],
        ]
    )
    rows = []
    for record in predictions:
        pred = record["prediction"]
        if not pred or "states" not in pred:
            continue
        x = np.asarray(pred["states"])
        preview = np.asarray(pred["preview"])
        errors = x[[0, 1, 2, 3, 5], :-1] - preview[[3, 4, 5, 8, 7], :-1]
        contributions = weights * np.sum(errors**2, axis=1)
        expected = record["diagnostics"]["objective_components"]["state_tracking"]
        np.testing.assert_allclose(sum(contributions), expected, atol=1e-9, rtol=1e-12)
        rows.append(
            dict(
                plan_id=record["plan_id"],
                **dict(zip(["vx", "vy", "r", "e_psi", "e_y"], contributions)),
            )
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(folder / "tracking_cost_channels.csv", index=False)
    return frame.drop(columns="plan_id").mean().to_dict()


def variation(group, column):
    """Do not count a sector's jump from one lap to the next as physical motion."""
    return float(sum(part[column].diff().abs().sum() for _, part in group.groupby("lap")))
