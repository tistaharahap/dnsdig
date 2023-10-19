import aiohttp
from cache import AsyncLRU

from dnsdig.libgeoip.models import IPLocationResult, IPInfoResponse, GeoObject, GeoType
from dnsdig.libshared.settings import settings


class IP2Geo:
    @classmethod
    @AsyncLRU(maxsize=8192)
    async def ip_to_location(cls, ip: str, ttl: int) -> IPLocationResult:
        async with aiohttp.ClientSession() as session:
            url = f"{settings.ipinfo_host}/{ip}/json"
            headers = {"Accept": "application/json", "Authorization": f"Bearer {settings.ipinfo_token}"}
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return IPLocationResult(ip=ip, ttl=ttl)
                location = IPInfoResponse.model_validate_json(await response.text())
                if not location:
                    return IPLocationResult(ip=ip, ttl=ttl)
                coords = location.loc.split(",")
                geo = GeoObject(type=GeoType.Point, coordinates=(float(coords[0]), float(coords[1])))
                return IPLocationResult(
                    ip=ip,
                    country_iso_code=location.country,
                    province=location.region,
                    city=location.city,
                    geo=geo,
                    ttl=ttl,
                )
