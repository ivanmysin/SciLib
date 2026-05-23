"""Application configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Domain & TLS
    domain: str = "localhost"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/scientific_library"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # GROBID
    grobid_url: str = "http://localhost:8070"

    # Storage
    storage_backend: str = "local"
    storage_path: str = "./storage"

    # Embeddings
    embedding_model: str = "allenai/specter2_base"
    embedding_dim: int = 768

    # Crossref
    crossref_mailto: str = "admin@example.org"

    # Application
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
