
from groq import Groq
from app.core.config import settings


class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature = 0.3,
            max_completion_tokens = 2000,
            reasoning_effort = "low"
        )

        # Debugging
        print("\nFULL GROQ RESPONSE:")
        print(response)

        print("\nCHOICES:")
        print(response.choices)

        if not response.choices:
            raise ValueError("Groq returned no choices")

        message = response.choices[0].message

        print("\nMESSAGE:")
        print(message)

        print("\nCONTENT:")
        print(repr(message.content))

        print("\nFINISH REASON:")
        print(response.choices[0].finish_reason)

        if not message.content or not message.content.strip():
            raise ValueError(
                "Groq returned empty content. "
                f"Finish reason: {response.choices[0].finish_reason}"
            )

        return message.content.strip()
