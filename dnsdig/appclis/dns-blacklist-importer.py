import asyncio

import aiohttp
import redis.asyncio as redis
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from dnsdig.appdnsdigd.settings import dnsdigd_settings

"""
Shoutout to these Github repos for the blacklist files:
- https://github.com/anudeepND/blacklist
"""
blacklist_hosts_files = ["https://raw.githubusercontent.com/anudeepND/blacklist/master/adservers.txt"]

app = typer.Typer()


async def download_hosts_file(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


def get_redis_client(redis_url: str | None = None) -> redis.Redis:
    _redis_url = redis_url
    if not _redis_url:
        _redis_url = dnsdigd_settings.redis_url
    return redis.from_url(_redis_url, encoding="utf-8", decode_responses=True)


async def process_hosts(hosts: str, redis_client: redis.Redis):
    parsed_hosts = [x for x in hosts.split("\n") if not x.startswith("#") and x != ""]
    for host in parsed_hosts:
        ns = "dnsdigd-blacklist"
        ip, hn = host.split(" ")
        await redis_client.hset(ns, hn, ip)


async def _run(redis_url: str, progress: Progress):
    redis_client = get_redis_client(redis_url)

    task_id = progress.add_task("Downloading hosts files...")
    for url in blacklist_hosts_files:
        progress.update(task_id, description=f"Downloading {url}")
        hosts = await download_hosts_file(url)
        progress.update(task_id, description=f"Processing {url}")
        await process_hosts(hosts, redis_client)


@app.command()
def main(redis_url: str = typer.Option(..., allow_dash=True, help='Redis URL')):
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=False) as progress:
        typer.echo("CLI utility to import DB IP City database")
        typer.echo(f"Redis URL: {redis_url}")
        asyncio.run(_run(redis_url, progress))

        progress.stop()


if __name__ == "__main__":
    app()
