from enum import Enum
from typing import List, Tuple

import pymongo
from pydantic import BaseModel
from pymongo import IndexModel

from dnsdig.libshared.models import BaseMongoDocument, BaseRequestResponse


class GeoType(str, Enum):
    Point = "Point"


class GeoObject(BaseModel):
    type: GeoType = GeoType.Point
    coordinates: Tuple[float, float]


class IP2Location(BaseMongoDocument):
    ip_range_start: int
    ip_range_end: int
    country_iso_code: str
    province: str
    city: str
    geo: GeoObject

    class Settings:
        name: str = "ip-to-locations"
        indexes: List[IndexModel] = [
            IndexModel(
                [("ip_range_start", pymongo.ASCENDING), ("ip_range_end", pymongo.ASCENDING)], name="ip_range_index"
            ),
            IndexModel([("country_iso_code", pymongo.ASCENDING)], name="country_index"),
            IndexModel([("geo", pymongo.GEOSPHERE)], name="location_index"),
        ]


class IPLocationResult(BaseRequestResponse):
    ip: str
    country_iso_code: str | None = None
    province: str | None = None
    city: str | None = None
    geo: GeoObject | None = None


class IPInfoResponse(BaseRequestResponse):
    ip: str
    hostname: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    loc: str | None = None
    org: str | None = None
    postal: str | None = None
    timezone: str | None = None
