
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    EMBEDDING_MODEL: str = "mixedbread-ai/mxbai-embed-large-v1"

    TOP_K: int = 10
    MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
