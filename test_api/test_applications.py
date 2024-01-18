from typing import Generator

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.utility import create_applications, create_job, create_jobs
from app import models as m
from app import schema as s
from config import config

from .test_data import TestData

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_applications(
    client: TestClient, test_data: TestData, db: Session, headers_gen: Generator[dict[str, str], None, None]
):
    headers: dict[str, str] = next(headers_gen)
    create_jobs(db, is_pending=True)
    create_applications(db)
    response = client.get("/api/applications", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    applications: s.ApplicationOutList = s.ApplicationOutList.model_validate(response.json())
    assert applications

    response = client.get(f"/api/applications/{applications.data[0].id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    application: s.ApplicationOut = s.ApplicationOut.model_validate(response.json())
    assert application.job_id == applications.data[0].job_id

    second_user: int = 2
    job: m.Job = create_job(db, second_user, is_pending=True)
    application_data: s.ApplicationIn = s.ApplicationIn(job_id=job.id, type=m.ApplicationType.APPLY.value, worker_id=1)
    len_before: int = len(applications.data)

    response = client.post("/api/applications", json=application_data.model_dump(mode="json"), headers=headers)

    assert response.status_code == status.HTTP_201_CREATED
    application = s.ApplicationOut.model_validate(response.json())
    assert application.job_id == application_data.job_id and application.type == application_data.type

    response = client.get("/api/applications", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    applications: s.ApplicationOutList = s.ApplicationOutList.model_validate(response.json())
    assert applications
    len_after: int = len(applications.data)
    assert len_after == len_before + 1

    application_put_data = s.ApplicationPut(
        status=m.ApplicationStatus.REJECTED,
    )
    headers = next(headers_gen)
    response = client.put(
        f"/api/applications/{application.id}", json=application_put_data.model_dump(mode="json"), headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    new_application = s.ApplicationOut.model_validate(response.json())
    assert new_application.status == application_put_data.status and new_application.job_id == application.job_id
