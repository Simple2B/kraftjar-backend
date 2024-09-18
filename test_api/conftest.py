from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi import status

from mypy_boto3_s3 import S3Client
from moto import mock_aws

load_dotenv("test_api/test.env")

# ruff: noqa: F401 E402
import os

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
        db.Model.metadata.create_all(bind=session.bind)

        from app.commands.locations import export_test_locations_from_json_file
        from app.commands.addresses import export_addresses_from_json_file
        from app.commands.cities import export_cities_from_json_file
        from app.commands.locations import export_regions_from_json_file
        from app.commands.service import export_services_from_json_file
        from app.commands.user import export_users_from_json_file
        from app.commands.job import export_jobs_from_json_file

        export_test_locations_from_json_file(with_print=False)
        export_services_from_json_file(with_print=False)
        export_regions_from_json_file(with_print=False)
        export_users_from_json_file(with_print=False, max_user_limit=10)
        export_cities_from_json_file(with_print=False)
        export_addresses_from_json_file(with_print=False)
        export_jobs_from_json_file(max_job_limit=10)

        def override_get_db() -> Generator:
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session

        # Clean up
        db.Model.metadata.drop_all(bind=session.bind)


@pytest.fixture
def full_db(db: orm.Session) -> Generator[orm.Session, None, None]:
    yield db


@pytest.fixture
def s3_client() -> Generator[S3Client, None, None]:
    """Returns a mock S3 client"""

    with mock_aws():
        from api.dependency.s3_client import get_s3_connect
        from config import config

        CFG = config()

        client = get_s3_connect()
        client.create_bucket(
            Bucket=CFG.AWS_S3_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": CFG.AWS_REGION},  # type: ignore
        )

        yield client


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
