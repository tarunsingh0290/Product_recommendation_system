
import json
from pathlib import Path

import numpy as np

from app.services.catalog_service import CatalogService


ARTIFACT_DIR = (
    Path(__file__).resolve().parents[1]
    / "artifacts"
)


def test_saved_index():
    vectors = np.load(
        ARTIFACT_DIR / "vectors.npy"
    )

    with (
        ARTIFACT_DIR / "product_ids.json"
    ).open(encoding="utf-8") as file:
        product_ids = json.load(file)

    catalog = CatalogService()
    products = catalog.get_eligible_products()

    assert vectors.ndim == 2
    assert vectors.shape[1] == 1024
    assert vectors.shape[0] == len(product_ids)
    assert len(product_ids) == len(products)

    assert len(product_ids) == len(set(product_ids))
    assert product_ids == [p.id for p in products]

    assert np.isfinite(vectors).all()

    # Embeddings should be normalized
    norms = np.linalg.norm(vectors, axis=1)

    assert np.allclose(norms, 1.0, atol=1e-3)
