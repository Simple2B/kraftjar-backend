from mypy_boto3_s3 import S3Client
import pytest

import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from api import app
from api.dependency.user import get_current_user
from app import models as m
from app import schema as s
from app.schema.language import Language
from config import config

CFG = config()


# TODO: must be refactoring like search users
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
#         lang=CFG.UA,
#         location_uuid=job.location.uuid,
#     )
#     response = client.post("/api/jobs/home", headers=auth_header, json=query.model_dump())
#     assert response.status_code == status.HTTP_200_OK
#     jobs = s.JobsCardList.model_validate(response.json())
#     assert len(jobs.recommended_jobs) > 0


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_job(
    client: TestClient,
    db: Session,
    auth_header: dict[str, str],
    s3_client: S3Client,
):
    with open("test_api/test_data/image_1.jpg", "rb") as image:
        response = client.post(
            "/api/jobs/files",
            headers=auth_header,
            files={"files": ("image_1.jpg", image, "image/npg")},
        )
        assert response.status_code == 201

        files_out: list[str] = [uuid for uuid in response.json()]
        assert files_out
    image_1_uuid = files_out[0]

    with open("test_api/test_data/image_2.png", "rb") as image:
        response = client.post(
            "/api/jobs/files",
            headers=auth_header,
            files={"files": ("image_2.jpg", image, "image/npg")},
        )

        assert response.status_code == 201
    image_2 = [uuid for uuid in response.json()]

    with open("test_api/test_data/image_2.png", "rb") as image:
        response = client.post(
            "/api/jobs/files",
            headers=auth_header,
            files={"files": ("image_3.jpg", image, "image/npg")},
        )
        assert response.status_code == 201
        assert response.json()
        files_out_3 = [uuid for uuid in response.json()]

    # delete image_3
    response = client.delete(f"/api/jobs/file/{files_out_3[0]}", headers=auth_header)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    user = db.scalar(sa.select(m.User))
    assert user

    service = db.scalar(sa.select(m.Service))
    assert service

    sattlement = db.scalar(sa.select(m.Settlement))
    assert sattlement

    address = db.scalar(sa.select(m.Address))
    assert address

    new_job = s.JobIn(
        service_uuid=service.uuid,
        title="Test Job",
        description="Test Description",
        settlement_uuid=sattlement.city_id,
        address_uuid=address.street_id,
        start_date="2024-09-13T15:23:20.911Z",
        end_date="2024-09-13T15:23:25.960Z",
        file_uuids=[image_1_uuid, image_2[0]],
    )

    response = client.post("/api/jobs", headers=auth_header, json=new_job.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    job = s.JobOut.model_validate(response.json())
    assert job
    assert job.title == new_job.title
    assert job.description == new_job.description
    assert job.location_id == sattlement.location_id
    assert job.owner_id == user.id
    assert job.files[0].uuid == image_1_uuid
    assert job.files[1].uuid == image_2[0]

    # Get job
    response = client.get(f"/api/jobs/{job.uuid}")
    assert response.status_code == status.HTTP_200_OK
    job_data = s.JobInfo.model_validate(response.json())
    assert job_data
    assert job_data.uuid == job.uuid

    # Another user should see the job in the main list
    mock_current_user = db.scalar(sa.select(m.User).where(m.User.id == 5))
    assert mock_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    query_data = s.JobsIn(query=job.title)
    response = client.get(
        "/api/jobs", params={"query": query_data.query, "selected_locations": ["all-ukraine"]}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsOut.model_validate(response.json())
    assert data.items[0].title == job.title

    # reset user dependency
    app.dependency_overrides[get_current_user] = get_current_user

    # Delete job
    response = client.delete(f"/api/jobs/{job.uuid}", headers=auth_header)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    deleted_job = db.scalar(sa.select(m.Job).where(m.Job.uuid == job.uuid))
    assert deleted_job
    assert deleted_job.is_deleted


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_jobs_by_query_params(client: TestClient, auth_header: dict[str, str], db: Session):
    # Житомирська, Львівська
    LOCATIONS = ["7", "14"]

    locations = db.execute(sa.select(m.Location).where(m.Location.id.in_(LOCATIONS))).scalars().all()
    assert locations
    locations_uuid = [loc.uuid for loc in locations]

    # Test query only
    query_data = s.JobsIn(query=" Ремонт ")
    response = client.get(f"/api/jobs?query={query_data.query}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsOut.model_validate(response.json())
    assert len(data.items) > 0

    # Test UA
    query_data = s.JobsIn(query="Сантехнік", lang=Language.UA, selected_locations=locations_uuid)
    response = client.get(
        f"/api/jobs?query={query_data.query}&lang={query_data.lang.value}&selected_locations={query_data.selected_locations[0]}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK
    data_ua = s.JobsOut.model_validate(response.json())
    assert len(data_ua.items) > 0

    # Test EN
    query_data = s.JobsIn(query="Plumber", lang=Language.EN, selected_locations=locations_uuid)
    response = client.get(
        f"/api/jobs?query={query_data.query}&lang={query_data.lang.value}&selected_locations={query_data.selected_locations[0]}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK
    data_en = s.JobsOut.model_validate(response.json())
    assert len(data_en.items) > 0
    assert len(data_en.items) == len(data_ua.items)

    # Test locations
    query_data = s.JobsIn(selected_locations=locations_uuid)
    response = client.get(
        f"/api/jobs?selected_locations={query_data.selected_locations[0]}&selected_locations={query_data.selected_locations[1]}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsOut.model_validate(response.json())
    assert len(data.items) > 0

    # All Ukraine
    query_data = s.JobsIn(selected_locations=locations_uuid)
    response = client.get(f"/api/jobs?selected_locations={CFG.ALL_UKRAINE}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsOut.model_validate(response.json())
    assert len(data.items) > 0

    # No query params
    response = client.get("/api/jobs", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    no_params_data = s.JobsOut.model_validate(response.json())
    assert len(no_params_data.items) > 0

    # Empty query with spaces
    response = client.get(f"/api/jobs?query={'   '}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsOut.model_validate(response.json())
    assert len(data.items) > 0
    assert len(data.items) == len(no_params_data.items)

    # All params
    query_data = s.JobsIn(
        query="Сантехнік",
        lang=Language.UA,
        selected_locations=locations_uuid,
        order_by=s.JobsOrderBy.COST,
        ascending=False,
    )
    response = client.get(
        f"/api/jobs?query={query_data.query}&lang={query_data.lang.value}&selected_locations={query_data.selected_locations[0]}&selected_locations={query_data.selected_locations[1]}&ascending={query_data.ascending}&order_by={query_data.order_by.value}",
        headers=auth_header,
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsOut.model_validate(response.json())
    assert len(data.items) > 0

    # Test no results
    query_data = s.JobsIn(query="Тест")
    response = client.get(f"/api/jobs?query={query_data.query}", headers=auth_header)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_jobs_by_status(client: TestClient, auth_header: dict[str, str], db: Session):
    job: m.Job | None = db.scalar(
        sa.select(m.Job).where(m.Job.worker_id.is_(None), m.Job.status == s.JobStatus.PENDING.value)
    )
    assert job

    # Create application
    app_data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=1, job_id=job.id)
    response = client.post("/api/applications", headers=auth_header, content=app_data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED

    # Test pending jobs
    response = client.get(
        "/api/jobs/jobs-by-status/", params={"job_status": s.JobStatus.PENDING.value}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsByStatusList.model_validate(response.json())
    assert data.owner
    assert data.worker
    assert not data.archived

    # Test in progress jobs
    response = client.get(
        "/api/jobs/jobs-by-status/", params={"job_status": s.JobStatus.IN_PROGRESS.value}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsByStatusList.model_validate(response.json())
    assert data.owner
    assert data.worker
    assert not data.archived

    # Test confirmaion jobs (not completed yet == in progress)
    response = client.get(
        "/api/jobs/jobs-by-status/", params={"job_status": s.JobStatus.ON_CONFIRMATION.value}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsByStatusList.model_validate(response.json())
    assert data.owner
    assert data.worker
    assert not data.archived

    # Test archived jobs
    response = client.get(
        "/api/jobs/jobs-by-status/", params={"job_status": s.JobStatus.CANCELED.value}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsByStatusList.model_validate(response.json())
    assert not data.owner
    assert not data.worker
    assert data.archived

    response = client.get(
        "/api/jobs/jobs-by-status/", params={"job_status": s.JobStatus.COMPLETED.value}, headers=auth_header
    )
    assert response.status_code == status.HTTP_200_OK
    data = s.JobsByStatusList.model_validate(response.json())
    assert not data.owner
    assert not data.worker
    assert data.archived


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_update_jobs_status(
    client: TestClient, auth_header: dict[str, str], worker_header: dict[str, str], db: Session
):
    service = db.scalar(sa.select(m.Service))

    if service is None:
        raise ValueError("Service not found")

    job_in = s.JobIn(
        service_uuid=service.uuid,
        title="Job2",
        description="job description",
    )
    res = client.post("/api/jobs", headers=auth_header, content=job_in.model_dump_json())
    assert res.status_code == status.HTTP_201_CREATED

    job = s.JobOut.model_validate(res.json())

    # Create application
    app_data = s.ApplicationIn(type=m.ApplicationType.APPLY, worker_id=2, job_id=job.id)
    response = client.post("/api/applications", headers=worker_header, content=app_data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED

    # Accept application
    app = s.ApplicationOut.model_validate(response.json())
    assert app

    response = client.put(
        f"/api/applications/{app.id}",
        headers=auth_header,
        content=s.ApplicationPutIn(status=m.ApplicationStatus.ACCEPTED).model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Check false statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.ON_CONFIRMATION}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.COMPLETED}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Check false users
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.IN_PROGRESS}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Check correct statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.IN_PROGRESS}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Check false statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.COMPLETED}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Check false users
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.ON_CONFIRMATION}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Check correct statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.ON_CONFIRMATION}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Check false users
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.COMPLETED}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    # Check correct statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.COMPLETED}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Check false statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.IN_PROGRESS}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.CANCELED}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_200_OK

    # Check false statuses
    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.PENDING}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = client.put(
        f"/api/jobs/{job.id}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate({"status": s.JobStatus.IN_PROGRESS}).model_dump_json(),
    )
    assert response.status_code == status.HTTP_409_CONFLICT
