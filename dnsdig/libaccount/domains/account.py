import urllib.parse
from datetime import datetime
from functools import lru_cache
from secrets import token_hex
from typing import List

import aiohttp
import jwt
import ujson
from fastapi import HTTPException

from dnsdig.libaccount.models.auth import Permissions, Roles, resolver_role, LoginUrlRequest
from dnsdig.libaccount.models.mongo import User, OAuthSession
from dnsdig.libaccount.models.responses import LoginUrlResponse, AccessTokenResponse
from dnsdig.libshared.monq import monq_find_one
from dnsdig.libshared.settings import settings


class Account:
    @classmethod
    async def create_user(
        cls,
        email: str,
        auth_provider_user_id: str,
        permissions: List[Permissions],
        roles: List[Roles],
        first_name: str | None = None,
        last_name: str | None = None,
        avatar: str | None = None,
    ) -> User:
        user = User(
            email=email,
            auth_provider_user_id=[auth_provider_user_id],
            permissions=permissions,
            roles=roles,
            first_name=first_name,
            last_name=last_name,
            avatar=avatar,
        )
        await user.save()
        return user

    @classmethod
    async def get_login_url(cls, payload: LoginUrlRequest) -> LoginUrlResponse:
        state = token_hex(32) if not payload.state else payload.state

        session = OAuthSession(state=state, store=payload.store)
        await session.save()

        query_params = {
            "client_id": settings.auth_provider_client_id,
            "response_type": "code",
            "redirect_uri": settings.auth_provider_redirect_uri,
            "scope": "openid profile email offline",
            "state": session.state,
        }
        encoded = urllib.parse.urlencode(query_params)
        url = f"{settings.auth_provider_host}/oauth2/auth?{encoded}"
        return LoginUrlResponse(login_url=url)

    @classmethod
    @lru_cache()
    def get_jwks_client(cls) -> jwt.PyJWKClient:
        return jwt.PyJWKClient(settings.auth_jwks_url)

    @classmethod
    async def maybe_create_user(cls, id_token: str):
        payload = jwt.decode(id_token, options={"verify_signature": False})

        email = payload.get("email")
        auth_provider_user_id = payload.get("sub")
        if not email or not auth_provider_user_id:
            return

        query = {"auth_provider_user_id": auth_provider_user_id}
        user = await monq_find_one(model=User, query=query, project_to=User)
        if user:
            return

        query = {"email": email}
        user = await monq_find_one(model=User, query=query, project_to=User)
        if user and user.auth_provider_user_id != auth_provider_user_id:
            user.auth_provider_user_id.append(auth_provider_user_id)
            await user.save()
            return

        await cls.create_user(
            email=email,
            auth_provider_user_id=auth_provider_user_id,
            permissions=resolver_role.permissions,
            roles=[resolver_role.role],
            first_name=payload.get("given_name"),
            last_name=payload.get("family_name"),
        )

    @classmethod
    async def exchange_for_access_token(
        cls, code: str, state: str | None = None, refresh_exchange: bool = False
    ) -> AccessTokenResponse:
        oauth_session = None
        if state and not refresh_exchange:
            # Exchanging authorization code for an access token
            query = {"state": state, "deleted_at": {"$eq": None}}
            oauth_session = await monq_find_one(model=OAuthSession, query=query, project_to=OAuthSession)
            if not oauth_session:
                raise HTTPException(status_code=400, detail="Invalid state")

            # Mark session as deleted
            oauth_session.deleted_at = datetime.utcnow()
            await oauth_session.save()

        data = {
            "client_id": settings.auth_provider_client_id,
            "client_secret": settings.auth_provider_client_secret,
            "grant_type": "authorization_code" if not refresh_exchange else "refresh_token",
            "code": code if not refresh_exchange else None,
            "redirect_uri": settings.auth_provider_redirect_uri,
            "refresh_token": code if refresh_exchange else None,
        }
        url = f"{settings.auth_provider_host}/oauth2/token"

        async with aiohttp.ClientSession() as session:
            headers = {"accept": "application/json"}
            async with session.post(url, headers=headers, data=data) as resp:
                text = await resp.text()
                kinde_token = ujson.decode(text)
                if not kinde_token.get("access_token"):
                    raise HTTPException(status_code=400, detail="Invalid or expired authorization code")

                if not refresh_exchange:
                    await cls.maybe_create_user(id_token=kinde_token.get("id_token"))

                return AccessTokenResponse(
                    access_token=kinde_token.get("access_token"),
                    refresh_token=kinde_token.get("refresh_token"),
                    expires_in=kinde_token.get("expires_in"),
                    scope=kinde_token.get("scope"),
                    token_type=kinde_token.get("token_type"),
                    store=oauth_session.store if oauth_session else None,
                )
