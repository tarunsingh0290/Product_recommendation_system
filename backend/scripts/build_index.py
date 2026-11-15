import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import Settings
from app.services.catalog_service import CatalogService
from app.services.embedding_service import build_index

if __name__ == '__main__':
    settings = Settings()
    catalog = CatalogService(settings.catalog_path)
    build_index(catalog, settings.artifacts_path)
    logging.basicConfig(level=logging.INFO)
    logging.info('Indexed %d eligible products.', len(catalog.products))
