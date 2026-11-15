import json
import httpx
import pytest
from app.ai.llm_client import LLMClient
from app.ai.product_validator import validate_products
from app.core.config import Settings
from app.core.exceptions import ServiceError
from app.schemas.llm import OccasionContext, ValidationBatch
from conftest import FakeLLM

@pytest.mark.parametrize('kind', ['fabricated', 'duplicate', 'partial'])
def test_candidate_id_contract(make_service, kind):
    service = make_service(2)
    context = FakeLLM().generate(OccasionContext, '', {'occasion': 'Birthday'})
    ids = ['unknown', 'p001'] if kind == 'fabricated' else ['p000', 'p000'] if kind == 'duplicate' else ['p000']
    class BadClient:
        def generate(self, *_):
            return ValidationBatch(evaluations=[dict(candidate_id=id, suitable=True,
                suitability_score=0.9, reason='Reason') for id in ids])
    with pytest.raises(ServiceError):
        validate_products(BadClient(), context, list(service.catalog.products.values()))

@pytest.mark.parametrize('behavior', ['timeout', '429', 'malformed', 'empty'])
def test_provider_failures(behavior, monkeypatch):
    monkeypatch.setattr('app.ai.llm_client.time.sleep', lambda _: None)
    client = LLMClient(Settings(groq_api_key='test-only', _env_file=None))
    client.http.close()
    calls = []
    def handler(request):
        calls.append(request)
        if behavior == 'timeout':
            raise httpx.ReadTimeout('timeout', request=request)
        if behavior == '429':
            return httpx.Response(429)
        return httpx.Response(200, json={'choices': [{'message': {'content': '' if behavior == 'empty' else '{invalid'}}]})
    client.http = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ServiceError):
            client.generate(OccasionContext, 'Test', {})
        assert len(calls) == (3 if behavior in ('timeout', '429') else 1)
    finally:
        client.close()

def test_structured_request_and_parsing():
    client = LLMClient(Settings(groq_api_key='test-only', _env_file=None))
    client.http.close()
    context = FakeLLM().generate(OccasionContext, '', {'occasion': 'Birthday'})
    def handler(request):
        body = json.loads(request.content)
        assert body['response_format']['json_schema']['strict'] is True
        assert body['model'] == 'openai/gpt-oss-20b'
        return httpx.Response(200, json={'choices': [{'message': {'content': context.model_dump_json()}}]})
    client.http = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        assert client.generate(OccasionContext, '', {}).valid
    finally:
        client.close()

def test_rate_limit_reset_is_not_retried_early(monkeypatch):
    client = LLMClient(Settings(groq_api_key='test-only', _env_file=None))
    client.http.close()
    calls, sleeps = [], []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={'retry-after': '120'})
    monkeypatch.setattr('app.ai.llm_client.time.sleep', sleeps.append)
    client.http = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ServiceError) as error:
            client.generate(OccasionContext, '', {})
        assert error.value.status == 429
        assert error.value.retry_after_seconds == 120
        assert len(calls) == 1
        assert sleeps == []
    finally:
        client.close()

@pytest.mark.parametrize('reset_seconds', [2, 45, 60])
def test_rate_limit_honors_short_reset(monkeypatch, reset_seconds):
    client = LLMClient(Settings(groq_api_key='test-only', _env_file=None))
    client.http.close()
    sleeps = []
    calls = []
    context = FakeLLM().generate(OccasionContext, '', {'occasion': 'Birthday'})
    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={'retry-after': str(reset_seconds)})
        return httpx.Response(200, json={'choices': [{'message': {'content': context.model_dump_json()}}]})
    monkeypatch.setattr('app.ai.llm_client.time.sleep', sleeps.append)
    client.http = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        assert client.generate(OccasionContext, '', {}).valid
        assert sleeps == [min(float(reset_seconds) + 1, 60)]
        assert len(calls) == 2
    finally:
        client.close()

def test_truncated_response_is_explicit():
    client = LLMClient(Settings(groq_api_key='test-only', _env_file=None))
    client.http.close()
    client.http = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200,
        json={'choices': [{'finish_reason': 'length', 'message': {'content': '{'}}]})))
    try:
        with pytest.raises(ServiceError, match='truncated'):
            client.generate(OccasionContext, '', {})
    finally:
        client.close()

def test_two_successive_cooldowns_are_bounded(monkeypatch):
    client = LLMClient(Settings(groq_api_key='test-only', _env_file=None))
    client.http.close()
    calls, sleeps = [], []
    context = FakeLLM().generate(OccasionContext, '', {'occasion': 'Birthday'})
    def handler(request):
        calls.append(request)
        if len(calls) <= 2:
            return httpx.Response(429, headers={'retry-after': '8' if len(calls) == 1 else '5'})
        return httpx.Response(200, json={'choices': [{'message': {'content': context.model_dump_json()}}]})
    monkeypatch.setattr('app.ai.llm_client.time.sleep', sleeps.append)
    client.http = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        assert client.generate(OccasionContext, '', {}).valid
        assert len(calls) == 3
        assert sleeps == [9, 6]
        assert sum(sleeps) <= 60
    finally:
        client.close()
