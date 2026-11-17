
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.products import router as products_router
from app.routers.recommendations import router as recommendation_router


app = FastAPI(
    title="AI Gift Recommendation System",
    description="Occasion-based gift recommendations using Groq and Mixedbread embeddings",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(products_router)

@app.get("/health")
def health_check():
    return {
        "status": "success",
        "message": "Gift Recommendation API is running"
    }


app.include_router(products_router)

app.include_router(recommendation_router)