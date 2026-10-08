"""Review the mandatory reproduction gate before any formulation experiment."""

import json
from pathlib import Path

from task007c.anchors import ANCHORS


def review(output=Path("results/task007c")):
    rows = []
    reports = {}
    for letter, previous in (*ANCHORS, ("e_repeat", "b3_g2.5_w1"), ("f_repeat", "b3_g2.5_w2")):
        new = json.loads((output / ("anchor_" + letter) / "analysis.json").read_text())
        old = json.loads((Path("results/task007b") / previous / "analysis.json").read_text())
        reports[letter] = new

        def lap_mean(r):
            values = r["lap_times"][1:] if len(r["lap_times"]) > 1 else r["lap_times"]
            return sum(values) / len(values)

        row = dict(
            anchor=letter,
            previous=previous,
            previous_lap_s=lap_mean(old),
            reproduced_lap_s=lap_mean(new),
            lap_difference_percent=100 * (lap_mean(new) / lap_mean(old) - 1),
            previous_slack_m=old["predicted_slack_max"],
            reproduced_slack_m=new["predicted_slack_max"],
        )
        for name, r in [("previous", old), ("reproduced", new)]:
            sweeper = next(s for s in r["sectors"] if s["sector"] == "fast_sweeper")["tracking"]
            row.update(
                {
                    name + "_" + k: v
                    for k, v in dict(
                        sweeper_heading_TV_rad=sweeper["apex_heading_total_variation"],
                        sweeper_ey_TV_m=sweeper["apex_ey_total_variation"],
                        sweeper_rate_limit_s=sweeper["steering_rate_limit_seconds"],
                        beta_max_rad=r["tracking"]["actual_beta"]["max_abs"],
                        local_ey_rms_m=r["tracking"]["error_e_y"]["rms"],
                        physical_clearance_m=r["physical_constraints"]["physical_clearance_min"],
                        front_max=r["physical_constraints"]["front_max"],
                        rear_max=r["physical_constraints"]["rear_max"],
                    ).items()
                }
            )
        rows.append(row)
    by_letter = {r["anchor"]: r for r in rows}
    # These are explicitly disclosed reproduction inspection gates, not a
    # difficulty score, controller threshold, or universal oscillation definition.
    checks = {
        "all_finish_without_physical_failure": all(
            r["failure"] is None
            and r["physical_constraints"]["boundary_violations"] == 0
            and r["physical_constraints"]["global_fallbacks"] == 0
            for r in reports.values()
        ),
        "conservative_lap_agreement_within_half_percent": all(
            abs(by_letter[k]["lap_difference_percent"]) < 0.5 for k in ["a", "b"]
        ),
        "gamma2_lap_agreement_within_two_percent": all(
            abs(by_letter[k]["lap_difference_percent"]) < 2 for k in ["c", "d"]
        ),
        "conservative_progress_benefit_reproduced": by_letter["b"]["reproduced_lap_s"]
        < by_letter["a"]["reproduced_lap_s"],
        "e_sweeper_large_heading_variation_reproduced": by_letter["e"][
            "reproduced_sweeper_heading_TV_rad"
        ]
        > 3,
        "e_sweeper_persistent_rate_activity_reproduced": by_letter["e"][
            "reproduced_sweeper_rate_limit_s"
        ]
        > 1,
        "f_material_slack_reproduced": reports["f"]["predicted_slack_max"] > 1e-6,
        "f_physical_tracking_margin_shortfall_reproduced": reports["f"]["physical_constraints"][
            "physical_clearance_min"
        ]
        < 0.08,
    }
    repeat_checks = {
        "e_sweeper_large_heading_variation_reproduced": by_letter["e_repeat"][
            "reproduced_sweeper_heading_TV_rad"
        ]
        > 3,
        "e_sweeper_persistent_rate_activity_reproduced": by_letter["e_repeat"][
            "reproduced_sweeper_rate_limit_s"
        ]
        > 1,
        "f_material_slack_reproduced": reports["f_repeat"]["predicted_slack_max"] > 1e-6,
        "f_physical_tracking_margin_shortfall_reproduced": reports["f_repeat"][
            "physical_constraints"
        ]["physical_clearance_min"]
        < 0.08,
    }
    result = dict(
        cases=rows,
        inspection_checks=checks,
        numerical_inspection_passed=all(checks.values()),
        additional_repeat_checks=repeat_checks,
        additional_repeats_reproduce_rejected_behavior=all(repeat_checks.values()),
        visual_review_required=True,
        note="Do not advance if rejected behavior is not reproduced; review all metrics.",
    )
    (output / "anchor_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    review()
