from __future__ import annotations

from collections import defaultdict

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier


def _features(rows: list[dict[str, float | int | str]]) -> np.ndarray:
    return np.array(
        [
            [
                row["engagement_score"],
                row["price_sensitivity"],
                row["tenure_score"],
                1.0 if row["segment"] == "new_high_intent" else 0.0,
                1.0 if row["segment"] == "dormant_price_sensitive" else 0.0,
                1.0 if row["segment"] == "casual_mid_value" else 0.0,
            ]
            for row in rows
        ]
    )


def estimate_uplift(rows: list[dict[str, float | int | str]], seed: int = 20260426) -> dict[str, object]:
    treated = [row for row in rows if row["treatment"] == 1]
    control = [row for row in rows if row["treatment"] == 0]

    treated_model = GradientBoostingClassifier(random_state=seed)
    control_model = GradientBoostingClassifier(random_state=seed + 1)
    treated_model.fit(_features(treated), [row["converted"] for row in treated])
    control_model.fit(_features(control), [row["converted"] for row in control])

    all_features = _features(rows)
    treated_scores = treated_model.predict_proba(all_features)[:, 1]
    control_scores = control_model.predict_proba(all_features)[:, 1]
    uplift_scores = treated_scores - control_scores

    segment_buckets: dict[str, list[float]] = defaultdict(list)
    for row, uplift_score in zip(rows, uplift_scores, strict=True):
        segment_buckets[str(row["segment"])].append(float(uplift_score))

    segment_summary = [
        {
            "segment": segment,
            "estimated_uplift": round(sum(scores) / len(scores), 4),
            "recommended": (sum(scores) / len(scores)) > 0.04,
        }
        for segment, scores in sorted(segment_buckets.items())
    ]

    ranked = sorted(
        (
            {
                "customer_id": row["customer_id"],
                "segment": row["segment"],
                "estimated_uplift": round(float(score), 6),
            }
            for row, score in zip(rows, uplift_scores, strict=True)
        ),
        key=lambda row: row["estimated_uplift"],
        reverse=True,
    )

    top_quartile = ranked[: len(ranked) // 4]
    top_quartile_ids = {row["customer_id"] for row in top_quartile}
    treated_top = [row for row in rows if row["customer_id"] in top_quartile_ids and row["treatment"] == 1]
    control_top = [row for row in rows if row["customer_id"] in top_quartile_ids and row["treatment"] == 0]
    uplift_at_top_quartile = (
        (sum(row["converted"] for row in treated_top) / len(treated_top))
        - (sum(row["converted"] for row in control_top) / len(control_top))
    )

    best_segment = max(segment_summary, key=lambda row: row["estimated_uplift"])

    return {
        "customers_analyzed": len(rows),
        "top_recommended_segment": best_segment["segment"],
        "segment_summary": segment_summary,
        "uplift_at_top_quartile": round(uplift_at_top_quartile, 4),
        "top_targets": top_quartile[:10],
    }
