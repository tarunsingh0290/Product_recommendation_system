
import json
from pathlib import Path

import numpy as np


BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = BASE_DIR / "artifacts"


class SimilaritySearchService:

    def __init__(self, artifact_dir: Path = ARTIFACT_DIR):
        artifact_dir = Path(artifact_dir)

        self.vectors = np.load(
            artifact_dir / "vectors.npy",
            allow_pickle=False
        )

        with (
            artifact_dir / "product_ids.json"
        ).open(encoding="utf-8") as file:
            self.product_ids = json.load(file)

        if self.vectors.ndim != 2:
            raise ValueError("Invalid embedding matrix")

        if self.vectors.shape[1] != 1024:
            raise ValueError("Expected 1024-dimensional vectors")

        if len(self.vectors) != len(self.product_ids):
            raise ValueError("Product IDs and vectors do not match")

        if len(set(self.product_ids)) != len(self.product_ids):
            raise ValueError("Duplicate product IDs in index")

        if not np.isfinite(self.vectors).all():
            raise ValueError("Index contains invalid vector values")

        # Normalize once, so dot product equals cosine similarity.
        norms = np.linalg.norm(
            self.vectors, axis=1, keepdims=True
        )

        if np.any(norms == 0):
            raise ValueError("Index contains zero vectors")

        self.vectors = self.vectors / norms

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10
    ) -> list[dict]:

        if top_k < 1:
            raise ValueError("top_k must be positive")

        query_vector = np.asarray(
            query_vector, dtype=np.float32
        ).reshape(-1)

        if query_vector.shape[0] != 1024:
            raise ValueError("Invalid query dimensions")

        if not np.isfinite(query_vector).all():
            raise ValueError("Invalid query vector")

        norm = np.linalg.norm(query_vector)

        if norm == 0:
            raise ValueError("Query vector cannot be zero")

        query_vector = query_vector / norm

        # Cosine similarity
        scores = self.vectors @ query_vector

        # Sort by highest similarity
        ranked_indices = np.argsort(-scores, kind="stable")

        results = []

        for index in ranked_indices[:top_k]:
            results.append({
                "product_id": self.product_ids[index],
                "similarity_score": float(scores[index])
            })

        return results
