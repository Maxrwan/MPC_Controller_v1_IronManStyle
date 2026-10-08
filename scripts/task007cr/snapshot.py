"""Opt-in numeric NLP capture; copies only, never edits requests or solver results."""

import json
from dataclasses import asdict
from time import perf_counter

import casadi as ca
import numpy as np


class RecordingSolver:
    def __init__(self, solver, controller):
        self.solver, self.controller = solver, controller
        self.records = []
        self.context = {}

    def solve(self, request):
        start = perf_counter()
        previous = self.controller.solution
        record = dict(
            **self.context,
            initial=np.array(request.initial, copy=True),
            parameters=np.array(request.parameters, copy=True),
            previous_solution=(
                None if previous is None else self.controller.problem.pack(*previous).copy()
            ),
        )
        before = perf_counter() - start
        result = self.solver.solve(request)
        start = perf_counter()
        record.update(
            solution=None if result.solution is None else np.array(result.solution, copy=True),
            success=result.success,
            status=result.status,
            statistics=dict(result.statistics),
        )
        self.records.append(record)
        record["capture_seconds"] = before + perf_counter() - start
        return result

    def save(self, folder, metadata):
        problem = self.controller.problem
        graph = ca.Function(
            "snapshot_nlp",
            [problem.nlp["x"], problem.nlp["p"]],
            [problem.nlp["f"], problem.nlp["g"]],
        ).serialize()
        model = dict(
            graph=graph,
            solver_options=self.solver.options,
            lbx=problem.lbx.tolist(),
            ubx=problem.ubx.tolist(),
            lbg=problem.lbg.tolist(),
            ubg=problem.ubg.tolist(),
            vehicle=asdict(self.controller.parameters),
            config=asdict(problem.config),
            casadi_version=ca.__version__,
            **metadata,
        )
        (folder / "nlp_model.json").write_text(json.dumps(model) + "\n")

        def serial(value):
            if isinstance(value, np.ndarray):
                return value.tolist()
            if isinstance(value, np.generic):
                return value.item()
            raise TypeError(type(value).__name__)

        (folder / "nlp_snapshots.json").write_text(json.dumps(self.records, default=serial) + "\n")


def reconstruct(model):
    """Recreate precisely the captured symbolic graph, numeric bounds and solver options."""
    function = ca.Function.deserialize(model["graph"])
    x = ca.MX.sym("x", len(model["lbx"]))
    p = ca.MX.sym("p", function.size1_in(1))
    f, g = function(x, p)
    solver = ca.nlpsol("exact_replay", "ipopt", dict(x=x, p=p, f=f, g=g), model["solver_options"])
    return solver, function
