"""Live two-search smoke check. Uses the backend Groq key and provider quota."""
import json
import logging
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings


def main():
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('app.ai.llm_client').setLevel(logging.INFO)
    settings = Settings()
    report = []
    with TestClient(create_app(settings)) as client:
        for occasion in ('Birthday', 'Anniversary'):
            started = perf_counter()
            response = client.post('/api/recommendations', json={'occasion': occasion, 'top_k': 10})
            data = response.json()
            summary = dict(occasion=occasion, http_status=response.status_code,
                           elapsed_ms=round((perf_counter() - started) * 1000, 2))
            if response.status_code == 200:
                ids = [item['product_id'] for item in data['recommendations']]
                catalog = client.app.state.service.catalog
                assert len(ids) == len(set(ids)) <= 10
                assert data['returned_count'] == len(ids)
                assert all(id in catalog.products and catalog.products[id].eligible for id in ids)
                scores = [item['similarity_score'] for item in data['recommendations']]
                assert scores == sorted(scores, reverse=True)
                assert all(not item['suitability_passed'] or item['suitability_score'] >= settings.suitability_threshold
                           for item in data['recommendations'])
                summary.update(returned_count=len(ids), status=data['status'],
                    llm_calls=data['llm_calls'], llm_tokens=data['llm_tokens'], all_ids_verified=True)
            else:
                summary.update(detail=data.get('detail'), retry_after_seconds=data.get('retry_after_seconds'))
            report.append(summary)
            print(json.dumps(summary), flush=True)
        repeat = client.post('/api/recommendations', json={'occasion': 'Birthday', 'top_k': 10})
        resized = client.post('/api/recommendations', json={'occasion': 'Birthday', 'top_k': 5})
        if repeat.status_code == resized.status_code == 200:
            print(json.dumps(dict(repeated_search_cached=repeat.json()['cached'],
                resized_count=resized.json()['returned_count'], resized_llm_calls=resized.json()['llm_calls'])), flush=True)
            assert repeat.json()['llm_calls'] == resized.json()['llm_calls'] == 0
    settings.artifacts_path.mkdir(parents=True, exist_ok=True)
    (settings.artifacts_path / 'consecutive_search_verification.json').write_text(
        json.dumps(report, indent=2), encoding='utf-8')
    if any(item['http_status'] != 200 for item in report):
        raise SystemExit('A provider request failed; see the sanitized report above.')


if __name__ == '__main__':
    main()
