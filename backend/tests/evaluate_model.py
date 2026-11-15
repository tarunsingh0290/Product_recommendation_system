"""Compare raw cosine retrieval with the validated system on held-out human labels.

Run from backend: python tests/evaluate_model.py --labels tests/ground_truth.json
This uses real embeddings and Groq; API costs apply. No synthetic relevance labels.
"""
import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ai.cosine_retriever import retrieve
from app.ai.embedding_model import encode
from app.ai.llm_client import LLMClient
from app.core.config import Settings
from app.schemas.recommendation import RecommendationRequest
from app.services.catalog_service import CatalogService
from app.services.embedding_service import EmbeddingService
from app.services.recommendation_service import RecommendationService


def summarize(records):
    return {
        'precision_at_10': float(np.mean([r['precision_at_10'] for r in records])),
        'occasion_success_rate': float(np.mean([r['precision_at_10'] >= 0.7 for r in records])),
        'invalid_catalog_id_rate': sum(r['invalid_ids'] for r in records) / max(1, sum(r['returned'] for r in records)),
        'duplicate_rate': sum(r['duplicates'] for r in records) / max(1, sum(r['returned'] for r in records)),
        'p95_latency_ms': float(np.percentile([r['latency_ms'] for r in records], 95)),
        'provider_failure_rate': sum(r['failed'] for r in records) / len(records),
        'llm_tokens': sum(r['llm_tokens'] for r in records),
        'per_occasion': records,
    }


def measure(occasion, relevant, ids, catalog, latency, failed=False, tokens=0):
    return dict(occasion=occasion, precision_at_10=len(set(ids) & relevant) / 10,
                returned=len(ids), invalid_ids=len(set(ids) - set(catalog.products)),
                duplicates=len(ids) - len(set(ids)), latency_ms=latency,
                failed=failed, llm_tokens=tokens)


def evaluate(labels_path, output):
    labels = json.loads(labels_path.read_text(encoding='utf-8'))
    if labels.get('split') != 'evaluation' or not labels.get('occasions'):
        raise SystemExit('Add independently human-labeled evaluation occasions first. No metrics were measured.')
    settings = Settings()
    catalog = CatalogService(settings.catalog_path)
    index = EmbeddingService(catalog, settings.artifacts_path)
    client = LLMClient(settings)
    baseline, system = [], []
    try:
        for label in labels['occasions']:
            relevant = set(label['relevant_product_ids'])
            judged = set(label['judged_product_ids'])
            if not relevant <= judged or not judged <= set(catalog.products):
                raise SystemExit('Labels must reference eligible catalog IDs; relevant IDs must be judged.')
            # Fully judge the catalog to avoid counting unjudged outputs as negatives.
            if judged != set(catalog.products):
                raise SystemExit('Every eligible catalog ID must be independently judged for each occasion.')
            occasion = label['occasion']
            start = perf_counter()
            ids = [id for id, _ in retrieve(index.vectors, encode([occasion])[0], index.ids, limit=10)]
            baseline.append(measure(occasion, relevant, ids, catalog, (perf_counter() - start) * 1000))
            # Fresh caches for each held-out occasion: report cold request latency.
            service = RecommendationService(catalog, index, client, settings)
            start = perf_counter()
            try:
                result = service.recommend(RecommendationRequest(occasion=occasion))
                ids = [p.product_id for p in result.recommendations]
                system.append(measure(occasion, relevant, ids, catalog,
                    (perf_counter() - start) * 1000, tokens=result.llm_tokens))
            except Exception as exc:
                record = measure(occasion, relevant, [], catalog, (perf_counter() - start) * 1000,
                                 failed=True, tokens=getattr(exc, 'llm_tokens', 0))
                record['error_type'] = type(exc).__name__
                system.append(record)
    finally:
        client.close()
    result = dict(policy='Precision@10 uses a fixed denominator of 10; fewer results reduce the score.',
                  baseline_a=summarize(baseline), system_b=summarize(system))
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labels', type=Path, default=Path(__file__).with_name('ground_truth.json'))
    parser.add_argument('--output', type=Path, default=Path('evaluation_results.json'))
    args = parser.parse_args()
    evaluate(args.labels, args.output)
