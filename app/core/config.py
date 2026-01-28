from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Product-to-Code"
    api_v1_prefix: str = ""

    # Storage
    storage_root: Path = Field(default=Path("data"), validation_alias="STORAGE_ROOT")
    max_upload_mb: int = Field(default=20, validation_alias="MAX_UPLOAD_MB")

    # Database
    database_url: str = Field(default="sqlite:///./data/app.db", validation_alias="DATABASE_URL")

    # Security
    jwt_secret: str = Field(default="change-me", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Optional: seed an admin account
    seed_admin_email: str | None = Field(default=None, validation_alias="SEED_ADMIN_EMAIL")
    seed_admin_password: str | None = Field(default=None, validation_alias="SEED_ADMIN_PASSWORD")

    # Milestone 2: Web research
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")
    research_max_results: int = Field(default=8, validation_alias="RESEARCH_MAX_RESULTS")
    research_search_depth: str = Field(default="basic", validation_alias="RESEARCH_SEARCH_DEPTH")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    return settings
