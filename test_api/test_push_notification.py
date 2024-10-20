import sqlalchemy as sa
from sqlalchemy.orm import Session

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
    assert notification.data["job_id"] == str(job.id)
    assert notification.data["original_id"] == str(notification.id)
