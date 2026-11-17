
from app.ai.context_generator import ContextGenerator
from app.ai.embedding_service import EmbeddingService
from app.ai.similarity_search import SimilaritySearchService
from app.ai.product_validator import ProductValidator
from app.services.catalog_service import CatalogService
from app.core.config import settings


class RecommendationService:

    def __init__(
        self,
        context_generator=None,
        embedding_service=None,
        similarity_search=None,
        catalog_service=None,
        product_validator=None
    ):
        self.context_generator = (
            context_generator if context_generator is not None
            else ContextGenerator()
        )

        self.embedding_service = (
            embedding_service if embedding_service is not None
            else EmbeddingService()
        )

        self.similarity_search = (
            similarity_search if similarity_search is not None
            else SimilaritySearchService()
        )

        self.catalog_service = (
            catalog_service if catalog_service is not None
            else CatalogService()
        )

        self.product_validator = (
            product_validator if product_validator is not None
            else ProductValidator()
        )

    def recommend(self, occasion: str, top_k: int = 10) -> dict:

        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")

        # Generate gift context
        context = self.context_generator.generate(occasion)

        # Generate query embedding
        query_vector = self.embedding_service.embed_query(context)

        # Retrieve ranked candidates
        ranked = self.similarity_search.search(
            query_vector,
            top_k=len(self.similarity_search.product_ids)
        )

        # Fetch eligible products
        eligible = {
            product.id: product
            for product in self.catalog_service.get_eligible_products()
        }

        candidates = []
        seen_ids = set()

        for item in ranked:
            product_id = item["product_id"]

            if product_id in seen_ids:
                continue

            product = eligible.get(product_id)

            if product is None:
                continue

            seen_ids.add(product_id)

            candidates.append((
                product,
                item["similarity_score"]
            ))

        recommendations = []
        rejected_ids = []

        cursor = 0
        attempts = 0

        # Maximum 3 validation batches
        while (
            len(recommendations) < top_k
            and attempts < settings.MAX_RETRIES
            and cursor < len(candidates)
        ):
            needed = top_k - len(recommendations)

            batch = candidates[cursor:cursor + needed]

            cursor += len(batch)
            attempts += 1

            decisions = self.product_validator.validate(
                occasion,
                [product for product, _ in batch]
            )

            for product, score in batch:

                if decisions.get(product.id) is not True:
                    rejected_ids.append(product.id)
                    continue

                recommendations.append({
                    "product_id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "mainImage": product.mainImage,
                    "similarity_score": round(score, 4)
                })

        return {
            "occasion": occasion,
            "generated_context": context,
            "total_recommendations": len(recommendations),
            "validation_attempts": attempts,
            "rejected_product_ids": rejected_ids,
            "recommendations": recommendations
        }
