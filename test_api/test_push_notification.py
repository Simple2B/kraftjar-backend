import sqlalchemy as sa
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient


from app import models as m, schema as s

from api.controllers.push_notification import create_new_job_notification


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


def test_get_my_push_notifications(client: TestClient, db: Session, auth_header: dict[str, str]):
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
