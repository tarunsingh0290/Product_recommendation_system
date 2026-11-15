import logging
from time import perf_counter
from app.ai.context_generator import generate_context
from app.ai.product_validator import validate_products
from app.ai.embedding_model import encode
from app.ai.llm_client import usage
from app.ai.text_processor import query_text
from app.ai.cosine_retriever import retrieve
from app.core.config import Settings
from app.core.exceptions import ServiceError
from app.schemas.recommendation import Recommendation, RecommendationResponse, RecommendationRequest
from app.services.cache_service import CacheService
from app.models.recommendation import RankedProduct

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, catalog, index, client, settings=None, encoder=encode):
        self.catalog, self.index, self.client, self.encoder = catalog, index, client, encoder
        self.settings = settings or Settings()
        self.cache = CacheService(ttl=self.settings.cache_ttl_seconds)
        self.context_cache = CacheService(ttl=self.settings.cache_ttl_seconds)
        self.validation_cache = CacheService(ttl=self.settings.cache_ttl_seconds)

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        started = perf_counter()
        self.catalog.assert_unchanged()
        if request.top_k > self.settings.max_top_k:
            raise ServiceError('Requested count exceeds configured maximum.', 422)
        key = (self.catalog.checksum, request.occasion.casefold(), request.top_k)
        cached = self.cache.get(key)
        if cached:
            cached.cached = True
            cached.llm_calls = cached.llm_tokens = 0
            cached.elapsed_ms = round((perf_counter() - started) * 1000, 2)
            return cached
        metrics = {'calls': 0, 'tokens': 0}
        token = usage.set(metrics)
        try:
            response = self._recommend(request, started)
            response.llm_calls, response.llm_tokens = metrics['calls'], metrics['tokens']
            if response.status != 'partial':
                self.cache.put(key, response)
            logger.info('recommendation completed count=%d latency_ms=%.2f calls=%d tokens=%d',
                        response.returned_count, response.elapsed_ms, metrics['calls'], metrics['tokens'])
            return response
        except ServiceError as exc:
            exc.llm_tokens = metrics['tokens']
            exc.llm_calls = metrics['calls']
            logger.warning('recommendation failed status=%d latency_ms=%.2f calls=%d tokens=%d',
                           exc.status, (perf_counter() - started) * 1000,
                           metrics['calls'], metrics['tokens'])
            raise
        finally:
            usage.reset(token)

    def _recommend(self, request: RecommendationRequest, started: float) -> RecommendationResponse:
        context_key = request.occasion.casefold()
        context = self.context_cache.get(context_key)
        if context is None:
            context = generate_context(self.client, request.occasion)
            self.context_cache.put(context_key, context)
        try:
            query = self.encoder([query_text(context)])[0]
        except Exception as exc:
            raise ServiceError('Embedding model unavailable. Check model installation and cache.') from exc
        # Retrieve the highest cosine matches, then assess them without removing low-suitability
        # products. This preserves the requested result count and exact similarity ordering.
        candidates = retrieve(self.index.vectors, query, self.index.ids,
                              limit=self.settings.candidate_batch_size)
        products = [self.catalog.products[id] for id, _ in candidates
                    if self.catalog.products[id].eligible]
        validation_key = (self.catalog.checksum, context_key, tuple(p.id for p in products))
        decisions = self.validation_cache.get(validation_key)
        if decisions is None:
            decisions = validate_products(self.client, context, products)
            self.validation_cache.put(validation_key, decisions)
        similarities = dict(candidates)
        ranked = []
        for item in decisions:
            product = self.catalog.products[item.candidate_id]
            if not product.eligible:
                continue
            ranked.append(RankedProduct(product=product,
                similarity_score=similarities[product.id],
                suitability_score=item.suitability_score, reason=item.reason,
                suitability_passed=item.suitable and
                    item.suitability_score >= self.settings.suitability_threshold))
        ranked = self._deduplicate(ranked)[:request.top_k]
        self.catalog.assert_unchanged()
        results = [Recommendation(product_id=item.product.id, name=item.product.name,
            brand=item.product.brand or None, price=item.product.price,
            currency=item.product.currency, image_url=item.product.image_url,
            category=item.product.category or None, similarity_score=item.similarity_score,
            suitability_score=item.suitability_score, reason=item.reason,
            suitability_passed=item.suitability_passed) for item in ranked]
        warnings = []
        caution_count = sum(not item.suitability_passed for item in results)
        if caution_count:
            warnings.append(f'{caution_count} similarity matches did not pass the occasion suitability '
                            'check. Review the cautions on their cards before choosing a gift.')
        if len(results) < request.top_k:
            warnings.append(f'Only {len(results)} eligible catalog products are available; '
                            'additional products cannot be invented.')
        return RecommendationResponse(occasion=request.occasion, requested_count=request.top_k,
            returned_count=len(results), status='ok' if results else 'no_results',
            recommendations=results, warning=' '.join(warnings) or None,
            elapsed_ms=round((perf_counter() - started) * 1000, 2))

    def _deduplicate(self, results: list[RankedProduct]) -> list[RankedProduct]:
        # Cosine descending; stable product ID breaks exact ties. Distinct variants can appear.
        results.sort(key=lambda item: (-item.similarity_score, item.product.id))
        seen = set()
        unique = []
        for item in results:
            if item.product.id not in seen:
                seen.add(item.product.id)
                unique.append(item)
        return unique
