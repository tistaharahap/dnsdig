import asyncio
from contextlib import asynccontextmanager
from typing import List

import pytest
import pytest_asyncio
from beanie import init_beanie
from faker import Faker
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from motor import motor_asyncio

from dnsdig.appdnsdigapi.web import app as dnsdig_app
from dnsdig.libaccount.domains.account import Account
from dnsdig.libaccount.models.auth import resolver_role, Permissions
from dnsdig.libaccount.models.mongo import User, OAuthSession
from dnsdig.libshared.models import mongo_client
from dnsdig.libshared.settings import settings
from dnsdig.libshared.utils import random_chars

fake = Faker()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    return asyncio.get_event_loop()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def beanie():
    await init_beanie(database=mongo_client[settings.db_name], document_models=[User, OAuthSession])


@pytest_asyncio.fixture(scope="function")
async def user() -> User:
    return await Account.create_user(
        email=f"{random_chars(23)}@{random_chars(10)}.com",
        auth_provider_user_id=random_chars(32),
        permissions=resolver_role.permissions,
        roles=[resolver_role.role],
        first_name=fake.first_name(),
        last_name=fake.last_name(),
    )


class FakeContext:
    def __init__(
        self,
        access_token: str | None = None,
        permissions: List[Permissions] | None = None,
        mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None,
        current_user: User | None = None,
    ):
        self.access_token = access_token
        self.permissions = permissions
        self.mongo_session = mongo_session
        self.current_user = current_user
        self.auth_provider_user_id = current_user.auth_provider_user_id

    @classmethod
    @asynccontextmanager
    async def protected(
        cls,
        authorization: HTTPAuthorizationCredentials,
        permissions: List[Permissions] | None = None,
        mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None,
        **kwargs,
    ):
        current_user = kwargs.get("current_user")
        if current_user.is_blocked:
            raise HTTPException(status_code=403)

        yield cls(
            access_token=authorization.credentials,
            permissions=permissions,
            mongo_session=mongo_session,
            current_user=current_user,
        )

    @classmethod
    @asynccontextmanager
    async def public(cls, mongo_session: motor_asyncio.AsyncIOMotorClientSession | None = None):
        yield cls(mongo_session=mongo_session)


@pytest_asyncio.fixture(autouse=True)
async def nullify_auth(monkeypatch, user: User):
    monkeypatch.setattr(
        "dnsdig.libshared.context.Context.protected",
        lambda *args, **kwargs: FakeContext.protected(*args, **kwargs, current_user=user),
    )
    monkeypatch.setattr("dnsdig.libshared.context.Context.public", FakeContext.public)


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app=dnsdig_app, base_url="http://dnsdigapp")
