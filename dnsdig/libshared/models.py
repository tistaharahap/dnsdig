import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal

from beanie import Document, before_event, ValidateOnSave, Update
from humps import camelize
from pydantic import BaseModel, Field, ConfigDict
from motor import motor_asyncio
from fastapi import Request

from dnsdig.libshared.settings import settings, Environments

client_options = {'appname': settings.app_name}
mongo_client = motor_asyncio.AsyncIOMotorClient(settings.mongo_url, **client_options)
mongo_client.get_io_loop = asyncio.get_running_loop


class BaseRequestResponse(BaseModel):
    model_config = ConfigDict(
        use_enum_values=True, alias_generator=camelize, json_encoders={Decimal: str}, populate_by_name=True
    )


class BaseDatetimeMeta(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class BaseMongoDocument(Document, BaseDatetimeMeta):
    @before_event(ValidateOnSave, Update)
    async def update_timestamps(self):
        self.updated_at = datetime.utcnow()


class MongoClient:
    def __init__(self):
        self.client = mongo_client
        self.is_testing = settings.testing == Environments.Testing.value

    @property
    def db_name(self) -> str:
        db_postfix = settings.env if not self.is_testing else "test"
        return f"dnsdig-{db_postfix}"

    @asynccontextmanager
    async def transaction(self) -> motor_asyncio.AsyncIOMotorClient:
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                except Exception as exc:
                    await session.abort_transaction()
                    raise exc


class MongoClientDependency:
    def __init__(self):
        self.client = MongoClient()

    async def __call__(self, request: Request) -> MongoClient:
        return self.client
