from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get('/api/health')
def health(request: Request):
    return {'status': 'ok', 'ready': request.app.state.service is not None}

@router.get('/api/health/ready')
def ready(request: Request):
    error = request.app.state.readiness_error
    if request.app.state.service is not None:
        try:
            request.app.state.service.catalog.assert_unchanged()
        except Exception:
            error = 'Catalog changed or unavailable. Rebuild index and restart.'
    return JSONResponse(status_code=503 if error else 200,
                        content={'ready': not bool(error), 'detail': error or 'Ready'})
