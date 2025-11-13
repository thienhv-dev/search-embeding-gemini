from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="Gemini Search API")

    database_url: str = Field(
        default="postgresql+psycopg://app:app@postgres:5432/app",
        validation_alias="DATABASE_URL",
    )

    opensearch_hosts: List[str] = Field(
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

    minio_endpoint: str = Field(default="minio:9000", validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="product-images", validation_alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, validation_alias="MINIO_SECURE")

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")

    embedding_model: str = Field(
        default="models/text-embedding-004",
        validation_alias="EMBEDDING_MODEL",
    )

    class Config:
        env_file = ".env"
        env_prefix = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()

