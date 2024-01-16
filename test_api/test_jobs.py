import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.utility import create_jobs
from app import schema as s
from config import config

from .test_data import TestData

CFG = config("testing")


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_jobs(client: TestClient, headers: dict[str, str], test_data: TestData, db: Session):
    create_jobs(db)
    response = client.get("/api/jobs")
    assert response.status_code == status.HTTP_200_OK
    jobs = s.JobOutList.model_validate(response.json())
    assert jobs

    response = client.get(f"/api/jobs/{jobs.jobs[0].id}")
    assert response.status_code == status.HTTP_200_OK
    job = s.JobOut.model_validate(response.json())
    assert job.title == jobs.jobs[0].title
