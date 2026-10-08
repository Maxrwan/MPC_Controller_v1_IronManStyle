"""Publish complete distributions and numerical summaries as readable Markdown tables."""

import json
from pathlib import Path


def number(value):
    return f"{value:.7g}"


def main():
    root = Path("results/task007cr")
    r = json.loads((root / "outcome_distributions.json").read_text())
    lines = [
        "# Task007C-R distributions",
        "",
        "Ten fresh measured runs per configuration. All retained.",
        "",
    ]
    for label, stats in r["distributions"].items():
        lines += [
            f"## {label.upper()}: run-wise distributions",
            "",
            "| Metric | min | p25 | median | p75 | p95 | max |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for metric, values in stats.items():
            if metric == "pooled_nonstartup_calls":
                continue
            lines.append(
                "| " + metric + " | " + " | ".join(number(v) for v in values.values()) + " |"
            )
        lines += [
            "",
            "### Pooled nonstartup calls",
            "",
            "| Metric | min | p25 | median | p75 | p95 | max |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for metric, values in stats["pooled_nonstartup_calls"].items():
            lines.append(
                "| " + metric + " | " + " | ".join(number(v) for v in values.values()) + " |"
            )
        lines += [
            "",
            "### Separate event counts",
            "",
            "| Event | Threshold | 0.8× threshold | baseline | 1.2× threshold |",
            "|---|---|---:|---:|---:|",
        ]
        for event, counts in r["event_counts"][label].items():
            metric, op, threshold = r["event_definitions"][event]
            vals = [f"{v['count']}/{v['denominator']}" for v in counts.values()]
            lines.append(f"| {event} | {metric} {op} {threshold:g} | " + " | ".join(vals) + " |")
        lines += [""]
    lines += [
        "Threshold multipliers are descriptive sensitivity checks; boundary threshold stays zero.",
        "",
        "Do not treat these indicators as one combined bad-run score or a safety certificate.",
    ]
    (root / "DISTRIBUTIONS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
