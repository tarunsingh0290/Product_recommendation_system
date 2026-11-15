import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.exceptions import ServiceError
from app.main import create_app


def test_details_returns_catalog_metadata_without_llm_calls(make_service):
    def metadata(rows):
        rows[0].update(description='Full product description', brand='Catalog brand', price='499',
            mainImage='https://example.com/main.jpg', discountPercentage='12.5', weight='0.2')
    service = make_service(1, changes=metadata)
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.service = service
        response = client.get('/api/products/p000')
        assert response.status_code == 200
        product = response.json()
        assert product['name'] == 'Gift p000'
        assert product['brand'] == 'Catalog brand'
        assert product['price'] == 499
        assert product['image_url'] == 'https://example.com/main.jpg'
        assert product['description'] == 'Full product description'
        assert product['discount_percentage'] == 12.5
        assert product['weight'] == '0.2'
        assert product['currency'] is None
        assert service.client.calls == []


def test_details_missing_fields_are_not_invented(make_service):
    service = make_service(1)
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.service = service
        product = client.get('/api/products/p000').json()
        assert product['discount_percentage'] is None
        assert product['weight'] is None


def test_unknown_or_ineligible_products_return_404(make_service):
    def unavailable(rows):
        rows[1]['stock'] = 0
    service = make_service(2, changes=unavailable)
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.service = service
        assert client.get('/api/products/made-up-product').status_code == 404
        assert client.get('/api/products/p001').status_code == 404


def test_details_work_without_recommendation_provider(make_service):
    service = make_service(1)
    with TestClient(create_app(Settings(groq_api_key='', _env_file=None))) as client:
        client.app.state.service = None
        client.app.state.catalog = service.catalog
        assert client.get('/api/products/p000').status_code == 200
        assert client.get('/api/health/ready').status_code == 503


def test_changed_catalog_blocks_old_details(make_service):
    service = make_service(1)
    with TestClient(create_app(Settings(_env_file=None))) as client:
        client.app.state.service = service
        service.catalog.path.write_text('[]')
        assert client.get('/api/products/p000').status_code == 503


@pytest.mark.parametrize('discount', [-1, 101, 'invalid'])
def test_invalid_discount_metadata_is_rejected(make_service, discount):
    with pytest.raises(ServiceError):
        make_service(1, changes=lambda rows: rows[0].update(discountPercentage=discount))
