import hashlib
import json
import numpy as np
from app.ai.embedding_model import MODEL, DIMENSION, encode
from app.core.exceptions import ServiceError

INDEX_VERSION = 1

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_index(catalog, directory):
    if not catalog.products:
        raise ServiceError('Catalog contains no eligible products.')
    directory.mkdir(parents=True, exist_ok=True)
    ids = sorted(catalog.products)
    vectors = encode([catalog.products[i].search_text for i in ids])
    # Manifest is the commit marker; interrupted builds fail checksum verification.
    np.save(directory / 'vectors.npy', vectors, allow_pickle=False)
    (directory / 'product_ids.json').write_text(json.dumps(ids), encoding='utf-8')
    manifest = dict(catalog_checksum=catalog.checksum, model=MODEL, dimension=DIMENSION,
                    normalized=True, index_version=INDEX_VERSION,
                    vectors_checksum=digest(directory / 'vectors.npy'),
                    ids_checksum=digest(directory / 'product_ids.json'))
    (directory / 'index_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

class EmbeddingService:
    def __init__(self, catalog, directory):
        try:
            manifest = json.loads((directory / 'index_manifest.json').read_text())
            expected = dict(catalog_checksum=catalog.checksum, model=MODEL,
                            dimension=DIMENSION, normalized=True, index_version=INDEX_VERSION,
                            vectors_checksum=digest(directory / 'vectors.npy'),
                            ids_checksum=digest(directory / 'product_ids.json'))
            if manifest != expected:
                raise ValueError('manifest mismatch')
            self.ids = json.loads((directory / 'product_ids.json').read_text())
            self.vectors = np.load(directory / 'vectors.npy', allow_pickle=False)
            if self.ids != sorted(catalog.products) or self.vectors.shape != (len(self.ids), DIMENSION):
                raise ValueError('index alignment mismatch')
            if not np.isfinite(self.vectors).all() or not np.allclose(np.linalg.norm(self.vectors, axis=1), 1, atol=1e-4):
                raise ValueError('invalid normalization')
        except (OSError, ValueError, TypeError) as exc:
            raise ServiceError('Index missing, stale, or corrupt. Run scripts/build_index.py.') from exc
