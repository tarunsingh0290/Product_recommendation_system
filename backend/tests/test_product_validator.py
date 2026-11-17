
import json

from app.ai.product_validator import ProductValidator


class FakeProduct:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.shortDescription = name
        self.description = None


class FakeGroqClient:
    def generate(self, system_prompt, user_prompt):
        payload = json.loads(user_prompt)

        return json.dumps({
            "results": [
                {
                    "product_id": product["product_id"],
                    "approved": product["name"] != "Car Tyre"
                }
                for product in payload["products"]
            ]
        })


def test_product_validation():
    validator = ProductValidator(client=FakeGroqClient())

    products = [
        FakeProduct("p1", "Diwali Sweets"),
        FakeProduct("p2", "Decorative Diyas"),
        FakeProduct("p3", "Car Tyre")
    ]

    result = validator.validate("Diwali", products)

    assert result == {
        "p1": True,
        "p2": True,
        "p3": False
    }
