"""Reproducible CX tables from raw outputs; run only after all workers finish."""

import argparse
import json
from pathlib import Path

from task007dc.analysis import compare, extra
from task007dc.export import csv_rows, write

from apex.coordinates.angles import wrap_angle
from apex.state import STATE_NAMES
from task007dcx.analysis import (
    cycle_rows,
    distribution,
    miss_consequences,
    paired_samples,
    quality,
    timing_summary,
)
from task007dcx.worker import geometry, hashes


def flatten(value, prefix=""):
    result = {}
    for k, v in value.items():
        key = prefix + k
        if isinstance(v, dict):
            result.update(flatten(v, key + "."))
        elif not isinstance(v, list):
            result[key] = v
    return result


def build(source, output):
    if (
        list(Path("results").rglob("MEASURED_ACTIVE"))
        or Path("results/task007d/D3_ACTIVE").exists()
    ):
        raise RuntimeError("Measurement still active")
    output.mkdir(parents=True, exist_ok=False)
    track, reference, parameters = geometry()
    allrows = []
    perrun = []
    misses = []
    provenance = {}
    extras = {}
    groups = {}
    for folder in sorted(source.glob("S[12]_*")):
        raw = json.loads((folder / "raw.json").read_text())
        s = json.loads((folder / "summary.json").read_text())
        segments = json.loads((folder / "segments.json").read_text())
        assert not s["stop_gate"], (folder, s["stop_gate"])
        name = folder.name
        arch = s["spec"]["architecture"]
        rows = [
            dict(case=name, architecture=arch, repetition=s["spec"]["repetition"], **r)
            for r in cycle_rows(raw)
        ]
        q = quality(raw, track, reference)
        ex = extra(raw, segments, track, parameters)
        ex.pop("clearances")
        m = miss_consequences(raw, track, reference.manifest["sectors"])
        misses.extend(
            dict(case=name, architecture=arch, repetition=s["spec"]["repetition"], **r) for r in m
        )
        info = dict(
            case=name,
            architecture=arch,
            repetition=s["spec"]["repetition"],
            study=s["spec"]["study"],
            timing=timing_summary(rows, arch != "A"),
            quality=q,
            physical=s["physical"],
            extra=ex,
            startup_preparation_seconds=raw["plans"][0]["planner_total_time"],
            observed_threads=s["observed_process_thread_counts"],
            cpu_wall_ratio=s["cpu_seconds"] / s["wall_seconds"],
            forecast_matches=s["active_A_forecast_exact_matches"],
            releases=s["release_count"],
        )
        assert q["complete_common_coverage"], name
        perrun.append(info)
        allrows.extend(rows)
        extras[name] = ex
        provenance[name] = dict(
            raw_hashes=hashes(folder.glob("*.json")),
            source_hashes=s["source_sha256"],
            fixture_hashes=s["fixture_sha256"],
            vehicle_hash=s["vehicle_sha256"],
            packages=s["packages"],
            platform=s["platform"],
            native=s["native"],
            git_sha=s["git_sha"],
        )
        if s["spec"]["study"] == 2:
            groups.setdefault(arch, []).append(info)
        csv_rows(
            output / f"{name}_segments.csv",
            [{k: r[k] for k in ["start", "end", "dt"]} for r in segments],
        )
    csv_rows(output / "cycles.csv", allrows)
    csv_rows(output / "per_run.csv", [flatten(r) for r in perrun])
    if misses:
        csv_rows(output / "miss_consequences.csv", misses)
    else:
        (output / "miss_consequences.csv").write_text("case,plan_id,time,recovery_time\n")
    aggregate = {}
    for arch, runs in groups.items():
        rows = [r for r in allrows if r["architecture"] == arch and r["case"].startswith("S2")]
        flat = [flatten(r) for r in runs]
        fields = [
            k for k, v in flat[0].items() if isinstance(v, (int, float)) and not isinstance(v, bool)
        ]
        aggregate[arch] = dict(
            runs=len(runs),
            timing=timing_summary(rows, arch != "A"),
            per_run_statistics={k: distribution([r[k] for r in flat]) for k in fields},
            stop_gates=[],
            all_complete_common_coverage=True,
        )
    jitter = {}
    for arch, folder, stem in [
        ("A", source, "S1_A_"),
        ("C70", Path("results/task007d/c/amended"), "C1_"),
    ]:
        raws = [
            json.loads((folder / (stem + n) / "raw.json").read_text()) for n in ["steady", "jitter"]
        ]
        samples, metrics = paired_samples(*raws)
        csv_rows(output / f"jitter_{arch}_samples.csv", samples)
        cmd = []
        bytime = [{round(c["time"], 10): c for c in r["controls"]} for r in raws]
        for t in sorted(bytime[0].keys() & bytime[1].keys()):
            a, b = bytime[0][t], bytime[1][t]
            keys = ["requested_delta", "requested_a_cmd", "delta", "a_cmd", "application_time"] + [
                "reference_" + k for k in STATE_NAMES
            ]
            row = dict(time=t, plan_id_steady=a["plan_id"], plan_id_jitter=b["plan_id"])
            row.update(
                {
                    k: wrap_angle(a[k] - b[k]) if k == "reference_e_psi" else a[k] - b[k]
                    for k in keys
                }
            )
            cmd.append(row)
        csv_rows(output / f"jitter_{arch}_controls_references.csv", cmd)
        for raw, label in zip(raws, ["steady", "jitter"]):
            csv_rows(output / f"jitter_{arch}_{label}_cycles.csv", cycle_rows(raw))
            seg = json.loads((folder / (stem + label) / "segments.json").read_text())
            csv_rows(
                output / f"jitter_{arch}_{label}_segments.csv",
                [{k: r[k] for k in ["start", "end", "dt"]} for r in seg],
            )
        jitter[arch] = dict(metrics=metrics, detail=compare(*raws))
    write(
        output / "summary.json",
        dict(
            aggregate=aggregate,
            runs=perrun,
            jitter=jitter,
            misses=misses,
            coverage="All runs 2 s; quality uses recorded common 0–1.99 s grid. "
            "Physical extrema use full observed event history.",
        ),
    )
    write(output / "provenance.json", provenance)
    selection(output, aggregate)
    print(json.dumps({a: v["timing"] for a, v in aggregate.items()}, indent=2))


def selection(output, agg):
    rows = []
    fields = [
        ("minimum reserve", "physical.minimum_reserve", "minimum"),
        ("minimum center clearance", "physical.minimum_center_clearance", "minimum"),
        ("maximum slack", "physical.max_predicted_slack", "maximum"),
        ("maximum abs beta", "extra.max_abs_beta", "maximum"),
        ("mean applied steering TV", "quality.applied_steering_tv", "mean"),
        ("mean actual heading TV", "quality.actual_heading_tv", "mean"),
        ("mean steering-rate limit occupancy", "quality.steering_rate_limit_fraction", "mean"),
        ("mean lateral tracking RMS", "quality.tracking.e_y.rms", "mean"),
        ("mean heading tracking RMS", "quality.tracking.e_psi.rms", "mean"),
        ("mean progress rate", "quality.progress_rate", "mean"),
    ]
    for title, key, stat in fields:
        rows.append(
            dict(
                metric=title,
                **{a: agg[a]["per_run_statistics"][key][stat] for a in ["A", "C70", "C80"]},
            )
        )
    for title, key, stat in [
        ("p95 preparation seconds", "preparation", "p95"),
        ("p99 preparation seconds", "preparation", "p99"),
        ("mean accepted authority latency seconds", "accepted_latency", "mean"),
    ]:
        rows.append(dict(metric=title, **{a: agg[a]["timing"][key][stat] for a in agg}))
    rows.append(
        dict(metric="deadline miss fraction", **{a: agg[a]["timing"]["miss_fraction"] for a in agg})
    )
    csv_rows(output / "architecture_selection.csv", rows)
    lines = [
        "# Architecture selection — numerical inputs",
        "",
        "No production selection. A has no fixed deadline; its miss fraction is not applicable.",
        "",
        "| Metric | A | C70 | C80 |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            "| "
            + r["metric"]
            + " | "
            + " | ".join("N/A" if r[a] is None else f"{r[a]:.10g}" for a in ["A", "C70", "C80"])
            + " |"
        )
    (output / "architecture_selection.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    build(args.source, args.output)
