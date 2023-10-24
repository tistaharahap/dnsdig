from datetime import datetime
from typing import Dict, Any

from pydantic import HttpUrl, Field

from dnsdig.libshared.models import BaseRequestResponse


class LoginUrlResponse(BaseRequestResponse):
    login_url: HttpUrl


class AccessTokenResponse(BaseRequestResponse):
    access_token: str
    expires_in: int
    refresh_token: str
    scope: str
    token_type: str
    store: Dict[str, Any] | None = None


class UserApplicationResponse(BaseRequestResponse):
    name: str
    description: str | None = None
    client_id: str
    client_secret: str
    website: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
