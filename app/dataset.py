from __future__ import annotations

import random


def generate_rows(seed: int = 20260426, size: int = 2400) -> list[dict[str, float | int | str]]:
    rng = random.Random(seed)
    rows: list[dict[str, float | int | str]] = []
    segments = [
        ("new_high_intent", 0.18, 0.14, 76.0, 3.2),
        ("loyal_discount_insensitive", 0.42, -0.02, 44.0, 5.8),
        ("dormant_price_sensitive", 0.08, 0.09, 68.0, 2.1),
        ("casual_mid_value", 0.15, 0.03, 58.0, 2.6),
    ]

    for index in range(size):
        segment_name, base_rate, treatment_effect, expected_margin, treatment_cost = segments[index % len(segments)]
        engagement = min(1.0, max(0.0, rng.gauss(0.5 + base_rate, 0.15)))
        price_sensitivity = min(1.0, max(0.0, rng.gauss(0.55 if "price" in segment_name else 0.35, 0.16)))
        tenure = min(1.0, max(0.0, rng.gauss(0.25 if "new" in segment_name else 0.7, 0.18)))
        treatment = 1 if rng.random() < 0.5 else 0
        probability = base_rate + 0.18 * engagement - 0.06 * tenure + (treatment_effect if treatment else 0.0)
        probability = min(0.95, max(0.02, probability))
        converted = 1 if rng.random() < probability else 0

        rows.append(
            {
                "customer_id": f"cust_{index + 1:04d}",
                "segment": segment_name,
                "engagement_score": round(engagement, 6),
                "price_sensitivity": round(price_sensitivity, 6),
                "tenure_score": round(tenure, 6),
                "expected_margin": expected_margin,
                "treatment_cost": treatment_cost,
                "treatment": treatment,
                "converted": converted,
            }
        )

    return rows
