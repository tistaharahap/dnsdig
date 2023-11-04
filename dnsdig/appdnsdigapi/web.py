import redis.asyncio as redis
import sentry_sdk
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi_limiter import FastAPILimiter
from starlette.middleware.cors import CORSMiddleware

from dnsdig.appdnsdigapi.views import router as dnsdig_router
from dnsdig.libaccount.models.mongo import User, OAuthSession, Token
from dnsdig.libshared.logging import logger
from dnsdig.libshared.models import mongo_client
from dnsdig.libshared.settings import settings, Environments


async def beanie_setup():
    if settings.env == Environments.Dev:
        logger.info(f"Mongo URL: {settings.mongo_url} - {settings.db_name}")
    logger.info("Initializing MongoDB - Start")
    collections = [User, OAuthSession, Token]
    await init_beanie(database=mongo_client[settings.db_name], document_models=collections)
    logger.info("Initializing MongoDB - End")


async def limiter_setup():
    if settings.env == Environments.Dev:
        logger.info(f"Redis URL: {settings.mongo_url} - {settings.db_name}")
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)
    logger.info("Initializing Redis - End")


app_params = {
    'title': settings.app_name,
    'description': settings.app_description,
    'version': settings.app_version,
    'docs_url': None,
    'redoc_url': None,
}
app = FastAPI(**app_params, on_startup=[beanie_setup, limiter_setup])

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)


@app.get("/healthcheck", status_code=200, tags=['System'])
def health_check():
    return "OK"


@app.get('/openapi.json', include_in_schema=False)
async def openapi():
    return app.openapi()


@app.get('/docs', include_in_schema=False)
async def swagger():
    return get_swagger_ui_html(
        openapi_url='/openapi.json',
        # swagger_css_url='https://cdn.jsdelivr.net/gh/Itz-fork/Fastapi-Swagger-UI-Dark/assets/swagger_ui_dark.min.css',
        title=f"{settings.app_name} - Swagger UI",
    )


app.include_router(dnsdig_router, prefix="/v1")

# Sentry setup
if settings.sentry_dsn == Environments.Production and settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_sample_rate,
        profiles_sample_rate=settings.sentry_sample_rate,
    )
