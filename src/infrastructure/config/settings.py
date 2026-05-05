from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/openspec"
    app_name: str = "open-spec-base-app"
    app_version: str = "0.1.0"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
