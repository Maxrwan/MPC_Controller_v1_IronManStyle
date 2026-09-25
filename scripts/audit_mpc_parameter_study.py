"""Audit parameter hashes, timing partitions and exported future trajectories."""

import hashlib
import json

import numpy as np
import pandas as pd
from parameter_study.common import OUT, canonical, records


def main():
    counts = {"experiments": 0, "solver_events": 0, "predictions": 0}
    for record in records():
        c, summary = record["configuration"], record["summary"]
        assert hashlib.sha256(canonical(c).encode()).hexdigest() == record["configuration_hash"]
        assert summary["mpc_config"]["horizon"] == c["n"]
        assert summary["mpc_config"]["dt"] == 1 / c["hz"]
        assert summary["mpc_config"]["substeps"] == c["substeps"]
        assert summary["tire_physics"]["model"] == "smooth_combined_grip"
        assert record["compute_ratio_p95"] == summary["solve_time"]["p95"] * c["hz"]
        if record.get("prediction_accuracy", {}).get("accuracy_pass") is False:
            assert not record["quality_pass"] and record["status"] == "rejected"
        folder = OUT / "runs" / record["id"]
        events = pd.read_csv(folder / "solver_events.csv", float_precision="round_trip")
        phases = [
            "preview_time",
            "warm_start_preparation_time",
            "parameter_update_time",
            "solver_adapter_time",
            "postprocessing_time",
        ]
        assert (events[phases] >= 0).all().all()
        assert (events[phases].sum(axis=1) <= events.total_compute_time + 1e-12).all()
        assert (events.solve_time <= events.solver_adapter_time + 1e-12).all()
        assert (
            (events.preview_geometry_time + events.reference_generation_time)
            <= events.preview_time + 1e-12
        ).all()
        assert np.allclose(
            events.release_time * c["hz"],
            np.round(events.release_time * c["hz"]),
            atol=1e-10,
            rtol=0,
        )
        with (folder / "predictions.jsonl").open() as stream:
            predictions = [json.loads(line) for line in stream]
        assert len(predictions) == len(events)
        for prediction, event in zip(predictions, events.itertuples()):
            offsets = np.arange(c["n"] + 1) / c["hz"]
            np.testing.assert_allclose(
                prediction["prediction_timestamps"],
                event.release_time + offsets,
                atol=1e-12,
                rtol=0,
            )
            assert (
                abs(
                    prediction["nominal_horizon_remaining_at_completion"]
                    - (c["n"] / c["hz"] - event.latency)
                )
                < 1e-12
            )
            assert prediction["completed"] == event.completed
            if event.completed:
                assert np.isfinite(prediction["actual_state_at_completion"]).all()
                assert abs(prediction["completion_time"] - event.application_time) < 1e-12
            else:
                assert prediction["completion_time"] is None
                assert all(v is None for v in prediction["actual_state_at_completion"])
            if "states" in prediction:
                assert np.asarray(prediction["states"]).shape == (6, c["n"] + 1)
                assert np.asarray(prediction["controls"]).shape == (2, c["n"])
        counts["experiments"] += 1
        counts["solver_events"] += len(events)
        counts["predictions"] += len(predictions)
    (OUT / "study_verification.json").write_text(json.dumps(counts, indent=2) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
