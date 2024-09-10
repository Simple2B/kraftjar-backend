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
def test_register(db: Session, client: TestClient):
    LOCATIONS_NUM = 3
    locations = db.scalars(sa.select(m.Location).limit(LOCATIONS_NUM)).all()
    assert locations

    SERVICES_NUM = 3
    services = db.scalars(sa.select(m.Service).limit(SERVICES_NUM)).all()
    assert services

    USER_PHONE = "1234567890"
    USER_FNAME = "TestFName"
    USER_LNAME = "TestLName"
    USER_PASSWORD = "test_password"
    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.phone == USER_PHONE))
    if db_user:
        db.delete(db_user)
        db.commit()

    user_data = s.RegistrationIn(
        fullname=USER_FNAME + " " + USER_LNAME,
        phone=USER_PHONE,
        password=USER_PASSWORD,
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

    # Try to register again with the same phone
    USER_PHONE2 = USER_PHONE
    user_data = s.RegistrationIn(
        fullname=USER_FNAME + " " + USER_LNAME,
        phone=USER_PHONE2,
        password=USER_PASSWORD,
    )
    response = client.post("/api/registration/", json=user_data.model_dump())
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_phone_validation(db: Session, client: TestClient, auth_header: dict[str, str]):
    db_user: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == 1))
    assert db_user

    db_user.phone_verified = False
    db.commit()

    NEW_USER_PHONE = "777777777777"
    user: m.User | None = db.scalar(sa.select(m.User).where(m.User.phone == NEW_USER_PHONE))
    if user:
        user.phone = "12345678901"
        db.commit()

    data: s.SetPhoneIn = s.SetPhoneIn(phone=NEW_USER_PHONE)
    response = client.post("/api/registration/set-phone", json=data.model_dump(), headers=auth_header)

    assert response.status_code == status.HTTP_201_CREATED
    assert db_user.phone == NEW_USER_PHONE

    data_validate: s.ValidatePhoneIn = s.ValidatePhoneIn(code="1234")
    response = client.post("/api/registration/validate-phone", json=data_validate.model_dump(), headers=auth_header)
    assert response.status_code == status.HTTP_200_OK

    assert db_user.phone_verified

    response = client.get("api/registration/set-otp", headers=auth_header)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    db.commit()
