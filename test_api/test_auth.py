import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app import schema as s
from config import config

from .test_data import TestData
from api.utility import create_locations, create_professions

CFG = config("testing")


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_auth(db, client: TestClient, test_data: TestData):
    create_locations(db)
    create_professions(db)
    user_auth = s.Auth(identificator=test_data.test_users[0].email, password=test_data.test_users[0].password)
    response = client.post("/api/auth/token", json=user_auth.model_dump())
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    assert token.access_token and token.token_type == "bearer"
    header = dict(Authorization=f"Bearer {token.access_token}")
    res = client.get("api/users/me", headers=header)
    assert res.status_code == status.HTTP_200_OK

    user_auth: s.GoogleAuth = s.GoogleAuth(
        email=test_data.test_users[0].email,
        first_name=test_data.test_users[0].first_name,
        last_name=test_data.test_users[0].last_name,
        locations=[1],
        uid="google_id",
    )
    response = client.post("/api/auth/google", json=user_auth.model_dump())
    assert response.status_code == status.HTTP_200_OK
    token: s.Token = s.Token.model_validate(response.json())
    assert token.access_token and token.token_type == "bearer"
    res = client.get("api/users/me", headers=header)
    assert res.status_code == status.HTTP_200_OK
