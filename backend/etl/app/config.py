from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql+psycopg://app:app@postgres:5432/app",
        validation_alias="DATABASE_URL",
    )
    opensearch_hosts: list[str] = Field(
        default_factory=lambda: ["https://opensearch:9200"],
        validation_alias="OPENSEARCH_HOSTS",
    )
    opensearch_index: str = Field(
        default="products",
        validation_alias="OPENSEARCH_INDEX",
    )
    opensearch_username: str = Field(
        default="admin",
        validation_alias="OPENSEARCH_USERNAME",
    )
    opensearch_password: str = Field(
        default="Opensearch#2025!",
        validation_alias="OPENSEARCH_PASSWORD",
    )
    embedding_model: str = Field(
        default="models/text-embedding-004",
        validation_alias="EMBEDDING_MODEL",
    )
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    chunk_size: int = Field(default=400, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, validation_alias="CHUNK_OVERLAP")
    poll_interval_seconds: int = Field(default=5, validation_alias="POLL_INTERVAL_SECONDS")
    max_attempts: int = Field(default=5, validation_alias="MAX_JOB_ATTEMPTS")

    class Config:
        env_file = ".env"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

