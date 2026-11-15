from dataclasses import dataclass
from app.models.product import Product

@dataclass(frozen=True)
class RankedProduct:
    product: Product
    similarity_score: float
    suitability_score: float
    reason: str
    suitability_passed: bool = True
