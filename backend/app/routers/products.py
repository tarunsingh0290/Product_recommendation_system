
from fastapi import APIRouter, HTTPException

from app.models.product import Product
from app.services.catalog_service import CatalogService


router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)

catalog = CatalogService()


@router.get("/", response_model=list[Product])
def get_products():
    return catalog.get_eligible_products()


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str):
    product = catalog.get_product_by_id(product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product
