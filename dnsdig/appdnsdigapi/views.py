import asyncio
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_limiter.depends import RateLimiter

from dnsdig.libaccount.domains.account import Account
from dnsdig.libaccount.models.auth import (
    LoginUrlRequest,
    Permissions,
    CreateApplicationRequest,
    ClientCredentialsRequest,
    RefreshTokenExchangeRequest,
)
from dnsdig.libaccount.models.responses import LoginUrlResponse, AccessTokenResponse, UserApplicationResponse
from dnsdig.libdns.constants import RecordTypes
from dnsdig.libdns.domains.resolver import ResolverResult, Resolver
from dnsdig.libshared.context import Context
from dnsdig.libshared.models import MongoClient, MongoClientDependency
from dnsdig.libshared.settings import settings

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
            group = [
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.A),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.AAAA),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.MX),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.TXT),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.SOA),
            ]
            group_results = await asyncio.gather(*group)
            results = {
                RecordTypes.A: group_results[0],
                RecordTypes.AAAA: group_results[1],
                RecordTypes.MX: group_results[2],
                RecordTypes.TXT: group_results[3],
                RecordTypes.SOA: group_results[4],
            }
            return results


@router.get(
    "/freesolve/{name}",
    summary="Resolve multiple DNS records - Throttled",
    tags=["Resolver", "Throttled"],
    response_model=Dict[RecordTypes, ResolverResult],
    dependencies=[Depends(RateLimiter(times=settings.throttler_times, seconds=settings.throttler_seconds))],
)
async def freesolve_dns_records(name: str, mongo_client: MongoClient = Depends(MongoClientDependency())):
    async with mongo_client.transaction():
        async with Context.public():
            group = [
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.A),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.AAAA),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.MX),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.TXT),
                Resolver.resolve_record(hostname=name, record_type=RecordTypes.SOA),
            ]
            group_results = await asyncio.gather(*group)
            results = {
                RecordTypes.A: group_results[0],
                RecordTypes.AAAA: group_results[1],
                RecordTypes.MX: group_results[2],
                RecordTypes.TXT: group_results[3],
                RecordTypes.SOA: group_results[4],
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
    "/freesolve/{name}/{record_type}",
    summary="Resolve a DNS record",
    tags=["Resolver", "Throttled"],
    response_model=ResolverResult,
    dependencies=[Depends(RateLimiter(times=settings.throttler_times, seconds=settings.throttler_seconds))],
)
async def freesolve_dns_record(
    name: str, record_type: RecordTypes = RecordTypes.A, mongo_client: MongoClient = Depends(MongoClientDependency())
):
    async with mongo_client.transaction():
        async with Context.public():
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
async def kinde_exchange_refresh_token(
    refresh_token: str, mongo_client: MongoClient = Depends(MongoClientDependency())
):
    async with mongo_client.transaction():
        async with Context.public():
            return await Account.exchange_for_access_token(code=refresh_token, refresh_exchange=True)


@router.post(
    "/oauth2/token",
    summary="Generate access token for several grant types for M2M apps",
    tags=["Me", "OAuth", "Applications"],
    response_model=AccessTokenResponse,
)
async def token_from_credentials(
    payload: ClientCredentialsRequest | RefreshTokenExchangeRequest,
    mongo_client: MongoClient = Depends(MongoClientDependency()),
):
    async with mongo_client.transaction():
        async with Context.public():
            match payload.grant_type:
                case "client_credentials":
                    return await Account.m2m_client_credentials_exchange(payload=payload)
                case "refresh_token":
                    return await Account.m2m_refresh_token_exchange(payload=payload)
                case _:
                    raise HTTPException(status_code=400, detail="Invalid grant_type")


@router.post(
    "/me/applications",
    summary="Create an application for a user",
    tags=["Me", "Applications"],
    response_model=UserApplicationResponse,
)
async def create_app(
    payload: CreateApplicationRequest,
    mongo_client: MongoClient = Depends(MongoClientDependency()),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    permissions = [Permissions.ReadApplication, Permissions.WriteApplication]

    async with mongo_client.transaction():
        async with Context.protected(authorization=credentials, permissions=permissions) as ctx:
            return await Account.create_application(payload=payload, context=ctx)


@router.get(
    "/me/applications",
    summary="List all my applications",
    tags=["Me", "Applications"],
    response_model=List[UserApplicationResponse],
)
async def list_app(
    mongo_client: MongoClient = Depends(MongoClientDependency()),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    permissions = [Permissions.ReadApplication]

    async with mongo_client.transaction():
        async with Context.protected(authorization=credentials, permissions=permissions) as ctx:
            return await Account.list_applications(context=ctx)
