from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_env: str = "local"
    project_name: str = "AI Infrastructure Radar"
    database_url: str = "sqlite+pysqlite:///./.data/radar-dev.db"
    redis_url: str = "redis://redis:6379/0"
    backend_cors_origins: list[str] = ["http://localhost:3000"]
    backend_trusted_hosts: list[str] = ["localhost", "127.0.0.1", "testserver", "backend"]
    internal_api_url: str = "http://localhost:8000"
    next_public_api_url: str = "http://localhost:8000"
    github_token: str | None = None
    huggingface_token: str | None = None
    sec_user_agent: str = "ai-infrastructure-radar dev@example.com"
    request_timeout_seconds: float = 20.0

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @field_validator("backend_trusted_hosts", mode="before")
    @classmethod
    def parse_trusted_hosts(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return [host.strip() for host in value.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
