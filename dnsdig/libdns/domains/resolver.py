from typing import List, Dict

import dns.asyncresolver

from dnsdig.libdns.constants import RecordTypes
from dnsdig.libdns.models.resolver import ResolverSet, MxResult, SoaResult
from dnsdig.libgeoip.domains.ip2geolocation import IP2Geo
from dnsdig.libgeoip.models import IPLocationResult

ResolverResult = Dict[str, List[str | IPLocationResult | MxResult | SoaResult]]


class Resolver:
    resolvers: ResolverSet = ResolverSet()

    @classmethod
    def _parse_mx_result(cls, result: str) -> MxResult:
        priority, hostname = result.split(" ")
        return MxResult(priority=int(priority), hostname=hostname[0:-1])

    @classmethod
    def _parse_soa_result(cls, result: str) -> SoaResult:
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
        )

    @classmethod
    def _parse_txt_result(cls, result: str) -> str:
        return result.replace('"', "")

    @classmethod
    async def _parse_a_result(cls, result: str) -> IPLocationResult:
        return await IP2Geo.ip_to_location(ip=result)

    @classmethod
    async def resolve_record(cls, hostname: str, record_type: RecordTypes, use_ipv6: bool = False) -> ResolverResult:
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
            for record in answer:
                _rec = str(record)

                match record_type:
                    case RecordTypes.MX:
                        _rec = cls._parse_mx_result(_rec)
                    case RecordTypes.NS:
                        _rec = _rec[0:-1]
                    case RecordTypes.SOA:
                        _rec = cls._parse_soa_result(_rec)
                    case RecordTypes.TXT:
                        _rec = cls._parse_txt_result(_rec)
                    case RecordTypes.A:
                        _rec = await cls._parse_a_result(_rec)

                records.append(_rec)
            results.update({name: records})

        return results

    @classmethod
    async def resolve_record6(cls, hostname: str, record_type: RecordTypes) -> ResolverResult:
        return await cls.resolve_record(hostname=hostname, record_type=record_type, use_ipv6=True)
