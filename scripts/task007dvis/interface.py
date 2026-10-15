"""apex-run/0.1.0 event phases, authority intervals and explicit availability semantics."""

from task007dvis.coverage import TOL

SCHEMA = "apex-run/0.1.0"
REQUEST_COVERAGE = dict(
    mode="applied_records_plus_available_release_snapshots",
    unapplied_tail_complete=False,
    terminal_unobserved_request="unknown",
)


def event_rows(raw):
    """Partial order from actual scheduler phases; never invent cross-stream tie order."""
    out = []

    def add(stream, index, kind, time, phase, row):
        out.append(
            dict(
                source_stream=stream,
                source_row=index,
                event_kind=kind,
                time=time,
                phase=phase,
                within_phase_order=None,
                ordering_status="phase_known_cross_stream_tie_unspecified",
                sample_provenance="native",
                plan_id=row.get("plan_id"),
                payload=row,
            )
        )

    for i, r in enumerate(raw.get("controls", [])):
        add("controls", i, "command_computed", r["time"], 5, r)
        add("controls", i, "command_applied", r["application_time"], 1, r)
    plans = {p["plan_id"]: p for p in raw.get("plans", [])}
    for i, p in enumerate(raw.get("plans", [])):
        if not p.get("startup") and p.get("completed"):
            add("plans", i, "preparation_ready", p["completion_time"], 2, p)
    for i, r in enumerate(raw.get("handoffs", [])):
        p = plans.get(r["plan_id"], {})
        immediate = abs(r["time"] - p.get("completion_time", -1)) <= TOL
        phase = 3 if "fixed_handoffs" in raw or not immediate else 2
        add(
            "handoffs",
            i,
            "handoff_accepted" if r["accepted"] else "handoff_rejected",
            r["time"],
            phase,
            r,
        )
    for stream, phase in [("releases", 6), ("misses", 6), ("codriver_misses", 5), ("fallbacks", 4)]:
        for i, r in enumerate(raw.get(stream, [])):
            add(stream, i, stream, r["time"], phase, r)
    for i, r in enumerate(raw.get("triggers", [])):
        add("triggers", i, r["kind"], r["time"], 5 if r["kind"] == "urgent_replan" else 4, r)
    for i, r in enumerate(raw.get("fixed_handoffs", [])):
        for field, phase in [("miss_time", 3), ("late_discard_time", 2)]:
            if r.get(field) is not None:
                add("fixed_handoffs", i, field, r[field], phase, r)
    return sorted(out, key=lambda r: (r["time"], r["phase"]))


def authority_intervals(raw):
    """Accepted trajectory authority, separate from command ownership and expiry."""
    if not raw.get("states"):
        return []
    packets = {p["plan_id"]: p for p in raw["packets"]}
    accepted = [(raw["states"][0]["time"], raw["states"][0]["plan_id"], "startup")]
    accepted.extend(
        (h["time"], h["plan_id"], "accepted_handoff") for h in raw["handoffs"] if h["accepted"]
    )
    end = raw.get("end_time", raw["states"][-1]["time"])
    out = []
    for i, (time, pid, origin) in enumerate(accepted):
        expiry = packets[pid]["horizon_end_time"]
        superseded = accepted[i + 1][0] if i + 1 < len(accepted) else None
        fallback = next((f["time"] for f in raw.get("fallbacks", []) if f["time"] >= time), None)
        stop = min([end, expiry] + [t for t in [superseded, fallback] if t is not None])
        out.append(
            dict(
                plan_id=pid,
                start=time,
                end=stop,
                origin=origin,
                expiry=expiry,
                superseded_at=superseded,
                fallback_at=fallback,
                right_censored=stop == end and superseded is None and expiry > end,
                interval_rule="left_inclusive; end_exclusive_except_observation_endpoint",
                sample_provenance="reconstructed",
                reconstruction="recorded_acceptance_and_expiry; no_packet_id_interpolation",
            )
        )
    return out


def missing_reasons(row, architecture):
    reasons = {}
    fixed_only = {
        "valid_from",
        "deadline_margin",
        "miss_time",
        "late_discard_time",
        "consecutive_misses",
    }
    for key, value in row.items():
        if value is not None:
            continue
        reasons[key] = (
            "not_applicable"
            if key in fixed_only and architecture == "A"
            else "ordering_not_recorded"
            if key == "within_phase_order"
            else "censored"
            if row.get("status") == "pending" or row.get("preparation_finish_censored")
            else "not_observed_or_not_applicable"
        )
    return reasons
