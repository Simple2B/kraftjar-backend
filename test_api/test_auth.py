import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
from config import config

CFG = config()


USER_PASSWORD = CFG.TEST_USER_PASSWORD


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_auth(db: Session, client: TestClient):
    USER_PHONE = db.scalar(sa.select(m.User.phone))
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
def test_google_apple_auth(full_db: Session, client: TestClient):
    db = full_db
    users_before: int | None = db.scalar(sa.select(sa.func.count(m.User.id)))
    assert users_before is not None

    new_user_auth: s.GoogleAuth = s.GoogleAuth(
        email="new_email@gmail.com",
        first_name="new-first-name",
        last_name="new-last-name",
        uid="new_google_id",
    )
    response = client.post("/api/auth/google", json=new_user_auth.model_dump())
    assert response.status_code == status.HTTP_403_FORBIDDEN  # TODO: implement google auth

    # users_after: int | None = db.scalar(sa.select(sa.func.count(m.User.id)))
    # assert users_after is not None
    # assert users_after == users_before + 1

    # token = s.Token.model_validate(response.json())
    # assert token.access_token and token.token_type == "bearer"
    # header = dict(Authorization=f"Bearer {token.access_token}")
    # res = client.get("api/users/me", headers=header)
    # assert res.status_code == status.HTTP_200_OK

    # # apple auth with the same data
    # users_before = db.scalar(sa.select(sa.func.count(m.User.id)))
    # assert users_before is not None

    # response = client.post("/api/auth/apple", json=new_user_auth.model_dump())
    # assert response.status_code == status.HTTP_200_OK

    # users_after = db.scalar(sa.select(sa.func.count(m.User.id)))
    # assert users_after == users_before

    # token = s.Token.model_validate(response.json())
    # assert token.access_token and token.token_type == "bearer"
    # header = dict(Authorization=f"Bearer {token.access_token}")
    # res = client.get("api/users/me", headers=header)
    # assert res.status_code == status.HTTP_200_OK
