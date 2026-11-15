import numpy as np

def retrieve(vectors: np.ndarray, query: np.ndarray, ids: list[str], limit: int = 50) -> list[tuple[str, float]]:
    scores = vectors @ query
    return sorted(zip(ids, scores.tolist()), key=lambda item: (-item[1], item[0]))[:limit]
