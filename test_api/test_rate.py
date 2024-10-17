import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sqlalchemy as sa
from sqlalchemy import select

from app import models as m
from app import schema as s
from config import config

CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_rate(client: TestClient, auth_header: dict[str, str], full_db: Session):
    current_user = full_db.scalar(select(m.User).where(m.User.id == 1))
    assert current_user

    current_user_job = full_db.scalar(select(m.Job).where(m.Job.owner_id == current_user.id))
    assert current_user_job

    job_worker = full_db.scalar(select(m.User).where(m.User.id == current_user_job.worker_id))
    assert job_worker

    data: s.RateIn = s.RateIn(
        rate=5,
        review="Good job",
        job_uuid=current_user_job.uuid,
        receiver_uuid=job_worker.uuid,
    )

    # Create rate for job worker
    response = client.post("/api/rates", headers=auth_header, content=data.model_dump_json())
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["rate"] == data.rate
    assert response.json()["review"] == data.review
    assert response.json()["job"]["uuid"] == data.job_uuid
    assert response.json()["receiver"]["uuid"] == data.receiver_uuid
    assert response.json()["giver"]["uuid"] == current_user.uuid
    rate_1_uuid = response.json()["uuid"]
    assert rate_1_uuid

    # get rate 1 by uuid
    response = client.get(f"/api/rates/{rate_1_uuid}", headers=auth_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == rate_1_uuid

    # Create authorized header for job owner
    authorized_header: dict[str, str] = {}

    response = client.post(
        "/api/auth/login",
        data={
            "username": job_worker.phone,
            "password": CFG.TEST_USER_PASSWORD,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    token = s.Token.model_validate(response.json())
    authorized_header["Authorization"] = f"Bearer {token.access_token}"

    # Create rate for job owner
    data_2: s.RateIn = s.RateIn(
        rate=4,
        review="So so job",
        job_uuid=current_user_job.uuid,
        receiver_uuid=current_user.uuid,
    )

    response_2 = client.post("/api/rates", headers=authorized_header, content=data_2.model_dump_json())
    assert response_2.status_code == status.HTTP_201_CREATED
    assert response_2.json()["rate"] == data_2.rate
    assert response_2.json()["receiver"]["uuid"] == current_user.uuid
    rate_2_uuid = response_2.json()["uuid"]
    assert rate_2_uuid

    # get rate 2 by uuid
    response = client.get(f"/api/rates/{rate_2_uuid}", headers=authorized_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == rate_2_uuid

    db_rates_current_user = (
        full_db.execute(
            select(m.Rate).where(sa.or_(m.Rate.receiver_id == current_user.id, m.Rate.gives_id == current_user.id))
        )
        .scalars()
        .all()
    )
    assert db_rates_current_user
    db_rates_current_user_uuids = [rate.uuid for rate in db_rates_current_user]
    assert rate_1_uuid in db_rates_current_user_uuids

    # Get rates for job owner
    response_3 = client.get("/api/rates", headers=auth_header)
    assert response_3.status_code == status.HTTP_200_OK
    assert len(response_3.json()) == len(db_rates_current_user)

    db_rates_worker = (
        full_db.execute(
            select(m.Rate).where(sa.or_(m.Rate.receiver_id == job_worker.id, m.Rate.gives_id == job_worker.id))
        )
        .scalars()
        .all()
    )
    assert db_rates_worker

    response_4 = client.get("/api/rates", headers=authorized_header)
    assert response_4.status_code == status.HTTP_200_OK
    assert len(response_4.json()) == len(db_rates_worker)
