import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from unittest import mock
from api import app
from api.dependency.user import get_current_user


from app.schema import GoogleTokenVerification, AppleTokenVerification

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
    name="Google User",
    picture="str",
    given_name="Google",
    family_name="User",
    locale="str",
    iat=1,
    exp=1,
)

ANOTHER_DUMMY_GOOGLE_VALIDATION = GoogleTokenVerification(
    iss="https://accounts.google.com",
    email="another_account@example.com",
    azp="str2",
    aud="str2",
    sub="str2",
    email_verified=True,
    name="Another Account",
    picture="str2",
    given_name="Another",
    family_name="Account",
    locale="str2",
    iat=1,
    exp=1,
)

DUMMY_IOS_VALIDATION = AppleTokenVerification(
    iss="https://appleid.apple.com",
    aud="str",
    exp=1,
    iat=1,
    sub="str",
    c_hash="str",
    email="apple.test@example.com",
    email_verified=True,
    auth_time=1,
    nonce_supported=True,
    fullName=s.AppleAuthenticationFullName(givenName="Apple", familyName="Test"),
)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_auth(db: Session, client: TestClient):
    USER_NAME = db.scalar(sa.select(m.User.fullname).order_by(m.User.id))
    assert USER_NAME
    user_auth = s.Auth(fullname=USER_NAME, password=USER_PASSWORD)
    response = client.post("/api/auth/token", json=user_auth.model_dump())
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    assert token.access_token and token.token_type == "bearer"
    header = dict(Authorization=f"Bearer {token.access_token}")
    res = client.get("api/users/me", headers=header)
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_register_google_account(monkeypatch, client: TestClient, auth_header: dict[str, str], db: Session):
    mock_verify_oauth2_token = mock.Mock(return_value=DUMMY_GOOGLE_VALIDATION)
    monkeypatch.setattr("api.routes.user.id_token.verify_oauth2_token", mock_verify_oauth2_token)

    data = s.GoogleAuthIn(id_token="test_token")

    # Start registration
    response = client.post("/api/auth/register-google-account", json=data.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    user = db.scalar(
        sa.select(m.User).where(m.User.auth_accounts.any(m.AuthAccount.email == DUMMY_GOOGLE_VALIDATION.email))
    )
    assert user

    token = s.Token.model_validate(response.json())
    assert len(token.access_token) > 0

    mock_verify_oauth2_token.assert_called_once_with(
        "test_token",
        mock.ANY,
        CFG.GOOGLE_CLIENT_ID,
    )

    # Test register same google account
    mock_verify_oauth2_token = mock.Mock(return_value=DUMMY_GOOGLE_VALIDATION)
    monkeypatch.setattr("api.routes.user.id_token.verify_oauth2_token", mock_verify_oauth2_token)

    # (new registered user)
    mock_current_user = db.scalar(sa.select(m.User).where(m.User.id == user.id))
    assert mock_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.post("/api/auth/register-google-account", headers=auth_header, json=data.model_dump())
    assert response.status_code == status.HTTP_409_CONFLICT

    mock_verify_oauth2_token.assert_called_once_with(
        "test_token",
        mock.ANY,
        CFG.GOOGLE_CLIENT_ID,
    )

    # Test login
    response = client.post("/api/auth/google", json=data.model_dump())
    assert response.status_code == status.HTTP_200_OK

    token = s.Token.model_validate(response.json())
    assert len(token.access_token) > 0

    # Check that the user was created in the database
    response = client.post("/api/users/me")
    assert response

    # User can't delete his last auth account
    response = client.delete(f"/api/users/auth-account/{user.id}", headers=auth_header)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Add additional auth account
    mock_verify_oauth2_token = mock.Mock(return_value=ANOTHER_DUMMY_GOOGLE_VALIDATION)
    monkeypatch.setattr("api.routes.user.id_token.verify_oauth2_token", mock_verify_oauth2_token)
    data = s.GoogleAuthIn(id_token="test_token")

    response = client.post("/api/users/add-google-account", headers=auth_header, json=data.model_dump())
    assert response.status_code == status.HTTP_201_CREATED

    # Delete auth account when there are multiple auth accounts
    response = client.delete(f"/api/users/auth-account/{user.id}", headers=auth_header)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # reset user dependency
    app.dependency_overrides[get_current_user] = get_current_user
