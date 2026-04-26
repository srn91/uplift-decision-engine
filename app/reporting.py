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
        f"- `{row['segment']}`: estimated uplift `{row['estimated_uplift']:.4f}`, recommended=`{row['recommended']}`"
        for row in report["segment_summary"]
    ]
    return "\n".join(
        [
            "# Uplift Targeting Brief",
            "",
            f"Top recommended segment: `{report['top_recommended_segment']}`",
            f"Uplift at top quartile: `{report['uplift_at_top_quartile']:.4f}`",
            "",
            "## Segment Summary",
            "",
            *segment_lines,
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
