from faker import Faker
from fastapi.testclient import TestClient

fake = Faker()


def test_create_application(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        payload = {
            "name": f"{fake.first_name()} {fake.last_name()}",
            "description": fake.sentence(),
            "website": "https://bango29.com",
        }
        print(payload)
        response = client.post("/v1/me/applications", headers=headers, json=payload)
        resp_body = response.json()

        assert response.status_code == 200
        assert resp_body.get("name") == payload.get("name")
        assert resp_body.get("description") == payload.get("description")
        assert resp_body.get("website") == payload.get("website")
        assert resp_body.get("clientId")
        assert resp_body.get("clientSecret")
        assert resp_body.get("createdAt")
        assert not resp_body.get("permissions")


def test_list_applications(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        payload = {
            "name": f"{fake.first_name()} {fake.last_name()}",
            "description": fake.sentence(),
            "website": "https://bango29.com",
        }
        response = client.post("/v1/me/applications", headers=headers, json=payload)
        resp_body = response.json()

        assert response.status_code == 200
        assert resp_body.get("name") == payload.get("name")
        assert resp_body.get("description") == payload.get("description")
        assert resp_body.get("website") == payload.get("website")
        assert resp_body.get("clientId")
        assert resp_body.get("clientSecret")
        assert resp_body.get("createdAt")
        assert not resp_body.get("permissions")

        response = client.get("/v1/me/applications", headers=headers)
        apps = response.json()
        client_ids = [app.get("clientId") for app in apps]

        assert response.status_code == 200
        assert resp_body.get("clientId") in client_ids


def test_generate_access_token(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        payload = {
            "name": f"{fake.first_name()} {fake.last_name()}",
            "description": fake.sentence(),
            "website": "https://bango29.com",
        }
        response = client.post("/v1/me/applications", headers=headers, json=payload)
        resp_body = response.json()
        client_id = resp_body.get("clientId")
        client_secret = resp_body.get("clientSecret")

        assert response.status_code == 200
        assert resp_body.get("name") == payload.get("name")
        assert resp_body.get("description") == payload.get("description")
        assert resp_body.get("website") == payload.get("website")
        assert client_id
        assert client_secret
        assert resp_body.get("createdAt")
        assert not resp_body.get("permissions")

        response = client.get("/v1/me/applications", headers=headers)
        apps = response.json()
        client_ids = [app.get("clientId") for app in apps]

        assert response.status_code == 200
        assert client_id in client_ids

        payload = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        response = client.post("/v1/oauth2/token", json=payload)
        resp_body = response.json()

        assert response.status_code == 200
        assert resp_body.get("accessToken")
        assert resp_body.get("refreshToken")
        assert resp_body.get("expiresIn")
        assert resp_body.get("tokenType") == "bearer"

        headers = {"authorization": f"Bearer {resp_body.get('accessToken')}"}
        response = client.get("/v1/resolve/google.com", headers=headers)

        assert response.status_code == 200


def test_exchange_refresh_token(client: TestClient):
    with client:
        headers = {"authorization": "Bearer 123"}
        payload = {
            "name": f"{fake.first_name()} {fake.last_name()}",
            "description": fake.sentence(),
            "website": "https://bango29.com",
        }
        response = client.post("/v1/me/applications", headers=headers, json=payload)
        resp_body = response.json()
        client_id = resp_body.get("clientId")
        client_secret = resp_body.get("clientSecret")

        assert response.status_code == 200
        assert resp_body.get("name") == payload.get("name")
        assert resp_body.get("description") == payload.get("description")
        assert resp_body.get("website") == payload.get("website")
        assert client_id
        assert client_secret
        assert resp_body.get("createdAt")
        assert not resp_body.get("permissions")

        response = client.get("/v1/me/applications", headers=headers)
        apps = response.json()
        client_ids = [app.get("clientId") for app in apps]

        assert response.status_code == 200
        assert client_id in client_ids

        payload = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        response = client.post("/v1/oauth2/token", json=payload)
        resp_body = response.json()
        refresh_token = resp_body.get("refreshToken")
        access_token = resp_body.get("accessToken")

        assert response.status_code == 200
        assert access_token
        assert refresh_token
        assert resp_body.get("expiresIn")
        assert resp_body.get("tokenType") == "bearer"

        headers = {"authorization": f"Bearer {resp_body.get('accessToken')}"}
        response = client.get("/v1/resolve/google.com", headers=headers)

        assert response.status_code == 200

        payload = {"refresh_token": refresh_token, "grant_type": "refresh_token"}
        response = client.post("/v1/oauth2/token", json=payload)
        resp_body = response.json()
        new_access_token = resp_body.get("accessToken")
        new_refresh_token = resp_body.get("refreshToken")

        assert response.status_code == 200
        assert new_access_token
        assert new_refresh_token
        assert new_access_token != access_token
        assert new_refresh_token != refresh_token
        assert resp_body.get("expiresIn")
        assert resp_body.get("tokenType") == "bearer"
