from typing import List, Dict

import dns.asyncresolver

from dnsdig.libdns.constants import RecordTypes
from dnsdig.libdns.models.resolver import ResolverSet, MxResult, SoaResult, NSResult, TXTResult
from dnsdig.libgeoip.domains.ip2geolocation import IP2Geo
from dnsdig.libgeoip.models import IPLocationResult
from dnsdig.libshared.logging import logger

ResolverResult = Dict[str, List[str | IPLocationResult | MxResult | SoaResult | NSResult | TXTResult]]


class Resolver:
    resolvers: ResolverSet = ResolverSet()

    @classmethod
    def _parse_mx_result(cls, result: str, ttl: int) -> MxResult:
        priority, hostname = result.split(" ")
        return MxResult(priority=int(priority), hostname=hostname[0:-1], ttl=ttl)

    @classmethod
    def _parse_soa_result(cls, result: str, ttl: int) -> SoaResult:
        primary_ns, email, serial, refresh, retry, expire, minimum = result.split(" ")
        email = email.replace(".", "@", 1)
        return SoaResult(
            primaryNs=primary_ns,
            email=email,
            serial=int(serial),
            refresh=int(refresh),
            retry=int(retry),
            expire=int(expire),
            minimum=int(minimum),
            ttl=ttl,
        )

    @classmethod
    def _parse_txt_result(cls, result: str, ttl: int) -> TXTResult:
        txt = result.replace('"', "")
        return TXTResult(txt=txt, ttl=ttl)

    @classmethod
    def _parse_ns_result(cls, result: str, ttl: int) -> NSResult:
        return NSResult(hostname=result, ttl=ttl)

    @classmethod
    async def _parse_a_result(cls, result: str, ttl: int) -> IPLocationResult:
        return await IP2Geo.ip_to_location(ip=result, ttl=ttl)

    @classmethod
    async def resolve_record(cls, hostname: str, record_type: RecordTypes, use_ipv6: bool = False) -> ResolverResult:
        logger.info(f"Resolving {hostname} {record_type}")
        results = {'metadata': []}
        for name, resolver in cls.resolvers.all:
            try:
                answer = await dns.asyncresolver.resolve_at(
                    where=resolver.random if not use_ipv6 else resolver.random6, qname=hostname, rdtype=record_type
                )
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as exc:
                results.update({name: []})
                metadata = results.get("metadata", [])
                if isinstance(exc, dns.resolver.NXDOMAIN):
                    metadata.append(f"{name}: NXDOMAIN")
                elif isinstance(exc, dns.resolver.NoAnswer):
                    metadata.append(f"{name}: NoAnswer")
                results.update({"metadata": metadata})
                continue

            records = []
            ttl = answer.chaining_result.minimum_ttl
            for record in answer:
                _rec = str(record)

                match record_type:
                    case RecordTypes.MX:
                        _rec = cls._parse_mx_result(_rec, ttl=ttl)
                    case RecordTypes.TXT:
                        _rec = cls._parse_txt_result(_rec, ttl=ttl)
                    case RecordTypes.NS:
                        _rec = cls._parse_ns_result(_rec[0:-1], ttl=ttl)
                    case RecordTypes.SOA:
                        _rec = cls._parse_soa_result(_rec, ttl=ttl)
                    case RecordTypes.A:
                        _rec = await cls._parse_a_result(_rec, ttl=ttl)
                    case RecordTypes.AAAA:
                        _rec = await cls._parse_a_result(_rec, ttl=ttl)

                records.append(_rec)
            results.update({name: records})

        return results

    @classmethod
    async def resolve_record6(cls, hostname: str, record_type: RecordTypes) -> ResolverResult:
        return await cls.resolve_record(hostname=hostname, record_type=record_type, use_ipv6=True)
