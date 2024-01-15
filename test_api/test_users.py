import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app import schema as s
from config import config

from .test_data import TestData

CFG = config("testing")


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_me(client: TestClient, headers: dict[str, str], test_data: TestData):
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    user = s.User.model_validate(response.json())
    assert user.first_name == test_data.test_users[0].first_name
