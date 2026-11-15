from pathlib import Path
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from app.models.product import Product
from app.core.exceptions import ServiceError

class CatalogRow(BaseModel):
    """Validated fields from the supplied catalog export."""
    model_config = ConfigDict(extra='ignore')
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    brand: str | None = None
    description: str | None = None
    shortDescription: str | None = None
    mainImage: str | None = None
    price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    stock: int = Field(strict=True, ge=0)
    isApproved: bool = Field(strict=True)
    status: str
    deletedAt: str | None
    productGroupId: str | None = None
    discountPercentage: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    weight: str | None = None

    @field_validator('weight', mode='before')
    @classmethod
    def preserve_weight(cls, value):
        if value is None or value == '':
            return None
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ValueError('Weight must be a catalog text or numeric value')
        return str(value)


    @field_validator('mainImage')
    @classmethod
    def safe_image(cls, value):
        if value and not value.startswith(('http://', 'https://')):
            raise ValueError('mainImage must use HTTP or HTTPS')
        return value

    def product(self) -> Product:
        return Product(id=self.id, name=self.name, brand=self.brand or '',
            description=self.description or '', short_description=self.shortDescription or '',
            image_url=self.mainImage, price=self.price,
            discount_percentage=self.discountPercentage, weight=self.weight,
            active=self.status == 'ACTIVE',
            approved=self.isApproved, deleted=self.deletedAt is not None, in_stock=self.stock > 0)

class CatalogService:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.reload()

    def reload(self) -> None:
        try:
            raw = self.path.read_bytes()
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError('Catalog root must be a list')
            rows = [CatalogRow.model_validate(row) for row in data]
            products = [row.product() for row in rows]
        except (OSError, ValueError, ValidationError) as exc:
            raise ServiceError('Catalog is missing or invalid; inspect catalog fields and eligibility states.') from exc
        if len({p.id for p in products}) != len(products):
            raise ServiceError('Catalog has duplicate product IDs.')
        self.checksum = hashlib.sha256(raw).hexdigest()
        self.products = {p.id: p for p in products if p.eligible}
        self.groups = {row.id: row.productGroupId for row in rows}
        stat = self.path.stat()
        self.fingerprint = stat.st_mtime_ns, stat.st_size

    def assert_unchanged(self) -> None:
        try:
            stat = self.path.stat()
        except OSError as exc:
            raise ServiceError('Catalog is unavailable.') from exc
        if (stat.st_mtime_ns, stat.st_size) != self.fingerprint:
            raise ServiceError('Catalog changed. Rebuild the index and restart the backend.')
