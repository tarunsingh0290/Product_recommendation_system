
from pydantic import BaseModel, Field, ConfigDict


class RecommendationRequest(BaseModel):
    occasion: str = Field(
        min_length=1,
        max_length=100
    )

    top_k: int = Field(
        default=10,
        ge=1,
        le=10
    )


class RecommendedProduct(BaseModel):
    product_id: str
    name: str
    price: str
    originalPrice: str | None = None
    discountedPrice: str | None = None
    discountPercentage: str | None = None
    discountAmount: str | None = None
    mainImage: str | None = None
    similarity_score: float


class RecommendationResponse(BaseModel):
    occasion: str
    generated_context: str
    total_recommendations: int
    validation_attempts: int
    rejected_product_ids: list[str]
    recommendations: list[RecommendedProduct]
