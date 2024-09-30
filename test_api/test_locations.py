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


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_addresses(client: TestClient, auth_header: dict[str, str], full_db: Session):
    # Test get settlements
    QUERY = "Воловець"
    response = client.get(
        "/api/locations/settlements", params={"lang": s.Language.UA.value, "query": QUERY}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    settlement_data = s.SettlementsListOut.model_validate(response.json())
    assert settlement_data
    settlement = settlement_data.settlements[0]
    assert settlement.uuid
    assert f"м. {QUERY}" in settlement.location

    # Test not found
    response = client.get(
        "/api/locations/settlements", params={"lang": s.Language.UA.value, "query": "Test"}, headers=auth_header
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Test get streets by settlement uuid
    address = full_db.scalars(sa.select(m.Address).where(m.Address.city_id == settlement.uuid)).first()
    assert address

    QUERY = "Водна"
    query_data = s.AddressIn(uuid=address.city_id, query=QUERY, lang=Language.UA)
    response = client.get(
        "/api/locations/addresses",
        params={"query": query_data.query, "uuid": query_data.uuid, "lang": query_data.lang.value},
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK
    address_data = s.AddressesListOut.model_validate(response.json())
    assert address_data
    assert address_data.addresses[0].uuid
    assert address_data.addresses[0].name == f"вул. {query_data.query}"

    # Test not found
    query_data = s.AddressIn(uuid=address.city_id, query="Test", lang=Language.UA)
    response = client.get(
        "/api/locations/addresses",
        params={"query": query_data.query, "uuid": query_data.uuid, "lang": query_data.lang.value},
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
