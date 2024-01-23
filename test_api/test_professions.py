import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa

from api.utility import create_professions
from app import schema as s
from app import models as m
from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_professions(client: TestClient, headers: list[dict[str, str]], test_data: TestData, db: Session):
    PROFESSION_NUMBER = 10
    create_professions(db, PROFESSION_NUMBER)
    response = client.get("/api/professions", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    professions = s.ProfessionList.model_validate(response.json())
    assert professions.professions and len(professions.professions) == PROFESSION_NUMBER

    profession: m.Profession | None = db.scalar(sa.select(m.Profession))
    assert profession
    profession.is_deleted = True
    db.commit()
    response = client.get("/api/professions", headers=headers[0])
    assert response.status_code == status.HTTP_200_OK
    professions = s.ProfessionList.model_validate(response.json())
    assert professions.professions and len(professions.professions) == PROFESSION_NUMBER - 1
