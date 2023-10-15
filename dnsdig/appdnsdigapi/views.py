from typing import Dict

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dnsdig.libaccount.domains.account import Account
from dnsdig.libaccount.models.auth import LoginUrlRequest, Permissions
from dnsdig.libaccount.models.responses import LoginUrlResponse, AccessTokenResponse
from dnsdig.libdns.constants import RecordTypes
from dnsdig.libdns.domains.resolver import ResolverResult, Resolver
from dnsdig.libshared.context import Context
from dnsdig.libshared.models import MongoClient, MongoClientDependency

router = APIRouter()


@router.get(
    "/resolve/{name}",
    summary="Resolve multiple DNS records",
    tags=["Resolver"],
    response_model=Dict[RecordTypes, ResolverResult],
)
async def resolve_dns_records(
    name: str,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    mongo_client: MongoClient = Depends(MongoClientDependency()),
):
    permissions = [Permissions.ReadResolver]

    async with mongo_client.transaction():
        async with Context.protected(authorization=credentials, permissions=permissions):
            results = {
                RecordTypes.A: await Resolver.resolve_record(hostname=name, record_type=RecordTypes.A),
                RecordTypes.AAAA: await Resolver.resolve_record(hostname=name, record_type=RecordTypes.AAAA),
                RecordTypes.MX: await Resolver.resolve_record(hostname=name, record_type=RecordTypes.MX),
                RecordTypes.TXT: await Resolver.resolve_record(hostname=name, record_type=RecordTypes.TXT),
                RecordTypes.SOA: await Resolver.resolve_record(hostname=name, record_type=RecordTypes.SOA),
            }
            return results


@router.get(
    "/resolve/{name}/{record_type}", summary="Resolve a DNS record", tags=["Resolver"], response_model=ResolverResult
)
async def resolve_dns_record(
    name: str,
    record_type: RecordTypes = RecordTypes.A,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    mongo_client: MongoClient = Depends(MongoClientDependency()),
):
    permissions = [Permissions.ReadResolver]

    async with mongo_client.transaction():
        async with Context.protected(authorization=credentials, permissions=permissions):
            return await Resolver.resolve_record(hostname=name, record_type=record_type)


@router.get(
    "/resolve6/{name}/{record_type}",
    summary="Resolve a DNS record using IPv6 resolvers",
    tags=["Resolver"],
    response_model=ResolverResult,
)
async def resolve6_dns_record(
    name: str,
    record_type: RecordTypes = RecordTypes.A,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    mongo_client: MongoClient = Depends(MongoClientDependency()),
):
    permissions = [Permissions.ReadResolver]

    async with mongo_client.transaction():
        async with Context.protected(authorization=credentials, permissions=permissions):
            return await Resolver.resolve_record(hostname=name, record_type=record_type)


@router.post("/me/login-url", summary="Get the login URL for a user", tags=["Me"], response_model=LoginUrlResponse)
async def get_login_url(payload: LoginUrlRequest, mongo_client: MongoClient = Depends(MongoClientDependency())):
    async with mongo_client.transaction():
        async with Context.public():
            return await Account.get_login_url(payload=payload)


@router.get("/callbacks/kinde", summary="OAuth callback", tags=["Me", "OAuth"], response_model=AccessTokenResponse)
async def kinde_callback(code: str, state: str, mongo_client: MongoClient = Depends(MongoClientDependency())):
    async with mongo_client.transaction():
        async with Context.public():
            return await Account.exchange_for_access_token(code=code, state=state)


@router.get(
    "/oauth2/token",
    summary="Exchange refresh token for access token",
    tags=["Me", "OAuth"],
    response_model=AccessTokenResponse,
)
async def kinde_callback(refresh_token: str, mongo_client: MongoClient = Depends(MongoClientDependency())):
    async with mongo_client.transaction():
        async with Context.public():
            return await Account.exchange_for_access_token(code=refresh_token, refresh_exchange=True)
