from typing import Sequence

import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_me(client: TestClient, auth_header: dict[str, str], full_db: Session):
    db: Session = full_db

    USER_PHONE = db.scalar(sa.select(m.User.phone).where(m.User.id == 1))
    response = client.get("/api/users/me", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    user = s.User.model_validate(response.json())
    assert user.phone == USER_PHONE


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
        users_with_services[10],
        users_with_services[31],
        users_with_services[36],
        users_with_services[43],
        users_with_services[50],
    ]
    locations: Sequence[m.Location] = db.scalars(sa.select(m.Location)).all()
    query_data: s.UserSearchIn = s.UserSearchIn(
        selected_locations=[locations[0].uuid, locations[1].uuid],
    )
    response = client.post("/api/users/search", headers=auth_header, json=query_data.model_dump())
    assert response.status_code == status.HTTP_200_OK
    users = s.UsersSearchOut.model_validate(response.json())
    assert len(users.top_users) == len(users_with_services)
    for i in range(len(users.top_users) - 1):
        assert (
            users.top_users[i].owned_rates_median >= users.top_users[i + 1].owned_rates_median
        ), f"User rates are not decreasing at index {i}"
