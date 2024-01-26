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
def test_get_locations(client: TestClient, full_db: Session):
    db = full_db
    response = client.post("/api/locations", json=s.LocationsIn(lang="ua", selected=[]).model_dump())
    assert response.status_code == status.HTTP_200_OK
    res = s.LocationsOut.model_validate(response.json())
    locations = res.locations
    assert locations

    db_regions = db.scalars(sa.select(m.Region).where(m.Region.is_deleted == sa.false())).all()
    assert len(db_regions) == len(locations)
