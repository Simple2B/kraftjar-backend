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
def test_get_services(client: TestClient, full_db: Session):
    db = full_db
    query = s.ServicesIn(lang="ua")
    response = client.post("/api/services", json=query.model_dump())
    assert response.status_code == status.HTTP_200_OK
    res = s.ServicesOut.model_validate(response.json())
    assert res.services
    assert not res.selected

    main_services = db.scalars(sa.select(m.Service).where(m.Service.parent_id.is_(None))).all()
    assert len(main_services) == len(res.services)
    uuids = [s.uuid for s in main_services]
    for service in res.services:
        assert service.uuid in uuids

    first_service = main_services[0]
    # select first service
    query = s.ServicesIn(lang="ua", selected=[first_service.uuid])
    response = client.post("/api/services", json=query.model_dump())
    assert response.status_code == status.HTTP_200_OK
    res = s.ServicesOut.model_validate(response.json())
    assert res.services
    assert res.selected
    assert len(res.selected) == 1
    assert res.selected[0] == first_service.uuid
    uuids = [s.uuid for s in res.services]
    children_uuids = [s.uuid for s in first_service.children]
    for uuid in children_uuids:
        assert uuid in uuids
