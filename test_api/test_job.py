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
def test_get_jobs(client: TestClient, full_db: Session, auth_header: dict[str, str]):
    db = full_db
    job = db.scalar(sa.select(m.Job))
    assert job

    job.worker_id = None  # type: ignore
    job.status = s.JobStatus.PENDING  # type: ignore
    job.is_public = True
    db.commit()

    query = s.JobHomePage(
        location_uuid=job.location.uuid,
    )
    response = client.post("/api/jobs/home", headers=auth_header, json=query.model_dump())
    assert response.status_code == status.HTTP_200_OK
    jobs = s.JobsCardList.model_validate(response.json())
    assert len(jobs.recommended_jobs) > 0
