from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    MODEL_NAME = "mixedbread-ai/mxbai-embed-large-v1"

    QUERY_PROMPT = (
        "Represent this sentence for searching relevant passages: "
    )

    def __init__(self):
        self.model = SentenceTransformer(self.MODEL_NAME)

    def embed_products(self, texts: list[str]) -> np.ndarray:
        """Generate normalized embeddings for products."""
        return self.model.encode(
            texts,
            batch_size=8,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

    def embed_query(self, query: str) -> np.ndarray:
        """Generate an embedding for a search query."""
        return self.model.encode(
            query,
            prompt=self.QUERY_PROMPT,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
