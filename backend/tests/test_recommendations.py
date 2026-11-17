
import numpy as np

from app.services.recommendation_service import RecommendationService


class FakeContextGenerator:
    def generate(self, occasion):
        return "Diwali sweets candles and decorative gifts"


class FakeEmbeddingService:
    def embed_query(self, context):
        return np.ones(1024, dtype=np.float32)


class FakeSimilaritySearch:
    product_ids = ["p1", "p2", "p3"]

    def search(self, query_vector, top_k=10):
        return [
            {"product_id": "p1", "similarity_score": 0.9},
            {"product_id": "p2", "similarity_score": 0.8},
            {"product_id": "p3", "similarity_score": 0.7}
        ][:top_k]


class FakeProduct:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.price = "100"
        self.mainImage = None


class FakeCatalogService:
    def get_eligible_products(self):
        return [
            FakeProduct("p1", "Diwali Sweets"),
            FakeProduct("p2", "Car Tyre"),
            FakeProduct("p3", "Decorative Diyas")
        ]


class FakeProductValidator:
    def validate(self, occasion, products):
        return {
            product.id: product.id != "p2"
            for product in products
        }


def test_recommendation_feedback_loop():
    service = RecommendationService(
        context_generator=FakeContextGenerator(),
        embedding_service=FakeEmbeddingService(),
        similarity_search=FakeSimilaritySearch(),
        catalog_service=FakeCatalogService(),
        product_validator=FakeProductValidator()
    )

    result = service.recommend("Diwali", top_k=2)

    assert result["total_recommendations"] == 2
    assert result["validation_attempts"] == 2
    assert result["rejected_product_ids"] == ["p2"]

    product_ids = [
        product["product_id"]
        for product in result["recommendations"]
    ]

    assert product_ids == ["p1", "p3"]
