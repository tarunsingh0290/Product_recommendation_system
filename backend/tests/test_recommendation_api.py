
from fastapi.testclient import TestClient

from app.main import app
from app.routers.recommendations import (
    get_recommendation_service
)


class FakeRecommendationService:

    def recommend(self, occasion: str, top_k: int = 10):
        return {
            "occasion": occasion,
            "generated_context": "Suitable gift products",
            "total_recommendations": 1,
            "validation_attempts": 1,
            "rejected_product_ids": [],
            "recommendations": [
                {
                    "product_id": "p1",
                    "name": "Decorative Diyas",
                    "price": "499",
                    "mainImage": None,
                    "similarity_score": 0.85
                }
            ]
        }


def test_recommendation_endpoint():
    app.dependency_overrides[
        get_recommendation_service
    ] = lambda: FakeRecommendationService()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/recommendations",
                json={
                    "occasion": "Diwali",
                    "top_k": 10
                }
            )

        assert response.status_code == 200

        data = response.json()

        assert data["occasion"] == "Diwali"
        assert data["total_recommendations"] == 1
        assert data["recommendations"][0]["product_id"] == "p1"

    finally:
        app.dependency_overrides.clear()


def test_invalid_top_k():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/recommendations",
            json={
                "occasion": "Birthday",
                "top_k": 15
            }
        )

    assert response.status_code == 422
