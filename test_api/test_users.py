from typing import Sequence
import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest import mock

from app import models as m
from app import schema as s
from app.schema.language import Language
from config import config
from test_api.test_auth import DUMMY_GOOGLE_VALIDATION, DUMMY_IOS_VALIDATION

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_user(client: TestClient, auth_header: dict[str, str], full_db: Session):
    db: Session = full_db

    USER_PHONE = db.scalar(sa.select(m.User.phone).where(m.User.id == 1))
    response = client.get("/api/users/me", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    me_user: s.User = s.User.model_validate(response.json())
    assert me_user.phone == USER_PHONE

    search_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == 1))
    assert search_user

    response = client.get(f"/api/users/{search_user.uuid}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK

    user: s.UserProfileOut = s.UserProfileOut.model_validate(response.json())
    assert user.id == search_user.id
    assert user.fullname == search_user.fullname
    assert user.average_rate == search_user.average_rate
    assert user.services[0].name == search_user.services[0].name_ua

    response = client.get(f"/api/users/{search_user.uuid}?lang={Language.EN.value}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK

    user = s.UserProfileOut.model_validate(response.json())
    assert user.id == search_user.id
    assert user.services[0].name == search_user.services[0].name_en


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_users(client: TestClient, auth_header: dict[str, str], full_db: Session):
    db: Session = full_db

    users_with_services: Sequence[m.User] = db.scalars(sa.select(m.User)).all()
    users_with_services = [
        users_with_services[0],
        users_with_services[1],
        users_with_services[3],
        users_with_services[5],
        users_with_services[9],
    ]
    locations: Sequence[m.Location] = db.scalars(sa.select(m.Location)).all()
    query_data: s.UserSearchIn = s.UserSearchIn(
        selected_locations=[locations[0].uuid, locations[1].uuid],
        lang=Language.UA,
    )

    response = client.post("/api/users/search", headers=auth_header, content=query_data.model_dump_json())
    assert response.status_code == status.HTTP_200_OK

    data: s.UsersSearchOut = s.UsersSearchOut.model_validate(response.json())
    assert len(data.top_users) == len(users_with_services)
    assert len(data.top_users) == len(set(data.top_users))

    for i in range(len(data.top_users) - 1):
        assert (
            data.top_users[i].average_rate >= data.top_users[i + 1].average_rate
        ), f"User rates are not decreasing at index {i}"
    for loc in data.user_locations:
        assert loc not in data.locations
    assert not data.near_users

    query_data = s.UserSearchIn(
        selected_locations=[locations[0].uuid, locations[1].uuid],
        query="Домашній майстер",
        lang=Language.UA,
    )

    response = client.post("/api/users/search", headers=auth_header, content=query_data.model_dump_json())
    assert response.status_code == status.HTTP_200_OK

    data = s.UsersSearchOut.model_validate(response.json())
    assert data

    query_data = s.UserSearchIn(
        selected_locations=[CFG.ALL_UKRAINE],
        lang=Language.UA,
    )

    response = client.post("/api/users/search", headers=auth_header, content=query_data.model_dump_json())
    assert response.status_code == status.HTTP_200_OK

    data = s.UsersSearchOut.model_validate(response.json())
    assert len(data.top_users) == 5

    for user in data.near_users:
        assert data.user_locations[0] in user.locations

    assert any([any([loc not in data.user_locations for loc in user.locations]) for user in data.top_users])

    query_data = s.UserSearchIn(query="Сантехнік", lang=Language.UA)
    response = client.post("/api/users/search", headers=auth_header, content=query_data.model_dump_json())
    assert response.status_code == status.HTTP_200_OK

    data = s.UsersSearchOut.model_validate(response.json())

    assert data


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_google_account(monkeypatch, client: TestClient, auth_header: dict[str, str]):
    mock_verify_oauth2_token = mock.Mock(return_value=DUMMY_GOOGLE_VALIDATION)
    monkeypatch.setattr("api.routes.user.id_token.verify_oauth2_token", mock_verify_oauth2_token)

    data = s.GoogleAuthIn(id_token="test_token")

    response = client.post("/api/users/register-google-account", headers=auth_header, json=data.model_dump())
    assert response.status_code == status.HTTP_201_CREATED

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


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_apple_account(monkeypatch, client: TestClient, auth_header: dict[str, str]):
    mock_verify_apple_token = mock.Mock(return_value=DUMMY_IOS_VALIDATION)
    monkeypatch.setattr("api.routes.user.c.verify_apple_token", mock_verify_apple_token)

    data = s.AppleAuthTokenIn(id_token="test_token")

    response = client.post("/api/users/register-apple-account", headers=auth_header, json=data.model_dump())
    assert response.status_code == status.HTTP_201_CREATED

    # Test login
    response = client.post("/api/auth/apple", json=data.model_dump())
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_delete_auth_account(client: TestClient, auth_header: dict[str, str], full_db: Session):
    AUTH_ACCOUNT_ID = 1

    auth_account = full_db.scalar(sa.select(m.AuthAccount).where(m.AuthAccount.id == AUTH_ACCOUNT_ID))
    assert auth_account

    response = client.delete(f"/api/users/auth-account/{auth_account.id}", headers=auth_header)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    auth_account = full_db.scalar(sa.select(m.AuthAccount).where(m.AuthAccount.id == auth_account.id))
    assert auth_account
    assert auth_account.is_deleted is True
