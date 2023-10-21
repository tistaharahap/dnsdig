import asyncio
import time
from typing import Dict

import aiohttp
import asyncudp
import dns.message
import redis.asyncio as redis
import ujson
from dns.rdatatype import RdataType
from rich.console import Console
from rich.table import Table

from dnsdig.appdnsdigd.settings import dnsdigd_settings
from dnsdig.libdns.domains.analytics import DNSAnalytics
from dnsdig.libdns.models.analytics import Analytics, StatsTimeframes, AnalyticsResults
from dnsdig.libdns.utils import to_doh_simple, from_doh_simple
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

    @classmethod
    async def query_doh(
        cls,
        doh_question: Dict[str, str | RdataType],
        session: aiohttp.ClientSession,
        redis_client: redis.Redis,
        use_cache: bool = True,
    ):
        # Get the cached response if it exists
        name = doh_question.get("name")
        type_: RdataType = doh_question.get("type")
        cache_key = f"dnsdigd-cache#{name}#{type_.value}"
        if use_cache:
            cached_response = await redis_client.get(cache_key)
            if cached_response:
                return ujson.loads(cached_response)

        async with session.get("https://dns.google/resolve", params=doh_question, allow_redirects=True) as resp:
            response = await resp.json()
            if use_cache:
                answers = response.get("Answer", [])
                if len(answers) > 0:
                    answer = answers[0]
                    ttl = answer.get("TTL", 0)
                    await redis_client.set(cache_key, ujson.encode(response), ex=ttl)
            return response

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

    async def run_forever(self, session: aiohttp.ClientSession):
        while True:
            data, addr = await self.socket.recvfrom()

            start_time = time.time()

            data = dns.message.from_wire(data)

            response = to_doh_simple(message=data)
            questions = response.get("Question", [])
            if len(questions) == 0:
                continue
            question = questions[0]
            doh_question = {"name": question.get("name"), "type": question.get("type")}
            logger.info(f"[{data.id}] Received query from {addr} - {question.get('name')} {question.get('type')}")

            try:
                doh_response = await DNSDigUDPServer.query_doh(
                    doh_question=doh_question, session=session, redis_client=self.redis_client, use_cache=True
                )
            except Exception as exc:
                logger.error(f"[{data.id}] Failed to query DoH - {exc}")
                continue

            dns_response = from_doh_simple(simple=doh_response, add_qr=True)
            dns_response.id = data.id

            end_time = time.time()
            delta = (end_time - start_time) * 1000
            logger.info(f"[{data.id}] Query took {int(delta)} ms")

            logger.info(f"[{data.id}] Sending response to {addr} - {question.get('name')} {question.get('type')}")
            self.socket.sendto(dns_response.to_wire(), addr)

            # Log if we get an answer
            if len(dns_response.answer) > 0:
                await self.analytics.log_resolver(
                    name=doh_question.get("name"),
                    record_type=doh_question.get("type"),
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

        # Use dns cache for aiohttp since we are using a single session
        conn = aiohttp.TCPConnector(ttl_dns_cache=86400)
        async with aiohttp.ClientSession(connector=conn) as session:
            await asyncio.gather(self.run_forever(session=session), DNSDigUDPServer.output_stats())
