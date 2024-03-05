from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi import status

load_dotenv("test_api/test.env")

# ruff: noqa: F401 E402
from fastapi.testclient import TestClient
from sqlalchemy import orm, select

from api import app
from app import models as m
from app import schema as s
from config import config

CFG = config()


@pytest.fixture
def db() -> Generator[orm.Session, None, None]:
    from app.database import db, get_db

    with db.Session() as session:
        # TODO: use already prepared sqlite3 db file
        db.Model.metadata.drop_all(bind=session.bind)
        db.Model.metadata.create_all(bind=session.bind)

        from app.commands.addresses import export_addresses_from_json_file
        from app.commands.job import export_jobs_from_json_file
        from app.commands.locations import export_regions_from_json_file
        from app.commands.service import export_services_from_json_file
        from app.commands.user import export_users_from_json_file

        export_services_from_json_file(with_print=False)
        export_regions_from_json_file(with_print=False)
        export_users_from_json_file(with_print=False, max_user_limit=30)
        export_addresses_from_json_file(with_print=False)
        export_jobs_from_json_file(max_job_limit=30)

        def override_get_db() -> Generator:
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session
        # clean up
        db.Model.metadata.drop_all(bind=session.bind)


@pytest.fixture
def full_db(db: orm.Session) -> Generator[orm.Session, None, None]:
    yield db


@pytest.fixture
def client(db) -> Generator[TestClient, None, None]:
    """Returns a non-authorized test client for the API"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_header(
    client: TestClient,
    db: orm.Session,
) -> Generator[dict[str, str], None, None]:
    """Returns an authorized test client for the API"""
    authorized_header: dict[str, str] = {}
    user = db.scalar(select(m.User).where(m.User.id == 1))
    assert user

    response = client.post(
        "/api/auth/login",
        data={
            "username": user.phone,
            "password": CFG.TEST_USER_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    authorized_header["Authorization"] = f"Bearer {token.access_token}"

    yield authorized_header
