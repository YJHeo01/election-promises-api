from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    custom_gpt_api_key: str = Field(
        default="change-me",
        validation_alias="CUSTOM_GPT_API_KEY",
        description="Bearer token expected from Custom GPT Actions.",
    )
    database_url: str = Field(
        default="sqlite:///./election_promises.db",
        validation_alias="DATABASE_URL",
        description="SQLAlchemy database URL.",
    )
    app_name: str = Field(
        default="Election Promise Context API",
        validation_alias="APP_NAME",
        description="Service name added to structured logs.",
    )
    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
        description="Deployment environment added to structured logs.",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
        description="Python logging level, for example DEBUG, INFO, WARNING, or ERROR.",
    )
    log_format: str = Field(
        default="json",
        validation_alias="LOG_FORMAT",
        description="Log formatter. Use json for collectors or text for local debugging.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
