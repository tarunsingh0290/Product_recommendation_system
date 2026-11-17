
from app.services.recommendation_service import RecommendationService


def main():
    service = RecommendationService()

    occasions = [
        "Birthday",
        "Wedding",
        "Anniversary",
        "Baby Shower",
        "Diwali"
    ]

    for occasion in occasions:
        print(f"\n{'=' * 50}")
        print(f"OCCASION: {occasion}")
        print("=" * 50)

        try:
            result = service.recommend(
                occasion=occasion,
                top_k=10
            )

            print("Generated Context:", result["generated_context"])
            print("Recommendations:", result["total_recommendations"])
            print("Validation Attempts:", result["validation_attempts"])
            print("Rejected IDs:", result["rejected_product_ids"])

            for index, product in enumerate(
                result["recommendations"], start=1
            ):
                print(
                    f"{index}. {product['name']} "
                    f"| Score: {product['similarity_score']}"
                )

            ids = [
                product["product_id"]
                for product in result["recommendations"]
            ]

            assert len(ids) == len(set(ids)), "Duplicate products"
            assert len(ids) <= 10, "Too many recommendations"

        except Exception as error:
            print(f"FAILED: {type(error).__name__}: {error}")
            raise


if __name__ == "__main__":
    main()
