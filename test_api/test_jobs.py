import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.utility import create_jobs
from app import models as m
from app import schema as s
from config import config

from .test_data import TestData

CFG = config("testing")


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_jobs(client: TestClient, headers: dict[str, str], test_data: TestData, db: Session):
    create_jobs(db)
    response = client.get("/api/jobs")
    assert response.status_code == status.HTTP_200_OK
    jobs = s.JobOutList.model_validate(response.json())
    assert jobs

    response = client.get(f"/api/jobs/{jobs.jobs[0].id}")
    assert response.status_code == status.HTTP_200_OK
    job = s.JobOut.model_validate(response.json())
    assert job.title == jobs.jobs[0].title

    job_data: s.JobIn = s.JobIn(
        title="Test Job",
        description="Test Description",
        address_id=1,
        location_id=1,
        time="2024-01-01 00:00:00",
        is_public=True,
    )
    len_before = len(jobs.jobs)
    response = client.post("/api/jobs", json=job_data.model_dump(), headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    job = s.JobOut.model_validate(response.json())
    assert job.title == job_data.title and job.location_id == job_data.location_id
    len_after = len(db.scalars(select(m.Job)).all())
    assert len_after == len_before + 1

    job_put_data = s.JobPut(
        title="Test Job",
    )
    response = client.put(f"/api/jobs/{job.id}", json=job_put_data.model_dump(), headers=headers)
    assert response.status_code == status.HTTP_200_OK
    new_job = s.JobOut.model_validate(response.json())
    assert new_job.title == job_put_data.title and new_job.description == job.description
