from enum import Enum
from functools import lru_cache
from os import environ

from pydantic import Extra
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
    env: Environments = environ.get('ENV', Environments.Dev.value)
    mongo_url: str = environ.get('MONGO_URL')
    testing: str | None = environ.get('TESTING')
    auth_jwks_url: str = environ.get('AUTH_JWKS_URL')
    auth_jwt_algo: str = environ.get('AUTH_JWT_ALGO')
    auth_provider_host: str = environ.get('AUTH_PROVIDER_HOST')
    auth_provider_client_id: str = environ.get('AUTH_PROVIDER_CLIENT_ID')
    auth_provider_client_secret: str = environ.get('AUTH_PROVIDER_CLIENT_SECRET')
    auth_provider_redirect_uri: str = environ.get('AUTH_PROVIDER_REDIRECT_URI')

    model_config = SettingsConfigDict(env_file=".env", extra=Extra.ignore)

    @property
    def db_name(self) -> str:
        db_postfix = settings.env.value if not settings.testing == Environments.Testing else "test"
        return f"dnsdig-{db_postfix}"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
