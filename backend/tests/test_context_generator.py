
import pytest

from app.ai.context_generator import ContextGenerator


class FakeGroqClient:
    def generate(self, system_prompt, user_prompt):
        return (
            "Suitable Diwali gifts include dry fruit hampers, "
            "traditional sweets, chocolates, decorative diyas, "
            "scented candles, festive home decor, personalized "
            "gifts, and assorted celebration gift boxes."
        )


def test_context_generation():
    generator = ContextGenerator(client=FakeGroqClient())

    context = generator.generate("Diwali")

    assert 20 <= len(context.split()) <= 30
    assert "dry fruit" in context.lower()


def test_invalid_occasion():
    generator = ContextGenerator(client=FakeGroqClient())

    with pytest.raises(ValueError):
        generator.generate("   ")


def test_excessive_occasion_length():
    generator = ContextGenerator(client=FakeGroqClient())

    with pytest.raises(ValueError):
        generator.generate("a" * 101)
