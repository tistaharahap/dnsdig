import ipaddress

from dnsdig.libgeoip.models import IPLocationResult, IP2Location
from dnsdig.libshared.monq import monq_find_one


class IP2Geo:
    @classmethod
    def ip_to_integer(cls, ip: str) -> int | None:
        try:
            return int(ipaddress.ip_address(ip))
        except ValueError:
            return None

    @classmethod
    def integer_to_ip(cls, integer: int) -> str | None:
        try:
            return str(ipaddress.ip_address(integer))
        except ValueError:
            return None

    @classmethod
    async def ip_to_location(cls, ip: str) -> IPLocationResult | None:
        query = {"ip_range_start": {"$lte": cls.ip_to_integer(ip)}, "ip_range_end": {"$gte": cls.ip_to_integer(ip)}}
        location = await monq_find_one(model=IP2Location, query=query, project_to=IP2Location)
        return IPLocationResult(ip=ip, **location.dict()) if location else IPLocationResult(ip=ip)
