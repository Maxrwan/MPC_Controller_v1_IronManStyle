"""Readable per-state and physical C tables, derived solely from saved summaries."""

import argparse
import json
from pathlib import Path


def build(source, output):
    s = json.loads(source.read_text())
    lines = [
        "# Task007D-C compact numerical tables",
        "",
        (
            "All C3 runs: recorded states 0–1.995 s, codriver samples 0–1.990 s; "
            "physical run ends at 2 s."
        ),
        (
            "Canonical state units: vx/vy m/s, r rad/s, e_psi rad, s_abs/e_y m. "
            "Heading residuals wrapped."
        ),
        "TV is sum of absolute changes; world heading uses track heading plus Frenet heading.",
        (
            "Nominal TV is the sequence actually sampled by TVLQR; actual steering "
            "is physically applied."
        ),
        (
            "Rate magnitudes divide actual applied increments by elapsed application "
            "time; the startup command is prepositioned."
        ),
        (
            "Rate occupancy uses the unchanged 1 rad/s bound; reversals ignore "
            "magnitudes below 1e-10 rad/s."
        ),
        "",
    ]
    cases = [k for k in s["runs"] if k.startswith("C3")]

    def table(headers, rows):
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            lines.append(
                "| "
                + " | ".join(f"{x:.8g}" if isinstance(x, float) else str(x) for x in row)
                + " |"
            )
        lines.append("")

    lines += ["## Active APEX-to-vehicle tracking", ""]
    table(
        ["Run", "State", "RMS", "Maximum absolute"],
        [
            [n, k, v["rms"], v["max_abs"]]
            for n in cases
            for k, v in s["runs"][n]["physical"]["apex_vehicle_tracking"].items()
        ],
    )
    lines += ["## Physical and rate metrics", ""]
    for keys in [
        [
            "max_front_utilization",
            "max_rear_utilization",
            "max_abs_beta",
            "steering_utilization",
            "minimum_frenet_denominator",
        ],
        [
            "steering_rate_max_abs_rad_s",
            "steering_rate_rms_rad_s",
            "rate_reversals",
            "rate_limit_occupancy",
        ],
        [
            "nominal_heading_tv",
            "nominal_steering_tv",
            "nominal_acceleration_tv",
            "applied_acceleration_tv",
        ],
    ]:
        table(["Run", *keys], [[n, *[s["extra"][n][k] for k in keys]] for n in cases])
    lines += ["## Physical coverage / validity", ""]
    keys = [
        "progress_reached",
        "minimum_center_clearance",
        "minimum_reserve",
        "max_predicted_slack",
        "accepted_handoffs",
    ]
    table(["Run", *keys], [[n, *[s["runs"][n]["physical"][k] for k in keys]] for n in cases])
    lines += [
        (
            "Progress differences are millimetres or less over this short trace, not "
            "established racing gains."
        ),
        "",
        "## First common-event divergence",
        "",
        (
            "Difference threshold is 1e-12 for reporting, not a physics error "
            "tolerance. Comparisons also retain bitwise equality flags."
        ),
        "",
    ]
    table(
        [
            "Pair",
            "First physical state difference [s]",
            "First command generation difference [s]",
            "First reference difference [s]",
        ],
        [
            [
                n,
                *[
                    c[k]["first_difference"]["time"] if c[k]["first_difference"] else None
                    for k in ["states", "controls", "references"]
                ],
            ]
            for n, c in s["comparisons"].items()
        ],
    )
    lines += ["## C2 state difference versus matched no-miss history", ""]
    table(
        ["State", "RMS", "Maximum absolute"],
        [
            [k, v["rms"], v["max_abs"]]
            for k, v in s["comparisons"]["C2"]["states"]["metrics"].items()
        ],
    )
    lines += [
        "## Same-time accepted-handoff continuity",
        "",
        (
            "These are actual-minus-new-nominal errors at accepted handoff, not the "
            "readiness-state diagnostic."
        ),
        "",
    ]
    table(
        ["Run", "State", "RMS", "Maximum absolute"],
        [
            [n, k, v["rms"], v["max_abs"]]
            for n in cases
            for k, v in s["runs"][n]["physical"]["handoff_continuity"].items()
        ],
    )
    lines += [
        "## Event partitions",
        "",
        (
            "Counts are overlapping event-boundary classifications; coincident "
            "events must not be summed."
        ),
        "",
    ]
    keys = [
        "count",
        "minimum_dt",
        "maximum_dt",
        "non_grid_readiness",
        "readiness_boundaries",
        "handoff_boundaries",
        "application_boundaries",
        "readiness_only_boundaries",
    ]
    table(["Run", *keys], [[n, *[s["extra"][n]["rk4"][k] for k in keys]] for n in s["runs"]])
    with output.open("x") as f:
        f.write("\n".join(lines).rstrip() + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    build(args.source, args.output)
