from __future__ import annotations

from app.dataset import generate_rows
from app.uplift import estimate_uplift


def test_uplift_report_recommends_high_intent_segment() -> None:
    report = estimate_uplift(generate_rows())

    assert report["customers_analyzed"] == 2400
    assert report["top_recommended_segment"] == "new_high_intent"
    assert report["uplift_at_top_quartile"] >= 0.09
    assert any(not row["recommended"] for row in report["segment_summary"])
