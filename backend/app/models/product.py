from dataclasses import dataclass, field

@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str = ''
    short_description: str = ''
    description: str = ''
    tags: list[str] = field(default_factory=list)
    category: str = ''
    price: float | None = None
    currency: str | None = None
    image_url: str | None = None
    discount_percentage: float | None = None
    weight: str | None = None
    active: bool = True
    deleted: bool = False
    approved: bool = True
    in_stock: bool = True

    @property
    def eligible(self) -> bool:
        return self.active and not self.deleted and self.approved and self.in_stock

    @property
    def search_text(self) -> str:
        return ' '.join([self.name, self.brand, self.short_description,
                         self.description, self.category, *self.tags])
