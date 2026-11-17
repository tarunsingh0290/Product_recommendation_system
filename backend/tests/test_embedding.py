
from app.ai.embedding_service import EmbeddingService


def test_embedding_dimensions():
    service = EmbeddingService()

    query = "Diwali gifts including dry fruits and sweets"

    embedding = service.embed_query(query)

    assert embedding.shape == (1024,)

    print("\nEmbedding shape:", embedding.shape)
    print("First 5 values:", embedding[:5])
