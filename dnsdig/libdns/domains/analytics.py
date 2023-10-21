from __future__ import annotations

import asyncio

from beanie import init_beanie
from dns.rdatatype import RdataType
from motor import motor_asyncio

from dnsdig.appdnsdigd.settings import dnsdigd_settings
from dnsdig.libdns.constants import RecordTypes
from dnsdig.libdns.models.analytics import Analytics


class DNSAnalytics:
    @classmethod
    async def create_instance(cls):
        instance = cls()
        await DNSAnalytics.init_beanie()
        return instance

    @classmethod
    async def init_beanie(cls):
        client_options = {'appname': dnsdigd_settings.app_name}
        mongo_client = motor_asyncio.AsyncIOMotorClient(dnsdigd_settings.mongo_url, **client_options)
        mongo_client.get_io_loop = asyncio.get_running_loop

        collections = [Analytics]
        await init_beanie(database=mongo_client[dnsdigd_settings.db_name], document_models=collections)

    async def log_resolver(self, name: str, record_type: RdataType, resolve_time: float, ttl: int) -> Analytics:
        rtype_map = {
            RdataType.A: RecordTypes.A,
            RdataType.AAAA: RecordTypes.AAAA,
            RdataType.MX: RecordTypes.MX,
            RdataType.NS: RecordTypes.NS,
            RdataType.CNAME: RecordTypes.CNAME,
            RdataType.TXT: RecordTypes.TXT,
            RdataType.SOA: RecordTypes.SOA,
            RdataType.PTR: RecordTypes.PTR,
            RdataType.SRV: RecordTypes.SRV,
        }
        row = Analytics(name=name, record_type=rtype_map.get(record_type), resolve_time=resolve_time, ttl=ttl)
        await row.save()
        return row
