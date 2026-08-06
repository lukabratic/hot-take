from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
"""Application settings loaded from environment variables."""

database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hot_take"
redis_url: str = "redis://localhost:6379/0"
clerk_issuer: str = ""
clerk_jwks_url: str = ""
frontend_origin: str = "http://localhost:5173"

@field_validator("database_url")
@classmethod
def ensure_asyncpg_scheme(cls, v: str) -> str:
"""Ensure database URL uses asyncpg driver."""
if v.startswith("postgresql://"):
return v.replace("postgresql://", "postgresql+asyncpg://", 1)
if v.startswith("postgres://"):
return v.replace("postgres://", "postgresql+asyncpg://", 1)
return v

class Config:
env_file = ".env"
env_file_encoding = "utf-8"


settings = Settings()