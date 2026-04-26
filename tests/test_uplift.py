from __future__ import annotations

from app.dataset import generate_rows
from app.uplift import estimate_uplift


def test_uplift_report_recommends_high_intent_segment() -> None:
    report = estimate_uplift(generate_rows())

    assert report["customers_analyzed"] == 2400
    assert report["top_recommended_segment"] == "new_high_intent"
    assert report["uplift_at_top_quartile"] >= 0.09
    assert any(not row["recommended"] for row in report["segment_summary"])
    assert report["portfolio_expected_net_value"] > 0
    assert report["targeted_customers"] > 0
    assert all("expected_net_value_per_1000" in row for row in report["segment_summary"])
    assert report["evaluation"]["qini_auc"] > 0
    assert len(report["evaluation"]["uplift_curve"]) == 10
    assert len(report["evaluation"]["qini_curve"]) == 10
