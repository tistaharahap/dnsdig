from typing import Dict, Any

from pydantic import HttpUrl

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
