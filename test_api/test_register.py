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
def test_register(full_db: Session, client: TestClient, test_data: TestData):
    db = full_db

    LOCATIONS_NUM = 3
    locations = db.scalars(sa.select(m.Location).limit(LOCATIONS_NUM)).all()
    assert locations

    SERVICES_NUM = 3
    services = db.scalars(sa.select(m.Service).limit(SERVICES_NUM)).all()
    assert services

    USER = test_data.test_users[0]
    USER.phone = "1234567890"
    USER.email = "test_user@kraftjar.net"
    user_data = s.RegistrationIn(
        fullname=USER.first_name + " " + USER.last_name,
        phone=USER.phone,
        email=USER.email,
        password=USER.password,
        services=[s.uuid for s in services],
        locations=[loc.uuid for loc in locations],
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    assert token.access_token and token.token_type == "bearer"
    header = dict(Authorization=f"Bearer {token.access_token}")
    res = client.get("api/users/me", headers=header)
    assert res.status_code == status.HTTP_200_OK

    # Try to register again with the same email
    USER = test_data.test_users[0]
    USER.phone = "999999999"
    user_data = s.RegistrationIn(
        fullname=USER.first_name + " " + USER.last_name,
        phone=USER.phone,
        email=USER.email,
        password=USER.password,
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_409_CONFLICT

    # Try to register again with the same phone
    USER = test_data.test_users[1]
    USER.email = "new_email@new.york.post.org"
    user_data = s.RegistrationIn(
        fullname=USER.first_name + " " + USER.last_name,
        phone=USER.phone,
        email=USER.email,
        password=USER.password,
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_phone_validation(full_db: Session, client: TestClient, test_data: TestData, headers: list[dict[str, str]]):
    db = full_db

    USER = test_data.test_users[0]
    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.email == USER.email))
    assert db_user

    assert not db_user.phone_verified
    phone: str = USER.phone.replace("0", "1")
    data: s.SetPhoneIn = s.SetPhoneIn(phone=phone)
    response = client.post("/api/registration/set-phone", json=data.model_dump(), headers=headers[0])

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() is None

    assert db_user.phone == phone

    data_validate: s.ValidatePhoneIn = s.ValidatePhoneIn(code="1234")
    response = client.post("/api/registration/validate-phone", json=data_validate.model_dump(), headers=headers[0])
    assert response.status_code == status.HTTP_200_OK

    assert db_user.phone_verified
    db.commit()
