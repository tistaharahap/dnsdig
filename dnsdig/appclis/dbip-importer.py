import asyncio

import aiocsv
import aiofiles
import typer
from beanie import init_beanie
from motor import motor_asyncio
from rich.progress import Progress, SpinnerColumn, TextColumn

from dnsdig.libgeoip.domains.ip2geolocation import IP2Geo
from dnsdig.libgeoip.models import IP2Location, GeoObject, GeoType

app = typer.Typer()


async def _run(mongodb_url: str, db_name: str, dbip_city_csv: str, progress: Progress):
    task_id = progress.add_task("Initializing MongoDB...")
    mongo_client = motor_asyncio.AsyncIOMotorClient(mongodb_url)
    db = mongo_client[db_name]
    doc_models = [IP2Location]
    await init_beanie(db, document_models=doc_models)
    progress.update(task_id, description="MongoDB initialized")

    async with aiofiles.open(dbip_city_csv, mode="r", encoding="utf-8") as csv:
        async for row in aiocsv.AsyncReader(csv):
            progress.update(task_id, description=f"Working on range {row[0]} - {row[1]}")
            geo = GeoObject(type=GeoType.Point, coordinates=(float(row[7]), float(row[8])))
            row = IP2Location(
                ip_range_start=IP2Geo.ip_to_integer(row[0]),
                ip_range_end=IP2Geo.ip_to_integer(row[1]),
                country_iso_code=row[2],
                province=row[3],
                city=row[5],
                geo=geo,
            )
            await row.save()


@app.command()
def main(
    mongodb_url: str = typer.Option(..., allow_dash=True, help='MongoDB URL'),
    db_name: str = typer.Option(..., allow_dash=True, help='MongoDB database name'),
    dbip_city_csv: str = typer.Option(..., allow_dash=True, help='DB IP CSV file path'),
):
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=False) as progress:
        typer.echo("CLI utility to import DB IP City database")
        typer.echo(f"MongoDB URL: {mongodb_url}")
        asyncio.run(_run(mongodb_url, db_name, dbip_city_csv, progress))

        progress.stop()


if __name__ == "__main__":
    app()
