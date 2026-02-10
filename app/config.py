from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    upstream_api_url: str = Field(...)
    cache_ttl_seconds: int = Field(...)

    host: str = Field(...)
    port: int = Field(...)

    request_timeout: int = 30
    upstream_timeout_seconds: float = 10.0

    bootstrap_limit: int = 200
    bootstrap_max_pages: int | None = None


settings = Settings()
