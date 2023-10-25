from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

import pymongo
from beanie import PydanticObjectId
from functional import seq
from pydantic import EmailStr, Field, HttpUrl, BaseModel
from pymongo import IndexModel

from dnsdig.libaccount.constants import TokenTypes
from dnsdig.libaccount.models.auth import Permissions, Roles
from dnsdig.libshared.models import BaseMongoDocument
from dnsdig.libshared.monq import monq_find_one


class UserApplication(BaseModel):
    name: str
    description: str | None = None
    permissions: List[Permissions] = Field(default_factory=list)
    client_id: str
    client_secret: str
    website: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None


class User(BaseMongoDocument):
    email: EmailStr
    auth_provider_user_id: List[str] = Field(default_factory=list)
    permissions: List[Permissions] = Field(default_factory=list)
    roles: List[Roles] = Field(default_factory=list)
    first_name: str | None = None
    last_name: str | None = None
    avatar: HttpUrl | None = None
    blocked_at: datetime | None = None
    applications: List[UserApplication] = Field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return self.blocked_at is not None

    @classmethod
    async def get_app_by_client_id(cls, client_id: str) -> UserApplication | None:
        query = {"applications.client_id": client_id}
        user = await monq_find_one(model=cls, query=query, project_to=cls)
        return seq(user.applications).find(lambda app: app.client_id == client_id)

    @classmethod
    async def get_user_by_app_client_id(cls, client_id: str) -> User | None:
        query = {"applications.client_id": client_id}
        return await monq_find_one(model=cls, query=query, project_to=cls)

    class Settings:
        name: str = "users"
        indexes: List[IndexModel] = [
            IndexModel([("email", pymongo.ASCENDING)], unique=True, name="unique_emails"),
            IndexModel([("auth_provider_user_id", pymongo.ASCENDING)], name="auth_provider_user_ids"),
        ]


class OAuthSession(BaseMongoDocument):
    state: str
    code: str | None = None
    user_id: PydanticObjectId | None = None
    store: Dict[str, Any] | None = None

    class Settings:
        name: str = "oauth-sessions"
        indexes: List[IndexModel] = [IndexModel([("state", pymongo.ASCENDING)], unique=True, name="unique_states")]


class Token(BaseMongoDocument):
    token: str
    token_type: TokenTypes
    expires_at: datetime
    owner_id: str

    @classmethod
    async def get_token(cls, token: str, token_type: TokenTypes) -> Token | None:
        query = {"token": token, "token_type": token_type}
        return await monq_find_one(model=cls, query=query, project_to=cls)

    class Settings:
        name: str = "tokens"
