from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import sqlalchemy as sa

from api.dependency.user import get_current_user
from app.database import get_db
from app import models as m, schema as s
from api import controllers as c

push_notification_router = APIRouter(prefix="/push_notifications", tags=["push_notifications"])


@push_notification_router.get("/", status_code=status.HTTP_200_OK, response_model=list[s.PushNotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    notifications = db.scalars(
        sa.select(m.PushNotification).where(
            sa.and_(
                m.PushNotification.is_deleted.is_(False),
                m.PushNotification.sent_to.any(m.Device.user_id == current_user.id),
            )
        )
    )
    return [
        s.PushNotificationOut(
            uuid=notification.uuid,
            job_uuid=notification.job.uuid,
            n_type=s.PushNotificationType(notification.n_type),
            job_title=notification.job.title,
            read_by_me=c.notification_is_read_by_user(notification, current_user),
        )
        for notification in notifications
    ]