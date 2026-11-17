
from pydantic import BaseModel, Field, ConfigDict


class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    shortDescription: str | None = None
    brand: str | None = None
    mainImage: str | None = None

    price: str
    stock: int = Field(ge=0)

    isApproved: bool
    status: str
    deletedAt: str | None = None

    def is_eligible(self) -> bool:
        return (
            self.isApproved is True
            and self.status == "ACTIVE"
            and self.deletedAt is None
            and self.stock > 0
        )

    def embedding_text(self) -> str:
        """Build searchable text for the embedding model."""
        fields = [
            self.name,
            self.shortDescription,
            self.description,
            self.brand,
        ]

        return ". ".join(
            value.strip()
            for value in fields
            if value and value.strip()
        )
