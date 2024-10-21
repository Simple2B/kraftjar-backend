import os

import requests
import sqlalchemy as sa
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicket,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError
from sqlalchemy.orm import Session as DbSession

# Optionally providing an access token within a session if you have enabled push security
from app import models as m
from app import schema as s
from app.logger import log
from config import config

CFG = config()
session = requests.Session()
session.headers.update(
    {
        "Authorization": f"Bearer {os.getenv('EXPO_TOKEN')}",
        "accept": "application/json",
        "accept-encoding": "gzip, deflate",
        "content-type": "application/json",
    }
)


def send_push_notification(notification: m.PushNotification) -> None:
    try:
        responses: list[PushTicket] = PushClient(session=session).publish_multiple(
            [
                PushMessage(
                    to=device.push_token,
                    body=notification.content,
                    title=notification.title,
                    data=notification.meta_data,
                    priority="high",
                    channel_id="default",
                    sound="default",
                )
                for device in notification.sent_to
            ]
        )
    except PushServerError as exc:
        # Encountered some likely formatting/validation error.
        log(log.ERROR, "[send_push_notification] PushServerError: %s", exc)
    except (ConnectionError, HTTPError) as exc:
        log(log.ERROR, "[send_push_notification] ConnectionError or HTTPError: %s", exc)
    for response in responses:
        try:
            # We got a response back, but we don't know whether it's an error yet.
            # This call raises errors so we can handle them with normal exception
            # flows.
            response.validate_response()

        except DeviceNotRegisteredError as exc:
            # Mark the push token as inactive
            log(log.WARNING, "[send_push_notification] DeviceNotRegisteredError: %s", exc)
        except PushTicketError as exc:
            # Encountered some other per-notification error.
            log(log.ERROR, "[send_push_notification] PushTicketError: %s", exc)


def create_new_job_notification(db: DbSession, job: m.Job) -> m.PushNotification:
    notification = m.PushNotification(
        title="New job available",
        content=f"A new job '{job.title}' is available, check it out!",
        n_type=s.PushNotificationType.job_created.value,
        created_by_id=job.owner_id,
        meta_data="",
        job=job,
    )
    db.add(notification)

    #  get all users whose id is not equal to job owner id and job.location is locations of user

    users = db.scalars(
        sa.select(m.User).join(m.User.locations).filter(m.User.id != job.owner_id, m.Location.id == job.location_id)
    ).all()

    for user in users:
        notification.sent_to.extend(user.active_devices)
    db.commit()

    return notification


def send_created_job_notification(db: DbSession, job: m.Job) -> None:
    notification = create_new_job_notification(db, job)
    send_push_notification(notification)


def notification_is_read_by_user(notification: m.PushNotification, user: m.User) -> bool:
    return user in notification.read_by
