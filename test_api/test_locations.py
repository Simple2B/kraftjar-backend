import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa

from app import schema as s
from app import models as m
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
    response_out = [
        s.CityAddressesOut(
            city=s.City.model_validate(city_addresses_out["city"]),
            addresses=[s.AddressOut.model_validate(address) for address in city_addresses_out["addresses"]],
        )
        for city_addresses_out in res
    ]
    assert response_out
    assert response_out[0].city.name_ua == QUERY
    assert response_out[0].addresses
    assert response_out[0].city.city_id == response_out[0].addresses[0].city_id
    assert response_out[0].city.city_id == response_out[0].addresses[1].city_id
