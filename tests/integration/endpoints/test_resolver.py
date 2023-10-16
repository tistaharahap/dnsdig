from fastapi.testclient import TestClient


def test_resolver_a(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        response = client.get("/v1/resolve/google.com/A", headers=headers)
        resp_body = response.json()

        metadata = resp_body.get("metadata")
        google = resp_body.get("google")
        cloudflare = resp_body.get("cloudflare")
        opendns = resp_body.get("opendns")

        assert response.status_code == 200
        assert google[0].get("ip")
        assert cloudflare[0].get("ip")
        assert opendns[0].get("ip")
        assert len(metadata) == 0
        assert len(google) > 0
        assert len(cloudflare) > 0
        assert len(opendns) > 0


def test_resolver_aaaa(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        response = client.get("/v1/resolve/google.com/AAAA", headers=headers)
        resp_body = response.json()

        metadata = resp_body.get("metadata")
        google = resp_body.get("google")
        cloudflare = resp_body.get("cloudflare")
        opendns = resp_body.get("opendns")

        assert response.status_code == 200
        assert len(metadata) == 0
        assert len(google) > 0
        assert len(cloudflare) > 0
        assert len(opendns) > 0


def test_resolver_mx(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        response = client.get("/v1/resolve/google.com/MX", headers=headers)
        resp_body = response.json()

        metadata = resp_body.get("metadata")
        google = resp_body.get("google")
        cloudflare = resp_body.get("cloudflare")
        opendns = resp_body.get("opendns")

        assert response.status_code == 200
        assert len(metadata) == 0
        assert len(google) > 0
        assert len(cloudflare) > 0
        assert len(opendns) > 0


def test_resolver_soa(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        response = client.get("/v1/resolve/google.com/SOA", headers=headers)
        resp_body = response.json()

        metadata = resp_body.get("metadata")
        google = resp_body.get("google")
        cloudflare = resp_body.get("cloudflare")
        opendns = resp_body.get("opendns")

        assert response.status_code == 200
        assert len(metadata) == 0
        assert len(google) > 0
        assert len(cloudflare) > 0
        assert len(opendns) > 0


def test_resolver_txt(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        response = client.get("/v1/resolve/google.com/TXT", headers=headers)
        resp_body = response.json()

        metadata = resp_body.get("metadata")
        google = resp_body.get("google")
        cloudflare = resp_body.get("cloudflare")
        opendns = resp_body.get("opendns")

        assert response.status_code == 200
        assert len(metadata) == 0
        assert len(google) > 0
        assert len(cloudflare) > 0
        assert len(opendns) > 0
