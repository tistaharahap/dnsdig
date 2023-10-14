import asyncio

import pytest
from beanie import init_beanie
import pytest_asyncio
from faker import Faker

from dnsdig.libaccount.domains.account import Account
from dnsdig.libaccount.models.auth import resolver_role
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


@pytest_asyncio.fixture(scope="session")
async def user() -> User:
    return await Account.create_user(
        email="",
        auth_provider_user_id=random_chars(32),
        permissions=resolver_role.permissions,
        roles=[resolver_role.role],
        first_name=fake.first_name(),
        last_name=fake.last_name(),
    )
