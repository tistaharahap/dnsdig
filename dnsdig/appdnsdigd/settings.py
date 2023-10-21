from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class DNSDigdSettings(BaseSettings):
    port: int = 5053
    host: str = "127.0.0.1"

    @classmethod
    @lru_cache()
    def get_settings(cls) -> DNSDigdSettings:
        return cls()


dnsdigd_settings = DNSDigdSettings.get_settings()
