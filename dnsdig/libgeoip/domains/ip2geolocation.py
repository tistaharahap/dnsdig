import ipaddress

import aiohttp
from cache import AsyncLRU

from dnsdig.libgeoip.models import IPLocationResult, IPInfoResponse, GeoObject, GeoType
from dnsdig.libshared.settings import settings


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
    @AsyncLRU(maxsize=8192)
    async def ip_to_location(cls, ip: str) -> IPLocationResult:
        async with aiohttp.ClientSession() as session:
            url = f"{settings.ipinfo_host}/{ip}/json"
            headers = {"Accept": "application/json", "Authorization": f"Bearer {settings.ipinfo_token}"}
            async with session.get(url, headers=headers) as response:
                location = IPInfoResponse.model_validate_json(await response.text())
                if not location:
                    return IPLocationResult(ip=ip)
                coords = location.loc.split(",")
                geo = GeoObject(type=GeoType.Point, coordinates=(float(coords[0]), float(coords[1])))
                return IPLocationResult(
                    ip=ip, country_iso_code=location.country, province=location.region, city=location.city, geo=geo
                )
