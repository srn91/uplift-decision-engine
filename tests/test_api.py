from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint_lists_demo_paths() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["project"] == "uplift-decision-engine"
    assert body["endpoints"]["recommendation"] == "/recommendation"


def test_recommendation_endpoint_returns_uplift_summary() -> None:
    response = client.get("/recommendation")

    assert response.status_code == 200
    body = response.json()
    assert body["top_recommended_segment"] == "new_high_intent"
    assert body["portfolio_expected_net_value"] > 0
    assert body["evaluation"]["qini_auc"] > 0
