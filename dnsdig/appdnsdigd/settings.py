from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class DNSDigdSettings(BaseSettings):
    app_name: str = "dnsdigd"
    db_name: str = "dnsdigd"
    port: int = 5053
    host: str = "127.0.0.1"
    mongo_url: str | None = "mongodb://localhost:27017"
    redis_url: str | None = "redis://localhost:6379"

    @classmethod
    @lru_cache()
    def get_settings(cls) -> DNSDigdSettings:
        return cls()


dnsdigd_settings = DNSDigdSettings.get_settings()
