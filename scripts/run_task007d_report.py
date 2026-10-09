"""Offline D3 compact evidence export; no simulation, overwrite or dashboard generation."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from threading_study.config import configure_accelerate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    configure_accelerate(1)
    import numpy as np
    from task007d.diagnostics import residual
    from task007d.metrics import compare
    from task007d.worker import write

    from apex.planning_reference.track import load_track
    from apex.state import STATE_NAMES

    args.output.mkdir(parents=True, exist_ok=False)
    runs, histories, statistics, releases, sources = {}, {}, [], [], {}
    for folder in sorted(args.input.iterdir()):
        if not (folder / "summary.json").exists():
            continue
        summary = json.loads((folder / "summary.json").read_text())
        rows = json.loads((folder / "scores.json").read_text())
        key = f"gamma{summary['gamma']:g}_{summary['architecture']}"
        if key in runs:
            raise ValueError("Duplicate successful case: select a distinct input root")
        sources[key] = summary.pop("source_sha256")
        summary["retained_directory"] = str(folder)
        for filename in ("raw.json", "release_contexts.json", "scores.json", "summary.json"):
            summary[filename + "_sha256"] = hashlib.sha256(
                (folder / filename).read_bytes()
            ).hexdigest()
        runs[key] = summary
        histories[key] = json.loads((folder / "raw.json").read_text())
        for state in STATE_NAMES:
            entry = dict(
                case=key,
                state=state,
                n=summary["matched"]["comparable"],
                pending=summary["matched"]["pending"],
            )
            for a in ("A", "B"):
                entry.update(
                    {
                        a + "_" + k: v
                        for k, v in summary["matched"]["per_state"][a]
                        .get(state, dict(mean_signed=None, rms=None, max_abs=None, p95_abs=None))
                        .items()
                    }
                )
            entry["rms_improvement_percent"] = summary["matched"]["rms_improvement_percent"].get(
                state
            )
            statistics.append(entry)
        for row in rows:
            entry = {
                k: row[k]
                for k in (
                    "plan_id",
                    "release_time",
                    "target_time",
                    "active_plan_id",
                    "pending",
                    "pending_application_time",
                    "readiness_minus_target",
                    "accepted_handoff_minus_target",
                )
            }
            entry.update(case=key, truth_kind=row["truth"]["kind"])
            for a in ("A", "B"):
                for i, state in enumerate(STATE_NAMES):
                    entry[a + "_error_" + state] = (
                        None if row["errors"][a] is None else row["errors"][a][i]
                    )
            releases.append(entry)
        reconstruction = [r["truth"] for r in rows if r["truth"]["kind"] == "reconstructed_rk4"]
        summary["reconstruction"] = dict(
            kinds={
                kind: sum(r["truth"]["kind"] == kind for r in rows)
                for kind in sorted({r["truth"]["kind"] for r in rows})
            },
            max_event_timestamp_offset=max(
                (abs(r["truth"].get("target_offset", 0)) for r in rows), default=0
            ),
            max_abs_interval_closure=np.max(
                np.abs([r["interval_closure_error"] for r in reconstruction]), axis=0
            ).tolist()
            if reconstruction
            else None,
            max_abs_step_doubling_difference=np.max(
                np.abs([r["step_doubling_difference"] for r in reconstruction]), axis=0
            ).tolist()
            if reconstruction
            else None,
        )
    pairs = {}
    for gamma in sorted({r["gamma"] for r in runs.values()}, reverse=True):
        ka, kb = f"gamma{gamma:g}_A", f"gamma{gamma:g}_B"
        if ka not in runs or kb not in runs:
            pairs[str(gamma)] = dict(
                status="incomplete_pair", available=[k for k in (ka, kb) if k in runs]
            )
            continue
        track, _, _ = load_track(Path(runs[ka]["fixture"]) / "track_source.json")
        pair = compare(histories[ka], histories[kb], track)
        by_time_b = {round(r["time"], 10): r for r in histories[kb]["states"]}
        pair["first_state_difference_over_1e-12"] = next(
            (
                dict(
                    time=a["time"],
                    a_minus_b=residual(
                        [a[k] for k in STATE_NAMES], [b[k] for k in STATE_NAMES]
                    ).tolist(),
                )
                for a in histories[ka]["states"]
                if (b := by_time_b.get(round(a["time"], 10))) is not None
                and np.max(abs(residual([a[k] for k in STATE_NAMES], [b[k] for k in STATE_NAMES])))
                > 1e-12
            ),
            None,
        )
        pairs[str(gamma)] = pair
    failed_launches = {
        str(f.parent): f.read_text()
        for f in args.input.glob("*/worker.log")
        if not (f.parent / "summary.json").exists()
    }
    write(
        args.output / "summary.json", dict(runs=runs, pairs=pairs, failed_launches=failed_launches)
    )
    write(args.output / "source_hashes.json", sources)
    for name, rows in [("accuracy", statistics), ("release_scores", releases)]:
        with (args.output / (name + ".csv")).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({"cases": list(runs), "releases": len(releases), "output": str(args.output)}))


if __name__ == "__main__":
    main()
