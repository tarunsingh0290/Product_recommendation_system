from fastapi import APIRouter, Request
from app.core.exceptions import ServiceError
from app.schemas.product import ProductDetail

router = APIRouter()


@router.get('/api/products/{product_id}', response_model=ProductDetail)
def product_details(product_id: str, request: Request):
    service = request.app.state.service
    catalog = service.catalog if service is not None else request.app.state.catalog
    if catalog is None:
        raise ServiceError('The product catalog is temporarily unavailable.')
    catalog.assert_unchanged()
    product = catalog.products.get(product_id)
    if product is None or not product.eligible:
        raise ServiceError('Product not found or no longer available.', 404)
    return ProductDetail(product_id=product.id, name=product.name,
        brand=product.brand or None, image_url=product.image_url, price=product.price,
        currency=product.currency, category=product.category or None,
        description=product.description, short_description=product.short_description,
        discount_percentage=product.discount_percentage, weight=product.weight)
