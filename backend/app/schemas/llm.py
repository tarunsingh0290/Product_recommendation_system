from pydantic import BaseModel, ConfigDict, Field

class StrictPayload(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

class OccasionContext(StrictPayload):
    valid: bool
    occasion: str
    intent_summary: str
    gift_categories: list[str]
    search_phrases: list[str]
    excluded_occasions: list[str]

class Suitability(StrictPayload):
    candidate_id: str
    suitable: bool
    suitability_score: float = Field(ge=0, le=1, allow_inf_nan=False)
    reason: str = Field(min_length=1, max_length=500)

class ValidationBatch(StrictPayload):
    evaluations: list[Suitability]
