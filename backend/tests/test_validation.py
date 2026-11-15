import json
import numpy as np
import pytest
from pydantic import ValidationError
from app.schemas.recommendation import RecommendationRequest
from app.services.catalog_service import CatalogService
from app.core.exceptions import ServiceError
from app.ai.cosine_retriever import retrieve
from app.services.embedding_service import build_index, EmbeddingService
from conftest import row

@pytest.mark.parametrize('payload', [dict(occasion=''), dict(occasion=' '), dict(occasion='123'),
    dict(occasion=12), dict(occasion='a' * 101), dict(occasion='Birthday', top_k=0),
    dict(occasion='Birthday', top_k=11), dict(occasion='Birthday', top_k=True),
    dict(occasion='Birthday', top_k='2'), dict(occasion='Birthday', extra=1)])
def test_invalid_requests(payload):
    with pytest.raises(ValidationError):
        RecommendationRequest(**payload)

def test_trimmed_request():
    assert RecommendationRequest(occasion='  Birthday  ').occasion == 'Birthday'

def test_catalog_filters(tmp_path):
    path = tmp_path / 'catalog.json'
    rows = [row(), row('p2', stock=0), row('p3', status='DRAFT'),
            row('p4', isApproved=False), row('p5', deletedAt='2026-01-01')]
    path.write_text(json.dumps(rows))
    catalog = CatalogService(path)
    assert list(catalog.products) == ['p1']
    assert catalog.products['p1'].price == 25
    assert catalog.products['p1'].currency is None

def test_duplicate_catalog_ids(tmp_path):
    path = tmp_path / 'catalog.json'
    path.write_text(json.dumps([row(), row()]))
    with pytest.raises(ServiceError):
        CatalogService(path)

def test_cosine_ties_are_stable():
    assert retrieve(np.eye(2), np.array([1, 1]), ['b', 'a']) == [('a', 1.0), ('b', 1.0)]

def test_index_integrity(make_service, tmp_path, monkeypatch):
    service = make_service(3)
    def fake_encode(texts):
        vectors = np.zeros((len(texts), 384), dtype=np.float32)
        vectors[:, 0] = 1
        return vectors
    monkeypatch.setattr('app.services.embedding_service.encode', fake_encode)
    directory = tmp_path / 'index'
    build_index(service.catalog, directory)
    index = EmbeddingService(service.catalog, directory)
    assert index.vectors.shape == (3, 384)
    assert np.allclose(np.linalg.norm(index.vectors, axis=1), 1)
    (directory / 'product_ids.json').write_text('["unknown"]')
    with pytest.raises(ServiceError):
        EmbeddingService(service.catalog, directory)

def test_catalog_mutation(make_service):
    service = make_service(1)
    service.catalog.path.write_text('[]')
    with pytest.raises(ServiceError):
        service.catalog.assert_unchanged()
