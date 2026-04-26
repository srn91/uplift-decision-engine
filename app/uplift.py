from __future__ import annotations

from collections import defaultdict
import math

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


def _evaluation_curves(
    rows: list[dict[str, float | int | str]],
    uplift_scores: np.ndarray,
) -> dict[str, object]:
    ranked = sorted(zip(rows, uplift_scores, strict=True), key=lambda row: float(row[1]), reverse=True)
    total_rows = len(ranked)
    overall_treated = [row for row, _score in ranked if int(row["treatment"]) == 1]
    overall_control = [row for row, _score in ranked if int(row["treatment"]) == 0]
    overall_treated_rate = sum(int(row["converted"]) for row in overall_treated) / len(overall_treated)
    overall_control_rate = sum(int(row["converted"]) for row in overall_control) / len(overall_control)
    overall_rate_gap = overall_treated_rate - overall_control_rate

    uplift_curve: list[dict[str, float | int]] = []
    qini_curve: list[dict[str, float | int]] = []
    qini_area = 0.0
    previous_fraction = 0.0
    previous_qini_gain = 0.0

    for step in range(1, 11):
        fraction = step / 10.0
        cutoff = max(1, math.ceil(total_rows * fraction))
        subset = ranked[:cutoff]
        treated_subset = [row for row, _score in subset if int(row["treatment"]) == 1]
        control_subset = [row for row, _score in subset if int(row["treatment"]) == 0]

        treated_rate = (
            sum(int(row["converted"]) for row in treated_subset) / len(treated_subset)
            if treated_subset
            else 0.0
        )
        control_rate = (
            sum(int(row["converted"]) for row in control_subset) / len(control_subset)
            if control_subset
            else 0.0
        )
        uplift = treated_rate - control_rate

        treated_successes = sum(int(row["converted"]) for row in treated_subset)
        control_successes = sum(int(row["converted"]) for row in control_subset)
        cumulative_gain = 0.0
        if treated_subset and control_subset:
            cumulative_gain = treated_successes - control_successes * (
                len(treated_subset) / len(control_subset)
            )
        random_baseline_gain = overall_rate_gap * cutoff
        qini_gain = cumulative_gain - random_baseline_gain

        uplift_curve.append(
            {
                "fraction": round(fraction, 2),
                "customers_seen": cutoff,
                "treated_rate": round(treated_rate, 4),
                "control_rate": round(control_rate, 4),
                "uplift": round(uplift, 4),
            }
        )
        qini_curve.append(
            {
                "fraction": round(fraction, 2),
                "customers_seen": cutoff,
                "cumulative_gain": round(cumulative_gain, 4),
                "random_baseline_gain": round(random_baseline_gain, 4),
                "qini_gain": round(qini_gain, 4),
            }
        )

        qini_area += (previous_qini_gain + qini_gain) * (fraction - previous_fraction) / 2.0
        previous_fraction = fraction
        previous_qini_gain = qini_gain

    return {
        "uplift_curve": uplift_curve,
        "qini_curve": qini_curve,
        "qini_auc": round(qini_area / total_rows, 4),
    }


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
    segment_rows: dict[str, list[dict[str, float | int | str]]] = defaultdict(list)
    for row, uplift_score in zip(rows, uplift_scores, strict=True):
        segment_buckets[str(row["segment"])].append(float(uplift_score))
        segment_rows[str(row["segment"])].append(row)

    segment_summary = [
        {
            "segment": segment,
            "estimated_uplift": round(sum(scores) / len(scores), 4),
            "incremental_conversions_per_1000": round((sum(scores) / len(scores)) * 1000, 2),
            "expected_net_value_per_1000": round(
                (((sum(scores) / len(scores)) * float(segment_rows[segment][0]["expected_margin"])) - float(segment_rows[segment][0]["treatment_cost"])) * 1000,
                2,
            ),
            "recommended": (
                (sum(scores) / len(scores)) > 0.04
                and ((((sum(scores) / len(scores)) * float(segment_rows[segment][0]["expected_margin"])) - float(segment_rows[segment][0]["treatment_cost"])) > 0)
            ),
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
    evaluation = _evaluation_curves(rows, uplift_scores)
    targeted_customers = [
        row for row, score in zip(rows, uplift_scores, strict=True)
        if any(
            summary["segment"] == row["segment"] and summary["recommended"]
            for summary in segment_summary
        )
    ]
    portfolio_net_value = round(
        sum(
            (float(score) * float(row["expected_margin"])) - float(row["treatment_cost"])
            for row, score in zip(rows, uplift_scores, strict=True)
            if any(summary["segment"] == row["segment"] and summary["recommended"] for summary in segment_summary)
        ),
        2,
    )

    return {
        "customers_analyzed": len(rows),
        "top_recommended_segment": best_segment["segment"],
        "segment_summary": segment_summary,
        "uplift_at_top_quartile": round(uplift_at_top_quartile, 4),
        "targeted_customers": len(targeted_customers),
        "portfolio_expected_net_value": portfolio_net_value,
        "top_targets": top_quartile[:10],
        "evaluation": evaluation,
    }
