from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi import status
from sqlalchemy import event

load_dotenv("test_api/test.env")

# ruff: noqa: F401 E402
import os

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, orm, select

from api import app
from app import models as m
from app import schema as s
from config import config

CFG = config()


@pytest.fixture
def db() -> Generator[orm.Session, None, None]:
    from app.database import db, get_db

    db_file = "database-test.sqlite3"

    if not os.path.exists(db_file):
        with db.Session() as session:
            db.Model.metadata.create_all(bind=session.bind)

            from app.commands.addresses import export_addresses_from_json_file
            from app.commands.locations import export_regions_from_json_file
            from app.commands.service import export_services_from_json_file
            from app.commands.user import export_users_from_json_file

            export_services_from_json_file(with_print=False)
            export_regions_from_json_file(with_print=False)
            export_users_from_json_file(with_print=False)
            export_addresses_from_json_file(with_print=False)

            def override_get_db() -> Generator:
                yield session

            app.dependency_overrides[get_db] = override_get_db
            yield session
    else:
        engine = create_engine(f"sqlite:///{db_file}")
        SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

        @event.listens_for(engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            dbapi_connection.create_function("lower", 1, lambda arg: arg.lower())

        with SessionLocal() as session:

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
