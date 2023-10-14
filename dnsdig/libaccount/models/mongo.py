from datetime import datetime
from typing import List, Dict, Any

import pymongo
from beanie import PydanticObjectId
from pydantic import EmailStr, Field, HttpUrl
from pymongo import IndexModel

from dnsdig.libaccount.models.auth import Permissions, Roles
from dnsdig.libshared.models import BaseMongoDocument


class User(BaseMongoDocument):
    email: EmailStr
    auth_provider_user_id: List[str] = Field(default_factory=list)
    permissions: List[Permissions] = Field(default_factory=list)
    roles: List[Roles] = Field(default_factory=list)
    first_name: str | None = None
    last_name: str | None = None
    avatar: HttpUrl | None = None
    blocked_at: datetime | None = None

    class Settings:
        name: str = "users"
        indexes: List[IndexModel] = [
            IndexModel([("email", pymongo.ASCENDING)], unique=True, name="unique_emails"),
            IndexModel([("auth_provider_user_id", pymongo.ASCENDING)], name="auth_provider_user_ids"),
        ]

    @property
    def is_blocked(self) -> bool:
        return self.blocked_at is not None


class OAuthSession(BaseMongoDocument):
    state: str
    code: str | None = None
    user_id: PydanticObjectId | None = None
    store: Dict[str, Any] | None = None

    class Settings:
        name: str = "oauth-sessions"
        indexes: List[IndexModel] = [IndexModel([("state", pymongo.ASCENDING)], unique=True, name="unique_states")]
