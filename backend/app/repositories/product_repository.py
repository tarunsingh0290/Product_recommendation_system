
import json
from pathlib import Path

from app.models.product import Product


DATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "products.json"
)


class ProductRepository:
    def __init__(self, file_path: Path = DATA_PATH):
        self.file_path = Path(file_path)

    def get_all(self) -> list[Product]:
        with self.file_path.open(
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Expected a JSON array")

        return [
            Product.model_validate(item)
            for item in data
        ]
