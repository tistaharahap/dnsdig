import asyncio
import random
import time

import asyncudp
import dns.message
import redis.asyncio as redis
from asyncer import asyncify
from rich.console import Console
from rich.table import Table

from dnsdig.appdnsdigd.analytics import DNSAnalytics
from dnsdig.appdnsdigd.analyticsmongo import Analytics, StatsTimeframes, AnalyticsResults
from dnsdig.appdnsdigd.settings import dnsdigd_settings
from dnsdig.libshared.logging import logger


class DNSDigUDPServer:
    def __init__(self, host: str, port: int, socket: asyncudp.Socket | None = None, use_cache: bool = True):
        self.host = host
        self.port = port
        self.socket = socket

        # Caching
        self.use_cache = use_cache
        self.redis_client: redis.Redis | None = None
        if self.use_cache:
            self.redis_client = redis.from_url(dnsdigd_settings.redis_url, encoding="utf-8", decode_responses=True)

        # Analytics
        self.analytics: DNSAnalytics | None = None

        # Resolvers
        self.resolvers = ['8.8.8.8', '8.8.4.4', '1.1.1.1', '1.0.0.1']

    @property
    def resolver(self) -> str:
        return random.choice(self.resolvers)

    @classmethod
    def render_stats_table(cls, stats: AnalyticsResults, timeframe: StatsTimeframes):
        print("\n")
        table = Table(
            "Average",
            "Median",
            "Minimum",
            "Maximum",
            "75%",
            "99%",
            title="Per Minute Stats",
            title_justify="center",
            caption=f"Last {timeframe.value} minutes",
        )
        table.add_row(
            f"{stats.average:.2f} ms",
            f"{stats.median:.2f} ms",
            f"{stats.minimum:.2f} ms",
            f"{stats.maximum:.2f} ms",
            f"{stats.percentiles[0]:.2f} ms",
            f"{stats.percentiles[1]:.2f} ms",
        )

        console = Console()
        console.print(table)
        print("\n")

    @classmethod
    async def output_stats(cls):
        while True:
            stats = await Analytics.statistics(timeframe=StatsTimeframes.Minutes60)
            if stats:
                cls.render_stats_table(stats=stats, timeframe=StatsTimeframes.Minutes60)
            await asyncio.sleep(60)

    async def query_dns_tls(self, message: dns.message.Message) -> dns.message.Message:
        name = message.question[0].name
        rtype = message.question[0].rdtype
        ns = f"dnsdigd-cache#{name}#{rtype}"
        cached = await self.redis_client.get(ns)
        if cached:
            logger.info(f"Cache hit for {name} {rtype}")
            return dns.message.from_text(cached)

        response = await dns.asyncquery.tls(message, where=self.resolver)
        if len(response.answer) > 0:
            await self.redis_client.set(ns, response.to_text(), ex=response.answer[0].ttl)
        return response

    async def run_forever(self):
        while True:
            data, addr = await self.socket.recvfrom()

            start_time = time.time()

            data = dns.message.from_wire(data)

            logger.info(f"[{data.id}] Received query from {addr} for {data.question[0].name} {data.question[0].rdtype}")
            dns_response = await self.query_dns_tls(data)

            end_time = time.time()
            delta = (end_time - start_time) * 1000
            logger.info(f"[{data.id}] Query took {int(delta)} ms")

            dns_response.id = data.id

            logger.info(f"[{data.id}] Sending response for {data.question[0].name} {data.question[0].rdtype}")
            await asyncify(self.socket.sendto)(dns_response.to_wire(), addr)

            if len(dns_response.answer) > 0:
                await self.analytics.log_resolver(
                    name=str(data.question[0].name),
                    record_type=data.question[0].rdtype,
                    resolve_time=delta,
                    ttl=dns_response.answer[0].ttl,
                )

    async def start(self):
        if not self.socket:
            try:
                self.socket = await asyncudp.create_socket(local_addr=(self.host, self.port))
            except OSError:
                logger.error(f"Failed to bind to {self.host}:{self.port} - Address and port already in use")
                return

        # Init analytics
        self.analytics = await DNSAnalytics.create_instance()

        # Start server
        await asyncio.gather(self.run_forever(), DNSDigUDPServer.output_stats())
