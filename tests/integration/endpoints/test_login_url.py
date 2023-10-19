from os import environ
from secrets import token_hex
from urllib.parse import urlparse, parse_qs

from fastapi.testclient import TestClient

AUTH_PROVIDER_HOST = environ.get("AUTH_PROVIDER_HOST")
AUTH_PROVIDER_CLIENT_ID = environ.get("AUTH_PROVIDER_CLIENT_ID")
AUTH_PROVIDER_REDIRECT_URI = environ.get("AUTH_PROVIDER_REDIRECT_URI")


def test_login_url_without_payload(client: TestClient):
    payload = {}
    response = client.post("/v1/me/login-url", json=payload)
    resp_body = response.json()
    login_url = urlparse(resp_body.get('loginUrl'))
    query_strings = parse_qs(login_url.query)

    assert f"{login_url.scheme}://{login_url.hostname}" == AUTH_PROVIDER_HOST
    assert query_strings.get("client_id")[0] == AUTH_PROVIDER_CLIENT_ID
    assert query_strings.get("redirect_uri")[0] == AUTH_PROVIDER_REDIRECT_URI
    assert query_strings.get("state")[0] is not None
    assert response.status_code == 200
    assert response.headers.get('content-type') == 'application/json'


def test_login_url_with_payload(client: TestClient):
    payload = {'state': token_hex(23)}
    response = client.post("/v1/me/login-url", json=payload)
    resp_body = response.json()
    login_url = urlparse(resp_body.get('loginUrl'))
    query_strings = parse_qs(login_url.query)

    assert f"{login_url.scheme}://{login_url.hostname}" == AUTH_PROVIDER_HOST
    assert query_strings.get("client_id")[0] == AUTH_PROVIDER_CLIENT_ID
    assert query_strings.get("redirect_uri")[0] == AUTH_PROVIDER_REDIRECT_URI
    assert query_strings.get("state")[0] == payload.get("state")
    assert response.status_code == 200
    assert response.headers.get('content-type') == 'application/json'
