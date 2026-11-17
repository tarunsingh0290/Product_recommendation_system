
import re

from app.ai.groq_client import GroqClient


SYSTEM_PROMPT = """
You are a gift recommendation assistant.

Generate one sentence of 20 to 30 words listing
specific gift product types suitable for the given occasion.

Focus on products, not explanations.
Do not include brands, prices, or product IDs.
Return only the sentence.
"""


class ContextGenerator:
    def __init__(self, client: GroqClient | None = None):
        self.client = client or GroqClient()

    def generate(self, occasion: str) -> str:
        occasion = occasion.strip()

        if not occasion or len(occasion) > 100:
            raise ValueError(
                "Occasion must contain 1 to 100 characters"
            )

        user_prompt = (
            f"Occasion: {occasion}\n"
            "List appropriate gift product types."
        )

        context = self.client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt
        )

        word_count = len(context.split())

        if not 20 <= word_count <= 100:
            raise ValueError(
                f"Expected 20–30 words, received {word_count}"
            )

        return context
