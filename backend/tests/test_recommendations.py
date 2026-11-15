import pytest
from app.schemas.recommendation import RecommendationRequest
from app.core.exceptions import ServiceError

@pytest.mark.parametrize('occasion', ['Birthday', 'Wedding', 'Anniversary', 'Baby shower', 'Diwali'])
@pytest.mark.parametrize('top_k', [1, 7, 10])
def test_catalog_only_bounded_results(make_service, occasion, top_k):
    service = make_service()
    result = service.recommend(RecommendationRequest(occasion=occasion, top_k=top_k))
    ids = [p.product_id for p in result.recommendations]
    assert result.returned_count == top_k
    assert len(set(ids)) == len(ids)
    assert set(ids) <= set(service.catalog.products)
    assert len(service.client.calls) == 2
    assert [p.product_id for p in result.recommendations] == sorted(ids)

def test_low_suitability_does_not_reduce_requested_count(make_service):
    service = make_service(suitable=False)
    result = service.recommend(RecommendationRequest(occasion='Birthday'))
    assert result.returned_count == 10
    assert len(service.client.calls) == 2
    assert result.warning
    assert all(not item.suitability_passed for item in result.recommendations)


def test_distinct_catalog_variants_can_fill_ten_results(make_service):
    def duplicates(rows):
        for item in rows:
            item['productGroupId'] = 'same-group'
    service = make_service(changes=duplicates)
    result = service.recommend(RecommendationRequest(occasion='Wedding'))
    assert result.returned_count == 10
    assert len({item.product_id for item in result.recommendations}) == 10

def test_response_and_context_cache(make_service):
    service = make_service()
    request = RecommendationRequest(occasion='Birthday', top_k=1)
    service.recommend(request)
    assert service.recommend(request).cached
    assert len(service.client.calls) == 2
    service.recommend(RecommendationRequest(occasion='Birthday', top_k=2))
    assert len(service.client.calls) == 2

def test_gibberish_rejected(make_service):
    service = make_service()
    service.client.invalid_context = True
    with pytest.raises(ServiceError) as error:
        service.recommend(RecommendationRequest(occasion='asdjkhqw'))
    assert error.value.status == 422

def test_cosine_order_takes_priority_over_suitability(make_service):
    import numpy as np
    service = make_service(12)
    scores = np.linspace(0.1, 0.99, 12)
    service.index.vectors[:, 0] = scores
    service.index.vectors[:, 1] = np.sqrt(1 - scores ** 2)
    original_generate = service.client.generate

    def reverse_suitability(schema, instruction, payload):
        result = original_generate(schema, instruction, payload)
        if 'products' in payload:
            for item in result.evaluations:
                # Lower cosine candidates deliberately have higher suitability scores.
                item.suitability_score = 1 - float(scores[int(item.candidate_id[1:])])
                item.suitable = item.suitability_score >= 0.7
        return result

    service.client.generate = reverse_suitability
    result = service.recommend(RecommendationRequest(occasion='Birthday', top_k=10))
    assert result.returned_count == 10
    assert [item.product_id for item in result.recommendations] == [f'p{i:03d}' for i in range(11, 1, -1)]
    similarities = [item.similarity_score for item in result.recommendations]
    assert similarities == sorted(similarities, reverse=True)


def test_fewer_than_ten_eligible_products_are_not_fabricated(make_service):
    service = make_service(6)
    result = service.recommend(RecommendationRequest(occasion='Birthday'))
    assert result.returned_count == 6
    assert result.warning
    assert all(item.product_id in service.catalog.products for item in result.recommendations)


def test_out_of_stock_products_never_fill_result_slots(make_service):
    def mark_unavailable(rows):
        for item in rows[:35]:
            item['stock'] = 0
    service = make_service(45, changes=mark_unavailable)
    result = service.recommend(RecommendationRequest(occasion='Birthday'))
    assert result.returned_count == 10
    assert all(int(item.product_id[1:]) >= 35 for item in result.recommendations)


def test_initial_rate_limit_does_not_return_unvalidated_results(make_service):
    service = make_service()
    original_generate = service.client.generate

    def limited_provider(schema, instruction, payload):
        if 'products' in payload:
            raise ServiceError('Provider allowance exhausted', 429, retry_after_seconds=45)
        return original_generate(schema, instruction, payload)

    service.client.generate = limited_provider
    with pytest.raises(ServiceError) as error:
        service.recommend(RecommendationRequest(occasion='Birthday'))
    assert error.value.status == 429
