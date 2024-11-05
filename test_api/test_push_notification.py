import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient


from app import models as m, schema as s

from api.controllers.push_notification import (
    create_invite_application_notification,
    create_job_confirmed_notification,
    create_job_finished_notification,
    create_job_started_notification,
    create_new_job_notification,
    create_apply_application_notification,
    create_accepted_application_notification,
    create_rejected_application_notification,
)
from config import config


CFG = config()


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_new_job_notification(db: Session):
    users = db.query(m.User).all()
    for user in users:
        device = m.Device(
            push_token=f"test_token_user_{user.id}",
            device_id=f"test_device_user_{user.id}",
            user=user,
            platform=s.DevicePlatform.ANDROID.value,
        )
        user.devices.append(device)
    db.commit()
    job = db.scalar(sa.select(m.Job))
    assert job
    notification = create_new_job_notification(db, job)
    assert notification.n_type == s.PushNotificationType.job_created.value
    assert len(notification.sent_to)
    sent_to_user_ids = [user.id for user in notification.sent_to]
    assert job.owner_id not in sent_to_user_ids
    assert notification.data["job_uuid"] == str(job.uuid)
    assert notification.data["original_uuid"] == str(notification.uuid)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_get_my_push_notifications(
    client: TestClient,
    db: Session,
    auth_header: dict[str, str],
):
    user = db.scalar(sa.select(m.User))
    assert user
    job = db.scalar(sa.select(m.Job))
    assert job
    device = m.Device(
        push_token="test_token",
        device_id="test_device",
        user=user,
    )
    db.add(device)
    user.devices.append(device)
    notification = m.PushNotification(
        title="Test",
        content="Test content",
        n_type=s.PushNotificationType.job_created.value,
        created_by_id=user.id,
        job_id=job.id,
        meta_data="",
    )
    db.add(notification)
    notification.sent_to.append(device)
    db.commit()

    response = client.get("/api/push_notifications", headers=auth_header)
    assert response.status_code == 200
    notifications = [s.PushNotificationOut.model_validate(notif) for notif in response.json()]

    assert len(notifications) == 1
    assert notifications[0].uuid == notification.uuid


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_mark_notification_as_read(client: TestClient, db: Session, auth_header: dict[str, str]):
    user = db.scalar(sa.select(m.User))
    assert user
    job = db.scalar(sa.select(m.Job))
    assert job
    device = m.Device(
        push_token="test_token",
        device_id="test_device",
        user=user,
    )
    db.add(device)
    user.devices.append(device)
    notification = m.PushNotification(
        title="Test",
        content="Test content",
        n_type=s.PushNotificationType.job_created.value,
        created_by_id=user.id,
        job_id=job.id,
        meta_data="",
    )
    db.add(notification)
    notification.sent_to.append(device)
    db.commit()

    response = client.put(f"/api/push_notifications/{notification.uuid}/read", headers=auth_header)
    assert response.status_code == 200
    notification_res = s.PushNotificationOut.model_validate(response.json())
    assert notification_res.read_by_me

    response = client.put(f"/api/push_notifications/{notification.uuid}/read", headers=auth_header)
    assert response.status_code == 200
    notification_res = s.PushNotificationOut.model_validate(response.json())
    assert notification_res.read_by_me


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_apply_application_notification(
    db: Session,
):
    job = db.scalar(
        sa.select(m.Job).where(
            sa.and_(m.Job.worker_id.is_(None), m.Job.status == s.JobStatus.PENDING.value),
            m.Job.owner_id == 1,
        )
    )
    assert job

    device = m.Device(
        push_token=f"test_token_user_{job.owner.id}",
        device_id=f"test_device_user_{job.owner.id}",
        user=job.owner,
        platform=s.DevicePlatform.ANDROID.value,
    )
    job.owner.devices.append(device)

    worker = db.scalar(sa.select(m.User).where(m.User.id == 2))
    assert worker

    notification = create_apply_application_notification(
        db,
        job,
        worker,
    )
    assert notification.n_type == s.PushNotificationType.application_created.value
    assert notification.sent_to  # owner
    assert notification.data["job_uuid"] == str(job.uuid)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_invite_application_notification(
    db: Session,
):
    job = db.scalar(
        sa.select(m.Job).where(
            sa.and_(m.Job.worker_id.is_(None), m.Job.status == s.JobStatus.PENDING.value),
            m.Job.owner_id == 1,
        )
    )
    assert job

    worker = db.scalar(sa.select(m.User).where(m.User.id == 2))
    assert worker

    device = m.Device(
        push_token=f"test_token_user_{job.owner.id}",
        device_id=f"test_device_user_{job.owner.id}",
        user=worker,
        platform=s.DevicePlatform.ANDROID.value,
    )
    worker.devices.append(device)

    notification = create_invite_application_notification(
        db,
        job,
        job.owner,
        worker,
    )
    assert notification.n_type == s.PushNotificationType.job_invite_created.value
    assert notification.sent_to  # worker
    assert notification.data["job_uuid"] == str(job.uuid)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_accepted_application_and_job_management_notifications(
    client: TestClient,
    worker_header: dict[str, str],
    auth_header: dict[str, str],
    db: Session,
):
    job = db.scalar(
        sa.select(m.Job).where(
            sa.and_(
                m.Job.status == s.JobStatus.PENDING.value,
                m.Job.owner_id == 1,
            )
        ),
    )
    assert job

    worker = db.scalar(sa.select(m.User).where(m.User.id == 2))
    assert worker

    # Create application
    app_data = s.ApplicationIn(
        type=m.ApplicationType.APPLY,
        worker_uuid=worker.uuid,
        job_uuid=job.uuid,
    )
    response = client.post(
        "/api/applications",
        headers=worker_header,
        content=app_data.model_dump_json(),
    )
    assert response.status_code == 201

    # Accept application
    app = s.ApplicationOut.model_validate(response.json())
    assert app

    response = client.put(
        f"/api/applications/{app.uuid}",
        headers=auth_header,
        content=s.ApplicationPutIn(status=m.ApplicationStatus.ACCEPTED).model_dump_json(),
    )
    assert response.status_code == 200

    device = m.Device(
        push_token=f"test_token_user_{job.worker.id}",
        device_id=f"test_device_user_{job.worker.id}",
        user=job.worker,
        platform=s.DevicePlatform.ANDROID.value,
    )
    job.worker.devices.append(device)

    worker = db.scalar(sa.select(m.User).where(m.User.id == 2))
    assert worker

    notification = create_accepted_application_notification(
        db,
        job,
    )
    assert notification.n_type == s.PushNotificationType.application_accepted.value
    assert len(notification.sent_to)  # worker
    assert notification.data["job_uuid"] == str(job.uuid)
    assert notification.data["original_uuid"] == str(notification.uuid)

    # Start job
    response = client.put(
        f"/api/jobs/{job.uuid}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate(
            {"status": s.JobStatus.IN_PROGRESS},
        ).model_dump_json(),
    )
    assert response.status_code == 200

    device = m.Device(
        push_token=f"test_token_user_{job.owner.id}",
        device_id=f"test_device_user_{job.owner.id}",
        user=job.owner,
        platform=s.DevicePlatform.ANDROID.value,
    )
    job.owner.devices.append(device)

    notification_2 = create_job_started_notification(job)
    assert notification_2.n_type == s.PushNotificationType.job_started.value
    assert len(notification.sent_to)  # owner
    assert notification.data["job_uuid"] == str(job.uuid)

    # Finished job
    response = client.put(
        f"/api/jobs/{job.uuid}/status",
        headers=worker_header,
        content=s.JobStatusIn.model_validate(
            {"status": s.JobStatus.ON_CONFIRMATION},
        ).model_dump_json(),
    )
    assert response.status_code == 200

    notification_3 = create_job_finished_notification(job)
    assert notification_3.n_type == s.PushNotificationType.job_finished.value
    assert len(notification.sent_to)  # owner
    assert notification.data["job_uuid"] == str(job.uuid)

    # Confirm job
    response = client.put(
        f"/api/jobs/{job.uuid}/status",
        headers=auth_header,
        content=s.JobStatusIn.model_validate(
            {"status": s.JobStatus.COMPLETED},
        ).model_dump_json(),
    )
    assert response.status_code == 200
    notification_4 = create_job_confirmed_notification(job)
    assert notification_4.n_type == s.PushNotificationType.job_confirmed.value
    assert len(notification.sent_to)  # worker
    assert notification.data["job_uuid"] == str(job.uuid)


@pytest.mark.skipif(not CFG.IS_API, reason="API is not enabled")
def test_create_rejected_application_notification(
    client: TestClient,
    worker_header: dict[str, str],
    auth_header: dict[str, str],
    db: Session,
):
    job = db.scalar(
        sa.select(m.Job).where(
            sa.and_(
                m.Job.status == s.JobStatus.PENDING.value,
                m.Job.owner_id == 1,
            )
        ),
    )
    assert job

    worker = db.scalar(sa.select(m.User).where(m.User.id == 2))
    assert worker

    # Create application 1
    app_data = s.ApplicationIn(
        type=m.ApplicationType.APPLY,
        worker_uuid=worker.uuid,
        job_uuid=job.uuid,
    )
    response = client.post(
        "/api/applications",
        headers=worker_header,
        content=app_data.model_dump_json(),
    )
    assert response.status_code == 201

    app = s.ApplicationOut.model_validate(response.json())
    assert app

    # check app in db
    app_db = db.scalar(
        sa.select(m.Application).where(
            m.Application.id == app.id,
        )
    )
    assert app_db

    device = m.Device(
        push_token=f"test_token_user_{app.worker_id}",
        device_id=f"test_device_user_{app.worker_id}",
        user=job.owner,
        platform=s.DevicePlatform.ANDROID.value,
    )
    worker.devices.append(device)

    # owner reject application
    response = client.put(
        f"/api/applications/{app_db.uuid}",
        headers=auth_header,
        content=s.ApplicationPutIn(status=m.ApplicationStatus.REJECTED).model_dump_json(),
    )
    assert response.status_code == 200

    notification = create_rejected_application_notification(
        db,
        job,
        rejected_applications=[app_db],
    )
    assert notification.n_type == s.PushNotificationType.application_rejected.value
    assert len(notification.sent_to)  # workers
    assert notification.data["job_uuid"] == str(job.uuid)
    assert notification.data["original_uuid"] == str(notification.uuid)
