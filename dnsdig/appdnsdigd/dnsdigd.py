import typer
import uvloop

from dnsdig.appdnsdigd.settings import dnsdigd_settings
from dnsdig.appdnsdigd.udpserver import DNSDigUDPServer

app = typer.Typer()


async def serve_dns(host: str, port: int, use_adblocker: bool):
    server = DNSDigUDPServer(host=host, port=port, use_adblocker=use_adblocker)
    await server.start()


@app.command()
def main(
    host: str | None = typer.Option(dnsdigd_settings.host, allow_dash=True, help='Host to listen'),
    port: int | None = typer.Option(dnsdigd_settings.port, allow_dash=True, help='Port to listen'),
    use_adblocker: bool = typer.Option(dnsdigd_settings.use_adblocker, allow_dash=True, help='Use adblocker'),
):
    typer.echo(f"DNSDig Daemon - {host}:{port} - {dnsdigd_settings.mongo_url} - {dnsdigd_settings.redis_url}")
    uvloop.run(serve_dns(host=host, port=port, use_adblocker=use_adblocker))


if __name__ == "__main__":
    app()
