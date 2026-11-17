
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse
)

from app.services.recommendation_service import (
    RecommendationService
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Recommendations"]
)


@lru_cache(maxsize=1)
def get_recommendation_service():
    return RecommendationService()


@router.post(
    "/recommendations",
    response_model=RecommendationResponse
)
def recommend_gifts(
    request: RecommendationRequest,
    service: RecommendationService = Depends(
        get_recommendation_service
    )
):
    try:
        return service.recommend(
            occasion=request.occasion.strip(),
            top_k=request.top_k
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error
