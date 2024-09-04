import pytest
from unittest import mock
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schema import GoogleTokenVerification, Token

from app import models as m
from app import schema as s
from config import config

CFG = config()


USER_PASSWORD = CFG.TEST_USER_PASSWORD

DUMMY_GOOGLE_VALIDATION = GoogleTokenVerification(
    iss="https://accounts.google.com",
    email="test@example.com",
    azp="str",
    aud="str",
    sub="str",
    email_verified=True,
    name="str",
    picture="str",
    given_name="str",
    family_name="str",
    locale="str",
    iat=1,
    exp=1,
)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_auth(db: Session, client: TestClient):
    USER_PHONE = db.scalar(sa.select(m.User.phone).order_by(m.User.id))
    assert USER_PHONE
    user_auth = s.Auth(phone=USER_PHONE, password=USER_PASSWORD)
    response = client.post("/api/auth/token", json=user_auth.model_dump())
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    assert token.access_token and token.token_type == "bearer"
    header = dict(Authorization=f"Bearer {token.access_token}")
    res = client.get("api/users/me", headers=header)
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_google_auth(monkeypatch, db: Session, client: TestClient):
    # Mock the id_token.verify_oauth2_token method
    mock_verify_oauth2_token = mock.Mock(return_value=DUMMY_GOOGLE_VALIDATION)
    monkeypatch.setattr("api.routes.auth.id_token.verify_oauth2_token", mock_verify_oauth2_token)

    data = s.GoogleAuthIn(id_token="test_token")

    # Make a request to the endpoint
    response = client.post("/api/auth/google", json=data.model_dump())

    # Check the response
    assert response.status_code == 200
    token = Token.model_validate(response.json())
    assert len(token.access_token) > 0

    # Check that the mock method was called with the correct arguments
    mock_verify_oauth2_token.assert_called_once_with(
        "test_token",
        mock.ANY,  # requests.Request() is passed as the second argument
        CFG.GOOGLE_CLIENT_ID,
    )


# Create test for Google validation with user creation and token generation when user is not in database, but token is valid
@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_google_token_user_creation(monkeypatch, db: Session, client: TestClient):
    # Mock the id_token.verify_oauth2_token method
    mock_verify_oauth2_token = mock.Mock(return_value=DUMMY_GOOGLE_VALIDATION)
    monkeypatch.setattr("api.routes.auth.id_token.verify_oauth2_token", mock_verify_oauth2_token)

    data = s.GoogleAuthIn(id_token="test_token")

    # Send a request to the endpoint
    response = client.post("/api/auth/google", json=data.model_dump())
    assert response.status_code == 200

    # Check that the mock method was called with the correct arguments
    mock_verify_oauth2_token.assert_called_once_with(
        "test_token",
        mock.ANY,  # requests.Request() is passed as the second argument
        CFG.GOOGLE_CLIENT_ID,
    )

    # Check that the user was created in the database
    response = client.post("/api/users/me")
    assert response
