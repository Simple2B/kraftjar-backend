import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa

from app import schema as s
from app import models as m
from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_services(client: TestClient, headers: list[dict[str, str]], test_data: TestData, db: Session):
    SERVICE_NUMBER = 10
    response = client.get("/api/services", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    services = s.ServiceList.model_validate(response.json())
    assert services.services and len(services.services) == SERVICE_NUMBER

    service: m.Service | None = db.scalar(sa.select(m.Service))
    assert service
    service.is_deleted = True
    db.commit()
    response = client.get("/api/services", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    services = s.ServiceList.model_validate(response.json())
    assert services.services and len(services.services) == SERVICE_NUMBER - 1
