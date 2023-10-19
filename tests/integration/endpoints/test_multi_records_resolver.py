from unittest import mock
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from dnsdig.libdns.constants import RecordTypes
from dnsdig.libgeoip.models import IPLocationResult

patched_ip2location = AsyncMock()
patched_ip2location.return_value = IPLocationResult(ip="127.0.0.1", ttl=300)


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
def test_multi_records_resolver(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        response = client.get("/v1/resolve/google.com", headers=headers)
        resp_body = response.json()

        for record_type, result in resp_body.items():
            metadata = result.get("metadata")
            google = result.get("google")
            cloudflare = result.get("cloudflare")
            opendns = result.get("opendns")

            assert response.status_code == 200
            assert record_type in RecordTypes.__members__.keys()
            assert len(metadata) == 0
            assert len(google) > 0
            assert len(cloudflare) > 0
            assert len(opendns) > 0


@mock.patch("dnsdig.libgeoip.domains.ip2geolocation.IP2Geo.ip_to_location", patched_ip2location)
def test_multi_records_freesolver(client: TestClient):
    with client:
        response = client.get("/v1/freesolve/google.com")
        resp_body = response.json()

        for record_type, result in resp_body.items():
            metadata = result.get("metadata")
            google = result.get("google")
            cloudflare = result.get("cloudflare")
            opendns = result.get("opendns")

            assert response.status_code == 200
            assert record_type in RecordTypes.__members__.keys()
            assert len(metadata) == 0
            assert len(google) > 0
            assert len(cloudflare) > 0
            assert len(opendns) > 0
