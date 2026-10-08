"""Fresh SINGLE offline exact-NLP and deterministic initialization/state sensitivity study."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(selection, output):
    import time

    import casadi as ca
    import numpy as np
    from task007cr.snapshot import reconstruct

    selected = json.loads(selection.read_text())
    records = []
    for item in selected:
        folder = Path(item["folder"])
        model = json.loads((folder / "nlp_model.json").read_text())
        snapshots = json.loads((folder / "nlp_snapshots.json").read_text())
        record = next(r for r in snapshots if r["plan_id"] == item["plan_id"])
        solver, evaluate = reconstruct(model)
        bounds = {k: model[k] for k in ["lbx", "ubx", "lbg", "ubg"]}
        zx = ca.MX.sym("z", len(model["lbx"]))
        pp = ca.MX.sym("p", evaluate.size1_in(1))
        ff, gg = evaluate(zx, pp)
        lg = ca.MX.sym("lam_g", len(model["lbg"]))
        lx = ca.MX.sym("lam_x", len(model["lbx"]))
        stationarity = ca.Function(
            "stationarity",
            [zx, pp, lg, lx],
            [ca.gradient(ff, zx) + ca.jacobian(gg, zx).T @ lg + lx],
        )
        guess = np.array(record["initial"])
        parameter = np.array(record["parameters"])
        n = model["config"]["horizon"]
        nx = 6 * (n + 1)
        nu = 2 * n
        # Separate sensitivity initials, leaving the frozen production policy untouched.
        zero = np.clip(np.zeros_like(guess), model["lbx"], model["ubx"])
        zero[:nx] = np.tile(parameter[:6], n + 1)
        guesses = {"captured": guess, "zero_controls_tiled_state": zero}
        from apex.control.mpc.cost import CostScales
        from apex.control.mpc.preview import Preview
        from apex.control.mpc.problem import MPCConfig, MPCProblem
        from apex.models.tire.config import TirePhysics
        from apex.models.vehicle.parameters import VehicleParameters

        config = dict(model["config"])
        config["costs"] = CostScales(**config["costs"])
        config["tire_physics"] = TirePhysics(**config["tire_physics"])
        problem = MPCProblem(VehicleParameters(**model["vehicle"]), MPCConfig(**config))
        preview = Preview(np.zeros(n + 1), parameter[8:-16].reshape(11, n + 1, order="F"))
        guesses["production_cold_start"] = problem.pack(
            *problem.cold_start(parameter[:6], parameter[6:8], preview)
        )
        for sign in [-1, 1]:
            perturb = guess.copy()
            perturb[nx : nx + nu : 2] += sign * 1e-4
            guesses[f"steering_guess_{sign:+d}e-4"] = np.clip(perturb, model["lbx"], model["ubx"])
        if item.get("smooth_folder"):
            other = json.loads((Path(item["smooth_folder"]) / "nlp_snapshots.json").read_text())
            smooth = min(other, key=lambda r: abs(r["parameters"][4] - parameter[4]))
            from apex.control.mpc.warm_start import shift_solution

            if smooth["previous_solution"] is not None:
                guesses["smooth_run_shifted_guess"] = problem.pack(
                    *shift_solution(*problem.unpack(smooth["previous_solution"]), parameter[:6])
                )
            else:
                guesses["smooth_run_startup_guess"] = np.array(smooth["initial"])
        base = None

        def solve(initial, p, label, repeat):
            start = time.perf_counter()
            answer = solver(x0=initial, p=p, **bounds)
            wall = time.perf_counter() - start
            stats = solver.stats()
            z = np.asarray(answer["x"]).ravel()
            g = np.asarray(answer["g"]).ravel()
            infeas = max(
                np.maximum(np.array(model["lbg"]) - g, 0).max(),
                np.maximum(g - np.array(model["ubg"]), 0).max(),
                np.maximum(np.array(model["lbx"]) - z, 0).max(),
                np.maximum(z - np.array(model["ubx"]), 0).max(),
            )
            it = stats.get("iterations", {})
            return dict(
                label=label,
                repeat=repeat,
                solution=z.tolist(),
                initial=initial.tolist(),
                parameters=p.tolist(),
                objective=float(answer["f"]),
                status=stats["return_status"],
                success=bool(stats["success"]),
                iterations=stats["iter_count"],
                seconds=wall,
                primal_residual=float(infeas),
                stationarity_inf=float(
                    np.max(abs(np.asarray(stationarity(z, p, answer["lam_g"], answer["lam_x"]))))
                ),
                ipopt_inf_pr=None if not it.get("inf_pr") else it["inf_pr"][-1],
                ipopt_inf_du=None if not it.get("inf_du") else it["inf_du"][-1],
                first_control=z[nx : nx + 2].tolist(),
                lam_x=np.asarray(answer["lam_x"]).ravel().tolist(),
                lam_g=np.asarray(answer["lam_g"]).ravel().tolist(),
            )

        exact = [solve(guess, parameter, "exact", i) for i in range(20)]
        base = np.array(exact[0]["solution"])
        # Rebuild the backend too: implicit solver object memory cannot explain an agreement.
        solver, evaluate = reconstruct(model)
        fresh = solve(guess, parameter, "fresh_backend", 0)
        sensitivity = [
            solve(g, parameter, label, 0) for label, g in guesses.items() if label != "captured"
        ]
        for field, index in [("vx", 0), ("vy", 1), ("r", 2), ("epsi", 3), ("ey", 5)]:
            magnitude = item["state_perturbations"][field]
            for sign in [-1, 1]:
                p = parameter.copy()
                p[index] += sign * magnitude
                sensitivity.append(solve(guess, p, f"state_{field}_{sign:+d}", 0))
        result = dict(
            selection=item,
            captured_solution=record["solution"],
            exact=exact,
            fresh_backend=fresh,
            sensitivity=sensitivity,
            exact_max_difference=float(
                np.max(abs(np.array([r["solution"] for r in exact]) - base))
            ),
            captured_max_difference=float(np.max(abs(base - np.array(record["solution"])))),
            fresh_backend_max_difference=float(np.max(abs(base - np.array(fresh["solution"])))),
            casadi_version=ca.__version__,
        )
        records.append(result)
        print(item["name"], "exact max", result["exact_max_difference"], flush=True)
    output.write_text(json.dumps(records, indent=2) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selection", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("results/task007cr/nlp_replay.json"))
    p.add_argument("--worker", action="store_true")
    a = p.parse_args()
    from threading_study.config import configure_accelerate, environment

    if a.worker:
        configure_accelerate(1)
        run(a.selection, a.output)
    else:
        subprocess.run(
            [sys.executable, __file__, *sys.argv[1:], "--worker"], env=environment(1), check=True
        )


if __name__ == "__main__":
    main()
