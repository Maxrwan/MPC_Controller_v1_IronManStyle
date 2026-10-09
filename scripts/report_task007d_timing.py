"""Offline D4 timing sensitivity report; reuses D3 evidence and scoring, never simulates."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from threading_study.config import configure_accelerate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results/task007d/d4"))
    parser.add_argument("--reference", type=Path, default=Path("results/task007d/d3"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    configure_accelerate(1)
    import numpy as np
    from task007d.diagnostics import residual
    from task007d.metrics import compare
    from task007d.sensitivity import REGIMES, release_table, stratify, transient_audit
    from task007d.worker import write

    from apex.planning_reference.track import load_track
    from apex.state import STATE_NAMES

    if (
        list(Path("results").rglob("MEASURED_ACTIVE"))
        or Path("results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Do not analyze concurrently with a campaign")
    cases = [
        (r, h, args.input / (r.replace("D4-", "") + "_" + h)) for r in REGIMES for h in ("A", "B")
    ]
    cases += [("D3-ref", h, args.reference / ("gamma2_" + h)) for h in ("A", "B")]
    runs, raw, sources, phase_rows, release_rows, gates, missing = {}, {}, {}, [], [], {}, []
    for regime, host, folder in cases:
        key = regime + "_" + host
        if not (folder / "summary.json").is_file():
            missing.append(
                dict(
                    case=key,
                    path=str(folder),
                    status="failed_without_summary" if folder.exists() else "not_run",
                    log=(folder / "worker.log").read_text()
                    if (folder / "worker.log").is_file()
                    else None,
                )
            )
            continue
        summary = json.loads((folder / "summary.json").read_text())
        scores = json.loads((folder / "scores.json").read_text())
        raw[key] = json.loads((folder / "raw.json").read_text())
        expected = (0.035, 0.015) if regime == "D3-ref" else REGIMES[regime]
        if (
            tuple(summary["timing"]["planner"]) != (expected[0],)
            or tuple(summary["timing"]["codriver"]) != (expected[1],)
            or summary["architecture"] != host
            or summary["gamma"] != 2.0
        ):
            raise ValueError("Case does not match the predeclared matrix: " + key)
        sources[key] = summary.pop("source_sha256")
        gates[key] = summary["stop_gate"]
        summary.update(
            regime=regime,
            retained_directory=str(folder),
            accuracy_by_phase=stratify(scores),
            exploratory_transient_audit=transient_audit(scores),
            evidence_sha256={
                name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                for name in ("raw.json", "summary.json", "scores.json", "release_contexts.json")
            },
        )
        summary["truth_kinds"] = {
            k: sum(r["truth"]["kind"] == k for r in scores)
            for k in sorted({r["truth"]["kind"] for r in scores})
        }
        reconstructed = [r["truth"] for r in scores if r["truth"]["kind"] == "reconstructed_rk4"]
        summary["reconstruction_max_abs"] = {
            channel: np.max(np.abs([r[channel] for r in reconstructed]), axis=0).tolist()
            if reconstructed
            else None
            for channel in ("interval_closure_error", "step_doubling_difference")
        }
        runs[key] = summary
        release_rows.extend(release_table(scores, raw[key], regime, host))
        for phase, stats in summary["accuracy_by_phase"].items():
            for state in STATE_NAMES:
                row = dict(
                    regime=regime,
                    host=host,
                    phase=phase,
                    state=state,
                    releases=stats["releases"],
                    comparable=stats["comparable"],
                    excluded=stats["excluded"],
                    **stats["pending_categories"],
                )
                for a in ("A", "B"):
                    row.update(
                        {
                            a + "_" + k: v
                            for k, v in stats["per_state"][a]
                            .get(
                                state, dict(mean_signed=None, rms=None, max_abs=None, p95_abs=None)
                            )
                            .items()
                        }
                    )
                    row[a + "_forecast_failures"] = stats["forecast_failures"][a]
                row.update(stats["individual_absolute_error_counts"][state])
                row["rms_change_b_minus_a"] = stats["rms_change_b_minus_a"].get(state)
                row["rms_reduction_percent"] = stats["rms_improvement_percent"].get(state)
                phase_rows.append(row)
    ref = runs["D3-ref_A"]
    comparable = {}
    for key, run in runs.items():
        comparable[key] = all(
            run[k] == ref[k]
            for k in (
                "configuration",
                "fixture_sha256",
                "vehicle_sha256",
                "initial_state",
                "requested_duration",
            )
        )
        comparable[key] &= all(
            v == sources["D3-ref_A"][f] for f, v in sources[key].items() if f.startswith("src/")
        )
        if not comparable[key]:
            raise ValueError("Frozen configuration/source mismatch: " + key)
    pairs = {}
    track, _, _ = load_track(Path(ref["fixture"]) / "track_source.json")
    for regime in [*REGIMES, "D3-ref"]:
        ka, kb = regime + "_A", regime + "_B"
        if ka not in raw or kb not in raw:
            pairs[regime] = dict(status="incomplete_pair")
            continue
        a, b = raw[ka], raw[kb]
        pair = compare(a, b, track)
        btimes = {round(r["time"], 10): r for r in b["states"]}
        pair["first_state_divergence"] = next(
            (
                dict(
                    time=ar["time"],
                    a_minus_b=residual(
                        [ar[k] for k in STATE_NAMES], [br[k] for k in STATE_NAMES]
                    ).tolist(),
                )
                for ar in a["states"]
                if (br := btimes.get(round(ar["time"], 10))) is not None
                and np.max(
                    abs(residual([ar[k] for k in STATE_NAMES], [br[k] for k in STATE_NAMES]))
                )
                > 1e-12
            ),
            None,
        )
        pair["accepted_handoff_chronology_identical"] = [
            (h["plan_id"], h["time"]) for h in a["handoffs"] if h["accepted"]
        ] == [(h["plan_id"], h["time"]) for h in b["handoffs"] if h["accepted"]]
        pair["fallbacks"] = {h: raw[regime + "_" + h]["fallbacks"] for h in ("A", "B")}
        pairs[regime] = pair
    args.output.mkdir(parents=True, exist_ok=False)
    write(
        args.output / "summary.json",
        dict(
            runs=runs,
            pairs=pairs,
            stop_gates=gates,
            missing_cases=missing,
            d3_reference_comparability=comparable,
        ),
    )
    write(args.output / "source_hashes.json", sources)
    for name, rows in [("accuracy_by_phase", phase_rows), ("release_scores", release_rows)]:
        with (args.output / (name + ".csv")).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(
        json.dumps(
            dict(
                cases=len(runs),
                new_cases=len([k for k in runs if k.startswith("D4")]),
                missing=missing,
                gates=gates,
            )
        )
    )


if __name__ == "__main__":
    main()
