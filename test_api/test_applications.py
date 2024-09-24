import pytest

import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.dependency.user import get_current_user
from app import models as m
from app import schema as s
from api import app
from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_applications(client: TestClient, auth_header: dict[str, str], db: Session):
    worker: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == 1))
    assert worker

    job: m.Job | None = db.scalar(
        sa.select(m.Job).where(m.Job.worker_id == worker.id, m.Job.status == s.JobStatus.PENDING.value)
    )
    assert job

    # worker can't invite himself
    data = s.ApplicationIn(type=m.ApplicationType.INVITE, worker_id=worker.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # owner can't apply to his job
    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=job.owner_id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # create application
    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=worker.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    application_data = s.ApplicationOut.model_validate(response.json())
    assert application_data

    # Another users apply to the same job
    another_worker_one: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == 2))
    assert another_worker_one

    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=another_worker_one.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    application_data = s.ApplicationOut.model_validate(response.json())
    assert application_data

    another_worker_two: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == 3))
    assert another_worker_two

    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=another_worker_two.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    application_data = s.ApplicationOut.model_validate(response.json())
    assert application_data

    # update application with status ACCEPTED
    # current_user == job owner
    mock_current_user = db.scalar(sa.select(m.User).where(m.User.id == job.owner_id))
    assert mock_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    data_put = s.ApplicationPutIn(status=m.ApplicationStatus.ACCEPTED)
    response = client.put(
        f"/api/applications/{application_data.id}", headers=auth_header, content=data_put.model_dump_json()
    )
    assert response.status_code == status.HTTP_200_OK
    data_out = s.ApplicationPutOut.model_validate(response.json())
    assert data_out
    data_app = data_out.application
    assert data_app.status == m.ApplicationStatus.ACCEPTED

    # another applications should be rejected
    another_job_applications = db.scalars(
        sa.select(m.Application).where(m.Application.job_id == data_app.job_id, m.Application.id != data_app.id)
    ).all()
    assert another_job_applications
    for application in another_job_applications:
        assert application.status == m.ApplicationStatus.REJECTED

    # accepted job should be in progress
    job = db.scalar(sa.select(m.Job).where(m.Job.id == data_app.job_id))
    assert job
    assert job.status == s.JobStatus.IN_PROGRESS.value

    # update application with status REJECTED after ACCEPTED (should fail)
    # current_user == job owner
    mock_current_user = db.scalar(sa.select(m.User).where(m.User.id == job.owner_id))
    assert mock_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    data_put = s.ApplicationPutIn(status=m.ApplicationStatus.REJECTED)
    response = client.put(
        f"/api/applications/{application_data.id}", headers=auth_header, content=data_put.model_dump_json()
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
