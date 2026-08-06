from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/hot_take",
        validation_alias=AliasChoices("DATABASE_URL", "database_url", "POSTGRES_URL"),
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    clerk_issuer: str = ""
    clerk_jwks_url: str = ""
    frontend_origin: str = "http://localhost:5173"

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_asyncpg_scheme(cls, v: object) -> object:
        """Ensure database URL uses the asyncpg driver expected by SQLAlchemy async engines."""
        if not isinstance(v, str):
            return v

        value = v.strip()
        if not value:
            return value

        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql+psycopg2://"):
            return value.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql+psycopg://"):
            return value.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
        return value


class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"


settings = Settings()