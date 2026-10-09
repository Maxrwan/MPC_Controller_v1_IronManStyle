"""Replay the retained N6 exhaustion chronology; never invent its unavailable tail."""

import csv
import hashlib
import json

from task007c_resume.campaign import ROOT, launch
from threading_study.config import configure_accelerate


def main():
    if (ROOT / "MEASURED_ACTIVE").exists():
        raise RuntimeError("Do not overlap measured work")
    source = ROOT / "g2_w0_vy1_r1_n6_measured_l1_rep00"
    events = json.loads((source / "events.json").read_text())
    with (source / "controls.csv").open() as handle:
        controls = list(csv.DictReader(handle))
    trace = dict(
        planner=[p["physical_delay"] for p in events["plans"] if not p["startup"]],
        codriver=[float(c["physical_latency"]) for c in controls],
        source=str(source),
        source_sha256={
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in ["events.json", "controls.csv", "summary.json"]
        },
        selection="The failed N6 measured repetition, selected as a post-hoc causal diagnostic.",
        exhaustion="No padding/cycling. The final planner delay is measured but pending at "
        "physical termination; its duration is retained. The driver history has no invented tail.",
    )
    path = ROOT / "trace_measured_n6_exhaustion.json"
    if path.exists():
        assert json.loads(path.read_text()) == trace
    else:
        path.write_text(json.dumps(trace, indent=2) + "\n")
    history = "measured_n6_exhaustion"
    histories = json.loads((ROOT / "histories.json").read_text())
    entry = dict(mode="replay", path=str(path), source=str(source))
    if history in histories:
        assert histories[history] == entry
    else:
        histories[history] = entry
        (ROOT / "histories.json").write_text(json.dumps(histories, indent=2) + "\n")
    repeated, summary = launch(gamma=2, history=history, horizon=6)
    configure_accelerate(1)
    from task007cr.compare import difference, pair

    report = pair(source, repeated)
    snapshots = [json.loads((f / "nlp_snapshots.json").read_text()) for f in [source, repeated]]
    offset = 6 * 7
    report["first_apex_control"] = difference(
        [p["solution"][offset : offset + 2] for p in snapshots[0]],
        [p["solution"][offset : offset + 2] for p in snapshots[1]],
        1e-9,
    )
    report["snapshot_counts"] = [len(p) for p in snapshots]
    assert len(set(report["snapshot_counts"])) == 1
    assert report["state_grid_exact"] and len(set(report["state_rows_original"])) == 1
    assert report["accepted_handoff_plan_ids_identical"]
    for k, v in report.items():
        if isinstance(v, dict) and "max_abs" in v:
            assert v["lengths_equal"] and v["max_abs"] == 0, (k, v)
    assert summary["stop_reason"] == "exhausted_outside_baseline_domain"
    report["exact_parity_passed"] = True
    (ROOT / "measured_n6_failure_replay_parity.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    reviews = json.loads((ROOT / "reviewed_failures.json").read_text())
    reviews[repeated.name] = dict(
        summary_sha256=hashlib.sha256((repeated / "summary.json").read_bytes()).hexdigest(),
        decision="Exact physical/NLP replay of the already reviewed measured N6 exhaustion; "
        "failure remains rejected evidence. Continue N8 only on this same finite history.",
    )
    (ROOT / "reviewed_failures.json").write_text(json.dumps(reviews, indent=2) + "\n")
    launch(gamma=2, history=history, horizon=8)
    print("Failure-history replay diagnostic complete; inspect N8 coverage explicitly", flush=True)


if __name__ == "__main__":
    main()
