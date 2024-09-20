import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa

from app import schema as s
from app import models as m
from app.schema.language import Language
from config import config


CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_locations(client: TestClient, full_db: Session):
    db = full_db
    response = client.post("/api/locations", json=s.LocationsIn(lang=CFG.UA, selected=[]).model_dump())
    assert response.status_code == status.HTTP_200_OK
    res = s.LocationsOut.model_validate(response.json())
    locations = res.locations
    assert locations

    db_regions = db.scalars(sa.select(m.Region).where(m.Region.is_deleted == sa.false())).all()
    assert len(db_regions) == len(locations)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_address(
    client: TestClient,
    db: Session,
    auth_header: dict[str, str],
):
    QUERY = "Воловець"
    response = client.get(
        "/api/locations/address", params={"lang": s.Language.UA.value, "query": QUERY}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()
    res = response.json()

    response_out: list[s.CityAddresse] = [s.CityAddresse.model_validate(city_adresse) for city_adresse in res]
    assert response_out
    assert response_out[0].city_addresses
    assert response_out[0].uuid
    assert QUERY in response_out[0].city_addresses
    assert QUERY in response_out[1].city_addresses

    response = client.get(
        "/api/locations/address", params={"lang": s.Language.UA.value, "query": ""}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_all_locations(client: TestClient, full_db: Session):
    db = full_db

    query_data = s.LocationsListIn(lang=Language.UA)

    response = client.get(f"/api/locations/all?lang={query_data.lang.value}")
    assert response.status_code == status.HTTP_200_OK

    data = s.LocationsListOut.model_validate(response.json())
    assert data.locations

    db_locations = db.scalars(sa.select(m.Location)).all()
    assert db_locations
    assert len(data.locations) == len(db_locations)
