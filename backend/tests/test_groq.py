
from app.ai.context_generator import ContextGenerator


def main():
    generator = ContextGenerator()

    occasions = [
        "Diwali",
        "Birthday",
        "Wedding",
        "Baby Shower",
        "Anniversary"
    ]

    for occasion in occasions:
        try:
            context = generator.generate(occasion)

            print(f"\nOccasion: {occasion}")
            print(f"Context: {context}")
            print(f"Words: {len(context.split())}")

        except Exception as error:
            print(f"\nOccasion: {occasion}")
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
