from pathlib import Path
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from typing import Annotated

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    groq_api_key: str = ''
    groq_model: str = 'openai/gpt-oss-20b'
    catalog_path: Path = ROOT / 'data/products.json'
    artifacts_path: Path = ROOT / 'artifacts'
    cors_origins: Annotated[list[str], NoDecode] = ['http://localhost:5173']
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    default_top_k: int = Field(default=10, ge=1, le=10)
    max_top_k: int = Field(default=10, ge=1, le=10)
    candidate_batch_size: int = Field(default=20, ge=20, le=30)
    max_validation_batches: int = Field(default=2, ge=1, le=2)
    llm_temperature: float = Field(default=0.1, ge=0, le=1)
    llm_timeout_seconds: float = Field(default=15, gt=0, le=60)
    llm_max_retry_wait_seconds: float = Field(default=60, ge=0, le=60)
    llm_max_http_attempts: int = Field(default=3, ge=1, le=3)
    suitability_threshold: float = Field(default=0.7, ge=0, le=1)
    similarity_minimum: float | None = Field(default=None, ge=-1, le=1)
    cache_ttl_seconds: int = Field(default=3600, ge=0)

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            import json
            return json.loads(value) if value.startswith('[') else [v.strip() for v in value.split(',') if v.strip()]
        return value

    @field_validator('embedding_model')
    @classmethod
    def supported_embedding(cls, value):
        if value != 'sentence-transformers/all-MiniLM-L6-v2':
            raise ValueError('This index configuration requires all-MiniLM-L6-v2')
        return value

    def model_post_init(self, context):
        for key in ('catalog_path', 'artifacts_path'):
            path = getattr(self, key)
            if not path.is_absolute():
                setattr(self, key, ROOT / path)

    @model_validator(mode='after')
    def validate_counts(self):
        if self.default_top_k > self.max_top_k:
            raise ValueError('DEFAULT_TOP_K must not exceed MAX_TOP_K')
        return self
