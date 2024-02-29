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
def test_get_jobs(client: TestClient, full_db: Session, auth_header: dict[str, str]):
    db = full_db
    user: m.User | None = db.scalar(sa.select(m.User))
    assert user
    query = s.JobHomePage(
        location_uuid=user.locations[0].uuid,
    )
    response = client.post("/api/jobs/home", headers=auth_header, json=query.model_dump())
    assert response.status_code == status.HTTP_200_OK
    # jobs = s.JobsCardList.parse_obj(response.json())
    # assert len(jobs.recommended_jobs) > 0
