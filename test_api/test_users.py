from typing import Sequence

import pytest
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_me(client: TestClient, headers: list[dict[str, str]], test_data: TestData):
    response = client.get("/api/users/me", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    user = s.User.model_validate(response.json())
    assert user.first_name == test_data.test_users[0].first_name


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_users(client: TestClient, headers: list[dict[str, str]], test_data: TestData, full_db: Session):
    db: Session = full_db

    users_with_services: Sequence[m.User] = db.scalars(sa.select(m.User)).all()
    users_with_services = [
        users_with_services[3],
        users_with_services[7],
        users_with_services[8],
        users_with_services[10],
        users_with_services[11],
        users_with_services[12],
    ]
    services: Sequence[m.Service] = db.scalars(sa.select(m.Service)).all()
    data: s.UserFilters = s.UserFilters(
        services=[services[0].uuid, services[1].uuid],
    )
    response = client.post("/api/users/", headers=headers[0], json=data.model_dump())
    assert response.status_code == status.HTTP_200_OK
    users = s.UserList.model_validate(response.json())
    assert len(users.users) == len(users_with_services)
    for user in users.users:
        assert user.id in [u.id for u in users_with_services]
