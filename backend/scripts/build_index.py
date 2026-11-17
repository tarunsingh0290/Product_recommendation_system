
import json
from pathlib import Path

import numpy as np

from app.services.catalog_service import CatalogService
from app.ai.embedding_service import EmbeddingService


BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = BASE_DIR / "artifacts"


def build_index():
    # Load eligible products
    catalog = CatalogService()
    products = catalog.get_eligible_products()

    if not products:
        raise ValueError("No eligible products found")

    # Prepare product text
    product_ids = [product.id for product in products]
    product_texts = [
        product.embedding_text()
        for product in products
    ]

    # Generate embeddings
    embedding_service = EmbeddingService()

    embeddings = embedding_service.embed_products(
        product_texts
    )

    # Validate embedding dimensions
    if embeddings.shape != (len(products), 1024):
        raise ValueError(
            f"Unexpected embedding shape: {embeddings.shape}"
        )

    # Save artifacts
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    np.save(
        ARTIFACT_DIR / "vectors.npy",
        embeddings
    )

    with (ARTIFACT_DIR / "product_ids.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(product_ids, file, indent=2)

    print("Index built successfully")
    print(f"Products indexed: {len(products)}")
    print(f"Embedding shape: {embeddings.shape}")


if __name__ == "__main__":
    build_index()
