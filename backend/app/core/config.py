from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "mhc_cloud_panel"
    postgres_user: str = "mhc"
    postgres_password: str = "mhc"
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")

    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = "change-me"
    jwt_access_token_expires_minutes: int = 15
    jwt_refresh_token_expires_days: int = 30
    jwt_issuer: str = "mhc-cloud-panel"

    seed_on_startup: bool = False

    proxmox_host: AnyUrl | None = None
    proxmox_user: str | None = None
    proxmox_realm: str = "pam"
    proxmox_token_name: str | None = None
    proxmox_token_secret: str | None = None
    proxmox_verify_ssl: bool = True
    proxmox_timeout_seconds: int = 15
    proxmox_retry_total: int = 3

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, get_settings]
