import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
    name="str",
    picture="str",
    given_name="str",
    family_name="str",
    locale="str",
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
