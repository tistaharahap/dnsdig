from dns.rdatatype import RdataType

from dnsdig.libshared.models import BaseMongoDocument


class Analytics(BaseMongoDocument):
    name: str
    record_type: RdataType
    resolve_time: float
    ttl: int

    class Settings:
        name: str = "analytics"
