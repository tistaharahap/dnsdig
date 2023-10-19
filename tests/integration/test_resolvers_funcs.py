from unittest import mock
from unittest.mock import AsyncMock

import pytest
from pydantic.networks import IPvAnyAddress, IPv4Address, IPv6Address

from dnsdig.libdns.constants import RecordTypes
from dnsdig.libdns.domains.resolver import Resolver, SoaResult, MxResult
from dnsdig.libdns.models.resolver import NSResult
from dnsdig.libgeoip.models import IPLocationResult
from dnsdig.libshared.utils import random_chars

patched_ip2location = AsyncMock()
patched_ip2location.return_value = IPLocationResult(ip="127.0.0.1", ttl=300)
patched6_ip2location = AsyncMock()
patched6_ip2location.return_value = IPLocationResult(ip="::1", ttl=300)


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
@pytest.mark.asyncio
async def test_resolver_a():
    records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.A)
    records = {k: v for k, v in records.items() if k != "metadata"}

    assert len(records) == 3

    for name, ips in records.items():
        assert name, "Nameserver name is not returned"
        assert len(ips) > 0
        assert IPvAnyAddress(ips[0].ip), "Not a valid IP Address"
        assert IPv4Address(ips[0].ip), "Not a valid IPv4 Address"


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched6_ip2location)
@pytest.mark.asyncio
async def test_resolver_aaaa():
    records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.AAAA)
    records = {k: v for k, v in records.items() if k != "metadata"}

    assert len(records) == 3

    for name, ips in records.items():
        assert name, "Nameserver name is not returned"
        assert len(ips) > 0
        assert IPvAnyAddress(ips[0].ip), "Not a valid IP Address"
        assert IPv6Address(ips[0].ip), "Not a valid IPv6 Address"


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
@pytest.mark.asyncio
async def test_resolver_mx():
    records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.MX)
    records = {k: v for k, v in records.items() if k != "metadata"}

    assert len(records) == 3

    for name, mailservers in records.items():
        assert name, "Nameserver name is not returned"
        assert len(mailservers) > 0
        result: MxResult = mailservers[0]
        assert result.priority, "Mailserver priority is not defined"
        assert isinstance(result.priority, int), "Mailserver priority must be an integer"
        assert result.hostname, "Mailserver hostname is not define"
        assert isinstance(result.hostname, str), "Hostname must be a string"


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
@pytest.mark.asyncio
async def test_resolver_ns():
    records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.NS)
    records = {k: v for k, v in records.items() if k != "metadata"}

    assert len(records) == 3

    for name, hostnames in records.items():
        assert name, "Nameserver name is not returned"
        assert len(hostnames) > 0
        result = hostnames[0]
        assert isinstance(result, NSResult)


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
@pytest.mark.asyncio
async def test_resolver_soa():
    records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.SOA)
    records = {k: v for k, v in records.items() if k != "metadata"}

    assert len(records) == 3

    for name, hostnames in records.items():
        assert name, "Nameserver name is not returned"
        assert len(hostnames) > 0
        result: SoaResult = hostnames[0]
        assert isinstance(result.primary_ns, str)
        assert isinstance(result.email, str)
        assert isinstance(result.serial, int)
        assert isinstance(result.refresh, int)
        assert isinstance(result.retry, int)
        assert isinstance(result.expire, int)
        assert isinstance(result.minimum, int)


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
@pytest.mark.asyncio
async def test_resolver_txt():
    records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.TXT)
    records = {k: v for k, v in records.items() if k != "metadata"}

    assert len(records) == 3

    for name, items in records.items():
        assert name, "Nameserver name is not returned"
        assert len(items) > 0


# @pytest.mark.asyncio
# async def test_resolver6_aaaa():
#     records = await Resolver.resolve_record6(hostname="google.com", record_type=RecordTypes.AAAA)
#     records = {k: v for k, v in records.items() if k != "metadata"}
#
#     assert len(records) == 3
#
#     for name, ips in records.items():
#         assert name, "Nameserver name is not returned"
#         assert len(ips) > 0
#         assert IPvAnyAddress(ips[0]), "Not a valid IP Address"
#         assert IPv6Address(ips[0]), "Not a valid IPv6 Address"
#
#
# @pytest.mark.asyncio
# async def test_resolver6_a():
#     records = await Resolver.resolve_record6(hostname="google.com", record_type=RecordTypes.A)
#     records = {k: v for k, v in records.items() if k != "metadata"}
#
#     assert len(records) == 3
#
#     for name, ips in records.items():
#         assert name, "Nameserver name is not returned"
#         assert len(ips) > 0
#         assert IPvAnyAddress(ips[0]), "Not a valid IP Address"
#         assert IPv4Address(ips[0]), "Not a valid IPv4 Address"
#
#
# @pytest.mark.asyncio
# async def test_resolver6_mx():
#     records = await Resolver.resolve_record6(hostname="google.com", record_type=RecordTypes.MX)
#     records = {k: v for k, v in records.items() if k != "metadata"}
#
#     assert len(records) == 3
#
#     for name, mailservers in records.items():
#         assert name, "Nameserver name is not returned"
#         assert len(mailservers) > 0
#         result: MxResult = mailservers[0]
#         assert result.priority, "Mailserver priority is not defined"
#         assert isinstance(result.priority, int), "Mailserver priority must be an integer"
#         assert result.hostname, "Mailserver hostname is not define"
#         assert isinstance(result.hostname, str), "Hostname must be a string"
#
#
# @pytest.mark.asyncio
# async def test_resolver6_ns():
#     records = await Resolver.resolve_record6(hostname="google.com", record_type=RecordTypes.NS)
#     records = {k: v for k, v in records.items() if k != "metadata"}
#
#     assert len(records) == 3
#
#     for name, hostnames in records.items():
#         assert name, "Nameserver name is not returned"
#         assert len(hostnames) > 0
#         result = hostnames[0]
#         assert isinstance(result, str)
#
#
# @pytest.mark.asyncio
# async def test_resolver6_soa():
#     records = await Resolver.resolve_record6(hostname="google.com", record_type=RecordTypes.SOA)
#     records = {k: v for k, v in records.items() if k != "metadata"}
#
#     assert len(records) == 3
#
#     for name, hostnames in records.items():
#         assert name, "Nameserver name is not returned"
#         assert len(hostnames) > 0
#         result: SoaResult = hostnames[0]
#         assert isinstance(result.primary_ns, str)
#         assert isinstance(result.email, str)
#         assert isinstance(result.serial, int)
#         assert isinstance(result.refresh, int)
#         assert isinstance(result.retry, int)
#         assert isinstance(result.expire, int)
#         assert isinstance(result.minimum, int)
#
#
# @pytest.mark.asyncio
# async def test_resolver6_txt():
#     records = await Resolver.resolve_record6(hostname="google.com", record_type=RecordTypes.TXT)
#     records = {k: v for k, v in records.items() if k != "metadata"}
#
#     assert len(records) == 3
#
#     for name, items in records.items():
#         assert name, "Nameserver name is not returned"
#         assert len(items) > 0
#
#
# @pytest.mark.asyncio
# async def test_resolver_nxdomain():
#     domain = f"{random_chars(23)}-{random_chars(7)}.com"
#     records = await Resolver.resolve_record(hostname=domain, record_type=RecordTypes.A)
#
#     metadata = records.get("metadata")
#
#     assert len(records) == 4
#     assert 'cloudflare: NXDOMAIN' in metadata
#     assert 'google: NXDOMAIN' in metadata
#     assert 'opendns: NXDOMAIN' in metadata
#
#
# @pytest.mark.asyncio
# async def test_resolver_noanswer():
#     records = await Resolver.resolve_record(hostname="google.com", record_type=RecordTypes.PTR)
#
#     metadata = records.get("metadata")
#
#     assert len(records) == 4
#     assert 'cloudflare: NoAnswer' in metadata
#     assert 'google: NoAnswer' in metadata
#     assert 'opendns: NoAnswer' in metadata
