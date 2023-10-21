import typer
import uvloop

from dnsdig.appdnsdigd.settings import dnsdigd_settings
from dnsdig.libdns.domains.dnsdigd import DNSDigUDPServer

app = typer.Typer()


async def serve_dns(host: str, port: int):
    server = DNSDigUDPServer(host=host, port=port)
    await server.start()


@app.command()
def main(
    host: str | None = typer.Option(dnsdigd_settings.host, allow_dash=True, help='Host to listen'),
    port: int | None = typer.Option(dnsdigd_settings.port, allow_dash=True, help='Port to listen'),
):
    typer.echo(f"DNSDig Daemon - Serving at: {host}:{port}")
    uvloop.run(serve_dns(host=host, port=port))


if __name__ == "__main__":
    app()
