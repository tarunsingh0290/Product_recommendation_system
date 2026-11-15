from functools import lru_cache
from threading import Lock
import numpy as np

MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
DIMENSION = 384
_model_lock = Lock()

@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer
    try:
        return SentenceTransformer(MODEL, local_files_only=True)
    except OSError:
        return SentenceTransformer(MODEL)

def load_model():
    with _model_lock:
        return _load_model()

def encode(texts: list[str]) -> np.ndarray:
    return np.asarray(load_model().encode(texts, normalize_embeddings=True,
                                         show_progress_bar=False), dtype=np.float32)
