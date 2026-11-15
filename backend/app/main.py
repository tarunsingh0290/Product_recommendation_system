from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import Settings
from app.core.exceptions import ServiceError
from app.services.catalog_service import CatalogService
from app.services.embedding_service import EmbeddingService
from app.services.recommendation_service import RecommendationService
from app.ai.llm_client import LLMClient
from app.routers import recommendations, health, products

def create_app(settings=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        client = None
        app.state.service = None
        app.state.catalog = None
        app.state.settings = settings
        app.state.readiness_error = ''
        try:
            catalog = CatalogService(settings.catalog_path)
            app.state.catalog = catalog
            if not catalog.products:
                raise ServiceError('No eligible catalog products. Supply products.json and build the index.')
            index = EmbeddingService(catalog, settings.artifacts_path)
            if not settings.groq_api_key:
                raise ServiceError('GROQ_API_KEY is not configured.')
            client = LLMClient(settings)
            app.state.service = RecommendationService(catalog, index, client, settings)
        except ServiceError as exc:
            app.state.readiness_error = str(exc)
        yield
        if client:
            client.close()

    app = FastAPI(title='Product Recommendation System', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, exc: ServiceError):
        content = {'detail': str(exc)}
        headers = {}
        if exc.retry_after_seconds is not None:
            content['retry_after_seconds'] = exc.retry_after_seconds
            headers['Retry-After'] = str(exc.retry_after_seconds)
        return JSONResponse(status_code=exc.status, content=content, headers=headers)

    app.include_router(recommendations.router)
    app.include_router(health.router)
    app.include_router(products.router)
    return app

app = create_app()
