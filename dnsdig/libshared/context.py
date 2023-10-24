from contextlib import asynccontextmanager
from datetime import datetime
from functools import lru_cache
from typing import List

import jwt
from asyncer import asyncify
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from motor import motor_asyncio

from dnsdig.libaccount.constants import TokenTypes
from dnsdig.libaccount.models.auth import Permissions
from dnsdig.libaccount.models.mongo import User, Token, UserApplication
from dnsdig.libshared.monq import monq_find_one
from dnsdig.libshared.settings import settings


class Context:
    def __init__(
        self,
        access_token: str | None = None,
        permissions: List[Permissions] | None = None,
        mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None,
    ):
        self.access_token: str = access_token
        self.permissions: List[Permissions] = permissions
        self.mongo_session: motor_asyncio.AsyncIOMotorClientSession = mongo_session

        self.current_user: User | None = None
        self.current_app: UserApplication | None = None
        self.auth_provider_user_id: str | None = None

    @classmethod
    @lru_cache()
    def get_jwks_client(cls) -> jwt.PyJWKClient:
        return jwt.PyJWKClient(settings.auth_jwks_url)

    async def _authorize_m2m_token(self):
        query = {"token": self.access_token}
        token = await monq_find_one(model=Token, query=query, project_to=Token)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token")
        if token.token_type != TokenTypes.M2M:
            raise HTTPException(status_code=401, detail="Invalid token")
        if token.expires_at < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")

        self.current_user = await User.get_user_by_app_client_id(client_id=token.owner_id)
        if self.current_user.is_blocked:
            raise HTTPException(
                status_code=403, detail="The owner of the application is blocked from using this service"
            )

        self.current_app = await User.get_app_by_client_id(client_id=token.owner_id)

        for permission in self.permissions:
            if permission not in self.current_app.permissions:
                raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    async def _authorize_jwt_token(self):
        jwks_client = await asyncify(Context.get_jwks_client)()
        signing_key = jwks_client.get_signing_key_from_jwt(self.access_token)
        payload = jwt.decode(self.access_token, signing_key.key, algorithms=[settings.auth_jwt_algo])

        iss = payload.get("iss")
        if iss != settings.auth_provider_host:
            raise HTTPException(status_code=401, detail="Invalid issuer")

        expire_at_unix_timestamp = payload.get("exp")
        if expire_at_unix_timestamp is None or expire_at_unix_timestamp < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")

        self.auth_provider_user_id = payload.get("sub")

        query = {"auth_provider_user_id": self.auth_provider_user_id}
        self.current_user = await monq_find_one(model=User, query=query, project_to=User)
        if not self.current_user:
            raise HTTPException(status_code=401, detail="User not found")

        if self.current_user.is_blocked:
            raise HTTPException(status_code=403, detail="You are blocked from using this platform")

        for permission in self.permissions:
            if permission not in self.current_user.permissions:
                raise HTTPException(status_code=403, detail="You do not have permission to perform this action")

    async def authorize_access_token(self):
        if self.access_token.startswith("m2m"):
            return await self._authorize_m2m_token()
        else:
            return await self._authorize_jwt_token()

    @classmethod
    @asynccontextmanager
    async def protected(
        cls,
        authorization: HTTPAuthorizationCredentials,
        permissions: List[Permissions] | None = None,
        mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None,
    ):
        if authorization is None or authorization.credentials is None:
            raise HTTPException(status_code=401, detail="Unrecognized or missing authorization header")

        instance = cls(access_token=authorization.credentials, permissions=permissions, mongo_session=mongo_session)

        await instance.authorize_access_token()

        yield instance

    @classmethod
    @asynccontextmanager
    async def public(cls, mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None):
        instance = cls(mongo_session=mongo_session)

        yield instance
