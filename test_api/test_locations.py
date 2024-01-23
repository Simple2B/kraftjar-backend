import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa

from api.utility import create_locations
from app import schema as s
from app import models as m
from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_locations(client: TestClient, headers: list[dict[str, str]], test_data: TestData, db: Session):
    LOCATION_NUMBER = 10
    create_locations(db, LOCATION_NUMBER)
    response = client.get("/api/locations", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    locations = s.LocationList.model_validate(response.json())
    assert locations.locations and len(locations.locations) == LOCATION_NUMBER

    location: m.Location | None = db.scalar(sa.select(m.Location))
    assert location
    location.is_deleted = True
    db.commit()
    response = client.get("/api/locations", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    locations = s.LocationList.model_validate(response.json())
    assert locations.locations and len(locations.locations) == LOCATION_NUMBER - 1
