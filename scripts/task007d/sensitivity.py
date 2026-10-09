"""D4-only stratification of retained D3 matched-release scores; no new forecasts."""

import numpy as np
from task007d.diagnostics import TIME_TOL, accuracy

from apex.state import STATE_NAMES

# Each tuple is planner/codriver seconds. D3 is a retained reference, never a rerun.
REGIMES = {
    "D4-R1": (0.035, 0.0),
    "D4-R2": (0.035, 0.005),
    "D4-R3": (0.060, 0.005),
    "D4-R4": (0.060, 0.015),
}
CATEGORIES = ("none", "due_now", "future")
ERROR_TIE = 1e-12  # Per-state absolute SI roundoff band, not a controller tolerance.


def pending_category(row):
    due = row["pending_application_time"]
    if not row["pending"]:
        if due is not None:
            raise ValueError("Inconsistent absent pending command")
        return "none"
    if due is None or not np.isfinite(due) or due < row["release_time"] - TIME_TOL:
        raise ValueError("Invalid release-known pending timestamp")
    return "due_now" if due <= row["release_time"] + TIME_TOL else "future"


def statistics(rows):
    summary = accuracy(rows)
    summary["pending_categories"] = {
        k: sum(pending_category(r) == k for r in rows) for k in CATEGORIES
    }
    paired = [r for r in rows if all(r["errors"][a] is not None for a in ("A", "B"))]
    counts = {}
    for i, state in enumerate(STATE_NAMES):
        difference = np.asarray(
            [abs(r["errors"]["B"][i]) - abs(r["errors"]["A"][i]) for r in paired]
        )
        counts[state] = dict(
            better=int(np.sum(difference < -ERROR_TIE)),
            worse=int(np.sum(difference > ERROR_TIE)),
            tie=int(np.sum(abs(difference) <= ERROR_TIE)),
        )
    summary["individual_absolute_error_counts"] = counts
    # Signed change is B-A; positive deterioration. D3 also retains percent reduction.
    summary["rms_change_b_minus_a"] = {
        k: summary["per_state"]["B"][k]["rms"] - summary["per_state"]["A"][k]["rms"]
        for k in summary["per_state"]["A"]
    }
    return summary


def stratify(rows):
    first = min((r["release_time"] for r in rows), default=None)
    return {
        "all": statistics(rows),
        "first": statistics([r for r in rows if r["release_time"] == first]),
        "subsequent": statistics([r for r in rows if r["release_time"] != first]),
    }


def release_table(rows, raw, regime, host):
    first = min((r["release_time"] for r in rows), default=None)
    plans = {p["plan_id"]: p for p in raw["plans"]}
    output = []
    for r in rows:
        plan = plans[r["plan_id"]]
        row = dict(
            regime=regime,
            host=host,
            plan_id=r["plan_id"],
            release_time=r["release_time"],
            phase="first" if r["release_time"] == first else "subsequent",
            estimated_delay=plan["estimated_delay"],
            target_time=r["target_time"],
            imposed_readiness_time=plan["completion_time"],
            readiness_processed=plan.get("completed", False),
            scheduled_readiness_minus_target=r["scheduled_readiness_minus_target"],
            readiness_minus_target=r["readiness_minus_target"],
            accepted_handoff_time=next((h["time"] for h in r["handoffs"] if h["accepted"]), None),
            accepted_handoff_minus_target=r["accepted_handoff_minus_target"],
            pending_category=pending_category(r),
            pending_application_time=r["pending_application_time"],
            truth_kind=r["truth"]["kind"],
            A_failure=r["forecasts"]["A"]["failure"],
            B_failure=r["forecasts"]["B"]["failure"],
        )
        for a in ("A", "B"):
            for i, state in enumerate(STATE_NAMES):
                row[a + "_error_" + state] = None if r["errors"][a] is None else r["errors"][a][i]
        output.append(row)
    return output


def transient_audit(rows):
    """Exploratory D4 follow-up: first-two-release dominance, not a replacement endpoint."""
    ordered = sorted(rows, key=lambda r: r["release_time"])
    output = {}
    for i, state in enumerate(STATE_NAMES):
        paired = [r for r in ordered if all(r["errors"][a] is not None for a in ("A", "B"))]
        denominator = sum(r["errors"]["A"][i] ** 2 for r in paired)
        shares = []
        for r in ordered[:2]:
            shares.append(
                100 * r["errors"]["A"][i] ** 2 / denominator
                if denominator and r in paired
                else None
            )
        tail = [r for r in ordered[2:] if r in paired]
        ar = float(np.sqrt(np.mean([r["errors"]["A"][i] ** 2 for r in tail]))) if tail else None
        br = float(np.sqrt(np.mean([r["errors"]["B"][i] ** 2 for r in tail]))) if tail else None
        worst = max(
            paired, key=lambda r: abs(r["errors"]["B"][i]) - abs(r["errors"]["A"][i]), default=None
        )
        output[state] = dict(
            first_A_squared_error_share_percent=shares[0] if shares else None,
            second_A_squared_error_share_percent=shares[1] if len(shares) > 1 else None,
            after_second_count=len(tail),
            after_second_A_rms=ar,
            after_second_B_rms=br,
            after_second_rms_reduction_percent=100 * (1 - br / ar) if ar else None,
            maximum_B_absolute_error_increase=None
            if worst is None
            else dict(
                plan_id=worst["plan_id"],
                release_time=worst["release_time"],
                A_error=worst["errors"]["A"][i],
                B_error=worst["errors"]["B"][i],
                increase=abs(worst["errors"]["B"][i]) - abs(worst["errors"]["A"][i]),
            ),
        )
    return output
