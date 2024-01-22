import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import schema as s
from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_register(db: Session, client: TestClient, test_data: TestData):
    USER = test_data.test_users[0]
    USER.phone = "1234567890"
    USER.email = "test_user@kraftjar.net"
    user_data = s.RegistrationIn(
        fullname=USER.first_name + " " + USER.last_name,
        phone=USER.phone,
        email=USER.email,
        password=USER.password,
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    assert token.access_token and token.token_type == "bearer"
    header = dict(Authorization=f"Bearer {token.access_token}")
    res = client.get("api/users/me", headers=header)
    assert res.status_code == status.HTTP_200_OK

    # Try to register again with the same email
    USER = test_data.test_users[0]
    USER.phone = "999999999"
    user_data = s.RegistrationIn(
        fullname=USER.first_name + " " + USER.last_name,
        phone=USER.phone,
        email=USER.email,
        password=USER.password,
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_409_CONFLICT

    # Try to register again with the same phone
    USER = test_data.test_users[1]
    USER.email = "new_email@new.york.post.org"
    user_data = s.RegistrationIn(
        fullname=USER.first_name + " " + USER.last_name,
        phone=USER.phone,
        email=USER.email,
        password=USER.password,
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
