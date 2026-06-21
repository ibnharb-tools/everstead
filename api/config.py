"""App configuration from environment variables."""
import os
from functools import lru_cache
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./everstead.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week
    cors_origins: str = "*"
    allow_network: bool = True  # set ALLOW_NETWORK=false to use offline synthetic climate

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
