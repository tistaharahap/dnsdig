from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environments(str, Enum):
    Dev = "dev"
    Staging = "staging"
    Production = "prod"
    Testing = "pytest"


class Settings(BaseSettings):
    # App settings
    app_name: str = "DNS Dig API"
    app_version: str = "0.1.0"
    app_description: str = "An HTTP API to resolve DNS records for developers"

    # Env Vars
    env: Environments
    mongo_url: str
    redis_url: str
    testing: str | None = None
    auth_jwks_url: str
    auth_jwt_algo: str
    auth_provider_host: str
    auth_provider_client_id: str
    auth_provider_client_secret: str
    auth_provider_redirect_uri: str
    ipinfo_host: str
    ipinfo_token: str

    # Throttler
    throttler_times: int = 30
    throttler_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def db_name(self) -> str:
        db_postfix = settings.env.value if not settings.testing == Environments.Testing else "test"
        return f"dnsdig-{db_postfix}"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
