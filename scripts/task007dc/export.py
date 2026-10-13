"""Export compact numerical C tables from retained raw runs, without rerunning physics."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from apex.config import load_vehicle_parameters
from apex.planning_reference.track import load_track
from task007dc.analysis import compare, cycles, extra


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def csv_rows(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)), lineterminator="\n"
        )
        w.writeheader()
        w.writerows(rows)


def export(source, output):
    output.mkdir(parents=True, exist_ok=False)
    raws, summaries, extras = {}, {}, {}
    p = load_vehicle_parameters("configs/vehicles/synthetic_dynamic_test_vehicle.yaml")
    provenance = {}
    for folder in sorted(source.glob("C[123]_*")):
        raw = json.loads((folder / "raw.json").read_text())
        summary = json.loads((folder / "summary.json").read_text())
        segments = json.loads((folder / "segments.json").read_text())
        track, _, _ = load_track(Path(summary["fixture"]) / "track_source.json")
        name = folder.name
        ex = extra(raw, segments, track, p)
        csv_rows(output / (name + "_clearance.csv"), ex.pop("clearances"))
        csv_rows(output / (name + "_cycles.csv"), cycles(raw))
        # Timing/physical tables underlying figures, no full trajectory/gain archives.
        csv_rows(output / (name + "_states.csv"), raw["states"])
        keys = [
            "time",
            "plan_id",
            "application_time",
            "nominal_delta",
            "delta",
            "a_cmd",
            "requested_delta",
            "requested_a_cmd",
            "nominal_a_cmd",
            "reference_e_psi",
            "reference_s_abs",
        ]
        csv_rows(
            output / (name + "_controls.csv"), [{k: r[k] for k in keys} for r in raw["controls"]]
        )
        csv_rows(output / (name + "_reserve.csv"), raw["reserves"])
        csv_rows(
            output / (name + "_segments.csv"),
            [{k: r[k] for k in ["start", "end", "dt"]} for r in segments],
        )
        raws[name] = raw
        extras[name] = ex
        summaries[name] = {
            k: summary[k]
            for k in [
                "physical",
                "stop_gate",
                "chronology_issues",
                "active_A_forecast_exact_matches",
                "release_count",
            ]
        }
        provenance[name] = {k: v for k, v in summary.items() if k not in summaries[name]}
        provenance[name]["raw_sha256"] = {
            f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.glob("*.json")
        }
    pairs = {"C1": ("C1_steady", "C1_jitter"), "C2": ("C1_steady", "C2_miss")}
    for gamma in ["2.0", "1.8"]:
        for offset in [70, 80]:
            pairs[f"C3_g{gamma}_vs_{offset}"] = (
                f"C3_g{gamma}_variable",
                f"C3_g{gamma}_fixed{offset}",
            )
    comparisons = {n: dict(a=a, b=b, **compare(raws[a], raws[b])) for n, (a, b) in pairs.items()}
    c2 = raws["C2_miss"]
    miss = next(c for c in cycles(c2) if c["status"] == "missed")
    previous = max(
        (c for c in cycles(c2) if c["t_accept"] is not None and c["t_accept"] < miss["miss_time"]),
        key=lambda c: c["t_accept"],
    )
    recovery = next(
        c for c in cycles(c2) if c["t_accept"] is not None and c["t_accept"] > miss["miss_time"]
    )
    window = [
        s
        for s in c2["states"]
        if miss["miss_time"] - 1e-10 <= s["time"] < recovery["t_accept"] - 1e-10
    ]
    missed = dict(
        cycle=miss,
        recovery=recovery,
        old_plan=previous["plan_id"],
        authority_gap=recovery["t_accept"] - previous["t_accept"],
        deadline_to_recovery=recovery["t_accept"] - miss["miss_time"],
        codriver_samples_during_miss=sum(
            miss["miss_time"] - 1e-10 <= c["time"] < recovery["t_accept"] - 1e-10
            for c in c2["controls"]
        ),
        recorded_progress_during_window=window[-1]["s_abs"] - window[0]["s_abs"],
        never_consumed=all(c["plan_id"] != miss["plan_id"] for c in c2["controls"]),
    )
    write(
        output / "summary.json",
        dict(runs=summaries, extra=extras, comparisons=comparisons, controlled_miss=missed),
    )
    write(output / "provenance.json", provenance)
    csv_rows(
        output / "responsiveness.csv",
        [
            dict(offset_ms=d, speed_mps=v, distance_m=v * d / 1000)
            for d in [50, 60, 70, 80]
            for v in [1.5, 3.0, 6.0]
        ],
    )
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.source, args.output)
