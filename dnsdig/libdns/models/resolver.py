import random
from typing import List, Tuple

from pydantic import BaseModel

from dnsdig.libdns.constants import (
    GOOGLE_NAMESERVERS6,
    GOOGLE_NAMESERVERS,
    CLOUDFLARE_NAMESERVERS6,
    CLOUDFLARE_NAMESERVERS,
    OPENDNS_NAMESERVERS,
    OPENDNS_NAMESERVERS6,
)
from dnsdig.libshared.models import BaseRequestResponse


class DNSResolver(BaseModel):
    nameservers: List[str]
    nameservers6: List[str] | None = None

    @property
    def random(self) -> str:
        return random.choices(self.nameservers, k=1)[0]

    @property
    def random6(self) -> str:
        return random.choices(self.nameservers6, k=1)[0]


class ResolverSet(BaseModel):
    cloudflare: DNSResolver = DNSResolver(nameservers=CLOUDFLARE_NAMESERVERS, nameservers6=CLOUDFLARE_NAMESERVERS6)
    google: DNSResolver = DNSResolver(nameservers=GOOGLE_NAMESERVERS, nameservers6=GOOGLE_NAMESERVERS6)
    opendns: DNSResolver = DNSResolver(nameservers=OPENDNS_NAMESERVERS, nameservers6=OPENDNS_NAMESERVERS6)

    @property
    def all(self) -> List[Tuple[str, DNSResolver]]:
        return [("cloudflare", self.cloudflare), ("google", self.google), ("opendns", self.opendns)]


class MxResult(BaseRequestResponse):
    priority: int
    hostname: str


class SoaResult(BaseRequestResponse):
    primary_ns: str
    email: str
    serial: int
    refresh: int
    retry: int
    expire: int
    minimum: int
