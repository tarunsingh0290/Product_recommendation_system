from dataclasses import asdict, is_dataclass
from typing import Literal
from pydantic import Field, create_model
from app.schemas.llm import Suitability, ValidationBatch
from app.core.exceptions import ServiceError

def validate_products(client, context, products):
    candidate_ids = tuple(product.id for product in products)
    assessment_schema = create_model('CandidateAssessment', __base__=Suitability,
        candidate_id=(Literal[candidate_ids], ...))
    batch_schema = create_model('CandidateBatch', __base__=ValidationBatch,
        evaluations=(list[assessment_schema], Field(min_length=len(products), max_length=len(products))))
    result = client.generate(batch_schema,
        'Assess every supplied product for the exact gift occasion. Reject irrelevant products, '
        'products specific to incompatible occasions, and products with insufficient evidence. '
        'Return exactly one evaluation for EACH candidate, in the submitted order, including unsuitable '
        'candidates. Copy each candidate_id exactly. Never omit or repeat candidates. '
        'Score suitability from 0 to 1. Give one short sentence per reason, '
        'at most 140 characters, using catalog facts.',
        {'context': asdict(context) if is_dataclass(context) else context.model_dump(),
         'products': [dict(candidate_id=p.id, name=p.name, brand=p.brand,
            description=(p.short_description or p.description)[:350]) for p in products]})
    ids = [item.candidate_id for item in result.evaluations]
    if len(ids) != len(set(ids)) or set(ids) != {p.id for p in products}:
        raise ServiceError('Provider returned missing, duplicate, or unknown product IDs.', 502)
    return result.evaluations
