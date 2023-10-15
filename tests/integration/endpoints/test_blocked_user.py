from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from dnsdig.libaccount.models.mongo import User


@pytest.mark.asyncio
async def test_blocked_user(client: TestClient, user: User):
    user.blocked_at = datetime.utcnow()
    await user.save()

    headers = {"authorization": "Bearer 123"}
    response = client.get("/v1/resolve/google.com/A", headers=headers)

    assert response.status_code == 403
