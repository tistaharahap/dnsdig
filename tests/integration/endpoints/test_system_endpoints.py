from fastapi.testclient import TestClient


def test_healthcheck(client: TestClient):
    with client:
        response = client.get("/healthcheck")
        resp_body = response.json()

        assert response.status_code == 200
        assert resp_body == "OK"


def test_openapi(client: TestClient):
    with client:
        response = client.get("/openapi.json")

        assert response.status_code == 200


def test_api_docs(client: TestClient):
    with client:
        response = client.get("/docs")

        assert response.status_code == 200
