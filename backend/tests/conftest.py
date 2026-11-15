import json
from types import SimpleNamespace
import numpy as np
import pytest
from app.core.config import Settings
from app.services.catalog_service import CatalogService
from app.services.recommendation_service import RecommendationService
from app.schemas.llm import OccasionContext, ValidationBatch

def row(id='p1', **changes):
    item = dict(id=id, name=f'Gift {id}', brand='Test brand', description='Test description',
                shortDescription='A gift', mainImage=None, price='25', stock=1,
                isApproved=True, status='ACTIVE', deletedAt=None, productGroupId=id)
    item.update(changes)
    return item

class FakeLLM:
    def __init__(self, suitable=True, invalid_context=False):
        self.calls = []
        self.suitable = suitable
        self.invalid_context = invalid_context

    def generate(self, schema, instruction, payload):
        self.calls.append(payload)
        if schema is OccasionContext:
            return OccasionContext(valid=not self.invalid_context, occasion=payload['occasion'],
                intent_summary='Celebration gifts', gift_categories=['gifts'],
                search_phrases=['celebration'], excluded_occasions=[])
        return ValidationBatch(evaluations=[dict(candidate_id=p['candidate_id'],
            suitable=self.suitable, suitability_score=0.9 if self.suitable else 0.1,
            reason='Fixture assessment') for p in payload['products']])

@pytest.fixture
def make_service(tmp_path):
    def create(count=45, suitable=True, changes=None):
        path = tmp_path / 'products.json'
        rows = [row(f'p{i:03d}') for i in range(count)]
        if changes:
            changes(rows)
        path.write_text(json.dumps(rows), encoding='utf-8')
        catalog = CatalogService(path)
        vectors = np.zeros((len(catalog.products), 384), dtype=np.float32)
        vectors[:, 0] = 1
        index = SimpleNamespace(ids=sorted(catalog.products), vectors=vectors)
        client = FakeLLM(suitable)
        query = np.zeros((1, 384), dtype=np.float32)
        query[0, 0] = 1
        return RecommendationService(catalog, index, client, Settings(_env_file=None), encoder=lambda _: query)
    return create
