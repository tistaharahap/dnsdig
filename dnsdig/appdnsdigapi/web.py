from beanie import init_beanie
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

from dnsdig.appdnsdigapi.views import router as dnsdig_router
from dnsdig.libaccount.models.mongo import User, OAuthSession
from dnsdig.libshared.logging import logger
from dnsdig.libshared.models import mongo_client
from dnsdig.libshared.settings import settings, Environments


async def startup_event():
    if settings.env == Environments.Dev:
        logger.info(f"Mongo URL: {settings.mongo_url}")
    logger.info("Initializing MongoDB - Start")
    collections = [User, OAuthSession]
    await init_beanie(database=mongo_client[settings.db_name], document_models=collections)
    logger.info("Initializing MongoDB - End")


app_params = {
    'title': settings.app_name,
    'description': settings.app_description,
    'version': settings.app_version,
    'docs_url': None,
    'redoc_url': None,
}
app = FastAPI(**app_params, on_startup=[startup_event])


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
