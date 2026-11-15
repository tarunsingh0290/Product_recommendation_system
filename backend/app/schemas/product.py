from pydantic import BaseModel

class ProductResponse(BaseModel):
    product_id: str
    name: str
    brand: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    category: str | None = None


class ProductDetail(ProductResponse):
    description: str = ''
    short_description: str = ''
    discount_percentage: float | None = None
    weight: str | None = None
