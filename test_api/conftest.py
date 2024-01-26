from typing import Generator
import pytest
from fastapi import status
from dotenv import load_dotenv

load_dotenv("test_api/test.env")

# ruff: noqa: F401 E402
from fastapi.testclient import TestClient
from sqlalchemy import orm

from app import models as m
from app import schema as s

from api import app
from .test_data import TestData


@pytest.fixture
def db(test_data: TestData) -> Generator[orm.Session, None, None]:
    from app.database import db, get_db

    with db.Session() as session:
        db.Model.metadata.drop_all(bind=session.bind)
        db.Model.metadata.create_all(bind=session.bind)
        for test_user in test_data.test_users:
            user = m.User(
                first_name=test_user.first_name,
                last_name=test_user.last_name,
                phone=test_user.phone,
                email=test_user.email,
                password=test_user.password,
            )
            session.add(user)
        session.commit()

        def override_get_db() -> Generator:
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session
        # clean up
        db.Model.metadata.drop_all(bind=session.bind)


@pytest.fixture
def full_db(db: orm.Session) -> Generator[orm.Session, None, None]:
    from app.commands.service import export_services_from_json_file
    from app.commands.locations import export_regions_from_json_file

    export_services_from_json_file(with_print=False)
    export_regions_from_json_file(with_print=False)
    yield db


@pytest.fixture
def client(db) -> Generator[TestClient, None, None]:
    """Returns a non-authorized test client for the API"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_data() -> Generator[TestData, None, None]:
    """Returns a TestData object"""
    with open("test_api/test_data.json", "r") as f:
        yield TestData.model_validate_json(f.read())


@pytest.fixture
def headers(
    client: TestClient,
    test_data: TestData,
) -> Generator[list[dict[str, str]], None, None]:
    """Returns an authorized test client for the API"""
    users: list[dict[str, str]] = list()

    for user in test_data.test_users:
        response = client.post(
            "/api/auth/login",
            data={
                "username": user.phone,
                "password": user.password,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        token = s.Token.model_validate(response.json())
        users.append(dict(Authorization=f"Bearer {token.access_token}"))

    yield users
