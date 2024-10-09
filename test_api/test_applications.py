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
    USERS_TEST_COUNT = 3
    workers_list = db.scalars(sa.select(m.User).where(m.User.is_deleted.is_(False))).all()[:USERS_TEST_COUNT]
    assert len(workers_list) == USERS_TEST_COUNT

    main_worker = workers_list[0]

    job: m.Job | None = db.scalar(
        sa.select(m.Job).where(m.Job.worker_id.is_(None), m.Job.status == s.JobStatus.PENDING.value)
    )
    assert job

    # current_user == main worker
    mock_current_user = db.scalar(sa.select(m.User).where(m.User.id == main_worker.id))
    assert mock_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    # worker can't invite himself
    data = s.ApplicationIn(type=m.ApplicationType.INVITE, worker_id=main_worker.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # owner can't apply to his job
    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=job.owner_id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Create application
    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=main_worker.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    application_data = s.ApplicationOut.model_validate(response.json())
    assert application_data

    # Get application
    response = client.get(f"/api/applications/{application_data.id}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    app_data_out = s.ApplicationOut.model_validate(response.json())
    assert app_data_out
    assert app_data_out.id == application_data.id

    # Another users apply to the same job
    another_worker_one: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == workers_list[1].id))
    assert another_worker_one

    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=another_worker_one.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    another_app = s.ApplicationOut.model_validate(response.json())
    assert another_app

    another_worker_two: m.User | None = db.scalar(sa.select(m.User).where(m.User.id == workers_list[2].id))
    assert another_worker_two

    data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=another_worker_two.id, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    another_app = s.ApplicationOut.model_validate(response.json())
    assert another_app

    # Get applications list
    response = client.get(f"/api/applications?job_id={job.id}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    app_list_out = s.ApplicationOutList.model_validate(response.json())
    assert app_list_out
    assert len(app_list_out.data) == len(workers_list)

    # Update application with status ACCEPTED
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

    # Another applications should be rejected
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

    # Delete application
    # current_user == worker
    mock_current_user = db.scalar(sa.select(m.User).where(m.User.id == application_data.worker_id))
    assert mock_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = client.delete(f"/api/applications/{application_data.id}", headers=auth_header)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    deleted_app = db.scalar(sa.select(m.Application).where(m.Application.id == application_data.id))
    assert deleted_app
    assert deleted_app.is_deleted

    # reset user dependency
    app.dependency_overrides[get_current_user] = get_current_user
