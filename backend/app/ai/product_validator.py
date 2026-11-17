
import json

from app.ai.groq_client import GroqClient


SYSTEM_PROMPT = """
You are a gift recommendation product validator.

Evaluate whether each product is suitable as a gift
for the specified occasion.

Rules:
1. Evaluate each product using its name and description.
2. Approve relevant gift products.
3. Reject unrelated or inappropriate products.
4. Do not invent product IDs.
5. Return one decision for every supplied product.
6. Return ONLY valid JSON in this format:

{
    "results": [
        {
            "product_id": "original_id",
            "approved": true
        }
    ]
}
"""


class ProductValidator:

    def __init__(self, client=None):
        self.client = client if client is not None else GroqClient()

    def validate(self, occasion: str, products: list) -> dict:
        if not products:
            return {}

        payload = {
            "occasion": occasion,
            "products": [
                {
                    "product_id": product.id,
                    "name": product.name,
                    "description": (
                        product.shortDescription
                        or product.description
                        or ""
                    )[:500]
                }
                for product in products
            ]
        }

        response = self.client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=json.dumps(payload, ensure_ascii=False)
        )

        # Parse Groq JSON response
        try:
            data = json.loads(response)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Groq returned invalid JSON"
            ) from error

        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")

        results = data.get("results")

        if not isinstance(results, list):
            raise ValueError("Missing results list")

        expected_ids = {product.id for product in products}
        decisions = {}

        for item in results:
            if not isinstance(item, dict):
                raise ValueError("Invalid result item")

            product_id = item.get("product_id")
            approved = item.get("approved")

            if (
                product_id not in expected_ids
                or product_id in decisions
                or type(approved) is not bool
            ):
                raise ValueError(
                    "Invalid product validation decision"
                )

            decisions[product_id] = approved

        if set(decisions) != expected_ids:
            raise ValueError(
                "Missing product validation decisions"
            )

        return decisions
