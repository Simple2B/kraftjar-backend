from mypy_boto3_s3 import S3Client
import pytest

import sqlalchemy as sa
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
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

        assert response.json()[0]["original_name"] == "image_1.jpg"
    image_1_uuid = response.json()[0]["uuid"]

    with open("test_api/test_data/image_2.png", "rb") as image:
        response = client.post(
            "/api/jobs/files",
            headers=auth_header,
            files={"files": ("image_2.jpg", image, "image/npg")},
        )
        assert response.status_code == 201

        assert response.json()[0]["original_name"] == "image_2.jpg"
    image_2_uuid = response.json()[0]["uuid"]

    with open("test_api/test_data/image_2.png", "rb") as image:
        response = client.post(
            "/api/jobs/files",
            headers=auth_header,
            files={"files": ("image_3.jpg", image, "image/npg")},
        )
        assert response.status_code == 201

        assert response.json()[0]["original_name"] == "image_3.jpg"
    image_3_uuid = response.json()[0]["uuid"]

    # delete image_3
    response = client.delete(f"/api/jobs/file/{image_3_uuid}", headers=auth_header)
    assert response.status_code == status.HTTP_204_NO_CONTENT

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
        file_uuids=[image_1_uuid, image_2_uuid],
    )

    response = client.post("/api/jobs", headers=auth_header, json=new_job.model_dump())
    assert response.status_code == status.HTTP_201_CREATED
    job = s.JobOut.model_validate(response.json())
    assert job
    assert job.title == new_job.title
    assert job.description == new_job.description
    assert job.location_id == location.id
    assert job.owner_id == user.id
    assert job.files[0].uuid == image_1_uuid
    assert job.files[1].uuid == image_2_uuid
