from fastapi import APIRouter, Request
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.core.exceptions import ServiceError

router = APIRouter()

@router.post('/api/recommendations', response_model=RecommendationResponse)
def recommend(payload: RecommendationRequest, request: Request):
    if 'top_k' not in payload.model_fields_set:
        payload.top_k = request.app.state.settings.default_top_k
    if request.app.state.service is None:
        raise ServiceError(request.app.state.readiness_error)
    return request.app.state.service.recommend(payload)
