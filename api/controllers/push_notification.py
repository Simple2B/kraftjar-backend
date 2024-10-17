import json

import firebase_admin
import sqlalchemy as sa
from firebase_admin import credentials, messaging
from firebase_admin.exceptions import FirebaseError
from sqlalchemy.orm import Session

from app import models as m
from app import schema as s
from app.logger import log
from config import config

CFG = config()


def init_firebase() -> bool:
    try:
        cred = credentials.Certificate("admin_key.json")
        firebase_admin.initialize_app(cred)
        return True
    except ValueError as e:
        log(
            log.ERROR, "Firebase initialization error: %s", e
        )  # just log for now, implement proper error handling if needed
        return False


def send_push_notification(notification: m.PushNotification) -> None:
    try:
        init_firebase()

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=notification.title, body=notification.content),
            tokens=notification.device_tokens,
        )
        message.data = notification.data

        response: messaging.BatchResponse = messaging.send_each_for_multicast(message)

        if not response.success_count:
            log(log.WARNING, "[send_push_notification] Failed to send notification: %s", response)
            return

        log(log.INFO, "[send_push_notification] Notification sent: %s", response)
    except ValueError as e:
        log(log.ERROR, "[send_push_notification] Wrong notification args: %s", e)
    except FirebaseError as e:
        log(log.ERROR, "[send_push_notification] Firebase error: %s", e)


def create_new_job_notification(db: Session, job: m.Job) -> m.PushNotification:
    metadata = {"job_id": job.id}
    notification = m.PushNotification(
        title="New job available",
        content="A new job is available, check it out!",
        n_type=s.PushNotificationType.job_created.value,
        created_by_id=job.owner_id,
        metadata=json.dumps(metadata),
    )
    db.add(notification)

    #  get all users whose id is not equal to job owner id and job.location is locations of user

    users = db.scalars(
        sa.select(m.User).join(m.User.locations).filter(m.User.id != job.owner_id, m.Location.id == job.location_id)
    ).all()

    for user in users:
        notification.sent_to.extend(user.devices)
    db.commit()

    return notification


def send_created_job_notification(db: Session, job: m.Job) -> None:
    notification = create_new_job_notification(db, job)
    send_push_notification(notification)
