from __future__ import annotations

import json
from pathlib import Path

from app.config import GENERATED_DIR


def _portable(path: Path) -> str:
    cwd = Path.cwd()
    try:
        return str(path.relative_to(cwd))
    except ValueError:
        return str(path)


def render_markdown(report: dict[str, object]) -> str:
    segment_lines = [
        f"- `{row['segment']}`: estimated uplift `{row['estimated_uplift']:.4f}`, "
        f"incremental_conversions_per_1000=`{row['incremental_conversions_per_1000']:.2f}`, "
        f"expected_net_value_per_1000=`{row['expected_net_value_per_1000']:.2f}`, recommended=`{row['recommended']}`"
        for row in report["segment_summary"]
    ]
    evaluation = report["evaluation"]
    uplift_curve_lines = [
        "| Fraction | Customers Seen | Treated Rate | Control Rate | Uplift |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    qini_curve_lines = [
        "| Fraction | Customers Seen | Cumulative Gain | Random Baseline | Qini Gain |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for point in evaluation["uplift_curve"]:
        uplift_curve_lines.append(
            f"| {point['fraction']:.2f} | {point['customers_seen']} | {point['treated_rate']:.4f} | "
            f"{point['control_rate']:.4f} | {point['uplift']:.4f} |"
        )
    for point in evaluation["qini_curve"]:
        qini_curve_lines.append(
            f"| {point['fraction']:.2f} | {point['customers_seen']} | {point['cumulative_gain']:.4f} | "
            f"{point['random_baseline_gain']:.4f} | {point['qini_gain']:.4f} |"
        )
    return "\n".join(
        [
            "# Uplift Targeting Brief",
            "",
            f"Top recommended segment: `{report['top_recommended_segment']}`",
            f"Uplift at top quartile: `{report['uplift_at_top_quartile']:.4f}`",
            f"Targeted customers: `{report['targeted_customers']}`",
            f"Portfolio expected net value: `{report['portfolio_expected_net_value']:.2f}`",
            f"Qini AUC: `{evaluation['qini_auc']:.4f}`",
            "",
            "## Segment Summary",
            "",
            *segment_lines,
            "",
            "## Uplift Curve",
            "",
            *uplift_curve_lines,
            "",
            "## Qini Curve",
            "",
            *qini_curve_lines,
            "",
        ]
    )


def write_outputs(report: dict[str, object]) -> tuple[str, str]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    json_path = GENERATED_DIR / "uplift_report.json"
    markdown_path = GENERATED_DIR / "targeting_brief.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    return _portable(json_path), _portable(markdown_path)
