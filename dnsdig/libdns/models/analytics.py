from dnsdig.libdns.constants import RecordTypes
from dnsdig.libshared.models import BaseMongoDocument


class Analytics(BaseMongoDocument):
    name: str
    record_type: RecordTypes
    resolve_time: float
    ttl: int

    class Settings:
        name: str = "analytics"
