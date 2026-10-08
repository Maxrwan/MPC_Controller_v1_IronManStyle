"""Real approved model round-trip; diagnostic capture cannot modify an NLP request."""

import json
import sys
from pathlib import Path

import numpy as np

from apex.control.mpc.controller import make_mpc
from apex.control.mpc.problem import MPCConfig
from apex.optimization.base import NLPRequest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from task007cr.snapshot import RecordingSolver, reconstruct  # noqa: E402


def test_exact_graph_request_and_warm_start_roundtrip(dynamic_vehicle, straight_geometry, tmp_path):
    c = make_mpc(
        dynamic_vehicle, straight_geometry, config=MPCConfig(horizon=4, dt=0.1, substeps=4)
    )
    recorder = RecordingSolver(c.solver, c)
    c.solver = recorder
    state = np.array([2.0, 0, 0, 0, 1.0, 0.01])
    c.compute_control(state, {"previous_control": np.zeros(2)})
    c.compute_control(state, {"previous_control": np.zeros(2)})
    assert len(recorder.records) == 2 and recorder.records[1]["previous_solution"] is not None
    recorder.save(tmp_path, {"seed": 0})
    records = json.loads((tmp_path / "nlp_snapshots.json").read_text())
    model = json.loads((tmp_path / "nlp_model.json").read_text())
    solver, evaluate = reconstruct(model)
    for record in records:
        numeric = NLPRequest(np.array(record["initial"]), np.array(record["parameters"]))
        initial = numeric.initial.copy()
        parameters = numeric.parameters.copy()
        answer = solver(
            x0=numeric.initial,
            p=numeric.parameters,
            **{k: model[k] for k in ["lbx", "ubx", "lbg", "ubg"]},
        )
        np.testing.assert_array_equal(numeric.initial, initial)
        np.testing.assert_array_equal(numeric.parameters, parameters)
        np.testing.assert_allclose(
            np.asarray(answer["x"]).ravel(), record["solution"], atol=1e-12, rtol=0
        )
        np.testing.assert_allclose(
            float(answer["f"]), record["statistics"]["objective"], atol=1e-12
        )
        old = c.problem.evaluate(numeric.initial, numeric.parameters)
        new = evaluate(numeric.initial, numeric.parameters)
        for a, b in zip(old, new):
            np.testing.assert_array_equal(np.asarray(a), np.asarray(b))
