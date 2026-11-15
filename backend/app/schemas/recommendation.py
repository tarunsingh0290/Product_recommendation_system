from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.utils.text import normalize
from app.schemas.product import ProductResponse

class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    occasion: str = Field(min_length=2, max_length=100)
    top_k: int = Field(default=10, ge=1, le=10)

    @field_validator('occasion', mode='before')
    @classmethod
    def meaningful(cls, value):
        if not isinstance(value, str):
            raise ValueError('Occasion must be a string')
        value = normalize(value)
        if len(value) < 2 or sum(c.isalpha() for c in value) < 2:
            raise ValueError('Describe a meaningful occasion')
        return value

class Recommendation(ProductResponse):
    similarity_score: float
    suitability_score: float
    reason: str
    suitability_passed: bool = True

class RecommendationResponse(BaseModel):
    occasion: str
    requested_count: int
    returned_count: int
    status: str = 'ok'
    recommendations: list[Recommendation]
    elapsed_ms: float
    cached: bool = False
    llm_calls: int = 0
    llm_tokens: int = 0
    warning: str | None = None
    retry_after_seconds: int | None = None
