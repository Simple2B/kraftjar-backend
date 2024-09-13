import pytest

from datetime import datetime, UTC, timedelta
import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
from config import config

CFG = config()


# @pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
# def test_get_jobs(client: TestClient, full_db: Session, auth_header: dict[str, str]):
#     db = full_db
#     job = db.scalar(sa.select(m.Job))
#     assert job

#     job.worker_id = None  # type: ignore
#     job.status = s.JobStatus.PENDING  # type: ignore
#     job.is_public = True
#     db.commit()

#     query = s.JobHomePage(
#         location_uuid=job.location.uuid,
#     )
#     response = client.post("/api/jobs/home", headers=auth_header, json=query.model_dump())
#     assert response.status_code == status.HTTP_200_OK
#     jobs = s.JobsCardList.model_validate(response.json())
#     assert len(jobs.recommended_jobs) > 0


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_job(client: TestClient, db: Session, auth_header: dict[str, str]):
    # db = full_db
    user = db.scalar(sa.select(m.User))
    assert user

    service = db.scalar(sa.select(m.Service))
    assert service

    location = db.scalar(sa.select(m.Location))
    assert location

    new_job = s.JobIn(
        service_uuid=service.uuid,
        title="Test Job",
        description="Test Description",
        location_uuid=location.uuid,
        start_date="2024-09-13T15:23:20.911Z",
        end_date="2024-09-13T15:23:25.960Z",
    )

    response = client.post("/api/jobs", headers=auth_header, json=new_job.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    job = s.JobOut.model_validate(response.json())
    assert job
    assert job.title == new_job.title
    assert job.description == new_job.description
