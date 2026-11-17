
from app.repositories.product_repository import ProductRepository
from app.models.product import Product


class CatalogService:
    def __init__(
        self,
        repository: ProductRepository | None = None
    ):
        self.repository = repository or ProductRepository()

    def get_eligible_products(self) -> list[Product]:
        products = self.repository.get_all()

        eligible = []
        seen_ids = set()

        for product in products:
            if product.id in seen_ids:
                continue

            if not product.is_eligible():
                continue

            eligible.append(product)
            seen_ids.add(product.id)

        return eligible

    def get_product_by_id(
        self, product_id: str
    ) -> Product | None:
        for product in self.get_eligible_products():
            if product.id == product_id:
                return product

        return None
