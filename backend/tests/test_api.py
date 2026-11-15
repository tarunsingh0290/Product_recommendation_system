import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings
from app.core.exceptions import ServiceError

@pytest.fixture
def client(make_service):
    app = create_app(Settings(_env_file=None))
    with TestClient(app) as client:
        app.state.service = make_service()
        app.state.readiness_error = ''
        yield client

@pytest.mark.parametrize('occasion', ['Birthday', 'Wedding', 'Anniversary', 'Baby shower', 'Diwali'])
def test_valid_occasions(client, occasion):
    response = client.post('/api/recommendations', json={'occasion': occasion, 'top_k': 3})
    assert response.status_code == 200
    assert response.json()['returned_count'] == 3

@pytest.mark.parametrize('payload', [{'occasion': ''}, {'occasion': '   '}, {'occasion': 'Birthday', 'top_k': 11},
                                     {'occasion': 'Birthday', 'top_k': '1'}, [], {'occasion': 'Birthday', 'x': 1}])
def test_api_validation(client, payload):
    assert client.post('/api/recommendations', json=payload).status_code == 422

def test_swagger_and_health(client):
    assert client.get('/docs').status_code == 200
    assert client.get('/openapi.json').status_code == 200
    assert client.get('/api/health').json()['status'] == 'ok'
    assert client.get('/api/health/ready').status_code == 200

def test_not_ready():
    with TestClient(create_app(Settings(groq_api_key='', _env_file=None))) as client:
        assert client.get('/api/health/ready').status_code == 503
        assert client.post('/api/recommendations', json={'occasion': 'Birthday'}).status_code == 503

def test_provider_error_translation(client):
    class FailedService:
        def recommend(self, payload):
            raise ServiceError('Provider timed out', 502)
    client.app.state.service = FailedService()
    assert client.post('/api/recommendations', json={'occasion': 'Birthday'}).status_code == 502

def test_provider_cooldown_is_exposed(client):
    class LimitedService:
        def recommend(self, payload):
            raise ServiceError('Allowance resets shortly', 429, retry_after_seconds=45)
    client.app.state.service = LimitedService()
    response = client.post('/api/recommendations', json={'occasion': 'Birthday'})
    assert response.status_code == 429
    assert response.headers['retry-after'] == '45'
    assert response.json()['retry_after_seconds'] == 45
